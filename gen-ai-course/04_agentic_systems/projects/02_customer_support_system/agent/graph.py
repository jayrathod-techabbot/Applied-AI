"""
LangGraph StateGraph for the Multi-Agent Customer Support System.

This module wires all nodes into a directed graph with conditional routing.

Architecture: Hub-and-Spoke
  - Hub: Orchestrator (intent_classifier → router)
  - Spokes: BillingAgent, TechAgent, GeneralAgent
  - HITL: escalation_handler (interrupt point) + hitl_resume

Graph topology:
  intake
    └─► intent_classifier
          └─► router
                ├─► billing_agent ─┐
                ├─► tech_agent    ─┼─► confidence_check
                ├─► general_agent ─┘       ├─► (low conf) ─► escalation_handler ─► END
                └─► escalation_handler     └─► (ok conf)  ─► responder ─► END

HITL pattern:
  - The graph is compiled with interrupt_before=["escalation_handler"].
  - When the interrupt fires, execution pauses and the ticket_id is surfaced
    to the caller (API route / Streamlit UI).
  - A human agent reviews the ticket and submits notes via POST /escalation/resolve/{ticket_id}.
  - The API calls resume_after_escalation(), which resumes the graph thread
    at hitl_resume with the human_agent_notes injected.

Thread-based memory:
  - Each ticket is processed on its own thread (config={"configurable": {"thread_id": ticket_id}}).
  - LangGraph's MemorySaver checkpoints the state at every node, enabling
    pause/resume across HTTP requests without losing state.
"""

from __future__ import annotations

import os
import uuid
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import TicketState
from agent.nodes import (
    intake,
    intent_classifier,
    router,
    billing_agent,
    tech_agent,
    general_agent,
    confidence_check,
    escalation_handler,
    responder,
    hitl_resume,
)

load_dotenv()

logger = logging.getLogger(__name__)

_CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def route_by_intent(state: TicketState) -> str:
    """
    Conditional edge: after intent_classifier → select specialist or escalate.

    This edge reads state["intent"] (set by intent_classifier) and returns
    the name of the next node. LangGraph uses the returned string to look up
    the target node in the graph's node registry.

    Returns:
        One of: "billing_agent" | "tech_agent" | "general_agent" | "escalation_handler"
    """
    intent = state.get("intent", "general")
    routing = {
        "billing": "billing_agent",
        "technical": "tech_agent",
        "general": "general_agent",
        "escalate": "escalation_handler",
    }
    target = routing.get(intent, "general_agent")
    logger.debug("[route_by_intent] intent=%s → %s", intent, target)
    return target


def route_after_confidence(state: TicketState) -> str:
    """
    Conditional edge: after confidence_check → escalate or resolve.

    Reads state["confidence_score"] and state["escalated"].
    If already escalated (e.g., intent was "escalate"), goes to END.
    If confidence is below threshold, routes to escalation_handler.
    Otherwise routes to responder.

    Returns:
        One of: "escalation_handler" | "responder" | END
    """
    # If the intent classifier itself decided to escalate, we skip to END
    if state.get("escalated", False):
        logger.debug("[route_after_confidence] already escalated → END")
        return END

    confidence = state.get("confidence_score", 0.0)
    if confidence < _CONFIDENCE_THRESHOLD:
        logger.debug(
            "[route_after_confidence] confidence=%.3f < %.3f → escalation_handler",
            confidence, _CONFIDENCE_THRESHOLD
        )
        return "escalation_handler"

    logger.debug(
        "[route_after_confidence] confidence=%.3f >= %.3f → responder",
        confidence, _CONFIDENCE_THRESHOLD
    )
    return "responder"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_support_graph(enable_hitl: bool = True) -> Any:
    """
    Construct and compile the LangGraph StateGraph for customer support.

    Args:
        enable_hitl: If True, compile with interrupt_before=["escalation_handler"]
                     to pause execution for human review. Set to False for
                     automated testing where HITL interrupts are not needed.

    Returns:
        Compiled LangGraph graph object with MemorySaver checkpoint backend.
    """
    # Initialize the state graph with our TicketState schema
    workflow = StateGraph(TicketState)

    # ------------------------------------------------------------------
    # Register all nodes
    # ------------------------------------------------------------------
    workflow.add_node("intake", intake)
    workflow.add_node("intent_classifier", intent_classifier)
    workflow.add_node("router", router)
    workflow.add_node("billing_agent", billing_agent)
    workflow.add_node("tech_agent", tech_agent)
    workflow.add_node("general_agent", general_agent)
    workflow.add_node("confidence_check", confidence_check)
    workflow.add_node("escalation_handler", escalation_handler)
    workflow.add_node("responder", responder)
    workflow.add_node("hitl_resume", hitl_resume)

    # ------------------------------------------------------------------
    # Define the entry point
    # ------------------------------------------------------------------
    workflow.set_entry_point("intake")

    # ------------------------------------------------------------------
    # Linear edges (deterministic transitions)
    # ------------------------------------------------------------------
    workflow.add_edge("intake", "intent_classifier")
    workflow.add_edge("intent_classifier", "router")

    # After each specialist finishes, always run confidence_check
    workflow.add_edge("billing_agent", "confidence_check")
    workflow.add_edge("tech_agent", "confidence_check")
    workflow.add_edge("general_agent", "confidence_check")

    # After escalation or resolution, terminate
    workflow.add_edge("escalation_handler", END)
    workflow.add_edge("responder", END)
    workflow.add_edge("hitl_resume", END)

    # ------------------------------------------------------------------
    # Conditional edges (dynamic routing)
    # ------------------------------------------------------------------

    # After router: send to correct specialist based on intent
    workflow.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "billing_agent": "billing_agent",
            "tech_agent": "tech_agent",
            "general_agent": "general_agent",
            "escalation_handler": "escalation_handler",
        },
    )

    # After confidence_check: escalate or resolve
    workflow.add_conditional_edges(
        "confidence_check",
        route_after_confidence,
        {
            "escalation_handler": "escalation_handler",
            "responder": "responder",
            END: END,
        },
    )

    # ------------------------------------------------------------------
    # Compile with MemorySaver for thread-based multi-turn state
    # ------------------------------------------------------------------
    memory = MemorySaver()

    if enable_hitl:
        # interrupt_before=["escalation_handler"] pauses execution just before
        # the escalation node runs, allowing a human agent to inject notes
        # via the resume_after_escalation() function before the graph continues.
        compiled = workflow.compile(
            checkpointer=memory,
            interrupt_before=["escalation_handler"],
        )
        logger.info("Support graph compiled with HITL interrupt enabled.")
    else:
        compiled = workflow.compile(checkpointer=memory)
        logger.info("Support graph compiled without HITL interrupt (testing mode).")

    return compiled


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def process_ticket(
    message: str,
    session_id: Optional[str] = None,
    graph: Any = None,
    user_id: Optional[str] = None,
    channel: str = "api",
) -> Dict[str, Any]:
    """
    Submit a new support ticket and run it through the graph.

    This is the primary entry point for the FastAPI routes and the Streamlit UI.

    Args:
        message:    The user's support message.
        session_id: Optional existing session ID. A new one is created if None.
        graph:      Compiled LangGraph graph. Built fresh if None.
        user_id:    Optional user identifier for metadata.
        channel:    Source channel: "api" | "chat" | "email" | "web".

    Returns:
        The final TicketState dict after all nodes have executed (or after
        interrupt, in which case the graph is paused and the ticket_id is
        returned for later resumption).
    """
    if graph is None:
        graph = build_support_graph()

    if session_id is None:
        session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    initial_state: TicketState = {
        "session_id": session_id,
        "user_message": message,
        "intent": "",
        "assigned_agent": "",
        "kb_results": [],
        "agent_response": "",
        "confidence_score": 0.0,
        "escalated": False,
        "human_agent_notes": None,
        "conversation_history": [],
        "resolved": False,
        "ticket_id": ticket_id,
        "priority": "medium",
        "metadata": {
            "user_id": user_id or "anonymous",
            "channel": channel,
        },
    }

    # Each ticket runs on its own LangGraph thread (keyed by ticket_id).
    # This enables the graph to be paused (HITL interrupt) and resumed later.
    config = {"configurable": {"thread_id": ticket_id}}

    try:
        # stream(mode="values") yields state snapshots after each node.
        # We collect all snapshots and return the final one.
        final_state = None
        for snapshot in graph.stream(initial_state, config=config, stream_mode="values"):
            final_state = snapshot

        if final_state is None:
            logger.warning("[process_ticket] No state snapshots returned for ticket=%s", ticket_id)
            final_state = initial_state

        logger.info(
            "[process_ticket] ticket=%s done: intent=%s agent=%s confidence=%.3f escalated=%s resolved=%s",
            final_state.get("ticket_id"),
            final_state.get("intent"),
            final_state.get("assigned_agent"),
            final_state.get("confidence_score", 0.0),
            final_state.get("escalated"),
            final_state.get("resolved"),
        )
        return final_state

    except Exception as exc:
        logger.error("[process_ticket] Graph execution failed for ticket=%s: %s", ticket_id, exc)
        return {
            **initial_state,
            "agent_response": f"System error: {exc}. Please try again.",
            "escalated": True,
            "resolved": False,
        }


def resume_after_escalation(
    ticket_id: str,
    human_notes: str,
    graph: Any,
) -> Dict[str, Any]:
    """
    Resume a paused (HITL-interrupted) graph thread after human review.

    This function is called by the API route POST /escalation/resolve/{ticket_id}
    after a human agent submits their notes.

    How LangGraph HITL works:
    1. `process_ticket()` runs the graph until `interrupt_before=["escalation_handler"]`
       fires, pausing execution.
    2. The graph state is checkpointed in MemorySaver under thread_id=ticket_id.
    3. `resume_after_escalation()` injects human_agent_notes into the state,
       then calls `graph.invoke(None, config)` to resume from the checkpoint.
    4. The graph continues from `hitl_resume` (the next node after escalation_handler).

    Args:
        ticket_id:    The ticket whose thread to resume.
        human_notes:  Notes provided by the human agent.
        graph:        The same compiled graph instance used to process the ticket.

    Returns:
        Final TicketState after hitl_resume completes.
    """
    config = {"configurable": {"thread_id": ticket_id}}

    # Inject human notes into the checkpointed state
    state_update = {"human_agent_notes": human_notes}

    try:
        # graph.update_state() merges the update into the paused checkpoint
        graph.update_state(config, state_update, as_node="escalation_handler")

        # Resume execution from where it was interrupted
        final_state = None
        for snapshot in graph.stream(None, config=config, stream_mode="values"):
            final_state = snapshot

        if final_state is None:
            raise RuntimeError("No state returned after HITL resume")

        logger.info("[resume_after_escalation] ticket=%s resumed and resolved", ticket_id)
        return final_state

    except Exception as exc:
        logger.error("[resume_after_escalation] Failed for ticket=%s: %s", ticket_id, exc)
        return {
            "ticket_id": ticket_id,
            "agent_response": (
                f"Human review completed. Notes: {human_notes}. "
                f"Our team will follow up shortly."
            ),
            "human_agent_notes": human_notes,
            "resolved": True,
            "escalated": False,
        }


# ---------------------------------------------------------------------------
# Module-level singleton graph
# ---------------------------------------------------------------------------
# Built once at import time so FastAPI routes share a single graph instance
# (and thus the same MemorySaver checkpoint store).

_graph_instance: Optional[Any] = None


def get_graph(enable_hitl: bool = True) -> Any:
    """
    Return the module-level singleton graph, building it if necessary.

    Using a singleton avoids rebuilding the graph on every request while
    keeping the checkpoint store (MemorySaver) in memory between requests.

    Args:
        enable_hitl: Passed to build_support_graph() on first build.

    Returns:
        Compiled LangGraph graph instance.
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_support_graph(enable_hitl=enable_hitl)
    return _graph_instance
