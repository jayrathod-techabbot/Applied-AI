"""
memory.py - Short-term and context memory for the data analysis pipeline.

WHY two separate memory classes:
  ConversationMemory   – tracks the human/AI message sequence for the chat
                         interface. Feeds the answerer node so it can reference
                         prior questions and avoid repeating itself.
  DatasetContextMemory – stores structured analysis artefacts (summary, results,
                         charts) that are too large for a flat message buffer.
                         The context_retriever node queries this to inject
                         relevant facts into the follow-up answer prompt.

WHY in-memory storage (not Redis/vector DB):
  The pipeline is designed for single-session analysis of one dataset at a time.
  Persistence across server restarts is handled at the API layer via a session
  dict. A future production upgrade would swap the list buffers for a Redis
  hash or a vector store with semantic retrieval.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class ConversationMemory:
    """
    A rolling window buffer of LangChain BaseMessage objects.

    WHY rolling window (max_messages): LLM context windows are finite.
    Keeping the last N messages prevents context overflow while retaining
    enough history for coherent multi-turn dialogue.

    Attributes:
        session_id:   Unique ID of the analysis session.
        max_messages: Maximum number of messages to retain (default 50).
    """

    def __init__(self, session_id: str, max_messages: int = 50) -> None:
        self.session_id = session_id
        self.max_messages = max_messages
        self._messages: List[BaseMessage] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_human_message(self, text: str) -> None:
        """Append a user turn to the buffer."""
        self._messages.append(HumanMessage(content=text))
        self._trim()

    def add_ai_message(self, text: str) -> None:
        """Append an AI turn to the buffer."""
        self._messages.append(AIMessage(content=text))
        self._trim()

    def add_system_message(self, text: str) -> None:
        """Prepend a system context message (does not count toward the window)."""
        self._messages.insert(0, SystemMessage(content=text))

    def add_message(self, message: BaseMessage) -> None:
        """Append any BaseMessage subclass directly."""
        self._messages.append(message)
        self._trim()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_history(self) -> List[BaseMessage]:
        """Return the full retained message list."""
        return list(self._messages)

    def get_history_as_text(self) -> str:
        """
        Return a plain-text transcript for injection into prompts.

        Format: 'Human: ...\nAI: ...\n'
        """
        lines: List[str] = []
        for msg in self._messages:
            if isinstance(msg, HumanMessage):
                role = "Human"
            elif isinstance(msg, AIMessage):
                role = "AI"
            elif isinstance(msg, SystemMessage):
                role = "System"
            else:
                role = msg.__class__.__name__
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def get_last_n(self, n: int) -> List[BaseMessage]:
        """Return only the most recent n messages."""
        return self._messages[-n:]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Wipe all messages from memory."""
        self._messages.clear()

    def _trim(self) -> None:
        """Enforce the rolling-window limit (removes oldest messages)."""
        if len(self._messages) > self.max_messages:
            # Preserve any leading SystemMessages
            system_msgs = [m for m in self._messages if isinstance(m, SystemMessage)]
            non_system = [m for m in self._messages if not isinstance(m, SystemMessage)]
            excess = len(non_system) - (self.max_messages - len(system_msgs))
            if excess > 0:
                non_system = non_system[excess:]
            self._messages = system_msgs + non_system

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"ConversationMemory(session_id={self.session_id!r}, messages={len(self._messages)})"


# ---------------------------------------------------------------------------

class DatasetContextMemory:
    """
    Stores structured analysis artefacts for a single dataset session.

    The context_retriever node calls `get_context_for_query` to produce a
    focused text block that is injected into the follow-up answer prompt,
    avoiding the need to re-run the full analysis graph.

    Internal storage layout::

        {
            "dataset_summary": {...},            # DatasetSummary dict
            "analysis_results": [...],           # List[AnalysisResult dict]
            "charts": [...],                     # List[ChartOutput dict]
            "reflection": {...},                 # ReflectionOutput dict
            "final_report": "...",               # Markdown text
            "analysis_plan": [...],              # List[str]
            "created_at": "ISO timestamp",
        }

    Attributes:
        session_id: Unique ID of the analysis session.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._context: Dict[str, Any] = {
            "dataset_summary": None,
            "analysis_results": [],
            "charts": [],
            "reflection": None,
            "final_report": "",
            "analysis_plan": [],
            "created_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def update_dataset_summary(self, summary: Dict[str, Any]) -> None:
        """Store the DatasetSummary dict produced by data_profiler."""
        self._context["dataset_summary"] = summary

    def update_analysis_plan(self, plan: List[str]) -> None:
        """Store the ordered list of analysis steps from the planner."""
        self._context["analysis_plan"] = plan

    def add_analysis_result(self, result: Dict[str, Any]) -> None:
        """Append a single AnalysisResult dict."""
        self._context["analysis_results"].append(result)

    def update_analysis_results(self, results: List[Dict[str, Any]]) -> None:
        """Replace the full list of analysis results."""
        self._context["analysis_results"] = results

    def update_charts(self, charts: List[Dict[str, Any]]) -> None:
        """Store the list of ChartOutput dicts."""
        self._context["charts"] = charts

    def update_reflection(self, reflection: Dict[str, Any]) -> None:
        """Store the ReflectionOutput dict."""
        self._context["reflection"] = reflection

    def update_final_report(self, report: str) -> None:
        """Store the final markdown report."""
        self._context["final_report"] = report

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_dataset_summary(self) -> Optional[Dict[str, Any]]:
        """Return the stored dataset summary, or None."""
        return self._context.get("dataset_summary")

    def get_analysis_results(self) -> List[Dict[str, Any]]:
        """Return the list of analysis result dicts."""
        return self._context.get("analysis_results", [])

    def get_final_report(self) -> str:
        """Return the final markdown report text."""
        return self._context.get("final_report", "")

    def get_context_for_query(self, query: str, max_results: int = 5) -> str:
        """
        Retrieve relevant context for a follow-up query as a formatted text block.

        WHY keyword scoring: simple but effective for structured analysis data.
        Each analysis result is scored by how many query words appear in its
        step description and findings text, and the top-K are returned.

        Args:
            query:       The user's follow-up question.
            max_results: Maximum number of analysis results to include.

        Returns:
            A formatted string ready for injection into an LLM prompt.
        """
        query_words = set(query.lower().split())
        blocks: List[str] = []

        # --- Dataset summary ---
        summary = self._context.get("dataset_summary")
        if summary:
            columns = summary.get("columns", [])
            shape = summary.get("shape", [])
            blocks.append(
                f"**Dataset**: {shape[0] if shape else '?'} rows × "
                f"{shape[1] if len(shape) > 1 else '?'} columns. "
                f"Columns: {', '.join(columns[:15])}{'...' if len(columns) > 15 else ''}."
            )

        # --- Analysis results (keyword ranked) ---
        results = self._context.get("analysis_results", [])
        scored: List[tuple] = []
        for res in results:
            text = f"{res.get('step', '')} {res.get('findings', '')}".lower()
            score = sum(1 for w in query_words if w in text)
            scored.append((score, res))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_results = scored[:max_results]

        for _, res in top_results:
            step = res.get("step", "")
            findings = res.get("findings", "")
            if step or findings:
                blocks.append(f"**{step}**: {findings}")

        # --- Charts available ---
        charts = self._context.get("charts", [])
        if charts:
            chart_titles = [c.get("title", "") for c in charts]
            blocks.append(f"**Charts generated**: {', '.join(chart_titles)}.")

        # --- Final report snippet (first 800 chars) ---
        report = self._context.get("final_report", "")
        if report:
            snippet = report[:800].replace("\n", " ")
            blocks.append(f"**Report excerpt**: {snippet}...")

        return "\n\n".join(blocks) if blocks else "No prior analysis context available."

    def get_full_context(self) -> Dict[str, Any]:
        """Return the complete internal context dict (for serialisation)."""
        return dict(self._context)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Reset the context store."""
        self._context = {
            "dataset_summary": None,
            "analysis_results": [],
            "charts": [],
            "reflection": None,
            "final_report": "",
            "analysis_plan": [],
            "created_at": datetime.utcnow().isoformat(),
        }

    def to_json(self) -> str:
        """
        Serialise the context to a JSON string.

        Non-serialisable values (e.g. numpy scalars) are cast to str.
        """
        return json.dumps(self._context, default=str, indent=2)

    def __repr__(self) -> str:
        n_results = len(self._context.get("analysis_results", []))
        return (
            f"DatasetContextMemory(session_id={self.session_id!r}, "
            f"analysis_results={n_results})"
        )


# ---------------------------------------------------------------------------
# Module-level session registry
# ---------------------------------------------------------------------------
# WHY a module-level dict: both the graph nodes and the API routes need to
# access the same memory objects for a given session_id. A module-level
# registry provides a lightweight singleton store without a database.

_conversation_store: Dict[str, ConversationMemory] = {}
_context_store: Dict[str, DatasetContextMemory] = {}


def get_or_create_conversation_memory(session_id: str) -> ConversationMemory:
    """Return existing ConversationMemory for the session, or create a new one."""
    if session_id not in _conversation_store:
        _conversation_store[session_id] = ConversationMemory(session_id=session_id)
    return _conversation_store[session_id]


def get_or_create_context_memory(session_id: str) -> DatasetContextMemory:
    """Return existing DatasetContextMemory for the session, or create a new one."""
    if session_id not in _context_store:
        _context_store[session_id] = DatasetContextMemory(session_id=session_id)
    return _context_store[session_id]


def clear_session(session_id: str) -> None:
    """Remove all memory for a session (e.g. on explicit logout / expiry)."""
    _conversation_store.pop(session_id, None)
    _context_store.pop(session_id, None)
