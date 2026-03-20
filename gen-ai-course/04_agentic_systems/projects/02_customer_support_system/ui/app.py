"""
Streamlit Chat Interface for the Multi-Agent Customer Support System.

Features:
- Real-time chat with message history and agent avatars
- Intent badges (billing=blue, technical=green, general=gray, escalated=red)
- Confidence score display per response
- Escalation panel with estimated wait time
- Sidebar: session info, ticket history, category statistics
- Knowledge base sources (expandable)
- Clickable sample questions as quick-start chips
- "New Conversation" button to reset session

Run: streamlit run ui/app.py
"""

from __future__ import annotations

import os
import sys
import time
import uuid
import logging
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path so we can import agent modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Customer Support",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Chat message container */
.chat-message {
    display: flex;
    align-items: flex-start;
    margin-bottom: 1rem;
    gap: 0.75rem;
}

/* Intent badges */
.badge-billing   { background: #1E88E5; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.badge-technical { background: #43A047; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.badge-general   { background: #757575; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.badge-escalated { background: #E53935; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.badge-unknown   { background: #9E9E9E; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }

/* Escalation panel */
.escalation-panel {
    background: #FFF3E0;
    border-left: 4px solid #FF6F00;
    padding: 1rem 1.25rem;
    border-radius: 0 8px 8px 0;
    margin-top: 0.5rem;
}

/* Confidence bar */
.confidence-high   { color: #2E7D32; font-weight: 600; }
.confidence-medium { color: #F57C00; font-weight: 600; }
.confidence-low    { color: #C62828; font-weight: 600; }

/* Sample question chip */
.sample-chip {
    display: inline-block;
    background: #E3F2FD;
    color: #1565C0;
    border: 1px solid #90CAF9;
    padding: 4px 12px;
    border-radius: 16px;
    cursor: pointer;
    font-size: 0.85rem;
    margin: 3px;
}

/* KB source tag */
.kb-source {
    background: #F5F5F5;
    color: #424242;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: monospace;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sample questions
# ---------------------------------------------------------------------------
SAMPLE_QUESTIONS = [
    "How do I get a refund?",
    "What's included in the Professional plan?",
    "My API is returning a 401 error",
    "How do I download my invoice?",
    "What are your office hours?",
    "My payment failed, what should I do?",
    "How do I set up webhooks?",
    "Can I pause my subscription?",
]

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def init_session_state():
    """Initialize all Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
    if "messages" not in st.session_state:
        st.session_state.messages = []  # List of dicts: {role, content, meta}
    if "ticket_history" not in st.session_state:
        st.session_state.ticket_history = []
    if "category_counts" not in st.session_state:
        st.session_state.category_counts = {"billing": 0, "technical": 0, "general": 0, "escalated": 0}
    if "pending_input" not in st.session_state:
        st.session_state.pending_input = None
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "escalated_tickets" not in st.session_state:
        st.session_state.escalated_tickets = []


def reset_session():
    """Reset all session state for a new conversation."""
    st.session_state.session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
    st.session_state.messages = []
    st.session_state.ticket_history = []
    st.session_state.category_counts = {"billing": 0, "technical": 0, "general": 0, "escalated": 0}
    st.session_state.escalated_tickets = []
    st.session_state.pending_input = None
    st.session_state.graph = None


# ---------------------------------------------------------------------------
# Graph initialization (lazy — only when first message is sent)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_cached_graph():
    """
    Build and cache the support graph as a Streamlit resource.
    st.cache_resource ensures only one graph instance is created
    across all user sessions (shared MemorySaver store).
    """
    try:
        from agent.graph import build_support_graph
        return build_support_graph(enable_hitl=False)  # No HITL interrupts in UI demo
    except Exception as exc:
        st.error(f"Failed to build support graph: {exc}")
        return None


# ---------------------------------------------------------------------------
# Badge helper
# ---------------------------------------------------------------------------

def intent_badge(intent: str) -> str:
    """Return an HTML badge string for the given intent."""
    intent = (intent or "unknown").lower()
    css_class = f"badge-{intent}" if intent in ("billing", "technical", "general", "escalated") else "badge-unknown"
    label = intent.capitalize()
    return f'<span class="{css_class}">{label}</span>'


def confidence_class(score: float) -> str:
    if score >= 0.7:
        return "confidence-high"
    elif score >= 0.5:
        return "confidence-medium"
    return "confidence-low"


# ---------------------------------------------------------------------------
# Process a message through the graph
# ---------------------------------------------------------------------------

def process_message(user_message: str) -> Dict[str, Any]:
    """
    Send the user message through the LangGraph support pipeline.

    Returns a dict with response details for display.
    """
    graph = get_cached_graph()
    if graph is None:
        return {
            "response": "System error: support graph could not be initialized. Please check your GROQ_API_KEY.",
            "intent": "general",
            "agent": "SystemError",
            "confidence_score": 0.0,
            "escalated": False,
            "ticket_id": "N/A",
            "kb_sources": [],
            "priority": "medium",
        }

    try:
        from agent.graph import process_ticket
        final_state = process_ticket(
            message=user_message,
            session_id=st.session_state.session_id,
            graph=graph,
            channel="streamlit",
        )

        return {
            "response": final_state.get("agent_response", "No response generated."),
            "intent": final_state.get("intent", "general"),
            "agent": final_state.get("assigned_agent", "SupportAgent"),
            "confidence_score": round(final_state.get("confidence_score", 0.0), 3),
            "escalated": final_state.get("escalated", False),
            "ticket_id": final_state.get("ticket_id", ""),
            "kb_sources": final_state.get("metadata", {}).get("kb_sources", []),
            "priority": final_state.get("priority", "medium"),
            "kb_scores": final_state.get("metadata", {}).get("kb_scores", []),
            "kb_results": final_state.get("kb_results", []),
        }
    except Exception as exc:
        logger.error("process_message failed: %s", exc, exc_info=True)
        return {
            "response": f"I encountered an error processing your request: {exc}",
            "intent": "general",
            "agent": "ErrorHandler",
            "confidence_score": 0.0,
            "escalated": False,
            "ticket_id": f"TKT-ERROR-{uuid.uuid4().hex[:4].upper()}",
            "kb_sources": [],
            "priority": "medium",
        }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render the sidebar with session info, ticket history, and stats."""
    with st.sidebar:
        st.markdown("## 🎧 Support System")
        st.markdown("---")

        # Session info
        st.markdown("### 📋 Session Info")
        st.code(st.session_state.session_id, language=None)

        # New conversation button
        if st.button("🔄 New Conversation", use_container_width=True, type="secondary"):
            reset_session()
            st.rerun()

        st.markdown("---")

        # Category statistics
        st.markdown("### 📊 Category Stats")
        counts = st.session_state.category_counts
        total = sum(counts.values()) or 1

        for category, count in counts.items():
            pct = int(count / total * 100)
            emoji = {"billing": "💳", "technical": "⚙️", "general": "ℹ️", "escalated": "🚨"}.get(category, "❓")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{emoji} **{category.capitalize()}**")
                st.progress(pct / 100)
            with col2:
                st.markdown(f"<br><b>{count}</b>", unsafe_allow_html=True)

        st.markdown("---")

        # Ticket history
        st.markdown("### 🎫 Ticket History")
        if st.session_state.ticket_history:
            for ticket in reversed(st.session_state.ticket_history[-10:]):
                status_emoji = "✅" if ticket.get("resolved") else "🚨" if ticket.get("escalated") else "🔄"
                badge_color = {
                    "billing": "#1E88E5",
                    "technical": "#43A047",
                    "general": "#757575",
                    "escalated": "#E53935",
                }.get(ticket.get("intent", ""), "#9E9E9E")

                st.markdown(
                    f"{status_emoji} `{ticket.get('ticket_id', 'N/A')}` "
                    f"<span style='background:{badge_color};color:white;padding:1px 6px;border-radius:8px;font-size:0.7rem'>"
                    f"{ticket.get('intent', '?').upper()}</span>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("No tickets yet in this session.")

        st.markdown("---")

        # KB Status
        st.markdown("### 📚 Knowledge Base Status")
        try:
            from agent.memory import billing_kb, tech_kb, general_kb
            for kb, name in [(billing_kb, "Billing"), (tech_kb, "Technical"), (general_kb, "General")]:
                status = "🟢" if kb.is_ready else "🔴"
                st.markdown(f"{status} **{name}**: {kb.document_count} chunks")
        except Exception:
            st.caption("KB status unavailable")

        st.markdown("---")
        st.caption("Powered by Groq llama-3.3-70b + LangGraph")


# ---------------------------------------------------------------------------
# Chat display
# ---------------------------------------------------------------------------

def render_chat_message(message: Dict[str, Any]):
    """Render a single chat message with metadata."""
    role = message["role"]
    content = message["content"]
    meta = message.get("meta", {})

    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(content)

    elif role == "assistant":
        agent_name = meta.get("agent", "Agent")
        avatar_map = {
            "BillingAgent": "💳",
            "TechAgent": "⚙️",
            "GeneralAgent": "ℹ️",
            "EscalationHandler": "🚨",
            "ErrorHandler": "❌",
        }
        avatar = avatar_map.get(agent_name, "🤖")

        with st.chat_message("assistant", avatar=avatar):
            # Metadata row
            intent = meta.get("intent", "")
            confidence = meta.get("confidence_score", 0.0)
            ticket_id = meta.get("ticket_id", "")
            escalated = meta.get("escalated", False)

            col1, col2, col3 = st.columns([2, 2, 3])
            with col1:
                st.markdown(
                    f"**{agent_name}** {intent_badge(intent)}",
                    unsafe_allow_html=True
                )
            with col2:
                conf_pct = int(confidence * 100)
                conf_cls = confidence_class(confidence)
                st.markdown(
                    f'<span class="{conf_cls}">Confidence: {conf_pct}%</span>',
                    unsafe_allow_html=True
                )
            with col3:
                if ticket_id:
                    st.caption(f"Ticket: `{ticket_id}`")

            # Main response content
            st.markdown(content)

            # Escalation panel
            if escalated:
                st.markdown(
                    """<div class="escalation-panel">
                    <strong>🚨 Escalated to Human Agent</strong><br>
                    Your ticket has been queued for human review.
                    A specialist will follow up via email.
                    </div>""",
                    unsafe_allow_html=True
                )

            # Knowledge base sources (expandable)
            kb_sources = meta.get("kb_sources", [])
            kb_scores = meta.get("kb_scores", [])
            kb_results = meta.get("kb_results", [])
            if kb_sources:
                with st.expander(f"📚 Knowledge base sources ({len(kb_sources)})"):
                    for i, source in enumerate(kb_sources):
                        score = kb_scores[i] if i < len(kb_scores) else 0.0
                        st.markdown(
                            f'<span class="kb-source">{source}</span> '
                            f'<span style="color:#9E9E9E; font-size:0.8rem">relevance: {score:.2f}</span>',
                            unsafe_allow_html=True
                        )
                        if i < len(kb_results):
                            st.caption(kb_results[i][:200] + "..." if len(kb_results[i]) > 200 else kb_results[i])
                        st.markdown("---")


# ---------------------------------------------------------------------------
# Sample questions
# ---------------------------------------------------------------------------

def render_sample_questions():
    """Render clickable sample question chips."""
    st.markdown("**Try asking:**")
    cols = st.columns(4)
    for i, question in enumerate(SAMPLE_QUESTIONS):
        with cols[i % 4]:
            if st.button(question, key=f"sample_{i}", use_container_width=True):
                st.session_state.pending_input = question
                st.rerun()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    """Main Streamlit application entry point."""
    init_session_state()
    render_sidebar()

    # Header
    st.title("🎧 AI Customer Support")
    st.markdown(
        "Ask me about **billing**, **technical issues**, or **general questions**. "
        "I'll route you to the right specialist instantly."
    )

    # Show sample questions only if no messages yet
    if not st.session_state.messages:
        render_sample_questions()
        st.markdown("---")

    # Render existing messages
    for message in st.session_state.messages:
        render_chat_message(message)

    # Handle pending input (from sample question chips)
    if st.session_state.pending_input:
        user_input = st.session_state.pending_input
        st.session_state.pending_input = None
    else:
        user_input = st.chat_input("Type your support question here...")

    # Process new input
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "meta": {},
        })

        # Display user message immediately
        render_chat_message({"role": "user", "content": user_input, "meta": {}})

        # Show spinner while processing
        with st.spinner("Connecting you to the right specialist..."):
            result = process_message(user_input)

        # Build assistant message
        assistant_msg = {
            "role": "assistant",
            "content": result["response"],
            "meta": {
                "agent": result["agent"],
                "intent": result["intent"],
                "confidence_score": result["confidence_score"],
                "escalated": result["escalated"],
                "ticket_id": result["ticket_id"],
                "kb_sources": result.get("kb_sources", []),
                "kb_scores": result.get("kb_scores", []),
                "kb_results": result.get("kb_results", []),
            },
        }

        st.session_state.messages.append(assistant_msg)

        # Update ticket history
        st.session_state.ticket_history.append({
            "ticket_id": result["ticket_id"],
            "intent": result["intent"],
            "escalated": result["escalated"],
            "resolved": not result["escalated"],
            "confidence_score": result["confidence_score"],
        })

        # Update category counts
        intent = result["intent"].lower()
        if result["escalated"]:
            st.session_state.category_counts["escalated"] += 1
            st.session_state.escalated_tickets.append(result["ticket_id"])
        elif intent in st.session_state.category_counts:
            st.session_state.category_counts[intent] += 1
        else:
            st.session_state.category_counts["general"] += 1

        # Display the assistant response
        render_chat_message(assistant_msg)

        # If escalated, show prominent escalation notice
        if result["escalated"]:
            st.warning(
                f"⏳ **Your ticket has been escalated.**\n\n"
                f"Ticket ID: `{result['ticket_id']}`\n"
                f"A human specialist will review your case and respond via email. "
                f"Thank you for your patience."
            )

        # Rerun to refresh sidebar stats
        st.rerun()


if __name__ == "__main__":
    main()
