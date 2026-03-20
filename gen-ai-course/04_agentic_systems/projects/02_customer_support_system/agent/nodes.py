"""
LangGraph node implementations for the Multi-Agent Customer Support System.

Each function in this module is a LangGraph node — it receives the current
TicketState, performs its specific task, and returns a dict of state updates.
LangGraph merges the returned dict into the global state automatically.

Node execution order:
  intake → intent_classifier → router → specialist_agent
         → confidence_check → [escalation_handler | responder] → END

Design principles:
- Every node is a pure function: (state) → dict.
- Nodes do NOT mutate the state in place; they return only the fields they change.
- The LLM (Groq llama-3.3-70b) is invoked only where classification or
  language generation is genuinely needed. Routing logic (router node) is
  pure Python to avoid unnecessary API calls.
- Confidence scoring is derived from KB retrieval scores, not hallucinated
  by the LLM, making the escalation trigger deterministic and auditable.
"""

from __future__ import annotations

import os
import uuid
import logging
import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from agent.state import TicketState, KBResult
from agent.memory import billing_kb, tech_kb, general_kb, session_memory
from agent.tools import (
    lookup_billing_kb,
    lookup_tech_kb,
    lookup_general_kb,
    create_ticket,
    update_ticket,
    escalate_to_human,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM initialization
# ---------------------------------------------------------------------------
# Groq llama-3.3-70b is chosen for its 8k token context and sub-second latency,
# which is critical for a real-time customer support experience.
# Temperature=0.1 keeps responses factual and consistent; slight non-zero
# temperature avoids repetitive phrasing across similar tickets.

_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
_CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))


def _get_llm(temperature: float = 0.1) -> ChatGroq:
    """
    Return a configured ChatGroq instance.

    Centralising LLM construction means we can swap models or providers
    without touching individual node functions.
    """
    return ChatGroq(
        api_key=_GROQ_API_KEY,
        model=_GROQ_MODEL,
        temperature=temperature,
        max_tokens=1024,
    )


# ---------------------------------------------------------------------------
# Helper: compute confidence from KB results
# ---------------------------------------------------------------------------

def _compute_confidence(kb_results: List[Dict]) -> float:
    """
    Derive a confidence score (0.0–1.0) from KB retrieval relevance scores.

    Strategy:
    - If no results: confidence = 0.0 (escalate immediately).
    - If results: take a weighted average — top result counts 60%, second 30%,
      third 10% — then cap at 1.0.
    - This heuristic is transparent and auditable compared to asking the LLM
      to self-report confidence (which can be unreliable).

    Args:
        kb_results: List of result dicts with a 'relevance_score' key.

    Returns:
        Float in [0.0, 1.0].
    """
    if not kb_results:
        return 0.0

    weights = [0.6, 0.3, 0.1]
    scores = [r.get("relevance_score", 0.0) for r in kb_results[:3]]

    weighted = sum(s * w for s, w in zip(scores, weights[: len(scores)]))
    # Scale: TF-IDF cosine similarity rarely exceeds 0.4 for reasonable queries.
    # We scale by 2.5 so a "good" match (0.3) maps to ~0.75 confidence.
    scaled = min(weighted * 2.5, 1.0)
    return round(scaled, 3)


# ---------------------------------------------------------------------------
# Node 1: intake
# ---------------------------------------------------------------------------

def intake(state: TicketState) -> Dict[str, Any]:
    """
    Log the incoming ticket and initialise required state fields.

    Responsibilities:
    - Assign a ticket_id if one does not already exist.
    - Record metadata: timestamp, channel, user_id.
    - Register the ticket with SessionMemory for history tracking.
    - Add the user's message to session history.

    This node does NOT call an LLM — it is purely administrative.
    """
    ticket_id = state.get("ticket_id") or f"TKT-{uuid.uuid4().hex[:8].upper()}"
    session_id = state.get("session_id") or f"SES-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.utcnow().isoformat()

    metadata = state.get("metadata") or {}
    metadata.setdefault("timestamp", now)
    metadata.setdefault("channel", "api")
    metadata.setdefault("user_id", "anonymous")

    # Store the incoming user message in session memory
    session_memory.add_message(session_id, "human", state.get("user_message", ""))
    session_memory.register_ticket(session_id, ticket_id)

    # Retrieve full history so downstream nodes can access it
    history = session_memory.get_history(session_id)

    logger.info("[intake] ticket=%s session=%s message='%.80s'",
                ticket_id, session_id, state.get("user_message", ""))

    return {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "metadata": metadata,
        "conversation_history": history,
        "escalated": False,
        "resolved": False,
        "kb_results": [],
        "agent_response": "",
        "confidence_score": 0.0,
        "human_agent_notes": None,
        "assigned_agent": "",
        "intent": "",
        "priority": state.get("priority") or "medium",
    }


# ---------------------------------------------------------------------------
# Node 2: intent_classifier
# ---------------------------------------------------------------------------

_INTENT_SYSTEM_PROMPT = """You are an intent classifier for a customer support system.
Classify the user's message into EXACTLY ONE of these categories:
- billing   : questions about payments, invoices, refunds, subscriptions, pricing
- technical : questions about software bugs, API errors, setup, configuration, integrations
- general   : questions about company info, policies, contact details, account management
- escalate  : expressions of extreme frustration, legal threats, abuse, or requests for a manager

Also assign a priority:
- urgent: system down, payment failure, data loss, legal threat
- high  : significant feature broken, billing discrepancy > $100
- medium: general issue affecting workflow
- low   : general question, minor inconvenience

Respond with ONLY a JSON object, no markdown fences:
{"intent": "<billing|technical|general|escalate>", "priority": "<urgent|high|medium|low>"}
"""


def intent_classifier(state: TicketState) -> Dict[str, Any]:
    """
    Classify the user's message into a routing intent and priority.

    Uses Groq llama-3.3-70b with a strict JSON output format to ensure
    deterministic parsing. The conversation history is included so the
    classifier understands follow-up questions in context (e.g., "and for
    the Pro plan?" after discussing billing).

    Fallback: if the LLM response cannot be parsed, defaults to
    intent="general" and priority="medium" to avoid dropping the ticket.
    """
    import json

    user_message = state.get("user_message", "")
    history_context = session_memory.get_context(
        state.get("session_id", ""), max_messages=6
    )

    prompt_content = f"""Conversation history:
{history_context if history_context else "(no prior history)"}

Current message: {user_message}

Classify the intent and priority as instructed."""

    try:
        llm = _get_llm(temperature=0.0)
        messages = [
            SystemMessage(content=_INTENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt_content),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip any accidental markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        intent = parsed.get("intent", "general")
        priority = parsed.get("priority", "medium")

        if intent not in {"billing", "technical", "general", "escalate"}:
            intent = "general"
        if priority not in {"low", "medium", "high", "urgent"}:
            priority = "medium"

    except Exception as exc:
        logger.error("[intent_classifier] LLM call failed: %s. Defaulting to general.", exc)
        intent = "general"
        priority = "medium"

    session_memory.update_intent(state.get("session_id", ""), intent)

    logger.info("[intent_classifier] ticket=%s intent=%s priority=%s",
                state.get("ticket_id"), intent, priority)

    return {"intent": intent, "priority": priority}


# ---------------------------------------------------------------------------
# Node 3: router
# ---------------------------------------------------------------------------

def router(state: TicketState) -> Dict[str, Any]:
    """
    Route the ticket to the correct specialist agent.

    This is a pure conditional node — no LLM call. It simply records which
    agent will handle the ticket so the conditional edge in graph.py can
    route to the right node.

    The routing decision is deterministic and logged for auditability.
    """
    intent = state.get("intent", "general")
    agent_map = {
        "billing": "BillingAgent",
        "technical": "TechAgent",
        "general": "GeneralAgent",
        "escalate": "EscalationHandler",
    }
    assigned = agent_map.get(intent, "GeneralAgent")

    logger.info("[router] ticket=%s routing to %s", state.get("ticket_id"), assigned)
    return {"assigned_agent": assigned}


# ---------------------------------------------------------------------------
# Shared helper: build specialist response
# ---------------------------------------------------------------------------

def _run_specialist(
    state: TicketState,
    kb_lookup_fn,
    agent_name: str,
    domain_label: str,
    system_prompt: str,
) -> Dict[str, Any]:
    """
    Generic specialist agent logic shared by billing, tech, and general agents.

    Steps:
    1. Look up the domain KB using TF-IDF retrieval.
    2. Compute confidence from retrieval scores.
    3. Build a prompt that includes KB excerpts + conversation history.
    4. Invoke Groq to generate a grounded, KB-backed response.
    5. Update session memory with the agent's response.

    Args:
        state:         Current TicketState.
        kb_lookup_fn:  The @tool function to call (lookup_billing_kb, etc.).
        agent_name:    Human-readable agent name for state / logging.
        domain_label:  Label used in the user-facing response footer.
        system_prompt: Domain-specific system instruction for the LLM.

    Returns:
        Dict with fields: assigned_agent, kb_results, agent_response,
        confidence_score, conversation_history.
    """
    user_message = state.get("user_message", "")
    session_id = state.get("session_id", "")
    ticket_id = state.get("ticket_id", "")

    # Step 1: KB retrieval
    try:
        kb_results_raw = kb_lookup_fn.invoke({"query": user_message})
    except Exception as exc:
        logger.error("[%s] KB lookup failed: %s", agent_name, exc)
        kb_results_raw = []

    # Step 2: Confidence from retrieval scores
    confidence = _compute_confidence(kb_results_raw)

    # Step 3: Build context strings
    kb_context = ""
    if kb_results_raw:
        kb_context = "\n\n".join(
            f"[Source: {r.get('source', 'KB')} | Score: {r.get('relevance_score', 0):.2f}]\n{r.get('content', '')}"
            for r in kb_results_raw
        )
    else:
        kb_context = "No relevant knowledge base articles found."

    history_context = session_memory.get_context(session_id, max_messages=8)

    user_prompt = f"""Conversation history:
{history_context if history_context else "(first message)"}

Knowledge base excerpts:
{kb_context}

Customer's current question:
{user_message}

Provide a clear, helpful, and concise response based on the knowledge base.
If the KB doesn't fully answer the question, say so honestly and suggest escalation."""

    # Step 4: Generate response
    try:
        llm = _get_llm(temperature=0.15)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        llm_response = llm.invoke(messages)
        agent_response = llm_response.content.strip()
    except Exception as exc:
        logger.error("[%s] LLM call failed: %s", agent_name, exc)
        agent_response = (
            f"I apologize, but I encountered an error while processing your request. "
            f"Please try again or contact support directly. (Error: {exc})"
        )
        confidence = 0.0  # Force escalation on LLM failure

    # Step 5: Update session memory
    session_memory.add_message(session_id, "ai", agent_response)
    history = session_memory.get_history(session_id)

    # Extract plain text chunks for state.kb_results
    kb_chunks = [r.get("content", "") for r in kb_results_raw]

    logger.info(
        "[%s] ticket=%s confidence=%.3f kb_hits=%d",
        agent_name, ticket_id, confidence, len(kb_results_raw)
    )

    return {
        "assigned_agent": agent_name,
        "kb_results": kb_chunks,
        "agent_response": agent_response,
        "confidence_score": confidence,
        "conversation_history": history,
        "metadata": {
            **state.get("metadata", {}),
            "kb_sources": [r.get("source", "") for r in kb_results_raw],
            "kb_scores": [r.get("relevance_score", 0.0) for r in kb_results_raw],
        },
    }


# ---------------------------------------------------------------------------
# Node 4: billing_agent
# ---------------------------------------------------------------------------

_BILLING_SYSTEM_PROMPT = """You are a knowledgeable and empathetic Billing Support Agent.

Your responsibilities:
- Answer questions about pricing plans, invoices, refunds, subscriptions, and payments.
- Always reference the provided knowledge base excerpts when answering.
- Be transparent about what the KB says and what you are unsure about.
- If a refund or billing adjustment is needed, explain the process clearly.
- Never make up pricing or policy details not found in the KB.

Tone: Professional, empathetic, and solution-oriented.
Format: Concise paragraphs. Use bullet points for multi-step processes."""


def billing_agent(state: TicketState) -> Dict[str, Any]:
    """
    Handle billing-related support tickets.

    Retrieves from the billing KB (pricing, refunds, invoices, subscriptions),
    computes confidence from retrieval scores, and generates a grounded response
    using Groq llama-3.3-70b.
    """
    return _run_specialist(
        state=state,
        kb_lookup_fn=lookup_billing_kb,
        agent_name="BillingAgent",
        domain_label="Billing",
        system_prompt=_BILLING_SYSTEM_PROMPT,
    )


# ---------------------------------------------------------------------------
# Node 5: tech_agent
# ---------------------------------------------------------------------------

_TECH_SYSTEM_PROMPT = """You are an expert Technical Support Agent.

Your responsibilities:
- Diagnose and resolve software issues, API errors, integration problems, and setup questions.
- Reference the knowledge base excerpts precisely. Quote error codes and exact steps.
- For API issues, always ask for relevant details (endpoint, HTTP status, request payload).
- Provide step-by-step troubleshooting instructions when applicable.
- If the issue requires a code fix or patch, acknowledge this and escalate appropriately.

Tone: Technical, precise, and methodical.
Format: Use numbered steps for troubleshooting. Use code blocks (```code```) for commands."""


def tech_agent(state: TicketState) -> Dict[str, Any]:
    """
    Handle technical support tickets.

    Retrieves from the technical KB (setup, API docs, error codes, integrations),
    computes confidence from retrieval scores, and generates a precise technical
    response using Groq llama-3.3-70b.
    """
    return _run_specialist(
        state=state,
        kb_lookup_fn=lookup_tech_kb,
        agent_name="TechAgent",
        domain_label="Technical",
        system_prompt=_TECH_SYSTEM_PROMPT,
    )


# ---------------------------------------------------------------------------
# Node 6: general_agent
# ---------------------------------------------------------------------------

_GENERAL_SYSTEM_PROMPT = """You are a friendly and knowledgeable General Support Agent.

Your responsibilities:
- Answer questions about company policies, service availability, contact information,
  account management, privacy practices, and general FAQs.
- Always base your answers on the provided knowledge base excerpts.
- If a question falls outside your scope, direct the user to the right team.

Tone: Warm, approachable, and clear.
Format: Conversational paragraphs. Keep answers concise (2–4 sentences per point)."""


def general_agent(state: TicketState) -> Dict[str, Any]:
    """
    Handle general FAQ and policy tickets.

    Retrieves from the general KB (company info, SLA, policies, contacts),
    computes confidence from retrieval scores, and generates a friendly
    response using Groq llama-3.3-70b.
    """
    return _run_specialist(
        state=state,
        kb_lookup_fn=lookup_general_kb,
        agent_name="GeneralAgent",
        domain_label="General",
        system_prompt=_GENERAL_SYSTEM_PROMPT,
    )


# ---------------------------------------------------------------------------
# Node 7: confidence_check
# ---------------------------------------------------------------------------

def confidence_check(state: TicketState) -> Dict[str, Any]:
    """
    Evaluate the agent's confidence score and decide whether to escalate.

    This node does NOT change any state fields — it simply logs the decision.
    The actual routing is done by the conditional edge in graph.py that reads
    state["confidence_score"] and state["escalated"].

    Threshold is configurable via the CONFIDENCE_THRESHOLD env variable
    (default 0.6). Setting it higher increases escalation frequency (safer);
    setting it lower reduces HITL load (faster).
    """
    confidence = state.get("confidence_score", 0.0)
    ticket_id = state.get("ticket_id", "")
    threshold = _CONFIDENCE_THRESHOLD

    if confidence < threshold:
        logger.info(
            "[confidence_check] ticket=%s ESCALATING (confidence=%.3f < threshold=%.3f)",
            ticket_id, confidence, threshold
        )
    else:
        logger.info(
            "[confidence_check] ticket=%s OK (confidence=%.3f >= threshold=%.3f)",
            ticket_id, confidence, threshold
        )

    # No state changes; routing is handled by the conditional edge
    return {}


# ---------------------------------------------------------------------------
# Node 8: escalation_handler
# ---------------------------------------------------------------------------

def escalation_handler(state: TicketState) -> Dict[str, Any]:
    """
    Handle tickets that require Human-in-the-Loop intervention.

    Actions:
    1. Call escalate_to_human tool to notify a human agent.
    2. Update the ticket record with escalated status.
    3. Generate a user-facing message explaining the escalation.
    4. Set escalated=True in state so the graph can terminate gracefully.

    The graph is configured with `interrupt_before=["escalation_handler"]`
    so a human agent can review the ticket before this node runs in
    production. In the demo, interrupt is handled programmatically.
    """
    ticket_id = state.get("ticket_id", "")
    priority = state.get("priority", "medium")
    confidence = state.get("confidence_score", 0.0)
    session_id = state.get("session_id", "")

    reason = (
        f"Automated agent confidence ({confidence:.0%}) is below the threshold "
        f"({_CONFIDENCE_THRESHOLD:.0%}). This ticket requires human review."
    )

    # Call escalation tool
    try:
        escalation_result = escalate_to_human.invoke({
            "ticket_id": ticket_id,
            "reason": reason,
            "priority": priority,
        })
        estimated_wait = escalation_result.get("estimated_wait", "1–2 hours")
        escalation_id = escalation_result.get("escalation_id", "N/A")
    except Exception as exc:
        logger.error("[escalation_handler] escalate_to_human failed: %s", exc)
        estimated_wait = "as soon as possible"
        escalation_id = "N/A"

    # Update ticket status
    try:
        update_ticket.invoke({
            "ticket_id": ticket_id,
            "status": "escalated",
            "notes": f"Escalated to human agent. Reason: {reason}",
        })
    except Exception as exc:
        logger.error("[escalation_handler] update_ticket failed: %s", exc)

    # Generate user-facing escalation message
    escalation_message = (
        f"Thank you for your patience. Your question requires specialized attention "
        f"that goes beyond what our automated system can confidently answer right now.\n\n"
        f"**Your ticket has been escalated to a human support specialist.**\n\n"
        f"- Ticket ID: `{ticket_id}`\n"
        f"- Escalation ID: `{escalation_id}`\n"
        f"- Priority: {priority.capitalize()}\n"
        f"- Estimated response time: {estimated_wait}\n\n"
        f"You will receive a follow-up via email or the same channel you used to contact us. "
        f"If this is urgent, please call our support line at +1-800-SUPPORT."
    )

    # Add to session memory
    session_memory.add_message(session_id, "ai", escalation_message)
    history = session_memory.get_history(session_id)

    logger.info("[escalation_handler] ticket=%s escalated, escalation_id=%s",
                ticket_id, escalation_id)

    return {
        "escalated": True,
        "resolved": False,
        "agent_response": escalation_message,
        "conversation_history": history,
        "metadata": {
            **state.get("metadata", {}),
            "escalation_id": escalation_id,
            "escalation_reason": reason,
            "estimated_wait": estimated_wait,
        },
    }


# ---------------------------------------------------------------------------
# Node 9: responder
# ---------------------------------------------------------------------------

def responder(state: TicketState) -> Dict[str, Any]:
    """
    Finalize and format the agent's response for delivery to the user.

    Responsibilities:
    - Mark the ticket as resolved (agent was confident).
    - Update the ticket record in the tool store.
    - Ensure the agent_response is clean and well-formatted.

    The agent_response field is already set by the specialist agent node.
    This node adds the ticket reference footer and marks resolution.
    """
    ticket_id = state.get("ticket_id", "")
    agent_response = state.get("agent_response", "")
    assigned_agent = state.get("assigned_agent", "SupportAgent")
    confidence = state.get("confidence_score", 0.0)

    # Append a ticket reference footer
    footer = (
        f"\n\n---\n*Ticket: `{ticket_id}` | Agent: {assigned_agent} | "
        f"Confidence: {confidence:.0%}*"
    )
    final_response = agent_response + footer

    # Mark ticket as resolved
    try:
        update_ticket.invoke({
            "ticket_id": ticket_id,
            "status": "resolved",
            "notes": f"Resolved by {assigned_agent} with confidence {confidence:.2f}.",
        })
    except Exception as exc:
        logger.warning("[responder] update_ticket failed (non-critical): %s", exc)

    logger.info("[responder] ticket=%s resolved by %s", ticket_id, assigned_agent)

    return {
        "agent_response": final_response,
        "resolved": True,
        "escalated": False,
    }


# ---------------------------------------------------------------------------
# Node 10: hitl_resume
# ---------------------------------------------------------------------------

_HITL_SYSTEM_PROMPT = """You are a senior customer support specialist reviewing a case
that was escalated from the automated support system.

A junior agent attempted to answer but lacked confidence. You have been given:
1. The customer's original question.
2. The human agent's notes and resolution.
3. The conversation history.

Write a final, definitive, and empathetic response that resolves the customer's issue.
Incorporate the human agent's notes into your response naturally — do not just copy them verbatim.
Keep the response professional and solution-focused."""


def hitl_resume(state: TicketState) -> Dict[str, Any]:
    """
    Resume processing after a human agent has reviewed the escalated ticket.

    This node is invoked when the graph is resumed after an interrupt.
    The human agent's notes are available in state["human_agent_notes"].

    Steps:
    1. Read human_agent_notes from state.
    2. Use Groq to generate a polished final response incorporating the notes.
    3. Mark the ticket as resolved.
    4. Update session memory.
    """
    ticket_id = state.get("ticket_id", "")
    session_id = state.get("session_id", "")
    user_message = state.get("user_message", "")
    human_notes = state.get("human_agent_notes") or "The issue has been reviewed and resolved."
    history_context = session_memory.get_context(session_id, max_messages=10)

    user_prompt = f"""Conversation history:
{history_context if history_context else "(not available)"}

Customer's original question: {user_message}

Human agent's resolution notes: {human_notes}

Write the final customer-facing response."""

    try:
        llm = _get_llm(temperature=0.2)
        messages = [
            SystemMessage(content=_HITL_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        llm_response = llm.invoke(messages)
        final_response = llm_response.content.strip()
    except Exception as exc:
        logger.error("[hitl_resume] LLM call failed: %s", exc)
        final_response = (
            f"Thank you for your patience. Our support team has reviewed your case. "
            f"{human_notes}\n\nIf you have further questions, please don't hesitate to reach out."
        )

    footer = f"\n\n---\n*Ticket: `{ticket_id}` | Resolved by Human Agent*"
    final_response += footer

    # Update ticket record
    try:
        update_ticket.invoke({
            "ticket_id": ticket_id,
            "status": "resolved",
            "notes": f"Resolved after human review. Notes: {human_notes}",
        })
    except Exception as exc:
        logger.warning("[hitl_resume] update_ticket failed: %s", exc)

    # Update session memory
    session_memory.add_message(session_id, "ai", final_response)
    history = session_memory.get_history(session_id)

    logger.info("[hitl_resume] ticket=%s resolved after HITL", ticket_id)

    return {
        "agent_response": final_response,
        "resolved": True,
        "escalated": False,
        "conversation_history": history,
    }
