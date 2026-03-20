"""
agent/graph.py

LangGraph StateGraph definition for the AI DevOps Incident Responder.

Graph topology:
    detector
       ↓
    severity_router (conditional edge)
       ├─ low           → auto_responder → outcome_logger → END
       └─ medium/high/critical → planner → diagnoser → runbook_searcher
                                 → fix_proposer → hitl_checkpoint
                                 → [INTERRUPT BEFORE executor]
                                 → executor → outcome_logger → END

Design Decisions:
- MemorySaver checkpointer: persists graph state between invocations so
  that the HITL pause can survive server restarts (within the same process).
  For production, replace with SqliteSaver or RedisSaver.

- interrupt_before=["executor"]: LangGraph pauses execution BEFORE the
  executor node runs, giving the human time to review proposed_fixes.
  The graph resumes only when approve_incident() injects human_approved=True.

- thread_id == incident_id: using the incident UUID as the thread ID
  allows multiple concurrent incidents to have independent checkpointer
  state without collision.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agent.nodes import (
    auto_responder,
    detector,
    diagnoser,
    executor,
    fix_proposer,
    hitl_checkpoint,
    outcome_logger,
    planner,
    runbook_searcher,
    severity_router,
)
from agent.state import IncidentState, make_initial_state

load_dotenv()

# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    """
    Build and compile the incident-response StateGraph.

    Returns:
        A compiled LangGraph graph with MemorySaver checkpointer and
        interrupt_before=["executor"] for HITL.

    Notes:
        The graph is compiled once and reused across requests. The compiled
        graph is thread-safe for concurrent invocations with different thread IDs.
    """
    workflow = StateGraph(IncidentState)

    # --- Register nodes ---
    workflow.add_node("detector",         detector)
    workflow.add_node("auto_responder",   auto_responder)
    workflow.add_node("planner",          planner)
    workflow.add_node("diagnoser",        diagnoser)
    workflow.add_node("runbook_searcher", runbook_searcher)
    workflow.add_node("fix_proposer",     fix_proposer)
    workflow.add_node("hitl_checkpoint",  hitl_checkpoint)
    workflow.add_node("executor",         executor)
    workflow.add_node("outcome_logger",   outcome_logger)

    # --- Entry point ---
    workflow.set_entry_point("detector")

    # --- Conditional routing after detector ---
    # severity_router returns 'low' or 'medium_high_critical'
    workflow.add_conditional_edges(
        "detector",
        severity_router,
        {
            "low":                  "auto_responder",
            "medium_high_critical": "planner",
        },
    )

    # --- Low-severity fast path ---
    workflow.add_edge("auto_responder", "outcome_logger")

    # --- Main investigation path ---
    workflow.add_edge("planner",          "diagnoser")
    workflow.add_edge("diagnoser",        "runbook_searcher")
    workflow.add_edge("runbook_searcher", "fix_proposer")
    workflow.add_edge("fix_proposer",     "hitl_checkpoint")

    # --- HITL → executor (interrupted here) ---
    # The edge from hitl_checkpoint → executor exists in the graph, but
    # interrupt_before=["executor"] causes LangGraph to pause BEFORE
    # calling executor. Execution resumes when the graph is re-invoked
    # with the same thread_id and updated state (human_approved=True).
    workflow.add_edge("hitl_checkpoint", "executor")

    # --- Post-execution ---
    workflow.add_edge("executor",       "outcome_logger")
    workflow.add_edge("outcome_logger", END)

    # --- Compile with checkpointer and HITL interrupt ---
    checkpointer = MemorySaver()

    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["executor"],  # HITL: pause before any fix execution
    )

    return compiled


# ---------------------------------------------------------------------------
# Singleton graph instance (shared across the API)
# ---------------------------------------------------------------------------

_graph_instance: Optional[Any] = None


def get_graph() -> Any:
    """
    Return the singleton compiled graph instance.

    Lazy-initializes on first call. Subsequent calls return the same object.
    Thread-safe because Python's GIL protects the assignment.
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance


# ---------------------------------------------------------------------------
# Helper: run_incident
# ---------------------------------------------------------------------------

def run_incident(
    raw_logs: str,
    incident_id: Optional[str] = None,
    graph: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Start a new incident analysis.

    Invokes the graph from the entry point (detector) up to the HITL
    interrupt (just before executor).  The graph pauses automatically
    after hitl_checkpoint.

    Args:
        raw_logs:    Raw log text to analyze.
        incident_id: Optional UUID; generated if not provided.
        graph:       Compiled graph; uses singleton if not provided.

    Returns:
        Dict with keys:
          - incident_id  (str)
          - thread_id    (str)  same as incident_id
          - status       (str)  'awaiting_approval' | 'resolved' (low severity)
          - state        (Dict) full IncidentState snapshot
          - next_nodes   (List[str]) nodes queued to run after HITL resume
    """
    if graph is None:
        graph = get_graph()

    if incident_id is None:
        incident_id = str(uuid.uuid4())

    initial_state = make_initial_state(raw_logs=raw_logs, incident_id=incident_id)

    config = {
        "configurable": {"thread_id": incident_id},
        "recursion_limit": 25,
    }

    try:
        # stream() returns an iterator over state snapshots
        # We consume it fully to drive the graph to the interrupt point
        final_snapshot = None
        for snapshot in graph.stream(initial_state, config=config, stream_mode="values"):
            final_snapshot = snapshot

        if final_snapshot is None:
            final_snapshot = {}

        # Determine what happens next
        state_snapshot = graph.get_state(config)
        next_nodes = list(state_snapshot.next) if state_snapshot else []

        return {
            "incident_id": incident_id,
            "thread_id": incident_id,
            "status": final_snapshot.get("status", "unknown"),
            "state": dict(final_snapshot),
            "next_nodes": next_nodes,
        }

    except Exception as exc:
        return {
            "incident_id": incident_id,
            "thread_id": incident_id,
            "status": "failed",
            "state": {"error": str(exc), "incident_id": incident_id},
            "next_nodes": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Helper: approve_incident
# ---------------------------------------------------------------------------

def approve_incident(
    incident_id: str,
    approved: bool,
    notes: str = "",
    graph: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Resume the graph after the HITL checkpoint.

    Injects the human's decision (approved/rejected) into the checkpointer
    state, then re-invokes the graph.  If approved=True, the executor node
    runs and applies fixes.  If approved=False, the graph skips execution
    and logs the rejection.

    Args:
        incident_id: UUID of the incident (also the thread_id).
        approved:    True to execute fixes; False to reject.
        notes:       Optional human notes (rejection reason, caveats).
        graph:       Compiled graph; uses singleton if not provided.

    Returns:
        Dict with keys:
          - incident_id  (str)
          - status       (str)  'resolved' | 'failed'
          - state        (Dict) final IncidentState
          - executed_fixes (List[str])
    """
    if graph is None:
        graph = get_graph()

    config = {
        "configurable": {"thread_id": incident_id},
        "recursion_limit": 25,
    }

    try:
        # Update state with human decision
        # Design Decision: We update the graph's persisted checkpoint state
        # directly via update_state(). This is the standard LangGraph pattern
        # for injecting external input after an interrupt.
        graph.update_state(
            config,
            {
                "human_approved": approved,
                "human_notes": notes,
                "status": "executing" if approved else "rejected",
            },
        )

        if not approved:
            # Rejection: mark as resolved without executing
            graph.update_state(
                config,
                {
                    "status": "resolved",
                    "outcome": f"Incident rejected by human operator. Notes: {notes}",
                },
            )
            state_snapshot = graph.get_state(config)
            state = dict(state_snapshot.values) if state_snapshot else {}
            return {
                "incident_id": incident_id,
                "status": "resolved",
                "state": state,
                "executed_fixes": [],
                "message": f"Incident {incident_id[:8]}... rejected. Notes: {notes}",
            }

        # Resume graph from the interrupt point (executor onward)
        final_snapshot = None
        for snapshot in graph.stream(None, config=config, stream_mode="values"):
            final_snapshot = snapshot

        if final_snapshot is None:
            state_snapshot = graph.get_state(config)
            final_snapshot = dict(state_snapshot.values) if state_snapshot else {}

        return {
            "incident_id": incident_id,
            "status": final_snapshot.get("status", "resolved"),
            "state": dict(final_snapshot),
            "executed_fixes": final_snapshot.get("executed_fixes", []),
            "outcome": final_snapshot.get("outcome", ""),
        }

    except Exception as exc:
        return {
            "incident_id": incident_id,
            "status": "failed",
            "state": {"error": str(exc)},
            "executed_fixes": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Helper: get_incident_state
# ---------------------------------------------------------------------------

def get_incident_state(incident_id: str, graph: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve the current state of an in-flight incident from the checkpointer.

    Args:
        incident_id: UUID of the incident.
        graph:       Compiled graph; uses singleton if not provided.

    Returns:
        Dict of current IncidentState values, or None if not found.
    """
    if graph is None:
        graph = get_graph()

    config = {"configurable": {"thread_id": incident_id}}
    try:
        snapshot = graph.get_state(config)
        if snapshot and snapshot.values:
            return dict(snapshot.values)
        return None
    except Exception:
        return None
