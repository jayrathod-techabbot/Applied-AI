"""
State definitions for the Multi-Agent Customer Support System.

This module defines the TypedDict schemas used throughout the LangGraph
state machine. Having a single, centralized state schema ensures all nodes
operate on a consistent, type-safe data structure.

Pattern: Shared State Architecture — all agents read/write to the same
TicketState, which travels through the graph and accumulates information
at each node. This avoids the need for a separate message bus.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class KBResult(TypedDict):
    """
    A single result returned from a knowledge base search.

    Fields:
        content:         The raw text chunk retrieved from the KB.
        source:          Filename or document identifier the chunk came from.
        relevance_score: TF-IDF cosine similarity score (0.0 – 1.0).
                         Used downstream to compute the agent's confidence.
    """
    content: str
    source: str
    relevance_score: float


class SessionContext(TypedDict):
    """
    Tracks multi-turn session state that persists across requests.

    Unlike TicketState (which is per-ticket), SessionContext lives in
    SessionMemory and is keyed by session_id. This separation lets us
    keep a rolling conversation window without bloating every ticket's state.

    Fields:
        session_id:   Unique identifier for the user's session.
        user_id:      Optional external user identifier.
        created_at:   ISO-8601 timestamp when the session started.
        last_active:  ISO-8601 timestamp of the most recent interaction.
        ticket_ids:   All ticket IDs processed within this session.
        message_count: Running total of messages exchanged.
        dominant_intent: Most frequent intent so far (billing/technical/general).
    """
    session_id: str
    user_id: Optional[str]
    created_at: str
    last_active: str
    ticket_ids: List[str]
    message_count: int
    dominant_intent: Optional[str]


class TicketState(TypedDict):
    """
    Central state object that flows through every node of the support graph.

    Design rationale:
    - TypedDict (not Pydantic BaseModel) is required by LangGraph's StateGraph.
    - All fields are Optional where appropriate so nodes can safely read them
      even when they have not yet been populated by an upstream node.
    - conversation_history stores LangChain BaseMessage objects so we can
      pass the full history directly to any ChatModel without reformatting.

    Lifecycle:
        intake → intent_classifier → router → specialist_agent
               → confidence_check → [escalation_handler | responder] → END

    Fields:
        session_id:            Groups multiple tickets from one user session.
        user_message:          Raw text submitted by the user.
        intent:                Classified intent: billing | technical | general | escalate.
        assigned_agent:        Which specialist handled this ticket (for logging/display).
        kb_results:            List of retrieved knowledge-base text chunks.
        agent_response:        Final text response returned to the user.
        confidence_score:      0.0–1.0; below CONFIDENCE_THRESHOLD triggers HITL.
        escalated:             True once the ticket has been handed to a human agent.
        human_agent_notes:     Notes injected by a human agent during HITL resolution.
        conversation_history:  Full ordered list of messages for the session so far.
        resolved:              True once the ticket has a final resolution.
        ticket_id:             Unique ticket identifier (UUID).
        priority:              low | medium | high | urgent
        metadata:              Freeform dict: timestamp, user_id, channel, etc.
    """
    session_id: str
    user_message: str
    intent: str                          # billing | technical | general | escalate
    assigned_agent: str
    kb_results: List[str]                # Retrieved knowledge base chunks (plain text)
    agent_response: str
    confidence_score: float              # < CONFIDENCE_THRESHOLD → HITL escalation
    escalated: bool
    human_agent_notes: Optional[str]
    conversation_history: List[BaseMessage]
    resolved: bool
    ticket_id: str
    priority: str                        # low | medium | high | urgent
    metadata: Dict[str, Any]            # timestamp, user_id, channel, source_kb_results
