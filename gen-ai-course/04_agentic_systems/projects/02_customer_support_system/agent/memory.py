"""
Memory subsystem for the Multi-Agent Customer Support System.

Two distinct memory types are implemented here:

1. KnowledgeBaseMemory (long-term, domain-specific, read-mostly)
   - Loads Markdown/text documents from disk at startup.
   - Uses scikit-learn TF-IDF + cosine similarity for retrieval.
   - NOTE: The search() signature is identical to what a FAISS-backed
     implementation would expose, so swapping the backend requires only
     replacing the _build_index() and search() internals.

2. SessionMemory (short-term, per-user, read-write)
   - In-memory dict keyed by session_id.
   - Stores LangChain BaseMessage objects so the history can be fed
     directly to any ChatModel.
   - Provides a context string formatter for injecting history into prompts.

Pattern rationale:
- Keeping KB memory and session memory separate respects the Single
  Responsibility Principle and makes each independently testable.
- TF-IDF is chosen over FAISS for zero-dependency local operation (no GPU,
  no external API). FAISS upgrade path is documented inline.
"""

from __future__ import annotations

import os
import re
import glob
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from agent.state import KBResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Knowledge Base Memory
# ---------------------------------------------------------------------------

class KnowledgeBaseMemory:
    """
    Manages a domain-specific knowledge base backed by TF-IDF retrieval.

    Documents are loaded from *.md and *.txt files in `kb_dir/<domain>/`
    (or directly from `kb_dir` if no sub-directory exists). Each file is
    split into overlapping chunks to improve recall for long documents.

    FAISS upgrade path:
        Replace `_build_index()` with a FAISS IndexFlatIP build over
        sentence-transformer embeddings, and replace `search()` with an
        index.search() call. The public interface stays identical.

    Args:
        domain: One of "billing", "technical", "general". Used for logging
                and to locate domain-specific files.
        kb_dir: Root directory that contains the knowledge base files.
    """

    CHUNK_SIZE = 400       # characters per chunk
    CHUNK_OVERLAP = 80     # character overlap between consecutive chunks

    def __init__(self, domain: str, kb_dir: str) -> None:
        self.domain = domain
        self.kb_dir = kb_dir
        self._chunks: List[str] = []
        self._sources: List[str] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None  # sparse TF-IDF matrix, shape (n_chunks, vocab)

        self._load_documents()
        self._build_index()

    # ------------------------------------------------------------------
    # Document loading
    # ------------------------------------------------------------------

    def _load_documents(self) -> None:
        """
        Load all *.md and *.txt files from kb_dir, filtering by domain name.

        Files are matched by checking whether `domain` appears in the filename
        (e.g., `billing_kb.md` → domain "billing"). Falls back to all files
        in the directory if no domain-matching file is found.
        """
        kb_path = Path(self.kb_dir)
        if not kb_path.exists():
            logger.warning("KB directory %s does not exist. Starting empty.", kb_path)
            return

        # Find all candidate files
        all_files: List[Path] = []
        for pattern in ("*.md", "*.txt"):
            all_files.extend(kb_path.glob(pattern))
            all_files.extend(kb_path.rglob(f"{self.domain}*{pattern[1:]}"))

        # De-duplicate and filter to domain-relevant files
        seen = set()
        domain_files: List[Path] = []
        for f in all_files:
            if f in seen:
                continue
            seen.add(f)
            if self.domain in f.stem.lower() or not any(
                d in f.stem.lower() for d in ["billing", "technical", "general"]
            ):
                domain_files.append(f)

        if not domain_files:
            logger.warning("No KB files found for domain '%s' in %s", self.domain, kb_path)
            return

        for file_path in domain_files:
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                chunks = self._split_into_chunks(text)
                for chunk in chunks:
                    self._chunks.append(chunk)
                    self._sources.append(file_path.name)
                logger.info(
                    "Loaded %d chunks from %s for domain '%s'",
                    len(chunks), file_path.name, self.domain
                )
            except Exception as exc:
                logger.error("Failed to load %s: %s", file_path, exc)

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval granularity.

        Using character-based chunking (rather than sentence splitting) keeps
        the implementation dependency-free. Overlap ensures that sentences
        straddling chunk boundaries are captured in at least one chunk.
        """
        if not text.strip():
            return []

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.CHUNK_SIZE, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            start = end - self.CHUNK_OVERLAP

        return chunks

    # ------------------------------------------------------------------
    # Index construction
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        """
        Build a TF-IDF index over all loaded chunks.

        TF-IDF with sublinear term frequency dampening is well-suited for
        short support queries because it down-weights extremely common words
        (e.g., "the", "is") while still capturing domain-specific terminology
        (e.g., "invoice", "webhook", "OAuth").
        """
        if not self._chunks:
            logger.warning("No chunks to index for domain '%s'.", self.domain)
            return

        self._vectorizer = TfidfVectorizer(
            sublinear_tf=True,
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2),  # unigrams + bigrams for better phrase matching
            stop_words="english",
        )
        self._matrix = self._vectorizer.fit_transform(self._chunks)
        logger.info(
            "TF-IDF index built: %d chunks, %d features for domain '%s'",
            len(self._chunks), self._matrix.shape[1], self.domain
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 3) -> List[KBResult]:
        """
        Retrieve the top-k most relevant chunks for a query.

        Args:
            query:  Natural-language search query from the support ticket.
            top_k:  Maximum number of results to return.

        Returns:
            List of KBResult dicts sorted by relevance_score descending.
            Returns an empty list if the index has no documents.
        """
        if self._vectorizer is None or self._matrix is None:
            logger.warning("No index available for domain '%s'. Returning empty.", self.domain)
            return []

        try:
            query_vec = self._vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self._matrix).flatten()

            # Get indices of top-k scores
            top_indices = np.argsort(scores)[::-1][:top_k]

            results: List[KBResult] = []
            for idx in top_indices:
                score = float(scores[idx])
                if score > 0.0:  # filter zero-relevance results
                    results.append(
                        KBResult(
                            content=self._chunks[idx],
                            source=self._sources[idx],
                            relevance_score=round(score, 4),
                        )
                    )
            return results

        except Exception as exc:
            logger.error("Search failed for domain '%s': %s", self.domain, exc)
            return []

    def add_document(self, content: str, metadata: Dict) -> None:
        """
        Add a new document to the knowledge base and rebuild the index.

        This is an O(n) rebuild — acceptable for the infrequent case of adding
        new KB articles. For high-volume ingestion, batch updates are preferred.

        Args:
            content:  Plain-text or Markdown content to add.
            metadata: Dict with optional keys: source (str), tags (List[str]).
        """
        source = metadata.get("source", f"{self.domain}_dynamic.md")
        chunks = self._split_into_chunks(content)
        for chunk in chunks:
            self._chunks.append(chunk)
            self._sources.append(source)

        # Rebuild the index to incorporate the new chunks
        self._build_index()
        logger.info(
            "Added %d chunks from source '%s' to domain '%s'. Index rebuilt.",
            len(chunks), source, self.domain
        )

    @property
    def document_count(self) -> int:
        """Return the number of indexed chunks."""
        return len(self._chunks)

    @property
    def is_ready(self) -> bool:
        """True if the index has been built and has at least one chunk."""
        return self._vectorizer is not None and len(self._chunks) > 0


# ---------------------------------------------------------------------------
# Session Memory
# ---------------------------------------------------------------------------

class SessionMemory:
    """
    In-memory conversation history store keyed by session_id.

    Design decisions:
    - Uses a plain dict (not Redis/SQLite) to keep the demo dependency-free.
      For production, swap `self._store` with a Redis-backed implementation
      behind the same interface.
    - Stores LangChain BaseMessage objects so the history can be passed
      directly to any ChatGroq / ChatOpenAI call without conversion.
    - Each session also carries a SessionContext metadata dict for statistics.
    """

    def __init__(self) -> None:
        # {session_id: List[BaseMessage]}
        self._store: Dict[str, List[BaseMessage]] = {}
        # {session_id: dict} — lightweight session metadata
        self._contexts: Dict[str, Dict] = {}

    # ------------------------------------------------------------------
    # Message management
    # ------------------------------------------------------------------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Append a message to the session's conversation history.

        Args:
            session_id: Unique session identifier.
            role:       "human", "ai", or "system".
            content:    Message text.
        """
        if session_id not in self._store:
            self._store[session_id] = []
            self._contexts[session_id] = {
                "session_id": session_id,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "ticket_ids": [],
                "message_count": 0,
                "dominant_intent": None,
            }

        role_lower = role.lower()
        if role_lower in ("human", "user"):
            msg: BaseMessage = HumanMessage(content=content)
        elif role_lower in ("ai", "assistant", "agent"):
            msg = AIMessage(content=content)
        else:
            msg = SystemMessage(content=content)

        self._store[session_id].append(msg)
        self._contexts[session_id]["message_count"] += 1
        self._contexts[session_id]["last_active"] = datetime.datetime.utcnow().isoformat()

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """
        Return the full message history for a session.

        Args:
            session_id: Unique session identifier.

        Returns:
            Ordered list of BaseMessage objects (oldest first).
            Returns an empty list if the session does not exist.
        """
        return self._store.get(session_id, [])

    def get_context(self, session_id: str, max_messages: int = 10) -> str:
        """
        Format the most recent `max_messages` as a plain-text string.

        This formatted string is injected into agent prompts so the LLM
        understands what was discussed earlier in the session without needing
        to re-parse BaseMessage objects.

        Args:
            session_id:   Unique session identifier.
            max_messages: Maximum number of recent messages to include.

        Returns:
            Multi-line string with "User: ..." / "Agent: ..." prefixes,
            or an empty string if the session has no history.
        """
        history = self._store.get(session_id, [])
        if not history:
            return ""

        recent = history[-max_messages:]
        lines: List[str] = []
        for msg in recent:
            if isinstance(msg, HumanMessage):
                lines.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                lines.append(f"Agent: {msg.content}")
            elif isinstance(msg, SystemMessage):
                lines.append(f"System: {msg.content}")
            else:
                lines.append(f"Message: {msg.content}")

        return "\n".join(lines)

    def clear_session(self, session_id: str) -> None:
        """
        Remove all history for the given session.

        Args:
            session_id: Unique session identifier to clear.
        """
        self._store.pop(session_id, None)
        self._contexts.pop(session_id, None)
        logger.info("Session '%s' cleared.", session_id)

    def register_ticket(self, session_id: str, ticket_id: str) -> None:
        """Associate a ticket_id with the session for tracking purposes."""
        if session_id in self._contexts:
            self._contexts[session_id].setdefault("ticket_ids", []).append(ticket_id)

    def update_intent(self, session_id: str, intent: str) -> None:
        """Track the most-recently-seen intent for the session."""
        if session_id in self._contexts:
            self._contexts[session_id]["dominant_intent"] = intent

    def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Return session metadata, or None if the session does not exist."""
        return self._contexts.get(session_id)

    def list_sessions(self) -> List[str]:
        """Return all active session IDs."""
        return list(self._store.keys())

    def __len__(self) -> int:
        """Return the number of active sessions."""
        return len(self._store)


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
# These global instances are shared across all nodes and tools.
# They are initialized lazily on first import so that unit tests can
# override KB_DIR before importing this module.

import os as _os
from dotenv import load_dotenv as _load_dotenv

_load_dotenv()

_KB_DIR = _os.getenv("KB_DIR", "./data/knowledge_base")

billing_kb = KnowledgeBaseMemory(domain="billing", kb_dir=_KB_DIR)
tech_kb = KnowledgeBaseMemory(domain="technical", kb_dir=_KB_DIR)
general_kb = KnowledgeBaseMemory(domain="general", kb_dir=_KB_DIR)
session_memory = SessionMemory()

logger.info(
    "Memory initialized — billing: %d chunks, tech: %d chunks, general: %d chunks",
    billing_kb.document_count,
    tech_kb.document_count,
    general_kb.document_count,
)
