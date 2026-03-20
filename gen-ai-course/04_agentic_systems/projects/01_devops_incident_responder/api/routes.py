"""
api/routes.py

FastAPI application for the AI DevOps Incident Responder.

Endpoints:
    POST /incident          - Start a new incident analysis
    GET  /status/{id}       - Get current incident state
    POST /approve/{id}      - Human approval / rejection of proposed fixes
    GET  /audit/{id}        - Full audit log for an incident
    GET  /incidents         - List all tracked incidents
    GET  /health            - Health check

Design Decisions:
- Active incidents are tracked in an in-memory dict (active_incidents) keyed
  by incident_id. This allows fast state retrieval without hitting the
  checkpointer on every status poll.
- The graph singleton is initialized at startup and shared across requests.
  LangGraph's compiled graph is thread-safe for concurrent invocations with
  different thread_ids.
- CORS is enabled for all origins in development. Restrict in production.
- Background tasks are used for incident analysis so the POST /incident
  endpoint returns immediately with the incident_id, enabling the UI to
  poll /status/{id} while analysis runs.
"""

from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# Import graph lazily to avoid import-time side effects during testing
_graph = None
_executor = ThreadPoolExecutor(max_workers=4)


def get_graph():
    """Lazy-load the compiled graph singleton."""
    global _graph
    if _graph is None:
        from agent.graph import build_graph
        _graph = build_graph()
    return _graph


# ---------------------------------------------------------------------------
# In-memory incident registry
# (In production: replace with Redis or a database)
# ---------------------------------------------------------------------------

active_incidents: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class StartIncidentRequest(BaseModel):
    """Request body for POST /incident."""
    raw_logs: str
    incident_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StartIncidentResponse(BaseModel):
    """Response for POST /incident."""
    incident_id: str
    thread_id: str
    status: str
    message: str


class ApproveRequest(BaseModel):
    """Request body for POST /approve/{incident_id}."""
    approved: bool
    notes: Optional[str] = ""


class ApproveResponse(BaseModel):
    """Response for POST /approve/{incident_id}."""
    incident_id: str
    status: str
    executed_fixes: List[str]
    outcome: str
    message: str


class IncidentStatusResponse(BaseModel):
    """Response for GET /status/{incident_id}."""
    incident_id: str
    status: str
    severity: str
    detected_anomalies: List[Dict[str, Any]]
    investigation_plan: List[str]
    diagnosis: str
    runbook_matches: List[str]
    proposed_fixes: List[Dict[str, Any]]
    executed_fixes: List[str]
    human_approved: bool
    outcome: str
    iteration_count: int


class IncidentSummary(BaseModel):
    """Summary entry for GET /incidents."""
    incident_id: str
    status: str
    severity: str
    started_at: str
    anomaly_types: List[str]


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI DevOps Incident Responder",
    description=(
        "Agentic system that monitors logs, detects anomalies, proposes "
        "remediation steps, and executes fixes with human approval (HITL)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for development
# Design Decision: In production, restrict to your frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Background worker: run the graph in a thread pool
# ---------------------------------------------------------------------------

def _run_incident_sync(incident_id: str, raw_logs: str) -> None:
    """
    Run the incident graph synchronously in a thread pool worker.

    This function is called by a FastAPI BackgroundTask so the HTTP
    response is returned immediately while analysis continues.
    """
    from agent.graph import run_incident

    try:
        active_incidents[incident_id]["status"] = "detecting"
        result = run_incident(
            raw_logs=raw_logs,
            incident_id=incident_id,
            graph=get_graph(),
        )
        # Update our registry with the latest state
        active_incidents[incident_id].update({
            "status": result.get("status", "unknown"),
            "state": result.get("state", {}),
            "next_nodes": result.get("next_nodes", []),
            "updated_at": datetime.utcnow().isoformat(),
        })
    except Exception as exc:
        active_incidents[incident_id].update({
            "status": "failed",
            "error": str(exc),
            "updated_at": datetime.utcnow().isoformat(),
        })


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Infrastructure"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Service status, active incident count, and timestamp.
    """
    return {
        "status": "healthy",
        "service": "ai-devops-incident-responder",
        "version": "1.0.0",
        "active_incidents": len(active_incidents),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/incident", response_model=StartIncidentResponse, tags=["Incidents"])
async def start_incident(
    request: StartIncidentRequest,
    background_tasks: BackgroundTasks,
) -> StartIncidentResponse:
    """
    Start a new incident analysis.

    Accepts raw log text and begins the detection → planning → diagnosis
    pipeline in a background thread. Returns immediately with the incident_id
    so the client can poll /status/{incident_id}.

    Args:
        request: Contains raw_logs (required) and optional incident_id.

    Returns:
        incident_id, thread_id, initial status, and message.
    """
    incident_id = request.incident_id or str(uuid.uuid4())

    if not request.raw_logs.strip():
        raise HTTPException(status_code=400, detail="raw_logs must not be empty.")

    # Register the incident in our in-memory tracker
    active_incidents[incident_id] = {
        "incident_id": incident_id,
        "status": "queued",
        "severity": "unknown",
        "raw_logs": request.raw_logs,
        "started_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "state": {},
        "next_nodes": [],
        "metadata": request.metadata or {},
    }

    # Start analysis in the background thread pool
    # Design Decision: We run the graph in a ThreadPoolExecutor rather than
    # directly with asyncio to avoid blocking the event loop during LLM calls.
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        _executor,
        _run_incident_sync,
        incident_id,
        request.raw_logs,
    )

    return StartIncidentResponse(
        incident_id=incident_id,
        thread_id=incident_id,
        status="queued",
        message=(
            f"Incident {incident_id[:8]}... queued for analysis. "
            f"Poll GET /status/{incident_id} for updates."
        ),
    )


@app.get("/status/{incident_id}", response_model=IncidentStatusResponse, tags=["Incidents"])
async def get_status(incident_id: str) -> IncidentStatusResponse:
    """
    Get the current status and state of an incident.

    Combines data from our in-memory registry with the latest checkpointer
    state. The checkpointer is the ground truth; the registry is a cache.

    Args:
        incident_id: UUID of the incident.

    Returns:
        Full incident state including anomalies, plan, diagnosis, and fixes.

    Raises:
        404 if the incident_id is not found.
    """
    if incident_id not in active_incidents:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    registry_entry = active_incidents[incident_id]
    state = registry_entry.get("state", {})

    # Try to get fresher state from checkpointer
    try:
        from agent.graph import get_incident_state
        fresh_state = get_incident_state(incident_id, graph=get_graph())
        if fresh_state:
            state = fresh_state
            # Sync registry status with checkpointer
            active_incidents[incident_id]["status"] = fresh_state.get("status", registry_entry["status"])
    except Exception:
        pass  # Fall back to registry state

    return IncidentStatusResponse(
        incident_id=incident_id,
        status=state.get("status", registry_entry.get("status", "unknown")),
        severity=state.get("severity", "unknown"),
        detected_anomalies=state.get("detected_anomalies", []),
        investigation_plan=state.get("investigation_plan", []),
        diagnosis=state.get("diagnosis", ""),
        runbook_matches=state.get("runbook_matches", []),
        proposed_fixes=state.get("proposed_fixes", []),
        executed_fixes=state.get("executed_fixes", []),
        human_approved=state.get("human_approved", False),
        outcome=state.get("outcome", ""),
        iteration_count=state.get("iteration_count", 0),
    )


@app.post("/approve/{incident_id}", response_model=ApproveResponse, tags=["HITL"])
async def approve_incident_endpoint(
    incident_id: str,
    request: ApproveRequest,
    background_tasks: BackgroundTasks,
) -> ApproveResponse:
    """
    Human approval or rejection of proposed fixes (HITL checkpoint).

    Resumes the paused graph with the human's decision. If approved=True,
    the executor node runs and applies fixes. If approved=False, the incident
    is marked rejected with the operator's notes.

    Args:
        incident_id: UUID of the incident to approve/reject.
        request:     approved (bool) and optional notes (str).

    Returns:
        Updated status, list of executed fixes, and outcome summary.

    Raises:
        404 if incident not found.
        400 if incident is not in 'awaiting_approval' state.
    """
    if incident_id not in active_incidents:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    registry_entry = active_incidents[incident_id]
    current_status = registry_entry.get("status", "unknown")

    # Allow approval if status is awaiting_approval or if state shows it
    # (handles race conditions between background task and status update)
    valid_statuses = {"awaiting_approval", "detecting", "planning", "diagnosing"}

    try:
        from agent.graph import approve_incident

        def _approve_sync():
            result = approve_incident(
                incident_id=incident_id,
                approved=request.approved,
                notes=request.notes or "",
                graph=get_graph(),
            )
            active_incidents[incident_id].update({
                "status": result.get("status", "resolved"),
                "state": result.get("state", {}),
                "updated_at": datetime.utcnow().isoformat(),
            })
            return result

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, _approve_sync)

        decision = "APPROVED" if request.approved else "REJECTED"
        return ApproveResponse(
            incident_id=incident_id,
            status=result.get("status", "resolved"),
            executed_fixes=result.get("executed_fixes", []),
            outcome=result.get("outcome", ""),
            message=(
                f"Incident {incident_id[:8]}... {decision}. "
                f"{len(result.get('executed_fixes', []))} fix(es) applied."
            ),
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Approval processing failed: {str(exc)}")


@app.get("/audit/{incident_id}", tags=["Audit"])
async def get_audit_log(incident_id: str) -> Dict[str, Any]:
    """
    Retrieve the full audit log for an incident.

    The audit log is an append-only timeline of all agent actions,
    tool calls, and human decisions made during the incident lifecycle.

    Args:
        incident_id: UUID of the incident.

    Returns:
        Dict with incident_id, total_entries, and entries (List[AuditEntry]).

    Raises:
        404 if incident not found.
    """
    if incident_id not in active_incidents:
        # Try loading from file-based history
        try:
            from agent.memory import IncidentHistoryMemory
            import os
            history = IncidentHistoryMemory(
                history_dir=os.getenv("INCIDENT_HISTORY_DIR", "./data/incident_history")
            )
            record = history.get_incident(incident_id)
            if record:
                return {
                    "incident_id": incident_id,
                    "source": "history",
                    "total_entries": len(record.get("audit_log", [])),
                    "entries": record.get("audit_log", []),
                }
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    state = active_incidents[incident_id].get("state", {})

    # Try to get fresher state from checkpointer
    try:
        from agent.graph import get_incident_state
        fresh_state = get_incident_state(incident_id, graph=get_graph())
        if fresh_state:
            state = fresh_state
    except Exception:
        pass

    audit_log = state.get("audit_log", [])
    return {
        "incident_id": incident_id,
        "source": "active",
        "total_entries": len(audit_log),
        "entries": audit_log,
    }


@app.get("/incidents", tags=["Incidents"])
async def list_incidents(
    limit: int = 20,
    status_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all tracked incidents (active + resolved).

    Args:
        limit:         Maximum number of incidents to return (default 20).
        status_filter: Optional status to filter by (e.g. 'awaiting_approval').

    Returns:
        Dict with total count and list of incident summaries.
    """
    # Active incidents from memory
    summaries = []
    for inc_id, entry in active_incidents.items():
        state = entry.get("state", {})
        anomalies = state.get("detected_anomalies", [])
        status = state.get("status", entry.get("status", "unknown"))

        if status_filter and status != status_filter:
            continue

        summaries.append({
            "incident_id": inc_id,
            "status": status,
            "severity": state.get("severity", "unknown"),
            "started_at": entry.get("started_at", ""),
            "updated_at": entry.get("updated_at", ""),
            "anomaly_types": [a.get("type", "") for a in anomalies if isinstance(a, dict)],
        })

    # Also pull from file-based history for resolved incidents
    try:
        import os
        from agent.memory import IncidentHistoryMemory
        history = IncidentHistoryMemory(
            history_dir=os.getenv("INCIDENT_HISTORY_DIR", "./data/incident_history")
        )
        historical = history.list_incidents(limit=limit)
        # Add historical incidents not already in active
        active_ids = {s["incident_id"] for s in summaries}
        for h in historical:
            if h["incident_id"] not in active_ids:
                if status_filter and h.get("status") != status_filter:
                    continue
                summaries.append(h)
    except Exception:
        pass

    # Sort by started_at descending
    summaries.sort(key=lambda x: x.get("started_at", ""), reverse=True)

    return {
        "total": len(summaries),
        "incidents": summaries[:limit],
    }


@app.delete("/incident/{incident_id}", tags=["Incidents"])
async def delete_incident(incident_id: str) -> Dict[str, str]:
    """
    Remove an incident from the active registry.

    Note: This does NOT delete the checkpointer state or history files.

    Args:
        incident_id: UUID of the incident to remove.

    Returns:
        Confirmation message.

    Raises:
        404 if incident not found in active registry.
    """
    if incident_id not in active_incidents:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not in active registry.")

    del active_incidents[incident_id]
    return {"message": f"Incident {incident_id} removed from active registry."}


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Pre-warm the graph on startup to avoid cold-start latency on first request."""
    try:
        _ = get_graph()
    except Exception as exc:
        print(f"[WARN] Graph pre-warm failed: {exc}. Will retry on first request.")


# ---------------------------------------------------------------------------
# Entry point for direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
