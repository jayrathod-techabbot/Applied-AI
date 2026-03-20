"""
LangChain tools for the Multi-Agent Customer Support System.

Each tool is decorated with @tool so LangGraph nodes can call them as
standard Python functions while LangChain tracks their invocations for
observability. All KB lookup tools use local TF-IDF (no external API
required at runtime).

Tool categories:
  KB Lookup  — billing_kb, tech_kb, general_kb
  Ticketing  — create_ticket, update_ticket
  Escalation — escalate_to_human
  Session    — get_session_history

FAISS note:
  To switch to semantic search, replace the `memory.*_kb.search(query)`
  calls with FAISS index queries. The tool signatures and return types
  remain identical, so no downstream changes are required.
"""

from __future__ import annotations

import uuid
import datetime
import logging
from typing import Any, Dict, List

from langchain_core.tools import tool

# Import shared KB singletons and session memory
from agent.memory import billing_kb, tech_kb, general_kb, session_memory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory ticket store (replace with a DB in production)
# ---------------------------------------------------------------------------
# Dict[ticket_id, Dict[str, Any]]
_TICKET_STORE: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Knowledge Base Lookup Tools
# ---------------------------------------------------------------------------

@tool
def lookup_billing_kb(query: str) -> List[Dict[str, Any]]:
    """
    Search the billing knowledge base for relevant information.

    Covers: pricing plans, invoices, refunds, payment methods,
    subscription management, and common billing issues.

    Uses TF-IDF cosine similarity for retrieval. To upgrade to semantic
    search, replace `billing_kb.search()` with a FAISS/embedding call.

    Args:
        query: Natural-language question or keywords from the support ticket.

    Returns:
        List of dicts with keys: content (str), source (str), relevance_score (float).
        Sorted by relevance_score descending. Empty list if no relevant results.
    """
    try:
        results = billing_kb.search(query=query, top_k=3)
        output = [
            {
                "content": r["content"],
                "source": r["source"],
                "relevance_score": r["relevance_score"],
            }
            for r in results
        ]
        logger.debug("billing_kb lookup for '%s': %d results", query, len(output))
        return output
    except Exception as exc:
        logger.error("lookup_billing_kb failed: %s", exc)
        return []


@tool
def lookup_tech_kb(query: str) -> List[Dict[str, Any]]:
    """
    Search the technical knowledge base for relevant information.

    Covers: setup guides, API documentation, error codes, integration guides
    (webhooks, OAuth), troubleshooting steps, and system requirements.

    Uses TF-IDF cosine similarity for retrieval.

    Args:
        query: Natural-language question or error description from the ticket.

    Returns:
        List of dicts with keys: content (str), source (str), relevance_score (float).
        Sorted by relevance_score descending.
    """
    try:
        results = tech_kb.search(query=query, top_k=3)
        output = [
            {
                "content": r["content"],
                "source": r["source"],
                "relevance_score": r["relevance_score"],
            }
            for r in results
        ]
        logger.debug("tech_kb lookup for '%s': %d results", query, len(output))
        return output
    except Exception as exc:
        logger.error("lookup_tech_kb failed: %s", exc)
        return []


@tool
def lookup_general_kb(query: str) -> List[Dict[str, Any]]:
    """
    Search the general knowledge base for relevant information.

    Covers: company information, service availability / SLA, privacy policy,
    contact information, account management, and security practices.

    Uses TF-IDF cosine similarity for retrieval.

    Args:
        query: Natural-language question from the support ticket.

    Returns:
        List of dicts with keys: content (str), source (str), relevance_score (float).
        Sorted by relevance_score descending.
    """
    try:
        results = general_kb.search(query=query, top_k=3)
        output = [
            {
                "content": r["content"],
                "source": r["source"],
                "relevance_score": r["relevance_score"],
            }
            for r in results
        ]
        logger.debug("general_kb lookup for '%s': %d results", query, len(output))
        return output
    except Exception as exc:
        logger.error("lookup_general_kb failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Ticketing Tools
# ---------------------------------------------------------------------------

@tool
def create_ticket(session_id: str, priority: str, summary: str) -> Dict[str, Any]:
    """
    Create a new support ticket record in the system.

    In production this would write to a CRM or ticketing system (Zendesk,
    Jira Service Management, etc.). Here we use an in-memory store.

    Args:
        session_id: The user's session ID this ticket belongs to.
        priority:   One of: low | medium | high | urgent.
        summary:    Brief human-readable description of the issue.

    Returns:
        Dict with: ticket_id (str), session_id (str), priority (str),
        status (str), created_at (str), summary (str).
    """
    valid_priorities = {"low", "medium", "high", "urgent"}
    if priority not in valid_priorities:
        priority = "medium"

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.utcnow().isoformat()

    ticket: Dict[str, Any] = {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "priority": priority,
        "status": "open",
        "summary": summary,
        "created_at": now,
        "updated_at": now,
        "notes": [],
        "escalated": False,
        "resolved": False,
    }
    _TICKET_STORE[ticket_id] = ticket
    logger.info("Ticket created: %s (priority=%s)", ticket_id, priority)
    return ticket


@tool
def update_ticket(ticket_id: str, status: str, notes: str) -> Dict[str, Any]:
    """
    Update the status and add notes to an existing support ticket.

    Args:
        ticket_id: The ticket to update.
        status:    New status: open | in_progress | escalated | resolved | closed.
        notes:     Free-text notes to append to the ticket history.

    Returns:
        Updated ticket dict, or an error dict if the ticket is not found.
    """
    if ticket_id not in _TICKET_STORE:
        logger.warning("update_ticket: ticket %s not found", ticket_id)
        return {"error": f"Ticket {ticket_id} not found", "ticket_id": ticket_id}

    now = datetime.datetime.utcnow().isoformat()
    ticket = _TICKET_STORE[ticket_id]
    ticket["status"] = status
    ticket["updated_at"] = now
    if notes:
        ticket["notes"].append({"timestamp": now, "note": notes})

    if status == "resolved":
        ticket["resolved"] = True
    elif status == "escalated":
        ticket["escalated"] = True

    logger.info("Ticket %s updated: status=%s", ticket_id, status)
    return ticket


@tool
def escalate_to_human(ticket_id: str, reason: str, priority: str) -> Dict[str, Any]:
    """
    Trigger the Human-in-the-Loop escalation workflow for a ticket.

    This tool performs three actions:
    1. Updates the ticket's status to "escalated" in the store.
    2. Logs the escalation with a reason and timestamp.
    3. Returns an escalation record that the escalation_handler node uses
       to format the user-facing message.

    In production, this would notify a human agent via PagerDuty, Slack,
    or a CRM webhook. Here we log and return a structured response.

    Args:
        ticket_id: The ticket being escalated.
        reason:    Why automated handling failed (e.g., "low confidence score").
        priority:  Escalation priority: low | medium | high | urgent.

    Returns:
        Dict with: escalation_id, ticket_id, reason, priority, estimated_wait,
        escalated_at, status.
    """
    # Update the ticket record
    if ticket_id in _TICKET_STORE:
        _TICKET_STORE[ticket_id]["status"] = "escalated"
        _TICKET_STORE[ticket_id]["escalated"] = True
        _TICKET_STORE[ticket_id]["escalation_reason"] = reason

    # Estimate wait time based on priority
    wait_times = {
        "urgent": "5–15 minutes",
        "high": "15–30 minutes",
        "medium": "1–2 hours",
        "low": "4–8 hours",
    }
    estimated_wait = wait_times.get(priority, "1–2 hours")

    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.utcnow().isoformat()

    escalation_record = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "priority": priority,
        "estimated_wait": estimated_wait,
        "escalated_at": now,
        "status": "pending_human_review",
    }

    logger.info(
        "Escalated ticket %s (escalation_id=%s, priority=%s, reason=%s)",
        ticket_id, escalation_id, priority, reason
    )
    return escalation_record


# ---------------------------------------------------------------------------
# Session History Tool
# ---------------------------------------------------------------------------

@tool
def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve the conversation history for a session.

    Converts LangChain BaseMessage objects to plain dicts for easy
    serialization in API responses and logging.

    Args:
        session_id: The session whose history to retrieve.

    Returns:
        List of dicts with keys: role (str), content (str).
        Ordered oldest-first. Empty list if session not found.
    """
    try:
        messages = session_memory.get_history(session_id)
        history = []
        for msg in messages:
            role = type(msg).__name__.replace("Message", "").lower()
            history.append({"role": role, "content": msg.content})
        return history
    except Exception as exc:
        logger.error("get_session_history failed for session %s: %s", session_id, exc)
        return []


# ---------------------------------------------------------------------------
# Helper: get raw ticket (not a @tool, used by API routes directly)
# ---------------------------------------------------------------------------

def get_ticket_raw(ticket_id: str) -> Dict[str, Any]:
    """
    Return raw ticket dict from the in-memory store.

    Not a LangChain tool — intended for direct use by the FastAPI routes.

    Args:
        ticket_id: Ticket to look up.

    Returns:
        Ticket dict, or {"error": "..."} if not found.
    """
    if ticket_id in _TICKET_STORE:
        return _TICKET_STORE[ticket_id]
    return {"error": f"Ticket {ticket_id} not found"}


def list_all_tickets() -> List[Dict[str, Any]]:
    """Return all tickets in the store. Not a tool — used by API routes."""
    return list(_TICKET_STORE.values())
