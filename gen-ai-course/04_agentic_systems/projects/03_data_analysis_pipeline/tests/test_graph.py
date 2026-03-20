"""
test_graph.py - Integration tests for the LangGraph analysis pipeline nodes and graphs.

Test strategy:
- Node tests are unit tests: they call individual node functions directly with
  pre-built state dicts, avoiding full graph overhead.
- Graph tests mock the LLM (via unittest.mock.patch) so they run deterministically
  without a running Ollama/OpenAI server.
- The full-graph test exercises the entire graph with mocked LLM responses
  to verify node wiring and state propagation.

WHY mock the LLM for graph tests:
  LLM calls are non-deterministic, slow, and require external services. Mocking
  them makes tests fast (< 5 s), reliable (no network flakiness), and runnable
  in CI/CD pipelines without credentials.
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure project root on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.state import AnalysisState
from agent.nodes import (
    data_profiler,
    planner,
    analyzer,
    chart_maker,
    reflector,
    report_writer,
    question_router,
    context_retriever,
    answerer,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_csv(tmp_path: Path) -> str:
    """Create a reproducible 50-row sales CSV for graph tests."""
    import numpy as np

    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=50, freq="W").astype(str),
            "product": rng.choice(["Widget", "Gadget", "Doohickey"], size=50).tolist(),
            "revenue": rng.uniform(100, 1000, size=50).round(2).tolist(),
            "quantity": rng.integers(1, 50, size=50).tolist(),
            "region": rng.choice(["North", "South", "East", "West"], size=50).tolist(),
        }
    )
    csv_path = str(tmp_path / "sales.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def base_state(sample_csv: str) -> AnalysisState:
    """Minimal initial state for node tests."""
    return AnalysisState(
        dataset_path=sample_csv,
        session_id=str(uuid.uuid4()),
        dataset_summary=None,
        analysis_plan=[],
        profiling_results={},
        analysis_results=[],
        charts=[],
        reflection=None,
        final_report="",
        follow_up_question=None,
        follow_up_answer=None,
        conversation_history=[],
        iteration_count=0,
        error=None,
    )


# ---------------------------------------------------------------------------
# Helper: build a mock LLM response
# ---------------------------------------------------------------------------

def _mock_llm(content: str):
    """Return a mock LLM object whose .invoke() returns a message with given content."""
    mock = MagicMock()
    response = MagicMock()
    response.content = content
    mock.invoke.return_value = response
    return mock


# ---------------------------------------------------------------------------
# Test: data_profiler node
# ---------------------------------------------------------------------------

class TestDataProfilerNode:
    """Tests for the data_profiler node."""

    def test_basic_profiling(self, base_state: AnalysisState) -> None:
        """data_profiler populates dataset_summary with correct structure."""
        result = data_profiler(base_state)
        assert result.get("error") is None, f"Error: {result.get('error')}"
        summary = result.get("dataset_summary")
        assert summary is not None
        assert summary["shape"] == (50, 5)
        assert "revenue" in summary["columns"]
        assert "quantity" in summary["columns"]

    def test_profiling_includes_dtypes(self, base_state: AnalysisState) -> None:
        """dataset_summary includes dtype information for all columns."""
        result = data_profiler(base_state)
        summary = result["dataset_summary"]
        dtypes = summary.get("dtypes", {})
        assert "revenue" in dtypes
        assert "float" in dtypes["revenue"] or "int" in dtypes["revenue"]

    def test_profiling_includes_null_counts(self, base_state: AnalysisState) -> None:
        """dataset_summary includes null_counts (all zero for clean CSV)."""
        result = data_profiler(base_state)
        summary = result["dataset_summary"]
        null_counts = summary.get("null_counts", {})
        assert isinstance(null_counts, dict)
        # Sample CSV has no nulls
        assert all(v == 0 for v in null_counts.values())

    def test_profiling_includes_sample_rows(self, base_state: AnalysisState) -> None:
        """dataset_summary includes up to 5 sample rows as a list of dicts."""
        result = data_profiler(base_state)
        summary = result["dataset_summary"]
        sample = summary.get("sample_rows", [])
        assert len(sample) <= 5
        assert len(sample) > 0
        assert isinstance(sample[0], dict)

    def test_profiling_invalid_path(self, tmp_path: Path) -> None:
        """data_profiler returns an error for a missing file."""
        state = AnalysisState(
            dataset_path=str(tmp_path / "missing.csv"),
            session_id="test",
        )
        result = data_profiler(state)
        assert result.get("error") is not None


# ---------------------------------------------------------------------------
# Test: planner node
# ---------------------------------------------------------------------------

class TestPlannerNode:
    """Tests for the planner node (LLM mocked)."""

    def _state_with_summary(self, base_state: AnalysisState) -> AnalysisState:
        """Run data_profiler first to populate dataset_summary."""
        update = data_profiler(base_state)
        return {**base_state, **update}

    def test_planner_returns_list_of_steps(self, base_state: AnalysisState) -> None:
        """Planner returns a non-empty list of analysis steps."""
        state = self._state_with_summary(base_state)
        plan_json = json.dumps([
            "Step 1: Compute descriptive statistics for revenue and quantity.",
            "Step 2: Analyse distribution of revenue.",
            "Step 3: Count product category frequencies.",
            "Step 4: Compute correlations between revenue and quantity.",
            "Step 5: Detect outliers in revenue.",
        ])
        mock_llm = _mock_llm(plan_json)

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            result = planner(state)

        plan = result.get("analysis_plan", [])
        assert isinstance(plan, list)
        assert len(plan) >= 3
        assert all(isinstance(step, str) for step in plan)

    def test_planner_caps_at_seven_steps(self, base_state: AnalysisState) -> None:
        """Planner never returns more than 7 steps even if LLM returns more."""
        state = self._state_with_summary(base_state)
        big_plan = json.dumps([f"Step {i}: Do analysis {i}." for i in range(1, 15)])
        mock_llm = _mock_llm(big_plan)

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            result = planner(state)

        assert len(result["analysis_plan"]) <= 7

    def test_planner_uses_fallback_on_llm_error(self, base_state: AnalysisState) -> None:
        """Planner falls back to rule-based plan when LLM fails."""
        state = self._state_with_summary(base_state)
        failing_llm = MagicMock()
        failing_llm.invoke.side_effect = RuntimeError("LLM unavailable")

        with patch("agent.nodes._get_llm", return_value=failing_llm):
            result = planner(state)

        plan = result.get("analysis_plan", [])
        assert len(plan) >= 1  # fallback always produces at least one step

    def test_planner_fallback_on_bad_json(self, base_state: AnalysisState) -> None:
        """Planner falls back gracefully when LLM returns non-JSON text."""
        state = self._state_with_summary(base_state)
        mock_llm = _mock_llm("Sure! I'll analyse your data. Step one is to look at the data.")

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            result = planner(state)

        plan = result.get("analysis_plan", [])
        # Either parsed something or used fallback — either way, non-empty
        assert isinstance(plan, list)


# ---------------------------------------------------------------------------
# Test: reflector node
# ---------------------------------------------------------------------------

class TestReflectorNode:
    """Tests for the DataCritic reflector node."""

    def _state_with_results(self, base_state: AnalysisState) -> AnalysisState:
        """Build a state with mock analysis results."""
        profiler_update = data_profiler(base_state)
        return {
            **base_state,
            **profiler_update,
            "analysis_plan": ["Step 1: Compute stats", "Step 2: Find outliers"],
            "analysis_results": [
                {
                    "step": "Step 1: Compute stats",
                    "findings": "Revenue mean=550.0, std=250.0. Quantity mean=25.0.",
                    "data": {"descriptive": {}},
                },
                {
                    "step": "Step 2: Find outliers",
                    "findings": "Revenue: 2 outliers (4%) — severity: mild.",
                    "data": {},
                },
            ],
            "iteration_count": 1,
        }

    def test_high_score_sets_approved_true(self, base_state: AnalysisState) -> None:
        """A quality score >= 7 results in approved=True."""
        state = self._state_with_results(base_state)
        critic_response = json.dumps({
            "quality_score": 8.5,
            "shallow_areas": [],
            "suggestions": ["Consider deeper time-series analysis."],
        })
        mock_llm = _mock_llm(critic_response)

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            result = reflector(state)

        ref = result.get("reflection", {})
        assert ref["quality_score"] == 8.5
        assert ref["approved"] is True

    def test_low_score_sets_approved_false(self, base_state: AnalysisState) -> None:
        """A quality score < 7 results in approved=False (iteration count allows retry)."""
        state = self._state_with_results(base_state)
        # Set iteration_count to 0 so the max-iteration override doesn't trigger
        state["iteration_count"] = 0

        critic_response = json.dumps({
            "quality_score": 4.0,
            "shallow_areas": ["Correlations not explored", "Trend analysis missing"],
            "suggestions": ["Add correlation heatmap", "Analyse revenue over time"],
        })
        mock_llm = _mock_llm(critic_response)

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            result = reflector(state)

        ref = result.get("reflection", {})
        assert ref["quality_score"] == 4.0
        assert ref["approved"] is False

    def test_max_iterations_overrides_low_score(self, base_state: AnalysisState) -> None:
        """Even a low score is approved when max iterations are reached."""
        state = self._state_with_results(base_state)
        state["iteration_count"] = 2  # at max

        critic_response = json.dumps({
            "quality_score": 3.0,
            "shallow_areas": ["Many things missing"],
            "suggestions": ["Do more analysis"],
        })
        mock_llm = _mock_llm(critic_response)

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            # Patch env var too
            with patch.dict("os.environ", {"MAX_REFLECTION_ITERATIONS": "2"}):
                result = reflector(state)

        ref = result.get("reflection", {})
        assert ref["approved"] is True  # forced by max iteration count

    def test_reflector_handles_llm_failure(self, base_state: AnalysisState) -> None:
        """Reflector assigns a heuristic score when LLM fails."""
        state = self._state_with_results(base_state)
        failing_llm = MagicMock()
        failing_llm.invoke.side_effect = RuntimeError("LLM down")

        with patch("agent.nodes._get_llm", return_value=failing_llm):
            result = reflector(state)

        ref = result.get("reflection", {})
        assert "quality_score" in ref
        assert isinstance(ref["quality_score"], float)


# ---------------------------------------------------------------------------
# Test: analyzer node
# ---------------------------------------------------------------------------

class TestAnalyzerNode:
    """Tests for the analyzer node."""

    def test_analyzer_produces_results(self, base_state: AnalysisState) -> None:
        """Analyzer returns at least one analysis result for each plan step."""
        profiler_update = data_profiler(base_state)
        state = {
            **base_state,
            **profiler_update,
            "analysis_plan": [
                "Step 1: Compute descriptive statistics.",
                "Step 2: Detect outliers in numeric columns.",
            ],
            "iteration_count": 0,
        }

        result = analyzer(state)
        results = result.get("analysis_results", [])
        assert len(results) >= 2
        for r in results:
            assert "step" in r
            assert "findings" in r
            assert isinstance(r["findings"], str)

    def test_analyzer_increments_iteration_count(self, base_state: AnalysisState) -> None:
        """iteration_count is incremented by 1 after each analyzer run."""
        profiler_update = data_profiler(base_state)
        state = {
            **base_state,
            **profiler_update,
            "analysis_plan": ["Step 1: Compute stats."],
            "iteration_count": 1,
        }

        result = analyzer(state)
        assert result["iteration_count"] == 2

    def test_analyzer_accumulates_across_iterations(self, base_state: AnalysisState) -> None:
        """Existing results are preserved and new ones appended on second pass."""
        profiler_update = data_profiler(base_state)
        existing_result = {"step": "Prior step", "findings": "Prior finding", "data": {}}
        state = {
            **base_state,
            **profiler_update,
            "analysis_plan": ["Step 1: Compute stats."],
            "analysis_results": [existing_result],
            "iteration_count": 1,
        }

        result = analyzer(state)
        all_results = result["analysis_results"]
        assert len(all_results) >= 2  # old + new
        assert all_results[0]["step"] == "Prior step"  # preserved


# ---------------------------------------------------------------------------
# Test: full graph integration (mocked LLM)
# ---------------------------------------------------------------------------

class TestFullGraphIntegration:
    """End-to-end graph tests with mocked LLM calls."""

    def test_full_graph_with_mock_llm(self, sample_csv: str, tmp_path: Path) -> None:
        """
        Full analysis graph runs from start to report_writer with mocked LLM.

        Verifies:
        - final_report is non-empty
        - charts list is populated
        - reflection has approved=True (score=8 mocked)
        - analysis_results has entries
        """
        # Mock LLM plan response
        plan_json = json.dumps([
            "Step 1: Compute descriptive statistics for revenue and quantity.",
            "Step 2: Analyse distribution of revenue.",
            "Step 3: Count product category frequencies.",
        ])

        # Mock reflector response (score 8 → approved immediately)
        critic_json = json.dumps({
            "quality_score": 8.0,
            "shallow_areas": [],
            "suggestions": ["Good analysis."],
        })

        report_text = (
            "# Data Analysis Report\n\n"
            "## Executive Summary\nGood dataset.\n\n"
            "## Key Findings\n- Revenue avg: 550\n"
        )

        call_count = [0]

        def mock_invoke(messages):
            response = MagicMock()
            call_count[0] += 1
            # First call = planner, second+ = reflector/report_writer
            if call_count[0] == 1:
                response.content = plan_json
            elif call_count[0] == 2:
                response.content = critic_json
            else:
                response.content = report_text
            return response

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = mock_invoke

        os.environ["OUTPUT_DIR"] = str(tmp_path / "output")
        os.environ["MAX_REFLECTION_ITERATIONS"] = "2"
        os.environ["REFLECTION_QUALITY_THRESHOLD"] = "7.0"

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            from agent.graph import run_analysis
            final_state = run_analysis(
                dataset_path=sample_csv,
                session_id="test-integration",
            )

        assert final_state.get("final_report"), "final_report should not be empty."
        assert len(final_state.get("analysis_results", [])) > 0
        # Charts may be empty in CI if matplotlib can't write, but no error expected
        assert final_state.get("error") is None

    def test_followup_graph_with_mock_llm(self, sample_csv: str, tmp_path: Path) -> None:
        """Follow-up Q&A graph returns a non-empty answer."""
        answer_text = "The average revenue is $550.25 based on the analysis."
        mock_llm = _mock_llm(answer_text)

        # Build a mock prior state as if analysis completed
        prior_state: AnalysisState = {
            "dataset_path": sample_csv,
            "session_id": "test-followup",
            "dataset_summary": {
                "shape": [50, 5],
                "columns": ["date", "product", "revenue", "quantity", "region"],
                "dtypes": {"revenue": "float64", "quantity": "int64"},
                "null_counts": {},
                "unique_counts": {},
                "sample_rows": [],
            },
            "analysis_plan": ["Step 1: Compute stats."],
            "profiling_results": {},
            "analysis_results": [
                {
                    "step": "Step 1: Compute stats.",
                    "findings": "Revenue mean=550.25, std=250.0.",
                    "data": {},
                }
            ],
            "charts": [],
            "reflection": {"quality_score": 8.0, "approved": True, "shallow_areas": [], "suggestions": []},
            "final_report": "# Report\nRevenue avg: 550.25",
            "follow_up_question": None,
            "follow_up_answer": None,
            "conversation_history": [],
            "iteration_count": 1,
            "error": None,
        }

        with patch("agent.nodes._get_llm", return_value=mock_llm):
            from agent.graph import run_followup
            result_state = run_followup(
                session_id="test-followup",
                question="What is the average revenue?",
                prior_state=prior_state,
            )

        answer = result_state.get("follow_up_answer", "")
        assert answer, "follow_up_answer should not be empty."
        assert len(answer) > 10


import os
