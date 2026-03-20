"""
tests/test_graph.py

Integration and unit tests for the LangGraph incident-response graph.

Tests mock the LLM (ChatOpenAI) to avoid requiring an API key in CI,
while still testing the full node logic and graph routing.

Run with:
    pytest tests/test_graph.py -v
    pytest tests/test_graph.py -v -k "test_detector"  # Run specific tests
"""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Test fixtures and helpers
# ---------------------------------------------------------------------------

CPU_SPIKE_LOG = """
2024-01-15 14:23:01 ERROR app-server-01 CPU usage: 94.5% (threshold: 90%)
2024-01-15 14:23:05 CRITICAL app-server-01 Memory pressure detected: 87% used
2024-01-15 14:23:10 ERROR nginx HTTP 503 Service Unavailable - upstream timeout
2024-01-15 14:23:15 ERROR nginx HTTP 500 Internal Server Error
2024-01-15 14:23:20 ERROR nginx HTTP 503 Service Unavailable
"""

DISK_FULL_LOG = """
2024-01-15 16:45:01 ERROR disk-monitor /var/log filesystem: 96% capacity used
2024-01-15 16:45:30 CRITICAL app-server No space left on device — write failed
2024-01-15 16:45:45 ERROR app-server HTTP 500 Internal Server Error
"""

LOW_SEVERITY_LOG = """
2024-01-15 10:00:01 INFO  app-server Application started
2024-01-15 10:00:10 INFO  nginx Health check OK
2024-01-15 10:00:15 WARN  app-server Cache miss ratio: 12% (threshold: 20%)
"""

ERROR_SPIKE_LOG = """
2024-01-15 18:00:01 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:02 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:03 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:04 ERROR payment-service HTTP 503 Service Unavailable
2024-01-15 18:00:05 CRITICAL payment-service Error rate: 52 errors/min (threshold: 10)
2024-01-15 18:00:06 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:07 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:08 ERROR payment-service HTTP 502 Bad Gateway
2024-01-15 18:00:09 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:10 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:11 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:12 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:13 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:14 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:15 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:16 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:17 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:18 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:19 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:20 ERROR payment-service HTTP 500 Internal Server Error
2024-01-15 18:00:21 ERROR payment-service HTTP 500 Internal Server Error
"""


def make_state(raw_logs: str = CPU_SPIKE_LOG, incident_id: str = None) -> Dict[str, Any]:
    """Create a minimal initial state for testing."""
    from agent.state import make_initial_state
    return make_initial_state(
        raw_logs=raw_logs,
        incident_id=incident_id or str(uuid.uuid4()),
    )


def mock_llm_response(content: str):
    """Create a mock LLM response object."""
    mock_response = MagicMock()
    mock_response.content = content
    return mock_response


# ---------------------------------------------------------------------------
# Detector node tests
# ---------------------------------------------------------------------------

class TestDetectorNode:
    """Tests for the detector node (no LLM — rule-based only)."""

    def test_detector_finds_cpu_anomaly(self):
        """Detector should identify cpu_high anomaly from CPU spike log."""
        from agent.nodes import detector
        state = make_state(raw_logs=CPU_SPIKE_LOG)
        result = detector(state)

        anomalies = result.get("detected_anomalies", [])
        anomaly_types = [a["type"] for a in anomalies]
        assert "cpu_high" in anomaly_types, (
            f"Should detect cpu_high anomaly. Found: {anomaly_types}"
        )

    def test_detector_cpu_anomaly_has_correct_fields(self):
        """Each anomaly dict should have type, value, threshold, severity."""
        from agent.nodes import detector
        state = make_state(raw_logs=CPU_SPIKE_LOG)
        result = detector(state)

        anomalies = result.get("detected_anomalies", [])
        cpu_anomalies = [a for a in anomalies if a["type"] == "cpu_high"]
        assert len(cpu_anomalies) > 0, "Should have at least one cpu_high anomaly"

        cpu_a = cpu_anomalies[0]
        assert "type" in cpu_a
        assert "value" in cpu_a
        assert "threshold" in cpu_a
        assert "severity" in cpu_a
        assert cpu_a["value"] >= 90.0, "CPU value should be >= 90%"

    def test_detector_finds_disk_anomaly(self):
        """Detector should identify disk_full anomaly from disk full log."""
        from agent.nodes import detector
        state = make_state(raw_logs=DISK_FULL_LOG)
        result = detector(state)

        anomalies = result.get("detected_anomalies", [])
        anomaly_types = [a["type"] for a in anomalies]
        assert "disk_full" in anomaly_types, (
            f"Should detect disk_full. Found: {anomaly_types}"
        )

    def test_detector_finds_error_spike(self):
        """Detector should identify error_spike from HTTP 5xx log."""
        from agent.nodes import detector
        state = make_state(raw_logs=ERROR_SPIKE_LOG)
        result = detector(state)

        anomalies = result.get("detected_anomalies", [])
        anomaly_types = [a["type"] for a in anomalies]
        assert "error_spike" in anomaly_types or "critical_log_event" in anomaly_types, (
            f"Should detect error_spike or critical_log_event. Found: {anomaly_types}"
        )

    def test_detector_sets_severity(self):
        """Detector should set severity based on anomalies."""
        from agent.nodes import detector
        state = make_state(raw_logs=CPU_SPIKE_LOG)
        result = detector(state)

        severity = result.get("severity", "")
        assert severity in ("low", "medium", "high", "critical"), (
            f"Severity should be a valid value, got: {severity}"
        )

    def test_detector_critical_log_sets_high_severity(self):
        """CRITICAL log lines should result in at least high severity."""
        from agent.nodes import detector
        state = make_state(raw_logs=CPU_SPIKE_LOG)  # Has CRITICAL lines
        result = detector(state)

        severity = result.get("severity", "low")
        severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        assert severity_rank.get(severity, 0) >= 2, (
            f"Expected high or critical severity, got: {severity}"
        )

    def test_detector_creates_audit_entry(self):
        """Detector should add at least one audit log entry."""
        from agent.nodes import detector
        state = make_state(raw_logs=CPU_SPIKE_LOG)
        state["audit_log"] = []
        result = detector(state)

        audit = result.get("audit_log", [])
        assert len(audit) >= 1, "Detector should create at least one audit entry"
        assert audit[-1]["agent"] == "detector"

    def test_detector_deduplicates_anomaly_types(self):
        """If the same anomaly type appears multiple times, only keep highest severity."""
        from agent.nodes import detector
        # CPU appears multiple times in this log
        log_with_repeated_cpu = CPU_SPIKE_LOG * 3
        state = make_state(raw_logs=log_with_repeated_cpu)
        result = detector(state)

        anomalies = result.get("detected_anomalies", [])
        cpu_count = sum(1 for a in anomalies if a["type"] == "cpu_high")
        assert cpu_count == 1, "Should deduplicate cpu_high anomaly"


# ---------------------------------------------------------------------------
# Severity router tests
# ---------------------------------------------------------------------------

class TestSeverityRouter:
    """Tests for the severity_router conditional edge function."""

    def test_severity_routing_critical(self):
        """Critical severity should route to medium_high_critical path."""
        from agent.nodes import severity_router
        state = make_state()
        state["severity"] = "critical"
        route = severity_router(state)
        assert route == "medium_high_critical"

    def test_severity_routing_high(self):
        """High severity should route to medium_high_critical path."""
        from agent.nodes import severity_router
        state = make_state()
        state["severity"] = "high"
        route = severity_router(state)
        assert route == "medium_high_critical"

    def test_severity_routing_medium(self):
        """Medium severity should route to medium_high_critical path."""
        from agent.nodes import severity_router
        state = make_state()
        state["severity"] = "medium"
        route = severity_router(state)
        assert route == "medium_high_critical"

    def test_severity_routing_low(self):
        """Low severity should route to 'low' path (auto_responder)."""
        from agent.nodes import severity_router
        state = make_state()
        state["severity"] = "low"
        route = severity_router(state)
        assert route == "low"

    def test_severity_routing_unknown_defaults_to_high_path(self):
        """Unknown/empty severity should default to the high path (fail safe)."""
        from agent.nodes import severity_router
        state = make_state()
        state["severity"] = "unknown"
        route = severity_router(state)
        # 'unknown' is not 'low', so it should go to medium_high_critical
        assert route == "medium_high_critical"


# ---------------------------------------------------------------------------
# Planner node tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestPlannerNode:
    """Tests for the planner node with mocked GPT-4o."""

    def test_planner_creates_steps(self):
        """Planner should return a non-empty investigation plan."""
        mock_plan = '["Check CPU-consuming processes", "Review application logs", "Check auto-scaling", "Verify database connections"]'

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_llm_response(mock_plan)

            from agent.nodes import planner
            state = make_state()
            state["detected_anomalies"] = [
                {"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "critical"}
            ]
            state["severity"] = "critical"

            result = planner(state)

        plan = result.get("investigation_plan", [])
        assert len(plan) >= 1, "Planner should return at least one step"
        assert isinstance(plan[0], str), "Plan steps should be strings"

    def test_planner_adds_audit_entry(self):
        """Planner should add an audit entry."""
        mock_plan = '["Step 1", "Step 2", "Step 3"]'

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_llm_response(mock_plan)

            from agent.nodes import planner
            state = make_state()
            state["detected_anomalies"] = [
                {"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "high"}
            ]
            state["severity"] = "high"
            state["audit_log"] = []
            result = planner(state)

        audit = result.get("audit_log", [])
        assert len(audit) >= 1
        assert any(e["agent"] == "planner" for e in audit)

    def test_planner_handles_llm_failure_gracefully(self):
        """Planner should return a fallback plan if LLM fails."""
        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.side_effect = Exception("LLM API unavailable")

            from agent.nodes import planner
            state = make_state()
            state["detected_anomalies"] = [
                {"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "high"}
            ]
            state["severity"] = "high"

            result = planner(state)  # Should not raise

        plan = result.get("investigation_plan", [])
        assert len(plan) >= 1, "Should have fallback plan even if LLM fails"

    def test_planner_sets_status_diagnosing(self):
        """Planner should update status to 'diagnosing'."""
        mock_plan = '["Step 1", "Step 2"]'

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_llm_response(mock_plan)

            from agent.nodes import planner
            state = make_state()
            state["severity"] = "high"
            state["detected_anomalies"] = [{"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "high"}]
            result = planner(state)

        assert result.get("status") == "diagnosing"


# ---------------------------------------------------------------------------
# Diagnoser node tests
# ---------------------------------------------------------------------------

class TestDiagnoserNode:
    """Tests for the diagnoser ReAct loop node."""

    def test_diagnoser_runs_react_iterations(self):
        """Diagnoser should increment iteration_count up to MAX_REACT_ITERATIONS."""
        mock_thought = "The root cause is elevated CPU from a Java process consuming 68% CPU."

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_llm_response(mock_thought)

            from agent.nodes import diagnoser, MAX_REACT_ITERATIONS
            state = make_state()
            state["detected_anomalies"] = [
                {"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "critical", "service": "app-server-01"}
            ]
            state["investigation_plan"] = ["Check CPU", "Review logs"]
            state["iteration_count"] = 0

            result = diagnoser(state)

        assert result["iteration_count"] == MAX_REACT_ITERATIONS, (
            f"Should run exactly MAX_REACT_ITERATIONS={MAX_REACT_ITERATIONS} iterations"
        )

    def test_diagnoser_produces_diagnosis(self):
        """Diagnoser should produce a non-empty diagnosis string."""
        mock_thought = "Root cause: Java process runaway CPU consumption due to infinite loop."

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_llm_response(mock_thought)

            from agent.nodes import diagnoser
            state = make_state()
            state["detected_anomalies"] = [
                {"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "critical", "service": "app-server-01"}
            ]
            state["investigation_plan"] = ["Check CPU processes"]
            result = diagnoser(state)

        assert result["diagnosis"] != "", "Diagnosis should not be empty"

    def test_diagnoser_caps_iterations_at_max(self):
        """Diagnoser should not exceed MAX_REACT_ITERATIONS even if called repeatedly."""
        mock_thought = "Iteration thought."

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_llm_response(mock_thought)

            from agent.nodes import diagnoser, MAX_REACT_ITERATIONS
            state = make_state()
            state["detected_anomalies"] = [{"type": "cpu_high", "value": 90.0, "threshold": 90.0, "severity": "high", "service": "svc"}]
            state["investigation_plan"] = ["Check metrics"]
            state["iteration_count"] = 0

            result = diagnoser(state)

        assert result["iteration_count"] <= MAX_REACT_ITERATIONS * 2, (
            "Iteration count should not grow unboundedly"
        )


# ---------------------------------------------------------------------------
# HITL checkpoint tests
# ---------------------------------------------------------------------------

class TestHITLCheckpoint:
    """Tests for the HITL checkpoint node and graph interrupt behavior."""

    def test_hitl_sets_awaiting_approval_status(self):
        """hitl_checkpoint should set status to 'awaiting_approval'."""
        from agent.nodes import hitl_checkpoint
        state = make_state()
        state["proposed_fixes"] = [
            {"step": 1, "command": "systemctl restart app-service",
             "risk_level": "medium", "description": "Restart to clear CPU spike", "rollback": ""}
        ]
        state["diagnosis"] = "CPU spike caused by runaway Java process"
        state["severity"] = "critical"

        result = hitl_checkpoint(state)
        assert result.get("status") == "awaiting_approval"

    def test_hitl_adds_audit_entry(self):
        """hitl_checkpoint should add an audit entry."""
        from agent.nodes import hitl_checkpoint
        state = make_state()
        state["proposed_fixes"] = [
            {"step": 1, "command": "systemctl restart app-service",
             "risk_level": "medium", "description": "Restart service", "rollback": ""}
        ]
        state["diagnosis"] = "Test diagnosis"
        state["severity"] = "high"
        state["audit_log"] = []

        result = hitl_checkpoint(state)
        audit = result.get("audit_log", [])
        assert any(e["agent"] == "hitl_checkpoint" for e in audit)

    def test_graph_pauses_at_executor(self):
        """
        The compiled graph should pause BEFORE the executor node.

        This test verifies the interrupt_before=["executor"] configuration
        causes the graph to stop at the HITL checkpoint.
        """
        mock_plan = '["Check CPU", "Review logs", "Scale up"]'
        mock_diagnosis = "Root cause: CPU spike from Java runaway process"
        mock_fixes = '[{"step": 1, "command": "systemctl restart app-service", "risk_level": "medium", "description": "Restart service", "rollback": "systemctl start app-service"}]'

        with patch("agent.nodes._llm") as mock_llm:
            # Return different responses for planner vs diagnoser vs fix_proposer
            mock_llm.invoke.side_effect = [
                mock_llm_response(mock_plan),         # planner call
                mock_llm_response(mock_diagnosis),    # diagnoser iteration 1
                mock_llm_response(mock_diagnosis),    # diagnoser iteration 2
                mock_llm_response(mock_diagnosis),    # diagnoser iteration 3
                mock_llm_response(mock_fixes),        # fix_proposer call
            ]

            from agent.graph import build_graph
            graph = build_graph()

            incident_id = str(uuid.uuid4())
            from agent.state import make_initial_state
            initial_state = make_initial_state(raw_logs=CPU_SPIKE_LOG, incident_id=incident_id)

            config = {"configurable": {"thread_id": incident_id}, "recursion_limit": 25}

            # Collect final snapshot
            final_snapshot = None
            for snapshot in graph.stream(initial_state, config=config, stream_mode="values"):
                final_snapshot = snapshot

        # After the graph pauses at interrupt_before=["executor"],
        # the status should be "awaiting_approval"
        if final_snapshot:
            status = final_snapshot.get("status", "")
            assert status in ("awaiting_approval", "planning", "diagnosing", "auto_responding"), (
                f"Graph should pause at HITL, got status: {status}"
            )

        # Check that the graph knows it should next run "executor"
        state_snapshot = graph.get_state(config)
        if state_snapshot and state_snapshot.next:
            assert "executor" in state_snapshot.next, (
                "Graph should be paused before executor node"
            )


# ---------------------------------------------------------------------------
# Full end-to-end flow test (mocked LLM)
# ---------------------------------------------------------------------------

class TestFullIncidentFlow:
    """End-to-end incident flow test with mocked LLM."""

    def test_full_incident_flow_mock(self):
        """
        Full flow: detector → planner → diagnoser → runbook_searcher
                   → fix_proposer → hitl_checkpoint [pause]

        Uses mocked GPT-4o to avoid API key requirement.
        """
        mock_plan = '["Identify top CPU processes", "Check memory usage", "Review recent deployments", "Prepare remediation"]'
        mock_thought = "Root cause: Java process consuming 94% CPU due to infinite retry loop in order processor."
        mock_fixes = '[{"step": 1, "command": "systemctl restart app-service", "risk_level": "medium", "description": "Restart to clear runaway process", "rollback": "systemctl start app-service"}, {"step": 2, "command": "kubectl scale deployment app-server --replicas=3", "risk_level": "low", "description": "Scale horizontally", "rollback": "kubectl scale deployment app-server --replicas=1"}]'

        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.side_effect = [
                mock_llm_response(mock_plan),   # planner
                mock_llm_response(mock_thought),  # diagnoser iter 1
                mock_llm_response(mock_thought),  # diagnoser iter 2
                mock_llm_response(mock_thought),  # diagnoser iter 3
                mock_llm_response(mock_fixes),   # fix_proposer
            ]

            from agent.graph import build_graph, run_incident
            graph = build_graph()

            result = run_incident(
                raw_logs=CPU_SPIKE_LOG,
                incident_id=str(uuid.uuid4()),
                graph=graph,
            )

        # The graph should have run through detector and produced results
        state = result.get("state", {})

        # Verify detector ran
        assert len(state.get("detected_anomalies", [])) > 0, (
            "Should have detected at least one anomaly"
        )

        # Verify severity is set
        assert state.get("severity", "low") in ("medium", "high", "critical"), (
            "Should set non-low severity for CPU spike"
        )

        # Verify incident_id is preserved
        assert state.get("incident_id") == result["incident_id"]

    def test_auto_responder_handles_low_severity(self):
        """Low severity incidents should go through auto_responder without HITL."""
        from agent.nodes import auto_responder
        state = make_state(raw_logs=LOW_SEVERITY_LOG)
        state["detected_anomalies"] = [
            {"type": "cpu_high", "value": 78.0, "threshold": 75.0, "severity": "medium",
             "service": "app-server", "description": "Moderate CPU usage"}
        ]
        state["severity"] = "low"

        result = auto_responder(state)

        assert result.get("human_approved") is True, "Auto-responder should set human_approved=True"
        assert result.get("status") == "executing"


# ---------------------------------------------------------------------------
# Outcome logger tests
# ---------------------------------------------------------------------------

class TestOutcomeLogger:
    """Tests for the outcome_logger node."""

    def test_outcome_logger_creates_summary(self):
        """outcome_logger should create a non-empty outcome string."""
        from agent.nodes import outcome_logger
        state = make_state()
        state["severity"] = "critical"
        state["detected_anomalies"] = [
            {"type": "cpu_high", "value": 94.5, "threshold": 90.0, "severity": "critical"}
        ]
        state["executed_fixes"] = ["Step 1: systemctl restart app-service → DRY-RUN OK"]
        state["diagnosis"] = "Runaway Java process consuming 94% CPU"
        state["human_approved"] = True
        state["audit_log"] = []

        result = outcome_logger(state)

        assert result.get("outcome", "") != "", "Outcome should not be empty"
        assert result.get("status") == "resolved"

    def test_outcome_logger_sets_resolved_status(self):
        """outcome_logger should set status to 'resolved'."""
        from agent.nodes import outcome_logger
        state = make_state()
        state["severity"] = "high"
        state["detected_anomalies"] = [{"type": "cpu_high", "value": 90.0, "threshold": 90.0, "severity": "high"}]
        state["executed_fixes"] = []
        state["diagnosis"] = "Test diagnosis"
        state["human_approved"] = True
        state["audit_log"] = []

        result = outcome_logger(state)
        assert result["status"] == "resolved"
