"""
nodes.py - LangGraph node implementations for the data analysis pipeline.

Each node is a plain Python function that accepts an AnalysisState dict and
returns a partial state dict. LangGraph merges the returned keys into the
shared state automatically.

Node execution order (main graph):
  data_profiler → planner → analyzer → chart_maker
  → reflector → [conditional] → report_writer → END

Follow-up graph:
  question_router → context_retriever → answerer → END

WHY keep nodes as pure functions (not methods): LangGraph serialises nodes by
reference; plain functions are easiest to pickle and test in isolation.
"""

from __future__ import annotations

import json
import os
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

# Internal imports — resolved relative to the package root
from agent.state import (
    AnalysisState,
    DatasetSummary,
    AnalysisResult,
    ChartOutput,
    ReflectionOutput,
)
from agent.tools import (
    pandas_executor,
    chart_generator,
    stats_calculator,
    outlier_detector,
    pattern_finder,
)
from agent.memory import get_or_create_conversation_memory, get_or_create_context_memory


# ---------------------------------------------------------------------------
# LLM factory (imported lazily to avoid circular imports with graph.py)
# ---------------------------------------------------------------------------

def _get_llm():
    """
    Return the configured LLM instance.

    WHY lazy import: graph.py also imports from nodes.py; importing LLMProvider
    here at module level would create a circular dependency.
    """
    from agent.graph import LLMProvider
    return LLMProvider.get_llm()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _output_dir() -> str:
    """Return the configured output directory, creating it if needed."""
    out = os.getenv("OUTPUT_DIR", "./output")
    Path(out).mkdir(parents=True, exist_ok=True)
    return out


def _safe_invoke(tool_func, **kwargs) -> Dict[str, Any]:
    """Call a LangChain tool and return its result dict, catching all exceptions."""
    try:
        return tool_func.invoke(kwargs)
    except Exception as exc:
        return {"error": str(exc), "result": None}


# ---------------------------------------------------------------------------
# Node 1: data_profiler
# ---------------------------------------------------------------------------

def data_profiler(state: AnalysisState) -> Dict[str, Any]:
    """
    Load the CSV and compute a comprehensive DatasetSummary.

    WHY compute unique counts here: the planner needs to know which columns
    are high-cardinality (continuous) vs low-cardinality (categorical) so it
    can suggest appropriate chart types and analysis strategies.

    Returns state keys: dataset_summary, profiling_results, error.
    """
    dataset_path = state.get("dataset_path", "")
    session_id = state.get("session_id", "default")

    try:
        df = pd.read_csv(dataset_path)
    except Exception as exc:
        return {"error": f"Failed to load dataset: {exc}"}

    # Build DatasetSummary
    dtypes = {col: str(df[col].dtype) for col in df.columns}
    null_counts = {col: int(df[col].isnull().sum()) for col in df.columns}
    unique_counts = {col: int(df[col].nunique()) for col in df.columns}
    sample_rows = df.head(5).to_dict(orient="records")

    summary = DatasetSummary(
        shape=df.shape,
        columns=df.columns.tolist(),
        dtypes=dtypes,
        sample_rows=sample_rows,
        null_counts=null_counts,
        unique_counts=unique_counts,
    )

    # Additional profiling metrics stored in profiling_results
    numeric_df = df.select_dtypes(include="number")
    profiling_results: Dict[str, Any] = {}
    if not numeric_df.empty:
        profiling_results["describe"] = numeric_df.describe().round(4).to_dict()
        profiling_results["skewness"] = numeric_df.skew().round(4).to_dict()
        profiling_results["kurtosis"] = numeric_df.kurt().round(4).to_dict()

    # Persist to context memory for follow-up queries
    ctx_mem = get_or_create_context_memory(session_id)
    ctx_mem.update_dataset_summary(summary.to_dict())

    return {
        "dataset_summary": summary.to_dict(),
        "profiling_results": profiling_results,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Node 2: planner
# ---------------------------------------------------------------------------

def planner(state: AnalysisState) -> Dict[str, Any]:
    """
    Use the LLM to generate a tailored 5-7 step analysis plan.

    WHY LLM-generated plan: different datasets warrant different analyses.
    A dataset with many numeric columns should include correlation analysis;
    one with a date column needs time-series trending. The LLM infers this
    from the dataset summary rather than hard-coding rules.

    Returns state keys: analysis_plan.
    """
    summary = state.get("dataset_summary", {})
    session_id = state.get("session_id", "default")

    if not summary:
        return {"analysis_plan": ["Compute basic statistics for all columns."]}

    columns = summary.get("columns", [])
    dtypes = summary.get("dtypes", {})
    shape = summary.get("shape", [0, 0])
    null_counts = summary.get("null_counts", {})
    unique_counts = summary.get("unique_counts", {})

    numeric_cols = [c for c, t in dtypes.items() if "int" in t or "float" in t]
    categorical_cols = [c for c, t in dtypes.items() if "object" in t or "category" in t]
    date_cols = [c for c in columns if any(kw in c.lower() for kw in ["date", "time", "month", "year"])]
    has_nulls = any(v > 0 for v in null_counts.values())

    prompt = f"""You are a senior data analyst. Given the following dataset summary,
create a focused 5-7 step analysis plan. Each step should be a single, specific,
actionable analysis task. Return ONLY a JSON array of strings, no other text.

Dataset shape: {shape[0]} rows × {shape[1]} columns
Numeric columns: {numeric_cols}
Categorical columns: {categorical_cols}
Date/time columns: {date_cols}
Has missing values: {has_nulls}
Sample columns: {columns[:20]}

Return format (JSON array only):
["Step 1: ...", "Step 2: ...", ...]

Make steps specific to this dataset. Include:
- Descriptive statistics for numeric columns (if present)
- Distribution analysis for key numeric columns
- Category frequency analysis (if categorical columns present)
- Correlation analysis (if 2+ numeric columns)
- Trend analysis over time (if date column present)
- Outlier detection for important numeric columns
- Data quality assessment (nulls, duplicates)"""

    try:
        llm = _get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Parse JSON array from response
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            plan = json.loads(match.group())
        else:
            # Fallback: split by numbered lines
            plan = [line.strip() for line in raw.split("\n") if line.strip() and line.strip()[0].isdigit()]

        if not plan:
            raise ValueError("Empty plan returned by LLM.")

    except Exception as exc:
        # Fallback plan constructed from dataset metadata
        plan = _fallback_plan(numeric_cols, categorical_cols, date_cols)

    # Persist plan to context memory
    ctx_mem = get_or_create_context_memory(session_id)
    ctx_mem.update_analysis_plan(plan)

    return {"analysis_plan": plan[:7]}  # cap at 7 steps


def _fallback_plan(
    numeric_cols: List[str],
    categorical_cols: List[str],
    date_cols: List[str],
) -> List[str]:
    """Generate a rule-based fallback plan when the LLM fails."""
    steps: List[str] = []
    steps.append("Step 1: Compute descriptive statistics (mean, median, std, min, max) for all numeric columns.")
    if numeric_cols:
        steps.append(f"Step 2: Analyse the distribution and skewness of '{numeric_cols[0]}' and related columns.")
    if categorical_cols:
        steps.append(f"Step 3: Count value frequencies for categorical column '{categorical_cols[0]}'.")
    if len(numeric_cols) >= 2:
        steps.append("Step 4: Compute pairwise correlations between numeric columns.")
    if date_cols:
        steps.append(f"Step 5: Analyse trends over time using the '{date_cols[0]}' column.")
    if numeric_cols:
        steps.append(f"Step 6: Detect outliers in '{numeric_cols[0]}' using the IQR method.")
    steps.append("Step 7: Assess data quality — check for missing values and duplicate rows.")
    return steps


# ---------------------------------------------------------------------------
# Node 3: analyzer
# ---------------------------------------------------------------------------

def analyzer(state: AnalysisState) -> Dict[str, Any]:
    """
    Execute each step in the analysis plan and collect findings.

    WHY accumulate results across iterations: when the reflector sends the graph
    back for a deeper pass, previous results are preserved and new results are
    appended, giving the report writer a richer body of evidence.

    Returns state keys: analysis_results, iteration_count.
    """
    dataset_path = state.get("dataset_path", "")
    plan = state.get("analysis_plan", [])
    session_id = state.get("session_id", "default")
    existing_results: List[Dict] = list(state.get("analysis_results", []))
    iteration_count = state.get("iteration_count", 0)

    summary = state.get("dataset_summary", {})
    dtypes = summary.get("dtypes", {})
    columns = summary.get("columns", [])
    numeric_cols = [c for c, t in dtypes.items() if "int" in t or "float" in t]

    new_results: List[Dict] = []

    for step in plan:
        step_lower = step.lower()

        try:
            # --- Descriptive stats ---
            if any(kw in step_lower for kw in ["descriptive", "statistic", "mean", "median", "std"]):
                target_cols = numeric_cols[:8] if numeric_cols else columns[:8]
                raw = _safe_invoke(stats_calculator, dataset_path=dataset_path, columns=target_cols)
                findings = _summarise_stats(raw)
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

            # --- Distribution / skewness ---
            elif any(kw in step_lower for kw in ["distribution", "skew", "histogram"]):
                target_cols = numeric_cols[:4] if numeric_cols else columns[:4]
                raw = _safe_invoke(stats_calculator, dataset_path=dataset_path, columns=target_cols)
                skew_info = raw.get("skewness", {})
                findings = _summarise_skewness(skew_info)
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

            # --- Category frequencies ---
            elif any(kw in step_lower for kw in ["categor", "frequen", "count", "value"]):
                cat_cols = [c for c, t in dtypes.items() if "object" in t or "category" in t][:4]
                if cat_cols:
                    raw = _safe_invoke(stats_calculator, dataset_path=dataset_path, columns=cat_cols)
                    findings = _summarise_categories(raw.get("value_counts", {}))
                else:
                    findings = "No categorical columns found in the dataset."
                    raw = {}
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

            # --- Correlation ---
            elif any(kw in step_lower for kw in ["correlat", "relationship"]):
                if len(numeric_cols) >= 2:
                    raw = _safe_invoke(stats_calculator, dataset_path=dataset_path, columns=numeric_cols[:8])
                    findings = _summarise_correlations(raw.get("correlation", {}))
                else:
                    findings = "Fewer than 2 numeric columns — correlation analysis skipped."
                    raw = {}
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

            # --- Outlier detection ---
            elif any(kw in step_lower for kw in ["outlier", "anomal"]):
                outlier_findings: List[str] = []
                outlier_data: Dict = {}
                for col in numeric_cols[:3]:
                    res = _safe_invoke(outlier_detector, dataset_path=dataset_path, column=col)
                    if not res.get("error"):
                        outlier_data[col] = res
                        sev = res.get("severity", "none")
                        pct = res.get("outlier_pct", 0)
                        outlier_findings.append(
                            f"'{col}': {res.get('outlier_count', 0)} outliers ({pct}%) — severity: {sev}."
                        )
                findings = " | ".join(outlier_findings) if outlier_findings else "No numeric columns for outlier detection."
                new_results.append(AnalysisResult(step=step, findings=findings, data=outlier_data).to_dict())

            # --- Trend / time-series ---
            elif any(kw in step_lower for kw in ["trend", "time", "temporal", "date"]):
                raw = _safe_invoke(pattern_finder, dataset_path=dataset_path)
                trends = raw.get("trends", [])
                if trends:
                    trend_lines = [
                        f"'{t['value_column']}' shows {t['trend_direction']} trend over '{t['date_column']}' "
                        f"(R²={t['r_squared']}, p={t['p_value']})"
                        for t in trends
                    ]
                    findings = "; ".join(trend_lines)
                else:
                    findings = "No clear time-based trends detected (no date columns or insufficient data)."
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

            # --- Data quality ---
            elif any(kw in step_lower for kw in ["quality", "missing", "null", "duplicat"]):
                code = """
null_counts = df.isnull().sum()
dup_count = df.duplicated().sum()
null_pct = (null_counts / len(df) * 100).round(2)
f"Nulls: {null_counts[null_counts > 0].to_dict()} | Null%: {null_pct[null_pct > 0].to_dict()} | Duplicates: {dup_count}"
"""
                raw = _safe_invoke(pandas_executor, code=code.strip(), dataset_path=dataset_path)
                findings = raw.get("result", "Could not compute data quality metrics.") or ""
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

            # --- Generic fallback: use pattern_finder ---
            else:
                raw = _safe_invoke(pattern_finder, dataset_path=dataset_path)
                corrs = raw.get("correlations", [])
                top_corr = corrs[0] if corrs else {}
                findings = (
                    f"Top correlation: {top_corr.get('col_a')} ↔ {top_corr.get('col_b')} = "
                    f"{top_corr.get('correlation')}" if top_corr else "Pattern analysis completed."
                )
                new_results.append(AnalysisResult(step=step, findings=findings, data=raw).to_dict())

        except Exception as exc:
            new_results.append(AnalysisResult(
                step=step,
                findings=f"Analysis failed: {exc}",
                data={"error": traceback.format_exc(limit=3)},
            ).to_dict())

    # Merge with previous iteration results
    all_results = existing_results + new_results

    # Persist to context memory
    ctx_mem = get_or_create_context_memory(session_id)
    ctx_mem.update_analysis_results(all_results)

    return {
        "analysis_results": all_results,
        "iteration_count": iteration_count + 1,
    }


# --- Analyser helpers ---

def _summarise_stats(raw: Dict) -> str:
    desc = raw.get("descriptive", {})
    if not desc:
        return "No numeric columns available for descriptive statistics."
    lines: List[str] = []
    # desc is {col: {stat: value}}
    for col, stats in list(desc.items())[:5]:
        mean_val = stats.get("mean", "N/A")
        std_val = stats.get("std", "N/A")
        min_val = stats.get("min", "N/A")
        max_val = stats.get("max", "N/A")
        lines.append(f"'{col}': mean={mean_val}, std={std_val}, min={min_val}, max={max_val}")
    return " | ".join(lines)


def _summarise_skewness(skew_info: Dict) -> str:
    if not skew_info:
        return "Skewness could not be computed."
    lines: List[str] = []
    for col, val in skew_info.items():
        if abs(val) > 1:
            direction = "right-skewed (positive)" if val > 0 else "left-skewed (negative)"
            lines.append(f"'{col}': {direction} (skew={val:.2f}) — consider log transform")
        else:
            lines.append(f"'{col}': approximately symmetric (skew={val:.2f})")
    return " | ".join(lines)


def _summarise_categories(value_counts: Dict) -> str:
    if not value_counts:
        return "No categorical columns analysed."
    lines: List[str] = []
    for col, counts in value_counts.items():
        top_item = next(iter(counts.items()), ("N/A", 0))
        unique_n = len(counts)
        lines.append(f"'{col}': top value='{top_item[0]}' ({top_item[1]} occurrences), {unique_n} unique shown")
    return " | ".join(lines)


def _summarise_correlations(corr: Dict) -> str:
    if not corr:
        return "Correlation matrix could not be computed."
    # Find the highest-magnitude off-diagonal pair
    best_pair = ("N/A", "N/A", 0.0)
    for col_a, row in corr.items():
        for col_b, val in row.items():
            if col_a != col_b and abs(val) > abs(best_pair[2]):
                best_pair = (col_a, col_b, val)
    if best_pair[0] == "N/A":
        return "No significant correlations found."
    strength = "strong" if abs(best_pair[2]) > 0.7 else "moderate" if abs(best_pair[2]) > 0.4 else "weak"
    direction = "positive" if best_pair[2] > 0 else "negative"
    return (
        f"Strongest correlation: '{best_pair[0]}' ↔ '{best_pair[1]}' = {best_pair[2]:.3f} "
        f"({strength} {direction} relationship)."
    )


# ---------------------------------------------------------------------------
# Node 4: chart_maker
# ---------------------------------------------------------------------------

def chart_maker(state: AnalysisState) -> Dict[str, Any]:
    """
    Generate 3-5 charts relevant to the dataset column types.

    WHY column-type-driven chart selection: the right visualisation depends on
    data type. Histograms suit continuous numeric distributions; bar charts suit
    categorical frequencies; heatmaps suit multi-column correlations; line
    charts suit time-series data. Choosing blindly wastes chart budget.

    Returns state keys: charts.
    """
    dataset_path = state.get("dataset_path", "")
    summary = state.get("dataset_summary", {})
    session_id = state.get("session_id", "default")
    out_dir = os.path.join(_output_dir(), session_id)

    dtypes = summary.get("dtypes", {})
    columns = summary.get("columns", [])
    numeric_cols = [c for c, t in dtypes.items() if "int" in t or "float" in t]
    cat_cols = [c for c, t in dtypes.items() if "object" in t or "category" in t]
    date_cols = [c for c in columns if any(kw in c.lower() for kw in ["date", "time", "month", "year"])]

    chart_specs: List[Dict] = []
    generated: List[Dict] = []

    # 1. Histogram of the first numeric column
    if numeric_cols:
        chart_specs.append({
            "chart_type": "histogram",
            "x_col": numeric_cols[0],
            "y_col": "",
            "title": f"Distribution of {numeric_cols[0]}",
        })

    # 2. Box plot of second numeric column (outlier view)
    if len(numeric_cols) >= 2:
        chart_specs.append({
            "chart_type": "box",
            "x_col": numeric_cols[1],
            "y_col": "",
            "title": f"Box Plot of {numeric_cols[1]}",
        })

    # 3. Bar chart for first categorical column
    if cat_cols:
        chart_specs.append({
            "chart_type": "bar",
            "x_col": cat_cols[0],
            "y_col": "",
            "title": f"Frequency of {cat_cols[0]}",
        })

    # 4. Correlation heatmap (needs 2+ numeric cols)
    if len(numeric_cols) >= 2:
        chart_specs.append({
            "chart_type": "heatmap",
            "x_col": "",
            "y_col": "",
            "title": "Correlation Heatmap",
        })

    # 5. Scatter plot (first two numeric columns) or line (date + numeric)
    if date_cols and numeric_cols:
        chart_specs.append({
            "chart_type": "line",
            "x_col": date_cols[0],
            "y_col": numeric_cols[0],
            "title": f"{numeric_cols[0]} Over Time",
        })
    elif len(numeric_cols) >= 2:
        chart_specs.append({
            "chart_type": "scatter",
            "x_col": numeric_cols[0],
            "y_col": numeric_cols[1],
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
        })

    for spec in chart_specs[:5]:  # max 5 charts
        result = _safe_invoke(
            chart_generator,
            dataset_path=dataset_path,
            chart_type=spec["chart_type"],
            x_col=spec["x_col"],
            y_col=spec["y_col"],
            title=spec["title"],
            output_dir=out_dir,
        )
        if result.get("file_path"):
            chart_out = ChartOutput(
                title=spec["title"],
                chart_type=spec["chart_type"],
                file_path=result["file_path"],
                description=result.get("description", spec["title"]),
            )
            generated.append(chart_out.to_dict())

    # Persist to context memory
    ctx_mem = get_or_create_context_memory(session_id)
    ctx_mem.update_charts(generated)

    return {"charts": generated}


# ---------------------------------------------------------------------------
# Node 5: reflector (DataCritic)
# ---------------------------------------------------------------------------

def reflector(state: AnalysisState) -> Dict[str, Any]:
    """
    DataCritic: evaluate analysis quality and decide whether to iterate.

    WHY reflection loop: LLM-generated analyses often miss second-order insights
    (e.g. an outlier in one column correlating with a category in another). The
    DataCritic reads the findings and assigns a score, triggering a re-analysis
    when depth is insufficient.

    Approval logic:
      approved = (score >= threshold) OR (iteration_count >= MAX_REFLECTION_ITERATIONS)

    The second condition prevents infinite loops even when the LLM gives low scores.

    Returns state keys: reflection.
    """
    analysis_results = state.get("analysis_results", [])
    dataset_summary = state.get("dataset_summary", {})
    iteration_count = state.get("iteration_count", 0)
    session_id = state.get("session_id", "default")

    threshold = float(os.getenv("REFLECTION_QUALITY_THRESHOLD", "7.0"))
    max_iter = int(os.getenv("MAX_REFLECTION_ITERATIONS", "2"))

    # Summarise findings for the critic
    findings_text = "\n".join(
        f"- {r.get('step', '')}: {r.get('findings', '')}"
        for r in analysis_results
    )
    shape = dataset_summary.get("shape", [0, 0])
    columns = dataset_summary.get("columns", [])

    prompt = f"""You are a DataCritic — a senior analyst reviewing the quality of a data analysis.

Dataset: {shape[0]} rows × {shape[1]} columns. Columns: {columns[:15]}

Analysis findings so far:
{findings_text}

Evaluate the analysis quality on a scale of 0-10.
Look for:
- Are key numeric columns statistically characterised?
- Are outliers identified?
- Are correlations explored?
- Are category distributions understood?
- Are trends or time patterns noted?
- Are actionable insights present?

Return ONLY valid JSON in this exact format:
{{
  "quality_score": <float 0-10>,
  "shallow_areas": ["area1", "area2"],
  "suggestions": ["suggestion1", "suggestion2"]
}}"""

    try:
        llm = _get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Extract JSON block
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            parsed = json.loads(raw)

        score = float(parsed.get("quality_score", 5.0))
        shallow = parsed.get("shallow_areas", [])
        suggestions = parsed.get("suggestions", [])

    except Exception:
        # Fallback: assign moderate score based on number of completed steps
        score = min(5.0 + len(analysis_results) * 0.5, 8.0)
        shallow = ["Unable to parse LLM critique — using heuristic score."]
        suggestions = ["Ensure all numeric columns have been analysed for outliers and correlations."]

    approved = (score >= threshold) or (iteration_count >= max_iter)

    reflection = ReflectionOutput(
        quality_score=score,
        shallow_areas=shallow,
        suggestions=suggestions,
        approved=approved,
    )

    # Persist to context memory
    ctx_mem = get_or_create_context_memory(session_id)
    ctx_mem.update_reflection(reflection.to_dict())

    return {"reflection": reflection.to_dict()}


# ---------------------------------------------------------------------------
# Node 6: report_writer
# ---------------------------------------------------------------------------

def report_writer(state: AnalysisState) -> Dict[str, Any]:
    """
    Synthesise all analysis artefacts into a comprehensive markdown report.

    WHY LLM-generated prose + structured sections: pure LLM prose is fluent
    but can hallucinate numbers; pure data dumps are accurate but unreadable.
    Combining both — injecting verified numbers into a structured prompt —
    gives the best of both worlds.

    Returns state keys: final_report.
    """
    dataset_summary = state.get("dataset_summary", {})
    analysis_results = state.get("analysis_results", [])
    charts = state.get("charts", [])
    reflection = state.get("reflection", {})
    analysis_plan = state.get("analysis_plan", [])
    session_id = state.get("session_id", "default")

    shape = dataset_summary.get("shape", [0, 0])
    columns = dataset_summary.get("columns", [])
    dtypes = dataset_summary.get("dtypes", {})
    null_counts = dataset_summary.get("null_counts", {})
    quality_score = reflection.get("quality_score", "N/A") if reflection else "N/A"

    # --- Build structured context for the LLM ---
    findings_text = "\n".join(
        f"### {r.get('step', 'Step')}\n{r.get('findings', '')}"
        for r in analysis_results
    )

    chart_section = "\n".join(
        f"- **{c.get('title', '')}** ({c.get('chart_type', '')}): {c.get('description', '')}  \n"
        f"  `{c.get('file_path', '')}`"
        for c in charts
    )

    null_summary = {col: cnt for col, cnt in null_counts.items() if cnt > 0}

    prompt = f"""You are a senior data analyst writing a professional report.
Using the analysis findings below, write a comprehensive markdown report.

DATASET PROFILE:
- Rows: {shape[0]}, Columns: {shape[1]}
- Column names: {columns}
- Missing value columns: {null_summary}
- Analysis quality score (0-10): {quality_score}

ANALYSIS PLAN EXECUTED:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(analysis_plan))}

KEY FINDINGS FROM ANALYSIS:
{findings_text}

Write the report with these EXACT markdown sections:
# Data Analysis Report

## Executive Summary
(2-3 sentences covering the most important insights)

## Data Profile
(Table or bullet list of dataset shape, column types, missing values)

## Key Findings
(Numbered list of the most important analytical insights with specific numbers)

## Statistical Analysis
(Organised breakdown of statistics per column or analysis step)

## Data Quality Assessment
(Missing values, outliers, data integrity issues found)

## Visualisations
{chart_section if chart_section else "(No charts generated)"}

## Recommendations
(3-5 concrete, actionable recommendations based on the findings)

## Methodology
(Brief note on tools and methods used)

---
*Report generated by AI Data Analysis Pipeline | Quality score: {quality_score}/10*"""

    try:
        llm = _get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        report = response.content.strip()
    except Exception as exc:
        # Fallback: assemble report from raw data without LLM
        report = _fallback_report(state, chart_section)

    # Persist to context memory
    ctx_mem = get_or_create_context_memory(session_id)
    ctx_mem.update_final_report(report)

    # Optionally save to disk
    out_dir = os.path.join(_output_dir(), session_id)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    report_path = os.path.join(out_dir, "report.md")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
    except Exception:
        pass  # Non-critical; report is still in state

    return {"final_report": report}


def _fallback_report(state: AnalysisState, chart_section: str) -> str:
    """Construct a plain markdown report without LLM when the model fails."""
    ds = state.get("dataset_summary", {})
    shape = ds.get("shape", [0, 0])
    columns = ds.get("columns", [])
    results = state.get("analysis_results", [])

    findings_md = "\n".join(
        f"### {r.get('step', 'Step')}\n{r.get('findings', 'N/A')}\n"
        for r in results
    )

    return f"""# Data Analysis Report

## Executive Summary
Analysis of a dataset with {shape[0]} rows and {shape[1]} columns was completed.
Key findings are summarised in the sections below.

## Data Profile
- **Rows**: {shape[0]}
- **Columns**: {shape[1]}
- **Column names**: {', '.join(columns)}

## Key Findings
{findings_md}

## Visualisations
{chart_section if chart_section else "No charts were generated."}

## Recommendations
- Investigate columns with high null rates.
- Review outliers before building predictive models.
- Explore correlations highlighted in the analysis.

---
*Report generated by AI Data Analysis Pipeline (fallback mode)*"""


# ---------------------------------------------------------------------------
# Node 7: question_router
# ---------------------------------------------------------------------------

def question_router(state: AnalysisState) -> Dict[str, Any]:
    """
    Determine whether the follow-up question needs fresh dataset queries or
    can be answered from existing analysis results.

    WHY routing: re-running the full analysis graph for every follow-up question
    is expensive. Most follow-up questions ("What is the average revenue?",
    "Which region performed best?") can be answered from cached analysis results.
    Only questions about unseen columns or new time windows need re-querying.

    This node is a pass-through — it doesn't modify state, but the conditional
    edge in graph.py reads `follow_up_question` to decide the route.

    Returns: empty dict (routing decision made via edge condition).
    """
    # Routing logic is handled by the conditional edge in graph.py.
    # This node is intentionally lightweight; it could be expanded to set
    # a "needs_requery" flag if more nuanced routing is required.
    return {}


# ---------------------------------------------------------------------------
# Node 8: context_retriever
# ---------------------------------------------------------------------------

def context_retriever(state: AnalysisState) -> Dict[str, Any]:
    """
    Retrieve relevant prior analysis context for the follow-up question.

    WHY keyword scoring over vector search: the analysis results are small
    (< 50 entries), making semantic vector search unnecessary overhead.
    Simple keyword overlap is fast, deterministic, and sufficient at this scale.

    Returns state keys: conversation_history (with injected context).
    """
    question = state.get("follow_up_question", "")
    session_id = state.get("session_id", "default")
    history = list(state.get("conversation_history", []))

    ctx_mem = get_or_create_context_memory(session_id)
    context_text = ctx_mem.get_context_for_query(question, max_results=5)

    # Inject context as a system message prepended to the conversation
    system_msg = SystemMessage(
        content=f"Prior analysis context:\n{context_text}"
    )
    # Only prepend if not already present
    if not history or not isinstance(history[0], SystemMessage):
        history = [system_msg] + history
    else:
        history[0] = system_msg

    return {"conversation_history": history}


# ---------------------------------------------------------------------------
# Node 9: answerer
# ---------------------------------------------------------------------------

def answerer(state: AnalysisState) -> Dict[str, Any]:
    """
    Generate a specific, grounded answer to the follow-up question.

    WHY ground in prior analysis: free-form LLM answers may hallucinate numbers.
    By injecting verified analysis results via context_retriever, the LLM can
    cite real computed values rather than making them up.

    Returns state keys: follow_up_answer, conversation_history.
    """
    question = state.get("follow_up_question", "")
    session_id = state.get("session_id", "default")
    history = list(state.get("conversation_history", []))

    # Append the current question
    history.append(HumanMessage(content=question))

    prompt_messages = history + [
        HumanMessage(
            content=(
                f"Please answer the following question based on the analysis context provided:\n\n"
                f"Question: {question}\n\n"
                f"Provide a specific, data-grounded answer. Reference actual numbers where available."
            )
        )
    ]

    try:
        llm = _get_llm()
        response = llm.invoke(prompt_messages)
        answer = response.content.strip()
    except Exception as exc:
        answer = f"Unable to generate answer: {exc}"

    # Append AI answer to history
    history.append(AIMessage(content=answer))

    # Persist conversation
    conv_mem = get_or_create_conversation_memory(session_id)
    conv_mem.add_human_message(question)
    conv_mem.add_ai_message(answer)

    return {
        "follow_up_answer": answer,
        "conversation_history": history,
    }
