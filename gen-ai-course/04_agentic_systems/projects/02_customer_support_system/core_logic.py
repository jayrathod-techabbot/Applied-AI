"""
core_logic.py — Standalone Demo for the Multi-Agent Customer Support System

This script demonstrates all key architectural patterns end-to-end without
requiring a running FastAPI server or Streamlit UI. Each section is heavily
commented to explain the design rationale.

Run: python core_logic.py

Prerequisites:
  - GROQ_API_KEY set in .env or as an environment variable
  - Python dependencies installed: pip install -r requirements.txt
"""

from __future__ import annotations

import os
import sys
import uuid
import time
import json
import logging
from typing import Any, Dict, List

# Load environment variables FIRST before any module imports
from dotenv import load_dotenv
load_dotenv()

# Set up logging for a clean demo output
logging.basicConfig(
    level=logging.WARNING,  # Suppress INFO logs during demo for cleaner output
    format="%(levelname)s | %(name)s | %(message)s"
)

# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def section(title: str):
    """Print a prominent section header."""
    width = 70
    print(f"\n{'='*width}")
    print(f"  {title}")
    print(f"{'='*width}")


def subsection(title: str):
    """Print a subsection header."""
    print(f"\n{'-'*50}")
    print(f"  {title}")
    print(f"{'-'*50}")


def print_result(label: str, value: Any):
    """Print a key-value pair with formatting."""
    if isinstance(value, (dict, list)):
        print(f"  {label}:")
        print(f"    {json.dumps(value, indent=4, default=str)[:500]}")
    else:
        print(f"  {label}: {value}")


# ===========================================================================
# SECTION 1: Knowledge Base Initialization
# ===========================================================================
# WHY: We use TF-IDF (scikit-learn) instead of FAISS for the demo because:
#   1. Zero external dependencies (no GPU, no API key for embeddings).
#   2. The interface is identical to what a FAISS-backed implementation
#      would expose, so the upgrade is a pure internal swap.
#   3. TF-IDF works well for support tickets where keyword matching matters
#      more than semantic similarity (e.g., "401 error" → 401 articles).

section("1. Knowledge Base Initialization")

print("\n[Pattern] Vector Memory (TF-IDF backend, FAISS-upgradeable)")
print("""
  Each domain (billing, technical, general) has its own KnowledgeBaseMemory
  instance. This separation means:
  - The billing agent never retrieves technical articles (less noise).
  - KB files can be updated independently per domain.
  - We can swap the retrieval backend per domain (e.g., FAISS for technical,
    BM25 for billing) without changing the graph structure.
""")

try:
    from agent.memory import billing_kb, tech_kb, general_kb, session_memory

    print("  KB Loading Results:")
    print(f"    Billing KB  : {billing_kb.document_count} chunks | Ready: {billing_kb.is_ready}")
    print(f"    Technical KB: {tech_kb.document_count} chunks | Ready: {tech_kb.is_ready}")
    print(f"    General KB  : {general_kb.document_count} chunks | Ready: {general_kb.is_ready}")

    # Show a sample search to confirm the index is working
    print("\n  Sample KB search: 'refund policy 30 days'")
    results = billing_kb.search("refund policy 30 days", top_k=2)
    for i, r in enumerate(results, 1):
        print(f"    Result {i}: source={r['source']}, score={r['relevance_score']:.3f}")
        print(f"             content preview: {r['content'][:120]}...")

except Exception as e:
    print(f"  ERROR loading KB: {e}")
    print("  Make sure KB_DIR is set correctly in .env")
    sys.exit(1)


# ===========================================================================
# SECTION 2: Intent Classification Demo (3 ticket types)
# ===========================================================================
# WHY: Intent classification is the core routing mechanism.
#   - We use a Reactive Agent pattern: observe (user message + history) →
#     classify → act (route to specialist).
#   - Groq llama-3.3-70b is used because:
#     a. 8k context handles long conversation histories.
#     b. Sub-second latency (~200ms) is critical for real-time chat.
#     c. llama-3.3-70b scores well on instruction-following benchmarks,
#        which is critical for reliable JSON output parsing.
#   - We use temperature=0.0 for classification (need determinism).

section("2. Intent Classification — 3 Ticket Types")

print("\n[Pattern] Reactive Agent — intent_classifier node")
print("""
  The intent_classifier node:
  1. Takes the user message + last 6 messages of conversation history.
  2. Calls Groq llama-3.3-70b with a strict JSON-only prompt.
  3. Returns {"intent": "billing|technical|general|escalate", "priority": "..."}
  4. Falls back to {"intent": "general", "priority": "medium"} on parse failure.

  Including conversation history is critical for multi-turn accuracy.
  Example: "What about the refund for that?" requires knowing the prior
  topic was billing to be classified correctly.
""")

test_tickets = [
    {
        "description": "Billing ticket",
        "message": "I was charged twice this month and need a refund for the duplicate charge.",
        "expected_intent": "billing",
    },
    {
        "description": "Technical ticket",
        "message": "My webhook is not receiving events. I get a 200 from your API but nothing arrives at my endpoint.",
        "expected_intent": "technical",
    },
    {
        "description": "General ticket",
        "message": "Do you have offices in Europe? What are your support hours for UK customers?",
        "expected_intent": "general",
    },
]

groq_available = bool(os.getenv("GROQ_API_KEY", "").startswith("gsk_"))

if not groq_available:
    print("\n  ⚠️  GROQ_API_KEY not set or invalid. Showing simulated output.")
    print("     Set GROQ_API_KEY=gsk_... in .env to run live classification.\n")
    for ticket in test_tickets:
        print(f"  [{ticket['description']}]")
        print(f"    Message : {ticket['message'][:80]}...")
        print(f"    SIMULATED Intent: {ticket['expected_intent']} | Priority: medium")
else:
    from agent.nodes import intent_classifier

    for ticket in test_tickets:
        print(f"\n  [{ticket['description']}]")
        print(f"    Message: {ticket['message'][:80]}...")

        session_id = f"DEMO-{uuid.uuid4().hex[:6]}"
        state = {
            "session_id": session_id,
            "user_message": ticket["message"],
            "ticket_id": f"TKT-DEMO-{uuid.uuid4().hex[:6]}",
            "intent": "",
            "priority": "medium",
            "metadata": {},
            "conversation_history": [],
            "kb_results": [],
            "agent_response": "",
            "confidence_score": 0.0,
            "escalated": False,
            "human_agent_notes": None,
            "assigned_agent": "",
            "resolved": False,
        }

        try:
            result = intent_classifier(state)
            intent = result["intent"]
            priority = result["priority"]
            correct = "✅" if intent == ticket["expected_intent"] else "⚠️"
            print(f"    Intent  : {intent} {correct} (expected: {ticket['expected_intent']})")
            print(f"    Priority: {priority}")
        except Exception as e:
            print(f"    ERROR: {e}")


# ===========================================================================
# SECTION 3: Build the Support Graph
# ===========================================================================
# WHY Hub-and-Spoke architecture:
#   - The Orchestrator (intent_classifier + router) is the hub.
#   - Specialists (BillingAgent, TechAgent, GeneralAgent) are the spokes.
#   - Benefits:
#     a. Easy to add new specialist agents without touching existing ones.
#     b. The orchestrator is the only node that needs to "know" about all agents.
#     c. Each specialist can have its own KB, tools, and prompt style.
#   - Alternative (Mesh): Every agent can communicate with every other agent.
#     Mesh is more flexible but harder to reason about and debug.

section("3. Support Graph — Hub-and-Spoke Architecture")

print("""
[Pattern] Hierarchical Multi-Agent (Orchestrator → Specialists)

  Graph topology:

    intake
      └─► intent_classifier (Hub / Orchestrator)
            └─► router
                  ├─► billing_agent  ─┐
                  ├─► tech_agent     ─┼─► confidence_check
                  ├─► general_agent  ─┘       ├─► (conf < 0.6) → escalation_handler → END
                  └─► escalation_handler       └─► (conf >= 0.6) → responder → END

  State travels through the graph, accumulating information at each node.
  No direct agent-to-agent communication — all coordination goes through state.
""")

try:
    from agent.graph import build_support_graph, process_ticket
    graph = build_support_graph(enable_hitl=False)
    print("  Support graph compiled successfully.")
except Exception as e:
    print(f"  ERROR building graph: {e}")
    sys.exit(1)


# ===========================================================================
# SECTION 4: Billing Ticket End-to-End
# ===========================================================================
# WHY this matters:
#   The billing agent demonstrates the full KB-grounded response pattern:
#   1. TF-IDF retrieval → find relevant billing KB sections
#   2. Confidence scoring → derived from retrieval scores (auditable)
#   3. LLM generation → grounded in KB, no hallucination of pricing data

section("4. Billing Ticket — End-to-End")

print("""
[Pattern] KB-Grounded Response Generation

  Why ground responses in KB?
  - Without KB: LLM may hallucinate pricing ($29 vs $39, for example).
  - With KB: LLM is constrained to cite actual plan details from the KB.
  - Confidence derived from KB retrieval scores makes escalation auditable.

  Billing confidence scoring:
    top_result_score * 0.6 + second_result * 0.3 + third_result * 0.1
    Then scaled by 2.5 (TF-IDF max ~0.4 maps to confidence ~1.0)
""")

billing_message = "I need a refund. I was charged for the Professional plan but I cancelled 3 days ago."
print(f"\n  User message: {billing_message}\n")

if not groq_available:
    print("  [SIMULATED — set GROQ_API_KEY to run live]")
    print("  KB Results: 2 billing chunks retrieved (refund policy, cancellation)")
    print("  Confidence Score: 0.72 (above 0.6 threshold)")
    print("  Agent: BillingAgent")
    print("  Response: Refunds are available within 30 days. Go to Settings > Billing...")
else:
    session_id = f"DEMO-BILLING-{uuid.uuid4().hex[:6]}"
    try:
        start = time.time()
        result = process_ticket(message=billing_message, session_id=session_id, graph=graph)
        elapsed = time.time() - start

        print(f"  Intent          : {result.get('intent')}")
        print(f"  Agent           : {result.get('assigned_agent')}")
        print(f"  Confidence Score: {result.get('confidence_score', 0):.3f}")
        print(f"  Escalated       : {result.get('escalated')}")
        print(f"  Resolved        : {result.get('resolved')}")
        print(f"  KB Sources      : {result.get('metadata', {}).get('kb_sources', [])}")
        print(f"  Processing Time : {elapsed:.2f}s")
        print(f"\n  Response:\n")
        response = result.get('agent_response', '')
        print(f"    {response[:800]}")
    except Exception as e:
        print(f"  ERROR: {e}")


# ===========================================================================
# SECTION 5: Technical Ticket
# ===========================================================================

section("5. Technical Ticket — API Error Troubleshooting")

print("""
[Pattern] Domain-Specific Specialist Agent

  The TechAgent is configured with:
  - A system prompt that emphasizes precision and step-by-step instructions.
  - Access to the technical KB (API docs, error codes, troubleshooting).
  - Temperature=0.15 (slightly higher than classifier) for varied but accurate responses.
""")

tech_message = "I keep getting HTTP 429 errors from your API. My integration is on the Professional plan."
print(f"\n  User message: {tech_message}\n")

if not groq_available:
    print("  [SIMULATED]")
    print("  Intent: technical | Agent: TechAgent | Confidence: 0.68")
    print("  Response: HTTP 429 means rate limit exceeded. Professional plan allows 300 req/min...")
else:
    session_id = f"DEMO-TECH-{uuid.uuid4().hex[:6]}"
    try:
        result = process_ticket(message=tech_message, session_id=session_id, graph=graph)
        print(f"  Intent          : {result.get('intent')}")
        print(f"  Agent           : {result.get('assigned_agent')}")
        print(f"  Confidence Score: {result.get('confidence_score', 0):.3f}")
        print(f"\n  Response:\n")
        print(f"    {result.get('agent_response', '')[:600]}")
    except Exception as e:
        print(f"  ERROR: {e}")


# ===========================================================================
# SECTION 6: General Ticket
# ===========================================================================

section("6. General Ticket — Policy & Company Info")

general_message = "Is your platform GDPR compliant? We're a company based in Germany."
print(f"\n  User message: {general_message}\n")

if not groq_available:
    print("  [SIMULATED]")
    print("  Intent: general | Agent: GeneralAgent | Confidence: 0.74")
    print("  Response: Yes, we are GDPR compliant. EU customers have the right to...")
else:
    session_id = f"DEMO-GENERAL-{uuid.uuid4().hex[:6]}"
    try:
        result = process_ticket(message=general_message, session_id=session_id, graph=graph)
        print(f"  Intent          : {result.get('intent')}")
        print(f"  Agent           : {result.get('assigned_agent')}")
        print(f"  Confidence Score: {result.get('confidence_score', 0):.3f}")
        print(f"\n  Response:\n")
        print(f"    {result.get('agent_response', '')[:600]}")
    except Exception as e:
        print(f"  ERROR: {e}")


# ===========================================================================
# SECTION 7: Low Confidence → Escalation Trigger
# ===========================================================================
# WHY HITL escalation:
#   Customer support has HIGH stakes — a wrong answer about a $1000 charge
#   can cause churn or legal issues. We escalate when:
#   1. KB retrieval finds no relevant content (confidence = 0.0).
#   2. Retrieval scores are too low (weighted confidence < 0.6).
#
#   The threshold (0.6) is configurable via CONFIDENCE_THRESHOLD env var.
#   Lower threshold → fewer escalations but more risk of wrong answers.
#   Higher threshold → safer but more human agent load.

section("7. Low Confidence → HITL Escalation Simulation")

print("""
[Pattern] Human-in-the-Loop (HITL) Escalation

  Escalation trigger: confidence_score < CONFIDENCE_THRESHOLD (default: 0.6)

  How it works:
  1. Specialist agent runs, but KB has no relevant content.
  2. _compute_confidence() returns a low score (e.g., 0.05).
  3. confidence_check node evaluates: 0.05 < 0.6 → route to escalation_handler.
  4. escalation_handler calls escalate_to_human() tool, generates escalation message.
  5. Graph terminates with escalated=True.
  6. In production: graph pauses at interrupt_before=["escalation_handler"],
     a human reviews, and the graph resumes via resume_after_escalation().

  Benefits of explicit confidence scoring:
  - Auditable: we can explain WHY a ticket was escalated (not a black box).
  - Configurable: adjust threshold per domain or priority.
  - Graceful: user gets a clear escalation message, not a wrong answer.
""")

# Simulate low confidence by using an extremely obscure query
obscure_message = (
    "I need to integrate your platform with our custom Erlang-based distributed "
    "ledger using the Actor model for high-frequency trading compliance reporting."
)
print(f"\n  Obscure message (likely low KB relevance):")
print(f"  '{obscure_message[:100]}...'\n")

# Direct KB check to show why confidence would be low
print("  KB relevance check:")
billing_results = billing_kb.search(obscure_message, top_k=1)
tech_results = tech_kb.search(obscure_message, top_k=1)
general_results = general_kb.search(obscure_message, top_k=1)

for domain, results in [("billing", billing_results), ("technical", tech_results), ("general", general_results)]:
    score = results[0]["relevance_score"] if results else 0.0
    print(f"    {domain:10s} top score: {score:.4f}")

from agent.nodes import _compute_confidence
simulated_tech_confidence = _compute_confidence(tech_results)
print(f"\n  Simulated confidence for technical: {simulated_tech_confidence:.3f}")
print(f"  Threshold                         : {float(os.getenv('CONFIDENCE_THRESHOLD', '0.6')):.1f}")
escalate_flag = simulated_tech_confidence < float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
print(f"  Would trigger escalation          : {escalate_flag}")


# ===========================================================================
# SECTION 8: Multi-Turn Session Demo
# ===========================================================================
# WHY Buffer Memory for sessions:
#   - Buffer memory (a rolling window of N recent messages) is the right
#     choice for customer support because:
#     a. Most support conversations are resolved in < 10 turns.
#     b. The full history rarely fits in a 8k context LLM.
#     c. Recent context is more relevant than the first message.
#   - We use max_messages=10 in get_context() to stay within token limits.

section("8. Multi-Turn Session — Conversation Context")

print("""
[Pattern] Buffer Memory (SessionMemory)

  Session memory keeps a rolling window of messages per session_id.
  This enables:
  - Follow-up questions: "And for the Pro plan?" after discussing billing.
  - Pronoun resolution: "How do I fix it?" after discussing a specific error.
  - Personalization: agent knows what was already answered this session.

  Implementation: In-memory dict (session_id → List[BaseMessage]).
  Production upgrade: Replace with Redis + TTL for distributed deployments.
""")

multi_turn_session = f"DEMO-MULTI-{uuid.uuid4().hex[:6]}"

turns = [
    "What are the differences between your Starter and Professional plans?",
    "Great. And for the Professional plan, how do I upgrade from Starter?",
]

print(f"\n  Session ID: {multi_turn_session}")

if not groq_available:
    print("\n  [SIMULATED multi-turn output]")
    print("\n  Turn 1: 'What are the differences between Starter and Professional?'")
    print("    Agent: BillingAgent | Confidence: 0.75")
    print("    Response: Starter ($29/mo) offers 5 users, 10GB. Professional ($99/mo) offers 25 users, 100GB...")
    print("\n  Turn 2: 'And for Professional, how do I upgrade from Starter?'")
    print("    Agent: BillingAgent | Confidence: 0.71")
    print("    History includes Turn 1 — agent knows we're talking about plan differences.")
    print("    Response: To upgrade, go to Settings > Billing > Plan > Upgrade Plan...")
else:
    for i, message in enumerate(turns, 1):
        print(f"\n  Turn {i}: '{message}'")
        try:
            result = process_ticket(
                message=message,
                session_id=multi_turn_session,
                graph=graph,
            )

            print(f"    Agent     : {result.get('assigned_agent')}")
            print(f"    Intent    : {result.get('intent')}")
            print(f"    Confidence: {result.get('confidence_score', 0):.3f}")

            history = result.get("conversation_history", [])
            print(f"    History   : {len(history)} messages in context")

            response = result.get("agent_response", "")
            print(f"    Response  : {response[:300]}...")

        except Exception as e:
            print(f"    ERROR: {e}")


# ===========================================================================
# SECTION 9: Session Memory Contents
# ===========================================================================

section("9. Session Memory — State After Multi-Turn Demo")

print("""
[Pattern] State Inspection

  The session_memory object is a global singleton shared across all nodes.
  Here we inspect its state to verify that history was properly accumulated.
""")

from agent.memory import session_memory as sm

active_sessions = sm.list_sessions()
print(f"\n  Active sessions in memory: {len(active_sessions)}")

for session_id in active_sessions[:3]:  # Show first 3
    history = sm.get_history(session_id)
    ctx = sm.get_session_context(session_id)
    print(f"\n  Session: {session_id}")
    print(f"    Messages    : {len(history)}")
    print(f"    Dominant intent: {ctx.get('dominant_intent') if ctx else 'N/A'}")
    if history:
        print(f"    First message: {history[0].content[:80]}...")

if multi_turn_session in active_sessions:
    print(f"\n  Context string for multi-turn session (last 4 messages):")
    context = sm.get_context(multi_turn_session, max_messages=4)
    print(f"\n{context[:600]}")


# ===========================================================================
# Summary
# ===========================================================================

section("Summary — Patterns Demonstrated")

print("""
  Pattern                    | Implementation
  ---------------------------|---------------------------------------------
  Hub-and-Spoke Multi-Agent  | Orchestrator → BillingAgent/TechAgent/GeneralAgent
  Reactive Agent             | intent_classifier (observe → classify → route)
  Vector Memory              | TF-IDF KnowledgeBaseMemory (FAISS-upgradeable)
  Buffer Memory              | SessionMemory (rolling window, per session_id)
  HITL Escalation            | confidence_score < 0.6 → escalation_handler
  Hierarchical Orchestration | LangGraph StateGraph with conditional edges
  Thread-based State         | MemorySaver (one thread per ticket_id)

  All patterns work together:
  - Users submit messages → reactive classifier routes them
  - Specialists use vector memory for grounded responses
  - Buffer memory enables coherent multi-turn conversations
  - Low-confidence cases escalate to humans automatically
  - State machine (LangGraph) makes the flow inspectable and resumable
""")

print("\n  Demo complete. Run 'uvicorn api.routes:app --reload' for the API.")
print("  Run 'streamlit run ui/app.py' for the chat interface.\n")
