"""
Tests for intent routing and graph flow.

These tests verify:
1. Intent classification produces correct routing decisions.
2. Low confidence scores trigger HITL escalation.
3. Multi-turn sessions preserve conversation history.

Test strategy:
- Intent classification tests mock the LLM to avoid API calls and ensure
  deterministic results. This also makes tests fast and offline-capable.
- Graph-level tests use enable_hitl=False to skip HITL interrupts.
- The confidence escalation test directly patches the confidence_score
  in state to decouple it from KB content.

Running:
    pytest tests/test_routing.py -v
"""

from __future__ import annotations

import os
import sys
import json
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set dummy env vars before importing modules that call load_dotenv
os.environ.setdefault("GROQ_API_KEY", "test-api-key-placeholder")
os.environ.setdefault("KB_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base"))
os.environ.setdefault("CONFIDENCE_THRESHOLD", "0.6")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def support_graph():
    """Build a support graph with HITL disabled for testing."""
    from agent.graph import build_support_graph
    return build_support_graph(enable_hitl=False)


@pytest.fixture
def fresh_session_id():
    """Generate a unique session ID for each test."""
    return f"TEST-SES-{uuid.uuid4().hex[:6].upper()}"


def _make_llm_response(content: str) -> MagicMock:
    """Create a mock LLM response with the given content string."""
    mock_response = MagicMock()
    mock_response.content = content
    return mock_response


# ---------------------------------------------------------------------------
# Test: billing intent classification
# ---------------------------------------------------------------------------

class TestBillingIntentClassification:
    """Tests that billing-related messages route to the BillingAgent."""

    @patch("agent.nodes.ChatGroq")
    def test_billing_intent_classification(self, mock_chatgroq, fresh_session_id):
        """
        'I need a refund' should be classified as billing intent.

        We mock the LLM to return a deterministic JSON response so the test
        does not depend on the Groq API or its response variability.
        """
        # Set up the mock LLM instance
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance

        # intent_classifier LLM response
        mock_llm_instance.invoke.return_value = _make_llm_response(
            '{"intent": "billing", "priority": "medium"}'
        )

        from agent.nodes import intent_classifier
        state = {
            "session_id": fresh_session_id,
            "user_message": "I need a refund for my last payment",
            "ticket_id": f"TKT-{uuid.uuid4().hex[:6].upper()}",
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

        result = intent_classifier(state)
        assert result["intent"] == "billing", (
            f"Expected 'billing' but got '{result['intent']}'"
        )
        assert result["priority"] in {"low", "medium", "high", "urgent"}

    @patch("agent.nodes.ChatGroq")
    def test_billing_routes_to_billing_agent(self, mock_chatgroq, support_graph, fresh_session_id):
        """
        A ticket classified as billing should have assigned_agent='BillingAgent'.

        This test mocks the entire LLM to control all LLM-dependent nodes.
        """
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance

        # First call: intent_classifier → billing
        # Second call: billing_agent → response
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "billing", "priority": "medium"}'),
            _make_llm_response(
                "Our refund policy allows refunds within 30 days of purchase. "
                "Please go to Settings > Billing > Refund Request to submit your request."
            ),
        ]

        from agent.graph import process_ticket
        result = process_ticket(
            message="How do I get a refund?",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        assert result.get("assigned_agent") == "BillingAgent", (
            f"Expected BillingAgent but got {result.get('assigned_agent')}"
        )


# ---------------------------------------------------------------------------
# Test: technical intent classification
# ---------------------------------------------------------------------------

class TestTechnicalIntentClassification:
    """Tests that API/technical messages route to TechAgent."""

    @patch("agent.nodes.ChatGroq")
    def test_tech_intent_classification(self, mock_chatgroq, fresh_session_id):
        """
        'API returns 401 error' should be classified as technical intent.
        """
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _make_llm_response(
            '{"intent": "technical", "priority": "high"}'
        )

        from agent.nodes import intent_classifier
        state = {
            "session_id": fresh_session_id,
            "user_message": "My API is returning a 401 Unauthorized error",
            "ticket_id": f"TKT-{uuid.uuid4().hex[:6].upper()}",
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

        result = intent_classifier(state)
        assert result["intent"] == "technical", (
            f"Expected 'technical' but got '{result['intent']}'"
        )

    @patch("agent.nodes.ChatGroq")
    def test_tech_routes_to_tech_agent(self, mock_chatgroq, support_graph, fresh_session_id):
        """Technical intent should route to TechAgent."""
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "technical", "priority": "high"}'),
            _make_llm_response(
                "A 401 error means your API key is invalid or missing. "
                "Check that you are passing 'Authorization: Bearer YOUR_API_KEY' in the header."
            ),
        ]

        from agent.graph import process_ticket
        result = process_ticket(
            message="API returns 401 error on every request",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        assert result.get("assigned_agent") == "TechAgent", (
            f"Expected TechAgent but got {result.get('assigned_agent')}"
        )


# ---------------------------------------------------------------------------
# Test: general intent classification
# ---------------------------------------------------------------------------

class TestGeneralIntentClassification:
    """Tests that FAQ/general messages route to GeneralAgent."""

    @patch("agent.nodes.ChatGroq")
    def test_general_intent_classification(self, mock_chatgroq, fresh_session_id):
        """
        'What are your hours?' should be classified as general intent.
        """
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _make_llm_response(
            '{"intent": "general", "priority": "low"}'
        )

        from agent.nodes import intent_classifier
        state = {
            "session_id": fresh_session_id,
            "user_message": "What are your office hours?",
            "ticket_id": f"TKT-{uuid.uuid4().hex[:6].upper()}",
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

        result = intent_classifier(state)
        assert result["intent"] == "general", (
            f"Expected 'general' but got '{result['intent']}'"
        )
        assert result["priority"] == "low"

    @patch("agent.nodes.ChatGroq")
    def test_general_routes_to_general_agent(self, mock_chatgroq, support_graph, fresh_session_id):
        """General intent should route to GeneralAgent."""
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "general", "priority": "low"}'),
            _make_llm_response(
                "Our general support hours are Monday–Friday, 8 AM–8 PM EST. "
                "You can also reach us anytime via email at support@support-platform.com."
            ),
        ]

        from agent.graph import process_ticket
        result = process_ticket(
            message="What are your hours of operation?",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        assert result.get("assigned_agent") == "GeneralAgent", (
            f"Expected GeneralAgent but got {result.get('assigned_agent')}"
        )


# ---------------------------------------------------------------------------
# Test: low confidence triggers escalation
# ---------------------------------------------------------------------------

class TestEscalationOnLowConfidence:
    """Tests that tickets with low confidence are escalated."""

    @patch("agent.nodes.ChatGroq")
    @patch("agent.nodes._compute_confidence", return_value=0.1)
    def test_low_confidence_triggers_escalation(
        self, mock_confidence, mock_chatgroq, support_graph, fresh_session_id
    ):
        """
        When confidence_score < CONFIDENCE_THRESHOLD (0.6), the ticket
        should be escalated (escalated=True, resolved=False).

        We patch _compute_confidence to return 0.1 (very low) regardless
        of KB content, making the test deterministic without needing to
        manipulate the KB.
        """
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "technical", "priority": "medium"}'),
            _make_llm_response("I have some information but I am not very confident."),
        ]

        from agent.graph import process_ticket
        result = process_ticket(
            message="Why is my quantum entanglement integration not working with your API?",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        assert result.get("escalated") is True, (
            "Expected ticket to be escalated but it was not. "
            f"confidence_score={result.get('confidence_score')}"
        )
        assert result.get("resolved") is False, (
            "Escalated ticket should not be marked resolved"
        )


# ---------------------------------------------------------------------------
# Test: multi-turn preserves history
# ---------------------------------------------------------------------------

class TestMultiTurnHistory:
    """Tests that session history is preserved across multiple turns."""

    @patch("agent.nodes.ChatGroq")
    def test_multi_turn_preserves_history(self, mock_chatgroq, support_graph, fresh_session_id):
        """
        The second message in a session should have the first message
        in its conversation_history.

        This verifies SessionMemory correctly accumulates messages and
        the intake node retrieves the full history for each new ticket.
        """
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance

        # Turn 1: billing question
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "billing", "priority": "low"}'),
            _make_llm_response("The Professional plan costs $99/month and includes 25 users."),
        ]

        from agent.graph import process_ticket
        from agent.memory import session_memory as sm

        result1 = process_ticket(
            message="What is included in the Professional plan?",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        # Verify first message was stored
        history_after_turn1 = sm.get_history(fresh_session_id)
        assert len(history_after_turn1) >= 2, (  # at least: user msg + agent response
            f"Expected >= 2 messages after turn 1, got {len(history_after_turn1)}"
        )

        # Turn 2: follow-up question
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "billing", "priority": "low"}'),
            _make_llm_response("Yes, the Professional plan includes 100 GB of storage."),
        ]

        result2 = process_ticket(
            message="And how much storage does it include?",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        # Verify history grew
        history_after_turn2 = sm.get_history(fresh_session_id)
        assert len(history_after_turn2) > len(history_after_turn1), (
            "History should grow after a second turn"
        )

        # Verify conversation_history in the second result contains prior context
        conv_history = result2.get("conversation_history", [])
        assert len(conv_history) >= 2, (
            f"Second result should have at least 2 messages in history, got {len(conv_history)}"
        )

    @patch("agent.nodes.ChatGroq")
    def test_session_id_is_preserved(self, mock_chatgroq, support_graph, fresh_session_id):
        """
        The session_id returned in the state should match the one provided.
        """
        mock_llm_instance = MagicMock()
        mock_chatgroq.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            _make_llm_response('{"intent": "general", "priority": "low"}'),
            _make_llm_response("Our support hours are Monday to Friday, 9 AM to 6 PM EST."),
        ]

        from agent.graph import process_ticket
        result = process_ticket(
            message="What are your support hours?",
            session_id=fresh_session_id,
            graph=support_graph,
        )

        assert result.get("session_id") == fresh_session_id, (
            f"Expected session_id={fresh_session_id} but got {result.get('session_id')}"
        )


# ---------------------------------------------------------------------------
# Test: router node (pure unit test — no LLM)
# ---------------------------------------------------------------------------

class TestRouter:
    """Unit tests for the router node (no LLM involved)."""

    def test_router_billing(self):
        """billing intent → BillingAgent."""
        from agent.nodes import router
        result = router({"intent": "billing", "ticket_id": "T1"})
        assert result["assigned_agent"] == "BillingAgent"

    def test_router_technical(self):
        """technical intent → TechAgent."""
        from agent.nodes import router
        result = router({"intent": "technical", "ticket_id": "T2"})
        assert result["assigned_agent"] == "TechAgent"

    def test_router_general(self):
        """general intent → GeneralAgent."""
        from agent.nodes import router
        result = router({"intent": "general", "ticket_id": "T3"})
        assert result["assigned_agent"] == "GeneralAgent"

    def test_router_escalate(self):
        """escalate intent → EscalationHandler."""
        from agent.nodes import router
        result = router({"intent": "escalate", "ticket_id": "T4"})
        assert result["assigned_agent"] == "EscalationHandler"

    def test_router_unknown_defaults_to_general(self):
        """Unknown intent should fall back to GeneralAgent."""
        from agent.nodes import router
        result = router({"intent": "unknown_xyz", "ticket_id": "T5"})
        assert result["assigned_agent"] == "GeneralAgent"
