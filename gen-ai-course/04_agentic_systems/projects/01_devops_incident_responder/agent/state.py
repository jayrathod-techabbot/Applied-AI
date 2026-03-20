"""
agent/state.py

Defines the shared state schema for the AI DevOps Incident Responder graph.

Design Decision:
    TypedDict is used (instead of Pydantic BaseModel) because LangGraph's
    StateGraph natively expects TypedDict for state definitions. This avoids
    extra serialization overhead and keeps reducer annotations simple.

    Helper dataclasses (Anomaly, FixStep, AuditEntry) provide typed
    constructors for the dicts stored in the state lists. They can be
    converted to plain dicts with dataclasses.asdict() before storing into
    state, keeping the state fully JSON-serializable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Helper dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    """
    Represents a single detected anomaly in system metrics or logs.

    Fields:
        type        - Anomaly category, e.g. 'cpu_high', 'disk_full', 'error_spike'
        value       - Observed value (e.g. 94.5 for 94.5% CPU)
        threshold   - The threshold that was breached (e.g. 90 for 90%)
        severity    - One of: 'low' | 'medium' | 'high' | 'critical'
        service     - Name of the affected service / host (optional)
        description - Human-readable description of the anomaly
    """

    type: str
    value: float
    threshold: float
    severity: str
    service: str = "unknown"
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for JSON serialization and state storage."""
        return asdict(self)


@dataclass
class FixStep:
    """
    A single proposed remediation step.

    Fields:
        step        - Sequential step number (1-based)
        command     - Shell / kubectl / systemctl command to execute
        risk_level  - 'low' | 'medium' | 'high' — used by HITL to highlight danger
        description - Why this step is needed and what it does
        rollback    - Optional rollback command if this step goes wrong
    """

    step: int
    command: str
    risk_level: str
    description: str
    rollback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for JSON serialization and state storage."""
        return asdict(self)


@dataclass
class AuditEntry:
    """
    An immutable audit log record written by each node/agent as it executes.

    Design Decision:
        Every action that changes system state (or proposes to) is recorded
        here. This provides a tamper-evident chronological trail for
        post-incident review and compliance purposes.

    Fields:
        timestamp   - ISO-8601 UTC timestamp
        agent       - Name of the node/agent that generated this entry
        action      - Short verb phrase describing what was done
        result      - Outcome or summary (truncated to avoid bloat)
        incident_id - Links this entry to the parent incident
    """

    agent: str
    action: str
    result: str
    incident_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for JSON serialization and state storage."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Main LangGraph state schema
# ---------------------------------------------------------------------------

class IncidentState(TypedDict, total=False):
    """
    Shared state passed between all nodes in the incident-response graph.

    This is the single source of truth for an in-flight incident.  Every
    node reads from this dict and returns a *partial* update — LangGraph
    merges updates automatically, so nodes only need to return the keys
    they changed.

    Key design decisions:
    - `messages` carries the conversation history for LLM nodes (planner,
      diagnoser, fix_proposer) so they have full context.
    - `audit_log` is append-only: nodes always EXTEND, never overwrite, to
      preserve the full action history.
    - `iteration_count` guards the ReAct diagnoser loop against infinite
      recursion. MAX_REACT_ITERATIONS is enforced in the diagnoser node.
    - `human_approved` starts as False; it is set to True only when the
      human confirms via the HITL checkpoint, preventing accidental execution.
    - `incident_id` is a UUID assigned at graph entry; it keys checkpointer
      state and file-based history storage.
    """

    # --- Input ---
    raw_logs: str
    """Raw log text submitted by the monitoring system or operator."""

    incident_id: str
    """UUID string assigned at graph entry. Used as the checkpointer thread ID."""

    # --- Detection ---
    detected_anomalies: List[Dict[str, Any]]
    """
    List of Anomaly.to_dict() objects found by the detector node.
    Each dict has keys: type, value, threshold, severity, service, description.
    """

    severity: str
    """
    Overall incident severity: 'low' | 'medium' | 'high' | 'critical'.
    Derived from the worst anomaly; drives conditional routing.
    """

    # --- Planning ---
    investigation_plan: List[str]
    """Ordered list of investigation steps produced by the planner node."""

    # --- Diagnosis ---
    diagnosis: str
    """
    Root-cause hypothesis written by the diagnoser node after its ReAct loop.
    Combines evidence from metrics, logs, and historical patterns.
    """

    iteration_count: int
    """Number of ReAct iterations completed by the diagnoser. Caps at MAX_REACT_ITERATIONS."""

    # --- Runbook lookup ---
    runbook_matches: List[str]
    """
    Top-3 runbook excerpts returned by runbook_searcher.
    Passed to fix_proposer as grounding context.
    """

    # --- Fix proposal ---
    proposed_fixes: List[Dict[str, Any]]
    """
    List of FixStep.to_dict() objects proposed by fix_proposer.
    Presented to the human at the HITL checkpoint.
    """

    # --- HITL ---
    human_approved: bool
    """
    Set to True by the API/UI layer after the human reviews proposed_fixes.
    The executor node checks this before running any command.
    """

    human_notes: str
    """Optional notes from the human approver (rejection reason, caveats, etc.)."""

    # --- Execution ---
    executed_fixes: List[str]
    """Human-readable log of each fix command that was executed (or dry-run)."""

    # --- Outcome ---
    outcome: str
    """Free-text resolution summary written by outcome_logger."""

    # --- Infrastructure ---
    audit_log: List[Dict[str, Any]]
    """
    Append-only list of AuditEntry.to_dict() objects.
    Provides the tamper-evident timeline of all agent actions.
    """

    messages: List[BaseMessage]
    """LangChain message history shared across LLM-powered nodes."""

    status: str
    """
    Lifecycle status: detecting | planning | diagnosing | awaiting_approval
                     | executing | resolved | failed
    """


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def make_initial_state(raw_logs: str, incident_id: Optional[str] = None) -> IncidentState:
    """
    Create a fully-initialized IncidentState for a new incident.

    Args:
        raw_logs:    The raw log text to analyze.
        incident_id: Optional UUID; a new one is generated if not provided.

    Returns:
        An IncidentState dict with all list fields initialized to empty lists
        and all scalar fields set to sensible defaults.
    """
    if incident_id is None:
        incident_id = str(uuid.uuid4())

    return IncidentState(
        raw_logs=raw_logs,
        incident_id=incident_id,
        detected_anomalies=[],
        severity="low",
        investigation_plan=[],
        diagnosis="",
        iteration_count=0,
        runbook_matches=[],
        proposed_fixes=[],
        human_approved=False,
        human_notes="",
        executed_fixes=[],
        outcome="",
        audit_log=[],
        messages=[],
        status="detecting",
    )
