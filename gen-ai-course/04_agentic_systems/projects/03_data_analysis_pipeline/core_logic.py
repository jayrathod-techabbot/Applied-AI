"""
core_logic.py - Standalone demonstration of the AI Data Analysis Pipeline.

This script runs the full analysis pipeline without a server:
  1. Creates a synthetic 200-row sales dataset in memory
  2. Runs each pipeline stage explicitly and prints results
  3. Demonstrates the reflection loop (re-analyses if score < threshold)
  4. Saves charts to ./output/ and writes report.md
  5. Shows follow-up Q&A

Run with:
    python core_logic.py

No server, no Docker, no API keys needed if using Ollama (LLM_PROVIDER=ollama).
Set LLM_PROVIDER=openai and OPENAI_API_KEY=sk-... to use GPT-4o instead.

WHY a standalone script in addition to the graph:
  The graph is the production path. This script is the learning/debugging path —
  it calls each node function directly, prints intermediate state at each stage,
  and makes it easy to inspect what each node returns before the next runs.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load .env before any other imports so env vars are available
load_dotenv()

# ---------------------------------------------------------------------------
# Ensure the project root is on the Python path when run directly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REFLECTION_THRESHOLD = float(os.getenv("REFLECTION_QUALITY_THRESHOLD", "7.0"))
MAX_ITERATIONS = int(os.getenv("MAX_REFLECTION_ITERATIONS", "2"))


# ---------------------------------------------------------------------------
# Step 0: Generate synthetic sales dataset
# ---------------------------------------------------------------------------

def create_sample_dataset() -> str:
    """
    Create a 200-row synthetic sales dataset and save it to a temp CSV.

    WHY synthetic data: the demo must run without the user providing a file.
    The dataset is realistic enough to produce interesting analysis:
      - date column → enables time-series trend analysis
      - product + region → categorical analysis
      - revenue + quantity → numeric stats, correlation, outlier detection
      - A few outlier rows are injected to make outlier detection interesting

    Returns:
        Absolute path to the saved CSV file.
    """
    print("\n" + "="*60)
    print("STEP 0: Creating synthetic sales dataset (200 rows)")
    print("="*60)

    rng = np.random.default_rng(42)

    products = ["Widget Pro", "Gadget Basic", "Doohickey Plus", "Thingamajig", "Whatchamacallit"]
    regions = ["North", "South", "East", "West", "Central"]

    n = 200
    dates = pd.date_range("2023-01-01", periods=n, freq="B")  # business days

    # Base revenue with seasonal uplift
    base_revenue = rng.uniform(500, 3000, n)
    seasonal_factor = 1 + 0.3 * np.sin(np.linspace(0, 4 * np.pi, n))
    revenue = (base_revenue * seasonal_factor).round(2)

    # Inject 5 obvious outliers
    outlier_idx = rng.choice(n, size=5, replace=False)
    revenue[outlier_idx] = rng.uniform(15000, 25000, 5)

    df = pd.DataFrame({
        "date":      dates.strftime("%Y-%m-%d"),
        "product":   rng.choice(products, n),
        "region":    rng.choice(regions, n),
        "revenue":   revenue,
        "quantity":  rng.integers(1, 100, n),
        "discount":  rng.uniform(0, 0.3, n).round(3),
        "returned":  rng.choice([0, 1], n, p=[0.92, 0.08]),
    })

    # Save to a temp file that persists for the demo session
    csv_path = str(OUTPUT_DIR / "demo_sales.csv")
    df.to_csv(csv_path, index=False)

    print(f"Dataset created: {csv_path}")
    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Sample:\n{df.head(3).to_string(index=False)}")

    return csv_path


# ---------------------------------------------------------------------------
# Step 1: Data profiling
# ---------------------------------------------------------------------------

def run_profiling(state: dict) -> dict:
    """
    Run the data_profiler node and display its output.

    WHY call the node directly: this makes it easy to inspect the DatasetSummary
    dict before passing it to the planner. In the full graph this happens
    automatically, but here we want educational visibility.
    """
    print("\n" + "="*60)
    print("STEP 1: Data Profiling")
    print("="*60)

    from agent.nodes import data_profiler
    update = data_profiler(state)
    state.update(update)

    summary = state.get("dataset_summary", {})
    shape = summary.get("shape", [0, 0])
    dtypes = summary.get("dtypes", {})
    null_counts = summary.get("null_counts", {})

    print(f"  Rows: {shape[0]}, Columns: {shape[1]}")
    print(f"  Dtypes:\n    {dtypes}")
    null_total = sum(null_counts.values())
    print(f"  Total null values: {null_total}")

    if update.get("error"):
        print(f"  ERROR: {update['error']}")

    return state


# ---------------------------------------------------------------------------
# Step 2: Planning
# ---------------------------------------------------------------------------

def run_planning(state: dict) -> dict:
    """
    Run the planner node and display the generated analysis plan.

    WHY we print the plan before executing it: this is the agent's 'thought'
    before 'action', analogous to the Plan step in a Plan-and-Execute agent.
    """
    print("\n" + "="*60)
    print("STEP 2: Analysis Planning (LLM-generated)")
    print("="*60)

    from agent.nodes import planner
    update = planner(state)
    state.update(update)

    plan = state.get("analysis_plan", [])
    print(f"  Generated {len(plan)} analysis steps:")
    for i, step in enumerate(plan, 1):
        print(f"    {i}. {step}")

    return state


# ---------------------------------------------------------------------------
# Step 3: Analysis execution
# ---------------------------------------------------------------------------

def run_analysis(state: dict) -> dict:
    """
    Run the analyzer node and display key findings from each step.

    WHY the analyzer iterates the plan internally: encapsulating all steps in
    one node keeps the graph topology clean (one edge vs. N edges per step).
    """
    print("\n" + "="*60)
    print("STEP 3: Analysis Execution")
    print("="*60)

    from agent.nodes import analyzer
    update = analyzer(state)
    state.update(update)

    results = state.get("analysis_results", [])
    print(f"  Completed {len(results)} analysis steps.")
    for r in results:
        step = r.get("step", "Unknown step")
        findings = r.get("findings", "No findings.")
        print(f"\n  [{step[:50]}...]")
        print(f"    {findings[:200]}{'...' if len(findings) > 200 else ''}")

    return state


# ---------------------------------------------------------------------------
# Step 4: Chart generation
# ---------------------------------------------------------------------------

def run_chart_generation(state: dict) -> dict:
    """
    Run the chart_maker node and report which charts were created.

    WHY save charts to ./output/: the Streamlit UI reads them from disk.
    In Docker, OUTPUT_DIR is a named volume shared between containers.
    """
    print("\n" + "="*60)
    print("STEP 4: Chart Generation")
    print("="*60)

    from agent.nodes import chart_maker
    update = chart_maker(state)
    state.update(update)

    charts = state.get("charts", [])
    if charts:
        print(f"  Generated {len(charts)} charts:")
        for c in charts:
            print(f"    - [{c.get('chart_type')}] {c.get('title')} → {c.get('file_path')}")
    else:
        print("  No charts were generated.")

    return state


# ---------------------------------------------------------------------------
# Step 5: Reflection
# ---------------------------------------------------------------------------

def run_reflection(state: dict) -> dict:
    """
    Run the DataCritic reflector node and display the quality verdict.

    WHY reflection before report writing: the reflector may find that key
    analyses were missed (e.g. correlations not computed). Iterating before
    writing the report ensures the report is based on thorough analysis.
    """
    print("\n" + "="*60)
    print("STEP 5: DataCritic Reflection")
    print("="*60)

    from agent.nodes import reflector
    update = reflector(state)
    state.update(update)

    ref = state.get("reflection", {})
    score = ref.get("quality_score", 0)
    approved = ref.get("approved", False)
    shallow = ref.get("shallow_areas", [])
    suggestions = ref.get("suggestions", [])

    # Colour-coded console output
    if score >= 7:
        verdict = "APPROVED (high quality)"
    elif score >= 5:
        verdict = "BORDERLINE"
    else:
        verdict = "REJECTED (shallow)"

    print(f"  Quality score: {score}/10 — {verdict}")
    print(f"  Approved: {approved}")
    if shallow:
        print(f"  Shallow areas:")
        for s in shallow:
            print(f"    - {s}")
    if suggestions:
        print(f"  Suggestions:")
        for s in suggestions:
            print(f"    - {s}")

    return state


# ---------------------------------------------------------------------------
# Step 6: Optional re-analysis if score is low
# ---------------------------------------------------------------------------

def maybe_reanalyze(state: dict) -> dict:
    """
    If the reflector rejected the analysis, run a deeper pass.

    WHY a while loop with iteration cap: the reflector could theoretically
    keep rejecting indefinitely. The cap (MAX_ITERATIONS) ensures the demo
    terminates even if the LLM is erratic.

    This mirrors the conditional_edge logic in graph.py but makes it explicit
    for educational purposes.
    """
    iteration = state.get("iteration_count", 1)

    while not state.get("reflection", {}).get("approved", True) and iteration < MAX_ITERATIONS:
        print(f"\n  → Score below threshold ({REFLECTION_THRESHOLD}). Running deeper analysis (pass {iteration + 1})...")

        state = run_analysis(state)
        state = run_reflection(state)
        iteration = state.get("iteration_count", iteration + 1)
        state["iteration_count"] = iteration

    return state


# ---------------------------------------------------------------------------
# Step 7: Report writing
# ---------------------------------------------------------------------------

def run_report_writing(state: dict) -> dict:
    """
    Run the report_writer node and save the markdown report to disk.

    WHY save to OUTPUT_DIR: the file can be served by the API's GET /report
    endpoint or downloaded directly by the user without going through the API.
    """
    print("\n" + "="*60)
    print("STEP 6: Report Writing")
    print("="*60)

    from agent.nodes import report_writer
    update = report_writer(state)
    state.update(update)

    report = state.get("final_report", "")
    session_id = state.get("session_id", "demo")

    # Save report to output directory
    report_path = OUTPUT_DIR / f"report_{session_id[:8]}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"  Report written to: {report_path}")
    print(f"  Report length: {len(report)} characters")
    # Print first 500 chars as preview
    print("\n  --- Report Preview ---")
    print(report[:500])
    if len(report) > 500:
        print("  ... (truncated)")

    return state


# ---------------------------------------------------------------------------
# Step 8: Follow-up Q&A demonstration
# ---------------------------------------------------------------------------

def run_followup_demo(state: dict) -> None:
    """
    Demonstrate multi-turn follow-up Q&A using the cached analysis state.

    WHY demonstrate follow-ups: this is a key UX differentiator. Users don't
    just want a static report — they want to ask "why" and "what if" questions.
    """
    print("\n" + "="*60)
    print("STEP 7: Follow-up Q&A Demonstration")
    print("="*60)

    questions = [
        "Which product category has the highest average revenue?",
        "Are there any concerning trends in the data that I should address?",
    ]

    from agent.graph import run_followup

    for q in questions:
        print(f"\n  Q: {q}")
        updated = run_followup(
            session_id=state["session_id"],
            question=q,
            prior_state=state,
        )
        answer = updated.get("follow_up_answer", "No answer generated.")
        print(f"  A: {answer[:400]}{'...' if len(answer) > 400 else ''}")
        # Update state with new conversation history for multi-turn coherence
        state = updated


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Orchestrate the full demo pipeline.

    WHY call each step explicitly rather than using graph.invoke():
      The graph.invoke() path is the production path. Here we call each node
      directly so the learner can see intermediate state and add print
      statements without modifying graph.py.
    """
    print("\n" + "="*60)
    print("AI DATA ANALYSIS PIPELINE — Core Logic Demo")
    print("="*60)
    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'ollama')}")
    print(f"Output Dir:   {OUTPUT_DIR.resolve()}")
    print(f"Quality Threshold: {REFLECTION_THRESHOLD}")
    print(f"Max Iterations:    {MAX_ITERATIONS}")

    # --- Create dataset ---
    csv_path = create_sample_dataset()
    session_id = str(uuid.uuid4())

    # --- Build initial state ---
    # WHY build state manually: we're calling nodes directly, not via graph.invoke().
    # Each node reads from this dict and returns a partial update that we merge in.
    state: dict = {
        "dataset_path": csv_path,
        "session_id": session_id,
        "dataset_summary": None,
        "analysis_plan": [],
        "profiling_results": {},
        "analysis_results": [],
        "charts": [],
        "reflection": None,
        "final_report": "",
        "follow_up_question": None,
        "follow_up_answer": None,
        "conversation_history": [],
        "iteration_count": 0,
        "error": None,
    }

    # --- Execute pipeline stages ---
    state = run_profiling(state)
    state = run_planning(state)
    state = run_analysis(state)
    state = run_chart_generation(state)
    state = run_reflection(state)

    # --- Conditional re-analysis loop ---
    state = maybe_reanalyze(state)

    # --- Report writing ---
    state = run_report_writing(state)

    # --- Follow-up Q&A ---
    run_followup_demo(state)

    # --- Final summary ---
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    charts = state.get("charts", [])
    print(f"  Charts saved: {len(charts)}")
    for c in charts:
        print(f"    {c.get('file_path', 'N/A')}")
    print(f"  Report: {OUTPUT_DIR / ('report_' + session_id[:8] + '.md')}")
    print(f"  Session ID: {session_id}")
    print()


if __name__ == "__main__":
    main()
