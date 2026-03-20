"""
FastAPI routes for the Multi-Agent Customer Support System.

Endpoints:
  POST /ticket                        — Submit a new support ticket
  POST /chat/{session_id}             — Multi-turn chat continuation
  POST /escalation/resolve/{ticket_id} — Human agent resolves escalated ticket
  GET  /ticket/{ticket_id}            — Get ticket details
  GET  /session/{session_id}/history  — Get conversation history
  GET  /health                        — Health check with KB status

Design decisions:
- Session state (session_id → TicketState) is stored in-memory.
  For production, replace with Redis + LangGraph persistent checkpointer.
- The compiled graph instance is a module-level singleton shared across
  all requests (MemorySaver state is preserved between requests this way).
- CORS is configured to allow all origins for development. Restrict this
  in production to your frontend domain.
"""

from __future__ import annotations

import os
import uuid
import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.graph import get_graph, process_ticket, resume_after_escalation
from agent.memory import billing_kb, tech_kb, general_kb, session_memory
from agent.tools import get_ticket_raw, list_all_tickets

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Multi-Agent Customer Support API",
    description=(
        "AI-powered customer support system with intent-based routing, "
        "vector knowledge base retrieval, and HITL escalation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for development.
# In production, set allow_origins to your frontend URL(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Module-level singleton graph
# ---------------------------------------------------------------------------
# Build once at startup; shared across all requests so MemorySaver persists.
_graph = None


def _get_or_build_graph():
    global _graph
    if _graph is None:
        _graph = get_graph(enable_hitl=True)
    return _graph


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

class NewTicketRequest(BaseModel):
    """Request body for POST /ticket."""
    message: str = Field(..., description="The user's support message.", min_length=1)
    session_id: Optional[str] = Field(None, description="Existing session ID (optional).")
    user_id: Optional[str] = Field(None, description="External user identifier (optional).")
    channel: str = Field("api", description="Source channel: api | chat | email | web.")


class NewTicketResponse(BaseModel):
    """Response for POST /ticket."""
    ticket_id: str
    session_id: str
    response: str
    intent: str
    agent: str
    confidence_score: float
    escalated: bool
    resolved: bool
    priority: str
    kb_sources: List[str]


class ChatRequest(BaseModel):
    """Request body for POST /chat/{session_id}."""
    message: str = Field(..., description="Follow-up message in the ongoing session.", min_length=1)
    user_id: Optional[str] = Field(None, description="Optional user identifier.")


class ChatResponse(BaseModel):
    """Response for POST /chat/{session_id}."""
    ticket_id: str
    session_id: str
    response: str
    agent: str
    confidence_score: float
    escalated: bool
    intent: str


class EscalationResolveRequest(BaseModel):
    """Request body for POST /escalation/resolve/{ticket_id}."""
    notes: str = Field(..., description="Human agent's resolution notes.", min_length=1)
    resolution: str = Field("resolved", description="Resolution status: resolved | requires_followup.")


class EscalationResolveResponse(BaseModel):
    """Response for POST /escalation/resolve/{ticket_id}."""
    ticket_id: str
    response: str
    resolved: bool
    human_notes: str


class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str
    version: str
    kb_status: Dict[str, Any]
    active_sessions: int


class HistoryMessage(BaseModel):
    """A single message in conversation history."""
    role: str
    content: str


class SessionHistoryResponse(BaseModel):
    """Response for GET /session/{session_id}/history."""
    session_id: str
    messages: List[HistoryMessage]
    message_count: int


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Pre-build the graph on startup to avoid cold-start latency."""
    logger.info("Starting up — building support graph...")
    _get_or_build_graph()
    logger.info(
        "Support graph ready. KB status: billing=%d chunks, tech=%d chunks, general=%d chunks",
        billing_kb.document_count,
        tech_kb.document_count,
        general_kb.document_count,
    )


# ---------------------------------------------------------------------------
# Route: POST /ticket
# ---------------------------------------------------------------------------

@app.post(
    "/ticket",
    response_model=NewTicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new support ticket",
    description=(
        "Accepts a support message and runs it through the multi-agent graph. "
        "Returns the AI response, routing details, and confidence score. "
        "If confidence < threshold, the ticket is automatically escalated."
    ),
)
async def create_support_ticket(request: NewTicketRequest) -> NewTicketResponse:
    """
    Submit a new support ticket.

    The ticket is processed synchronously through the LangGraph pipeline:
    intake → intent_classifier → router → specialist → confidence_check
    → [escalation | responder].

    Returns the final state including the agent's response.
    """
    try:
        graph = _get_or_build_graph()
        final_state = process_ticket(
            message=request.message,
            session_id=request.session_id,
            graph=graph,
            user_id=request.user_id,
            channel=request.channel,
        )

        kb_sources = final_state.get("metadata", {}).get("kb_sources", [])
        if isinstance(kb_sources, str):
            kb_sources = [kb_sources]

        return NewTicketResponse(
            ticket_id=final_state.get("ticket_id", ""),
            session_id=final_state.get("session_id", ""),
            response=final_state.get("agent_response", ""),
            intent=final_state.get("intent", ""),
            agent=final_state.get("assigned_agent", ""),
            confidence_score=round(final_state.get("confidence_score", 0.0), 3),
            escalated=final_state.get("escalated", False),
            resolved=final_state.get("resolved", False),
            priority=final_state.get("priority", "medium"),
            kb_sources=kb_sources,
        )

    except Exception as exc:
        logger.error("POST /ticket failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ticket: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Route: POST /chat/{session_id}
# ---------------------------------------------------------------------------

@app.post(
    "/chat/{session_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-turn chat continuation",
    description=(
        "Submit a follow-up message in an existing session. "
        "The agent uses the full conversation history for context. "
        "Creates a new ticket for this turn and links it to the session."
    ),
)
async def chat_continuation(session_id: str, request: ChatRequest) -> ChatResponse:
    """
    Continue a multi-turn conversation within an existing session.

    Each message in a session generates a new ticket (for audit trail),
    but all tickets share the same session_id and conversation history.
    """
    try:
        graph = _get_or_build_graph()
        final_state = process_ticket(
            message=request.message,
            session_id=session_id,
            graph=graph,
            user_id=request.user_id,
            channel="chat",
        )

        return ChatResponse(
            ticket_id=final_state.get("ticket_id", ""),
            session_id=session_id,
            response=final_state.get("agent_response", ""),
            agent=final_state.get("assigned_agent", ""),
            confidence_score=round(final_state.get("confidence_score", 0.0), 3),
            escalated=final_state.get("escalated", False),
            intent=final_state.get("intent", ""),
        )

    except Exception as exc:
        logger.error("POST /chat/%s failed: %s", session_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Route: POST /escalation/resolve/{ticket_id}
# ---------------------------------------------------------------------------

@app.post(
    "/escalation/resolve/{ticket_id}",
    response_model=EscalationResolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve an escalated ticket (HITL)",
    description=(
        "Called by a human agent after reviewing an escalated ticket. "
        "Resumes the paused LangGraph thread, injects human notes, and "
        "generates a final customer-facing response via hitl_resume node."
    ),
)
async def resolve_escalation(
    ticket_id: str, request: EscalationResolveRequest
) -> EscalationResolveResponse:
    """
    Resume a HITL-paused graph and generate a final response using human notes.
    """
    try:
        graph = _get_or_build_graph()
        combined_notes = f"{request.notes}\n\nResolution: {request.resolution}"

        final_state = resume_after_escalation(
            ticket_id=ticket_id,
            human_notes=combined_notes,
            graph=graph,
        )

        return EscalationResolveResponse(
            ticket_id=ticket_id,
            response=final_state.get("agent_response", ""),
            resolved=final_state.get("resolved", True),
            human_notes=combined_notes,
        )

    except Exception as exc:
        logger.error("POST /escalation/resolve/%s failed: %s", ticket_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve escalation for ticket {ticket_id}: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Route: GET /ticket/{ticket_id}
# ---------------------------------------------------------------------------

@app.get(
    "/ticket/{ticket_id}",
    status_code=status.HTTP_200_OK,
    summary="Get ticket details",
    description="Retrieve full details for a specific ticket by ID.",
)
async def get_ticket(ticket_id: str) -> Dict[str, Any]:
    """Return the raw ticket record from the in-memory ticket store."""
    ticket = get_ticket_raw(ticket_id)
    if "error" in ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )
    return ticket


# ---------------------------------------------------------------------------
# Route: GET /tickets
# ---------------------------------------------------------------------------

@app.get(
    "/tickets",
    status_code=status.HTTP_200_OK,
    summary="List all tickets",
    description="Return all tickets in the system (for admin/debugging).",
)
async def get_all_tickets() -> List[Dict[str, Any]]:
    """Return all tickets in the in-memory store."""
    return list_all_tickets()


# ---------------------------------------------------------------------------
# Route: GET /session/{session_id}/history
# ---------------------------------------------------------------------------

@app.get(
    "/session/{session_id}/history",
    response_model=SessionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history for a session",
    description="Returns all messages exchanged in the specified session, oldest first.",
)
async def get_session_history(session_id: str) -> SessionHistoryResponse:
    """Return the full conversation history for a session."""
    messages = session_memory.get_history(session_id)
    if not messages and session_memory.get_session_context(session_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    history = []
    for msg in messages:
        role = type(msg).__name__.replace("Message", "").lower()
        history.append(HistoryMessage(role=role, content=msg.content))

    return SessionHistoryResponse(
        session_id=session_id,
        messages=history,
        message_count=len(history),
    )


# ---------------------------------------------------------------------------
# Route: GET /health
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check service health and knowledge base status.",
)
async def health_check() -> HealthResponse:
    """Return service health status and KB availability."""
    kb_status = {
        "billing": {
            "ready": billing_kb.is_ready,
            "chunks": billing_kb.document_count,
        },
        "technical": {
            "ready": tech_kb.is_ready,
            "chunks": tech_kb.document_count,
        },
        "general": {
            "ready": general_kb.is_ready,
            "chunks": general_kb.document_count,
        },
    }

    all_ready = all(v["ready"] for v in kb_status.values())

    return HealthResponse(
        status="healthy" if all_ready else "degraded",
        version="1.0.0",
        kb_status=kb_status,
        active_sessions=len(session_memory),
    )


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Multi-Agent Customer Support API", "docs": "/docs"}
