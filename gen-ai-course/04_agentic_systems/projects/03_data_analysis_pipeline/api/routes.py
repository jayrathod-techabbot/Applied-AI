"""
routes.py - FastAPI route definitions for the AI Data Analysis Pipeline API.

Design decisions:
- POST /analyze       accepts a multipart CSV upload, runs the full analysis
                      graph synchronously (background task fires and the client
                      polls), returns session_id immediately.
- POST /followup/{id} answers a follow-up question using cached session state.
- GET  /report/{id}   returns the stored markdown report.
- GET  /charts/{id}   returns the list of chart file paths for that session.
- GET  /health        liveness check for load balancers / Docker healthcheck.

WHY in-memory session store (not Redis):
  Sessions are keyed by UUID and hold the full AnalysisState. For a single-
  server deployment this is sufficient and avoids the operational overhead of
  a Redis cluster. A horizontal-scaling upgrade would replace `_sessions` with
  a Redis-backed store using the same dict-like interface.

WHY synchronous analysis in BackgroundTask:
  Analysis takes 20-120 seconds. Returning a session_id immediately and letting
  the client poll GET /report/{id} is more responsive than blocking the POST
  for two minutes. The BackgroundTask runs in the same process thread pool,
  which is fine for I/O-bound LLM calls.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Data Analysis Pipeline",
    description="Upload a CSV and get AI-powered data analysis, charts, and insights.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------

# WHY Dict[str, Dict]: each session stores the final LangGraph AnalysisState
# (which is itself a dict) plus metadata like status and file paths.
_sessions: Dict[str, Dict[str, Any]] = {}


def _get_session(session_id: str) -> Dict[str, Any]:
    """Retrieve a session or raise 404."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# Background analysis worker
# ---------------------------------------------------------------------------

def _run_analysis_bg(session_id: str, csv_path: str) -> None:
    """
    Execute the full analysis pipeline in a background thread.

    Updates _sessions[session_id] with status and results when done.
    Errors are caught and stored so the client can detect failures via polling.
    """
    try:
        from agent.graph import run_analysis
        _sessions[session_id]["status"] = "running"
        final_state = run_analysis(dataset_path=csv_path, session_id=session_id)
        _sessions[session_id]["status"] = "complete"
        _sessions[session_id]["state"] = final_state
        _sessions[session_id]["report"] = final_state.get("final_report", "")
        _sessions[session_id]["charts"] = [
            c.get("file_path", "") for c in final_state.get("charts", []) if c.get("file_path")
        ]
        _sessions[session_id]["analysis_plan"] = final_state.get("analysis_plan", [])
        _sessions[session_id]["dataset_summary"] = final_state.get("dataset_summary", {})
        _sessions[session_id]["reflection"] = final_state.get("reflection", {})
    except Exception as exc:
        _sessions[session_id]["status"] = "error"
        _sessions[session_id]["error"] = str(exc)
        _sessions[session_id]["traceback"] = traceback.format_exc(limit=10)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FollowUpRequest(BaseModel):
    question: str


class AnalyzeResponse(BaseModel):
    session_id: str
    status: str
    message: str


class FollowUpResponse(BaseModel):
    session_id: str
    question: str
    answer: str


class ReportResponse(BaseModel):
    session_id: str
    status: str
    report: Optional[str] = None
    analysis_plan: Optional[List[str]] = None
    reflection: Optional[Dict[str, Any]] = None
    dataset_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ChartsResponse(BaseModel):
    session_id: str
    charts: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    sessions_active: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Liveness check endpoint.

    Returns the API version and count of active sessions.
    Used by Docker HEALTHCHECK and load balancer probes.
    """
    return HealthResponse(
        status="ok",
        version="1.0.0",
        sessions_active=len(_sessions),
    )


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV file to analyse"),
    question: Optional[str] = Form(None, description="Optional initial question"),
) -> AnalyzeResponse:
    """
    Accept a CSV file upload and start the analysis pipeline.

    The analysis runs in a background thread. Poll GET /report/{session_id}
    to check status and retrieve the completed report.

    Returns a session_id immediately (status: "queued").
    """
    # Validate file type
    if not (file.filename or "").lower().endswith((".csv", ".tsv")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV or TSV files are supported.",
        )

    # Save upload to a temp directory that persists for the session lifetime
    session_id = str(uuid.uuid4())
    upload_dir = Path(tempfile.gettempdir()) / "data_pipeline" / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    csv_path = str(upload_dir / (file.filename or "dataset.csv"))

    try:
        contents = await file.read()
        with open(csv_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File save failed: {exc}")

    # Initialise session record
    _sessions[session_id] = {
        "status": "queued",
        "csv_path": csv_path,
        "state": None,
        "report": None,
        "charts": [],
        "analysis_plan": [],
        "dataset_summary": {},
        "reflection": {},
        "error": None,
        "initial_question": question,
    }

    # Launch background analysis
    background_tasks.add_task(_run_analysis_bg, session_id, csv_path)

    return AnalyzeResponse(
        session_id=session_id,
        status="queued",
        message=f"Analysis started. Poll GET /report/{session_id} for results.",
    )


@app.post("/followup/{session_id}", response_model=FollowUpResponse, tags=["Q&A"])
async def followup(session_id: str, request: FollowUpRequest) -> FollowUpResponse:
    """
    Answer a follow-up question about a completed analysis session.

    Requires the analysis to be in 'complete' status. Uses cached analysis
    results — does not re-run the full pipeline.

    Args:
        session_id: The session ID returned by POST /analyze.
        request:    JSON body with a 'question' field.
    """
    session = _get_session(session_id)

    if session["status"] != "complete":
        raise HTTPException(
            status_code=409,
            detail=f"Analysis is not complete (status: {session['status']}). "
                   f"Wait for status='complete' before asking follow-up questions.",
        )

    prior_state = session.get("state")
    if not prior_state:
        raise HTTPException(status_code=500, detail="Session state is missing.")

    try:
        from agent.graph import run_followup
        final_state = run_followup(
            session_id=session_id,
            question=request.question,
            prior_state=prior_state,
        )
        answer = final_state.get("follow_up_answer", "No answer generated.")
        # Update stored state with new conversation history
        session["state"] = final_state
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Follow-up failed: {exc}")

    return FollowUpResponse(
        session_id=session_id,
        question=request.question,
        answer=answer,
    )


@app.get("/report/{session_id}", response_model=ReportResponse, tags=["Analysis"])
async def get_report(session_id: str) -> ReportResponse:
    """
    Retrieve the analysis report and metadata for a session.

    Returns status='running'/'queued' while analysis is in progress.
    Returns status='complete' with the full markdown report when done.
    Returns status='error' with an error message if analysis failed.
    """
    session = _get_session(session_id)

    return ReportResponse(
        session_id=session_id,
        status=session["status"],
        report=session.get("report"),
        analysis_plan=session.get("analysis_plan"),
        reflection=session.get("reflection"),
        dataset_summary=session.get("dataset_summary"),
        error=session.get("error"),
    )


@app.get("/charts/{session_id}", response_model=ChartsResponse, tags=["Analysis"])
async def get_charts(session_id: str) -> ChartsResponse:
    """
    Return the list of chart file paths generated for a session.

    Chart files are PNGs saved to the OUTPUT_DIR/{session_id}/ directory.
    The Streamlit UI reads these paths to render images.
    """
    session = _get_session(session_id)
    charts = session.get("charts", [])
    # Filter to only paths that exist on disk
    charts = [p for p in charts if p and Path(p).exists()]
    return ChartsResponse(session_id=session_id, charts=charts)


@app.delete("/session/{session_id}", tags=["System"])
async def delete_session(session_id: str) -> JSONResponse:
    """
    Clean up a session: remove temp files and free memory.

    This is called by the Streamlit UI's reset button to avoid accumulating
    large CSV files in the temp directory.
    """
    session = _get_session(session_id)

    # Remove uploaded CSV temp dir
    csv_path = session.get("csv_path", "")
    if csv_path:
        try:
            shutil.rmtree(Path(csv_path).parent, ignore_errors=True)
        except Exception:
            pass

    # Remove from memory store
    from agent.memory import clear_session
    clear_session(session_id)
    del _sessions[session_id]

    return JSONResponse(content={"message": f"Session '{session_id}' deleted."})


@app.get("/sessions", tags=["System"])
async def list_sessions() -> JSONResponse:
    """
    List all active sessions with their status.

    Useful for debugging and admin dashboards.
    """
    summary = [
        {
            "session_id": sid,
            "status": data.get("status", "unknown"),
            "has_report": bool(data.get("report")),
            "chart_count": len(data.get("charts", [])),
        }
        for sid, data in _sessions.items()
    ]
    return JSONResponse(content={"sessions": summary, "total": len(summary)})
