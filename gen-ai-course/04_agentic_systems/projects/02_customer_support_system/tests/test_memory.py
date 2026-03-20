"""
Tests for the memory subsystem (KnowledgeBaseMemory and SessionMemory).

These tests are fully offline — no LLM API key needed. They verify:
1. KB search returns relevant results for domain-appropriate queries.
2. More relevant queries rank higher than less relevant ones.
3. Session memory correctly stores and retrieves messages.
4. Two sessions do not share history.
5. Adding a new document to the KB makes it searchable.

Running:
    pytest tests/test_memory.py -v
"""

from __future__ import annotations

import os
import sys
import uuid
import tempfile
from pathlib import Path
from typing import List

import pytest

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Point KB_DIR at the real knowledge base before importing memory
_KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
os.environ["KB_DIR"] = _KB_DIR
os.environ.setdefault("GROQ_API_KEY", "test-placeholder")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_kb_dir() -> str:
    """Return the path to the actual knowledge base directory."""
    return _KB_DIR


@pytest.fixture(scope="module")
def billing_memory(real_kb_dir):
    """Billing KnowledgeBaseMemory loaded from the real KB file."""
    from agent.memory import KnowledgeBaseMemory
    return KnowledgeBaseMemory(domain="billing", kb_dir=real_kb_dir)


@pytest.fixture(scope="module")
def tech_memory(real_kb_dir):
    """Technical KnowledgeBaseMemory loaded from the real KB file."""
    from agent.memory import KnowledgeBaseMemory
    return KnowledgeBaseMemory(domain="technical", kb_dir=real_kb_dir)


@pytest.fixture(scope="module")
def general_memory(real_kb_dir):
    """General KnowledgeBaseMemory loaded from the real KB file."""
    from agent.memory import KnowledgeBaseMemory
    return KnowledgeBaseMemory(domain="general", kb_dir=real_kb_dir)


@pytest.fixture
def session_mem():
    """Fresh SessionMemory instance for each test."""
    from agent.memory import SessionMemory
    return SessionMemory()


@pytest.fixture
def fresh_session_id() -> str:
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def another_session_id() -> str:
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Test: KB is ready after loading
# ---------------------------------------------------------------------------

class TestKBInitialization:
    """Verify that the KB loads documents and builds an index."""

    def test_billing_kb_is_ready(self, billing_memory):
        """Billing KB should have documents after loading billing_kb.md."""
        assert billing_memory.is_ready, "Billing KB should be ready (has indexed chunks)"

    def test_tech_kb_is_ready(self, tech_memory):
        """Technical KB should have documents after loading technical_kb.md."""
        assert tech_memory.is_ready, "Technical KB should be ready"

    def test_general_kb_is_ready(self, general_memory):
        """General KB should have documents after loading general_kb.md."""
        assert general_memory.is_ready, "General KB should be ready"

    def test_billing_kb_has_chunks(self, billing_memory):
        """Billing KB should have a meaningful number of indexed chunks."""
        assert billing_memory.document_count > 0, (
            f"Expected > 0 chunks but got {billing_memory.document_count}"
        )

    def test_kb_in_empty_dir_returns_empty(self):
        """A KB pointing to a non-existent directory should start empty."""
        from agent.memory import KnowledgeBaseMemory
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBaseMemory(domain="billing", kb_dir=tmpdir)
            assert kb.document_count == 0
            assert not kb.is_ready


# ---------------------------------------------------------------------------
# Test: KB search returns relevant results
# ---------------------------------------------------------------------------

class TestKBSearch:
    """Verify that KB search returns domain-appropriate results."""

    def test_kb_search_returns_relevant_billing(self, billing_memory):
        """
        A billing query should return results containing billing-related content.

        We check that at least one result's content mentions keywords expected
        in the billing KB (refund, invoice, plan, payment, etc.).
        """
        results = billing_memory.search("how do I get a refund", top_k=3)

        assert len(results) > 0, "Billing KB search should return at least one result"

        # Check that at least one result mentions refund-related content
        combined_content = " ".join(r["content"].lower() for r in results)
        billing_keywords = {"refund", "billing", "payment", "invoice", "plan", "subscription"}
        found_keywords = [kw for kw in billing_keywords if kw in combined_content]

        assert len(found_keywords) > 0, (
            f"Expected billing keywords in results but found none. "
            f"Content preview: {combined_content[:200]}"
        )

    def test_kb_search_returns_relevant_technical(self, tech_memory):
        """A technical query should return API/setup-related content."""
        results = tech_memory.search("API 401 authentication error", top_k=3)

        assert len(results) > 0, "Technical KB search should return at least one result"

        combined_content = " ".join(r["content"].lower() for r in results)
        tech_keywords = {"api", "401", "auth", "key", "bearer", "error", "unauthorized"}
        found_keywords = [kw for kw in tech_keywords if kw in combined_content]

        assert len(found_keywords) > 0, (
            f"Expected technical keywords in results. Content: {combined_content[:200]}"
        )

    def test_kb_search_returns_relevant_general(self, general_memory):
        """A general query should return company/contact-related content."""
        results = general_memory.search("what are your office hours", top_k=3)

        assert len(results) > 0, "General KB search should return at least one result"

        combined_content = " ".join(r["content"].lower() for r in results)
        general_keywords = {"hours", "support", "monday", "friday", "contact", "est", "am", "pm"}
        found_keywords = [kw for kw in general_keywords if kw in combined_content]

        assert len(found_keywords) > 0, (
            f"Expected general/hours keywords in results. Content: {combined_content[:200]}"
        )

    def test_kb_search_returns_at_most_top_k(self, billing_memory):
        """Search should return at most top_k results."""
        results = billing_memory.search("pricing plans", top_k=2)
        assert len(results) <= 2, f"Expected <= 2 results but got {len(results)}"

    def test_kb_search_empty_returns_list(self, billing_memory):
        """An empty query should return a list (possibly empty, no exception)."""
        results = billing_memory.search("", top_k=3)
        assert isinstance(results, list)

    def test_kb_search_gibberish_returns_empty_or_low_score(self, billing_memory):
        """
        A completely irrelevant query should return empty or very-low-score results.
        """
        results = billing_memory.search("xkcd purple elephant quantum teleport", top_k=3)
        # Either empty or all scores are very low
        for r in results:
            assert r["relevance_score"] < 0.3, (
                f"Gibberish query returned high-score result: {r}"
            )


# ---------------------------------------------------------------------------
# Test: KB search ranking
# ---------------------------------------------------------------------------

class TestKBSearchRanking:
    """Verify that more relevant queries score higher than less relevant ones."""

    def test_kb_search_ranking_refund(self, billing_memory):
        """
        A highly specific refund query should rank the refund section higher
        than a generic query. We compare top scores across two queries.
        """
        # Highly specific query — should match the refund policy section
        specific_results = billing_memory.search(
            "30 day money back guarantee refund policy purchase", top_k=1
        )
        # Generic query — low relevance expected
        generic_results = billing_memory.search("hello world", top_k=1)

        if not specific_results:
            pytest.skip("KB returned no results for specific query — check KB content")

        specific_score = specific_results[0]["relevance_score"] if specific_results else 0.0
        generic_score = generic_results[0]["relevance_score"] if generic_results else 0.0

        assert specific_score >= generic_score, (
            f"Expected specific query (score={specific_score:.3f}) to rank >= "
            f"generic query (score={generic_score:.3f})"
        )

    def test_kb_search_results_sorted_descending(self, billing_memory):
        """Results must be sorted by relevance_score in descending order."""
        results = billing_memory.search("invoice payment subscription billing", top_k=5)

        scores = [r["relevance_score"] for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"Results are not sorted descending: {scores}"
        )

    def test_kb_result_has_required_fields(self, billing_memory):
        """Each KBResult must have content, source, and relevance_score."""
        results = billing_memory.search("plan pricing", top_k=1)

        if not results:
            pytest.skip("No results returned")

        result = results[0]
        assert "content" in result, "KBResult missing 'content' field"
        assert "source" in result, "KBResult missing 'source' field"
        assert "relevance_score" in result, "KBResult missing 'relevance_score' field"
        assert isinstance(result["relevance_score"], float)
        assert 0.0 <= result["relevance_score"] <= 1.0


# ---------------------------------------------------------------------------
# Test: Session memory stores messages
# ---------------------------------------------------------------------------

class TestSessionMemoryStorage:
    """Verify that SessionMemory correctly stores and retrieves messages."""

    def test_session_memory_stores_messages(self, session_mem, fresh_session_id):
        """
        Messages added to a session should be retrievable in order.
        """
        session_mem.add_message(fresh_session_id, "human", "Hello, I need help.")
        session_mem.add_message(fresh_session_id, "ai", "Of course! How can I assist you?")
        session_mem.add_message(fresh_session_id, "human", "I need a refund.")

        history = session_mem.get_history(fresh_session_id)

        assert len(history) == 3, f"Expected 3 messages, got {len(history)}"

        # Verify order
        from langchain_core.messages import HumanMessage, AIMessage
        assert isinstance(history[0], HumanMessage)
        assert isinstance(history[1], AIMessage)
        assert isinstance(history[2], HumanMessage)
        assert history[0].content == "Hello, I need help."
        assert history[2].content == "I need a refund."

    def test_session_memory_empty_for_unknown_session(self, session_mem):
        """An unknown session ID should return an empty list, not raise."""
        result = session_mem.get_history("NONEXISTENT-SESSION")
        assert result == [], f"Expected empty list but got {result}"

    def test_session_memory_get_context_formats_correctly(self, session_mem, fresh_session_id):
        """
        get_context() should return a formatted string with 'User:' and 'Agent:' prefixes.
        """
        session_mem.add_message(fresh_session_id, "human", "What is the Professional plan?")
        session_mem.add_message(fresh_session_id, "ai", "It costs $99/month.")

        context = session_mem.get_context(fresh_session_id, max_messages=10)

        assert "User: What is the Professional plan?" in context
        assert "Agent: It costs $99/month." in context

    def test_session_memory_get_context_respects_max_messages(self, session_mem, fresh_session_id):
        """get_context(max_messages=2) should return only the last 2 messages."""
        for i in range(5):
            session_mem.add_message(fresh_session_id, "human", f"Question {i}")
            session_mem.add_message(fresh_session_id, "ai", f"Answer {i}")

        context = session_mem.get_context(fresh_session_id, max_messages=2)
        # Should only contain the last 2 messages (Question 4 and Answer 4)
        lines = [l for l in context.strip().split("\n") if l.strip()]
        assert len(lines) <= 2, f"Expected <= 2 lines but got {len(lines)}: {lines}"

    def test_session_memory_clear_removes_history(self, session_mem, fresh_session_id):
        """clear_session() should remove all messages."""
        session_mem.add_message(fresh_session_id, "human", "Test message")
        session_mem.clear_session(fresh_session_id)
        history = session_mem.get_history(fresh_session_id)
        assert history == [], f"Expected empty history after clear, got {history}"


# ---------------------------------------------------------------------------
# Test: Session isolation
# ---------------------------------------------------------------------------

class TestSessionIsolation:
    """Verify that two sessions do not share history."""

    def test_session_memory_isolation(self, session_mem, fresh_session_id, another_session_id):
        """
        Messages added to session A must not appear in session B's history.

        This is critical for multi-tenant support where different users
        must never see each other's conversations.
        """
        session_mem.add_message(fresh_session_id, "human", "I want a refund.")
        session_mem.add_message(fresh_session_id, "ai", "Refunds are available within 30 days.")

        session_mem.add_message(another_session_id, "human", "My API key stopped working.")
        session_mem.add_message(another_session_id, "ai", "Check your key in Settings > Developer.")

        history_a = session_mem.get_history(fresh_session_id)
        history_b = session_mem.get_history(another_session_id)

        # Each session should have exactly 2 messages
        assert len(history_a) == 2, f"Session A should have 2 messages, got {len(history_a)}"
        assert len(history_b) == 2, f"Session B should have 2 messages, got {len(history_b)}"

        # Session A's content should not appear in session B
        session_a_content = " ".join(m.content for m in history_a)
        session_b_content = " ".join(m.content for m in history_b)

        assert "refund" in session_a_content.lower()
        assert "refund" not in session_b_content.lower(), (
            "Session B should not contain Session A's refund message"
        )
        assert "api key" in session_b_content.lower()
        assert "api key" not in session_a_content.lower()

    def test_session_len_tracks_active_sessions(self, session_mem, fresh_session_id, another_session_id):
        """len(session_mem) should count distinct sessions."""
        initial_count = len(session_mem)
        session_mem.add_message(fresh_session_id, "human", "Message 1")
        session_mem.add_message(another_session_id, "human", "Message 2")
        # Two new sessions were added
        assert len(session_mem) >= initial_count + 2


# ---------------------------------------------------------------------------
# Test: KB can add document
# ---------------------------------------------------------------------------

class TestKBAddDocument:
    """Verify that new documents become searchable after being added."""

    def test_kb_can_add_document(self, real_kb_dir):
        """
        After adding a document with a unique term, searching for that term
        should return the added document.

        We use a uniquely misspelled word to avoid false positives from
        existing KB content.
        """
        from agent.memory import KnowledgeBaseMemory

        # Create a fresh KB pointing at the real KB dir
        kb = KnowledgeBaseMemory(domain="billing", kb_dir=real_kb_dir)
        initial_count = kb.document_count

        unique_term = "zxqvblorp"  # Nonsense word guaranteed not to be in the KB
        kb.add_document(
            content=f"This is a test article about {unique_term} pricing for enterprise customers.",
            metadata={"source": "test_dynamic_article.md"},
        )

        # Document count should increase
        assert kb.document_count > initial_count, (
            "document_count should increase after adding a document"
        )

        # The unique term should now be searchable
        results = kb.search(unique_term, top_k=1)
        assert len(results) > 0, (
            f"Expected to find the added document when searching for '{unique_term}'"
        )
        assert unique_term in results[0]["content"].lower(), (
            f"Expected '{unique_term}' in search result content"
        )

    def test_kb_added_document_source_is_tracked(self, real_kb_dir):
        """The source metadata of an added document should appear in results."""
        from agent.memory import KnowledgeBaseMemory

        kb = KnowledgeBaseMemory(domain="technical", kb_dir=real_kb_dir)
        custom_source = "dynamic_test_source.md"
        unique_content = "flobznix webhook configuration tutorial for advanced users"

        kb.add_document(
            content=unique_content,
            metadata={"source": custom_source},
        )

        results = kb.search("flobznix webhook", top_k=1)
        if results:
            assert results[0]["source"] == custom_source, (
                f"Expected source='{custom_source}' but got '{results[0]['source']}'"
            )
