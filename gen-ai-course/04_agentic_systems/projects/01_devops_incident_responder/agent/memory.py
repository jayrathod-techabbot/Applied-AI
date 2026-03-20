"""
agent/memory.py

Long-term memory components for the AI DevOps Incident Responder.

Design Decisions:
- RunbookMemory: Loads markdown runbooks into a TF-IDF index at startup.
  This is a "read-heavy" store — runbooks change rarely, so we index once
  and query many times. Documented upgrade path to FAISS for semantic search.

- IncidentHistoryMemory: Persists resolved incidents as JSON files keyed by
  incident_id. Provides keyword-based similarity search so future incidents
  can benefit from past resolutions — a lightweight form of case-based
  reasoning without requiring a vector database.

Both classes are designed to be stateless between requests (load from disk
every time) to avoid stale in-memory state in long-running API servers.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import datetime
from math import log
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class RunbookMemory:
    """
    In-memory TF-IDF index over markdown runbook files.

    Usage:
        memory = RunbookMemory(runbook_dir="./data/runbooks")
        results = memory.search("high CPU utilization upstream timeout")

    Upgrade to FAISS:
        Replace _build_tfidf_index() with SentenceTransformer embeddings
        stored in a faiss.IndexFlatIP index.  The search() signature stays
        identical — only the internals change.
    """

    def __init__(self, runbook_dir: str = "./data/runbooks") -> None:
        """
        Load all *.md files from runbook_dir and build the TF-IDF index.

        Args:
            runbook_dir: Path to directory containing markdown runbook files.
                         Falls back to the path relative to this file's location.
        """
        self.runbook_dir = self._resolve_dir(runbook_dir)
        self.docs: List[Dict[str, str]] = []  # [{"name": ..., "text": ..., "chunks": [...]}]
        self.idf: Dict[str, float] = {}
        self._load_runbooks()
        self._build_tfidf_index()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_dir(self, path: str) -> Path:
        """Resolve runbook directory, trying multiple fallback locations."""
        p = Path(path)
        if p.exists():
            return p
        # Try relative to this file
        alt = Path(__file__).parent.parent / "data" / "runbooks"
        if alt.exists():
            return alt
        return p  # Return even if it doesn't exist; load will handle gracefully

    def _load_runbooks(self) -> None:
        """Read all markdown files from the runbook directory."""
        self.docs = []
        if not self.runbook_dir.exists():
            return

        for md_file in sorted(self.runbook_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                # Split into chunks of ~300 words for finer-grained retrieval
                chunks = self._chunk_text(text, chunk_size=300)
                self.docs.append({
                    "name": md_file.name,
                    "text": text,
                    "chunks": chunks,
                    "path": str(md_file),
                })
            except Exception as exc:
                self.docs.append({
                    "name": md_file.name,
                    "text": f"[Error reading: {exc}]",
                    "chunks": [],
                    "path": str(md_file),
                })

    def _chunk_text(self, text: str, chunk_size: int = 300) -> List[str]:
        """Split text into overlapping word-level chunks."""
        words = text.split()
        chunks = []
        step = chunk_size // 2  # 50% overlap
        for i in range(0, max(1, len(words) - chunk_size + 1), step):
            chunk = " ".join(words[i: i + chunk_size])
            if chunk:
                chunks.append(chunk)
        if not chunks and words:
            chunks.append(text)
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        """Lowercase alphanumeric tokenization."""
        return re.findall(r"[a-z0-9]+", text.lower())

    def _build_tfidf_index(self) -> None:
        """Pre-compute IDF weights over all document full texts."""
        n = len(self.docs)
        if n == 0:
            return

        df: Dict[str, int] = defaultdict(int)
        for doc in self.docs:
            toks = set(self._tokenize(doc["text"]))
            for t in toks:
                df[t] += 1

        self.idf = {
            term: log((n + 1) / (count + 1)) + 1.0
            for term, count in df.items()
        }

    def _score(self, query_tokens: List[str], doc_text: str) -> float:
        """Compute TF-IDF dot-product score between query and document."""
        doc_tokens = self._tokenize(doc_text)
        if not doc_tokens:
            return 0.0

        freq: Dict[str, int] = defaultdict(int)
        for t in doc_tokens:
            freq[t] += 1

        total = 0.0
        for qt in query_tokens:
            tf = freq.get(qt, 0) / len(doc_tokens)
            idf = self.idf.get(qt, 1.0)
            total += tf * idf
        return total

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find the most relevant runbooks for the given query.

        Args:
            query:  Natural-language incident description or symptom.
            top_k:  Maximum number of results to return.

        Returns:
            List of dicts, each with keys:
              - name     (str)  runbook filename
              - score    (float) relevance score
              - excerpt  (str)  first 600 chars of the runbook
              - path     (str)  absolute file path
        """
        if not self.docs:
            return [{"name": "none", "score": 0.0, "excerpt": "No runbooks loaded.", "path": ""}]

        query_tokens = self._tokenize(query)
        scored: List[Tuple[float, Dict[str, str]]] = []

        for doc in self.docs:
            sc = self._score(query_tokens, doc["text"])
            scored.append((sc, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sc, doc in scored[:top_k]:
            results.append({
                "name": doc["name"],
                "score": round(sc, 4),
                "excerpt": doc["text"][:600].strip(),
                "path": doc.get("path", ""),
            })
        return results

    def get_all_runbook_names(self) -> List[str]:
        """Return filenames of all loaded runbooks."""
        return [doc["name"] for doc in self.docs]

    def reload(self) -> None:
        """Re-read runbook files from disk and rebuild the index."""
        self._load_runbooks()
        self._build_tfidf_index()


# ---------------------------------------------------------------------------
# IncidentHistoryMemory
# ---------------------------------------------------------------------------

class IncidentHistoryMemory:
    """
    File-based storage for resolved incidents with keyword search.

    Each resolved incident is saved as a JSON file named
    ``{incident_id}.json`` in the history directory.  The search
    method loads all files, extracts textual content, and ranks by
    overlap with the query — a simple but effective case-based retrieval
    mechanism that requires no external database.

    Design Decision:
        File-based storage was chosen over SQLite/Redis to keep the project
        self-contained and Docker-friendly.  For high-volume production use,
        swap to PostgreSQL + pgvector or Elasticsearch.
    """

    def __init__(self, history_dir: str = "./data/incident_history") -> None:
        """
        Initialize the incident history store.

        Args:
            history_dir: Directory where resolved incident JSON files are stored.
                         Created automatically if it does not exist.
        """
        self.history_dir = Path(history_dir)
        if not self.history_dir.exists():
            # Try relative to this file's location
            alt = Path(__file__).parent.parent / "data" / "incident_history"
            if not self.history_dir.exists():
                try:
                    self.history_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    self.history_dir = alt
                    self.history_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _incident_to_text(self, data: Dict[str, Any]) -> str:
        """Flatten an incident dict to a searchable text blob."""
        parts = []
        if data.get("diagnosis"):
            parts.append(data["diagnosis"])
        if data.get("severity"):
            parts.append(data["severity"])
        for anomaly in data.get("detected_anomalies", []):
            if isinstance(anomaly, dict):
                parts.append(anomaly.get("type", ""))
                parts.append(anomaly.get("description", ""))
        if data.get("outcome"):
            parts.append(data["outcome"])
        for plan_step in data.get("investigation_plan", []):
            parts.append(str(plan_step))
        return " ".join(parts)

    def _keyword_score(self, query_tokens: List[str], text: str) -> float:
        """Simple token overlap score (Jaccard-like)."""
        doc_tokens = set(self._tokenize(text))
        query_set = set(query_tokens)
        if not query_set or not doc_tokens:
            return 0.0
        return len(query_set & doc_tokens) / len(query_set | doc_tokens)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_incident(self, state: Dict[str, Any]) -> str:
        """
        Persist a resolved incident to disk as a JSON file.

        Extracts the key fields needed for future retrieval: incident_id,
        severity, anomalies, diagnosis, plan, outcome, and audit_log.

        Args:
            state: The final IncidentState dict after outcome_logger runs.

        Returns:
            Path to the saved JSON file as a string.
        """
        incident_id = state.get("incident_id", f"unknown-{datetime.utcnow().isoformat()}")
        filename = self.history_dir / f"{incident_id}.json"

        # Serialize only JSON-safe fields (drop BaseMessage objects)
        record = {
            "incident_id": incident_id,
            "saved_at": datetime.utcnow().isoformat(),
            "severity": state.get("severity", ""),
            "detected_anomalies": state.get("detected_anomalies", []),
            "investigation_plan": state.get("investigation_plan", []),
            "diagnosis": state.get("diagnosis", ""),
            "runbook_matches": state.get("runbook_matches", []),
            "proposed_fixes": state.get("proposed_fixes", []),
            "executed_fixes": state.get("executed_fixes", []),
            "outcome": state.get("outcome", ""),
            "audit_log": state.get("audit_log", []),
            "status": state.get("status", ""),
            "human_approved": state.get("human_approved", False),
        }

        try:
            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(record, fh, indent=2, default=str)
            return str(filename)
        except Exception as exc:
            raise RuntimeError(f"Failed to save incident {incident_id}: {exc}") from exc

    def find_similar(
        self,
        anomaly_description: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Find historical incidents similar to the given anomaly description.

        Args:
            anomaly_description: Text describing the current incident symptoms.
            top_k:               Maximum number of past incidents to return.

        Returns:
            List of dicts, each containing:
              - incident_id  (str)
              - severity     (str)
              - diagnosis    (str)
              - outcome      (str)
              - score        (float) keyword overlap score
              - saved_at     (str)  ISO timestamp when incident was saved
        """
        json_files = list(self.history_dir.glob("*.json"))
        if not json_files:
            return []

        query_tokens = self._tokenize(anomaly_description)
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                text = self._incident_to_text(data)
                sc = self._keyword_score(query_tokens, text)
                scored.append((sc, data))
            except Exception:
                continue  # Skip corrupted files

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sc, data in scored[:top_k]:
            if sc == 0.0:
                continue  # Skip completely unrelated incidents
            results.append({
                "incident_id": data.get("incident_id", ""),
                "severity":    data.get("severity", ""),
                "diagnosis":   data.get("diagnosis", "")[:300],
                "outcome":     data.get("outcome", "")[:300],
                "score":       round(sc, 4),
                "saved_at":    data.get("saved_at", ""),
            })
        return results

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific incident by ID.

        Args:
            incident_id: The UUID of the incident to load.

        Returns:
            The incident dict, or None if not found.
        """
        filename = self.history_dir / f"{incident_id}.json"
        if not filename.exists():
            return None
        try:
            with open(filename, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def list_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Return a summary list of all stored incidents, newest first.

        Args:
            limit: Maximum number of incidents to return.

        Returns:
            List of summary dicts with incident_id, severity, status, saved_at.
        """
        json_files = sorted(
            self.history_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        summaries = []
        for jf in json_files[:limit]:
            try:
                with open(jf, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                summaries.append({
                    "incident_id": data.get("incident_id", jf.stem),
                    "severity":    data.get("severity", "unknown"),
                    "status":      data.get("status", "unknown"),
                    "saved_at":    data.get("saved_at", ""),
                    "anomaly_types": [
                        a.get("type", "") for a in data.get("detected_anomalies", [])
                        if isinstance(a, dict)
                    ],
                })
            except Exception:
                continue
        return summaries
