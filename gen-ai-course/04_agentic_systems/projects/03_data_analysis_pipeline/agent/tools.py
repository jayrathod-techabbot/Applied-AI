"""
tools.py - LangChain tool definitions for the data analysis pipeline.

WHY @tool decorator: LangChain's @tool wraps a plain Python function in a
StructuredTool, giving it a JSON schema that the LLM can call in ReAct loops
and making it importable by LangGraph nodes without additional boilerplate.

Security note on pandas_executor:
  The most dangerous operation in this pipeline is executing LLM-generated
  Python code. We mitigate this with a restricted exec() sandbox that removes
  dangerous builtins (open, __import__, eval, exec) and only exposes the
  DataFrame already loaded from the validated path. This is defence-in-depth,
  not a complete sandbox — production deployments should use gVisor or similar.
"""

import io
import os
import sys
import traceback
import contextlib
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — no GUI needed on servers
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats as scipy_stats

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _load_csv(dataset_path: str) -> pd.DataFrame:
    """Load and return a DataFrame, raising ValueError on bad paths."""
    path = Path(dataset_path)
    if not path.exists():
        raise ValueError(f"Dataset not found: {dataset_path}")
    if path.suffix.lower() not in {".csv", ".tsv"}:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    return pd.read_csv(path, sep=sep)


def _safe_builtins() -> Dict[str, Any]:
    """
    Return a restricted __builtins__ dict for the exec sandbox.

    WHY whitelist instead of blacklist: new dangerous builtins may be added
    in future Python versions; a whitelist stays safe by default.
    """
    allowed = {
        "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr",
        "dict", "dir", "divmod", "enumerate", "filter", "float", "format",
        "frozenset", "getattr", "hasattr", "hash", "hex", "int", "isinstance",
        "issubclass", "iter", "len", "list", "map", "max", "min", "next",
        "oct", "ord", "pow", "print", "range", "repr", "reversed", "round",
        "set", "setattr", "slice", "sorted", "str", "sum", "tuple", "type",
        "zip", "None", "True", "False",
    }
    import builtins
    return {name: getattr(builtins, name) for name in allowed if hasattr(builtins, name)}


# ---------------------------------------------------------------------------
# Tool 1: pandas_executor
# ---------------------------------------------------------------------------

@tool
def pandas_executor(code: str, dataset_path: str) -> Dict[str, Any]:
    """
    Safely execute a snippet of pandas code in a restricted sandbox.

    The DataFrame is pre-loaded and available as `df` inside the code.
    The result of the last expression (if it is a DataFrame, Series, or
    scalar) is captured and returned together with any stdout output.

    Args:
        code: Python code string using `df` as the DataFrame variable.
        dataset_path: Path to the CSV file to load as `df`.

    Returns:
        Dict with keys: result (str), stdout (str), error (str or None).

    Security:
        - Dangerous builtins (open, __import__, eval, exec, compile) are removed.
        - os, sys, subprocess modules are not injected into the namespace.
        - The code runs in a fresh dict namespace with only df + safe builtins.
    """
    try:
        df = _load_csv(dataset_path)
    except ValueError as exc:
        return {"result": None, "stdout": "", "error": str(exc)}

    # Check for obviously dangerous patterns before exec
    danger_patterns = [
        "import os", "import sys", "import subprocess", "import shutil",
        "__import__", "open(", "exec(", "eval(", "compile(", "globals()",
        "locals()", "getattr(", "setattr(", "delattr(", "vars(",
        "os.system", "os.popen", "subprocess.run", "subprocess.call",
    ]
    for pattern in danger_patterns:
        if pattern in code:
            return {
                "result": None,
                "stdout": "",
                "error": f"Blocked: dangerous pattern detected — '{pattern}'",
            }

    # Build restricted namespace
    namespace: Dict[str, Any] = {
        "__builtins__": _safe_builtins(),
        "df": df,
        "pd": pd,
        "np": np,
    }

    # Capture stdout
    stdout_capture = io.StringIO()
    result_value = None

    try:
        with contextlib.redirect_stdout(stdout_capture):
            # Split code into statements; exec all but last; eval last for result
            import ast
            tree = ast.parse(code, mode="exec")
            if tree.body:
                last_node = tree.body[-1]
                # If the last statement is an expression, eval it for the result
                if isinstance(last_node, ast.Expr):
                    exec_tree = ast.Module(body=tree.body[:-1], type_ignores=[])
                    eval_expr = ast.Expression(body=last_node.value)
                    exec(compile(exec_tree, "<sandbox>", "exec"), namespace)
                    result_value = eval(compile(eval_expr, "<sandbox>", "eval"), namespace)
                else:
                    exec(compile(tree, "<sandbox>", "exec"), namespace)
    except Exception:
        return {
            "result": None,
            "stdout": stdout_capture.getvalue(),
            "error": traceback.format_exc(limit=5),
        }

    # Serialise result to string for JSON transport
    if result_value is None:
        result_str = stdout_capture.getvalue() or "Code executed successfully (no return value)."
    elif isinstance(result_value, pd.DataFrame):
        result_str = result_value.to_string(max_rows=20)
    elif isinstance(result_value, pd.Series):
        result_str = result_value.to_string(max_rows=20)
    else:
        result_str = str(result_value)

    return {
        "result": result_str,
        "stdout": stdout_capture.getvalue(),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Tool 2: chart_generator
# ---------------------------------------------------------------------------

@tool
def chart_generator(
    dataset_path: str,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str,
    output_dir: str,
) -> Dict[str, Any]:
    """
    Generate and save a matplotlib chart as a PNG file.

    Supported chart types: histogram, bar, scatter, line, box, heatmap.
    For heatmap, x_col and y_col are ignored (uses all numeric columns).

    Args:
        dataset_path: Path to the CSV file.
        chart_type:   One of histogram | bar | scatter | line | box | heatmap.
        x_col:        Column name for the x-axis (or value column for histogram/box).
        y_col:        Column name for the y-axis (ignored for histogram/box/heatmap).
        title:        Chart title used as filename slug and figure title.
        output_dir:   Directory where the PNG will be saved.

    Returns:
        Dict with keys: file_path (str), description (str), error (str or None).
    """
    try:
        df = _load_csv(dataset_path)
    except ValueError as exc:
        return {"file_path": None, "description": "", "error": str(exc)}

    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Sanitise filename
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)
    safe_title = safe_title.strip().replace(" ", "_")[:60]
    file_path = str(out_path / f"{safe_title}.png")

    fig, ax = plt.subplots(figsize=(10, 6))
    description = ""

    try:
        chart_type_lower = chart_type.lower()

        if chart_type_lower == "histogram":
            if x_col not in df.columns:
                return {"file_path": None, "description": "", "error": f"Column '{x_col}' not found."}
            ax.hist(df[x_col].dropna(), bins=30, color="steelblue", edgecolor="white", alpha=0.85)
            ax.set_xlabel(x_col)
            ax.set_ylabel("Frequency")
            description = f"Distribution of {x_col}"

        elif chart_type_lower == "bar":
            if x_col not in df.columns:
                return {"file_path": None, "description": "", "error": f"Column '{x_col}' not found."}
            counts = df[x_col].value_counts().head(15)
            ax.bar(counts.index.astype(str), counts.values, color="steelblue", edgecolor="white")
            ax.set_xlabel(x_col)
            ax.set_ylabel("Count")
            plt.xticks(rotation=45, ha="right")
            description = f"Value counts of {x_col} (top 15)"

        elif chart_type_lower == "scatter":
            for col in [x_col, y_col]:
                if col not in df.columns:
                    return {"file_path": None, "description": "", "error": f"Column '{col}' not found."}
            ax.scatter(df[x_col], df[y_col], alpha=0.5, color="steelblue", s=20)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            description = f"Scatter plot of {x_col} vs {y_col}"

        elif chart_type_lower == "line":
            for col in [x_col, y_col]:
                if col not in df.columns:
                    return {"file_path": None, "description": "", "error": f"Column '{col}' not found."}
            sorted_df = df[[x_col, y_col]].dropna().sort_values(by=x_col)
            ax.plot(sorted_df[x_col], sorted_df[y_col], color="steelblue", linewidth=1.5)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            plt.xticks(rotation=45, ha="right")
            description = f"Line chart of {y_col} over {x_col}"

        elif chart_type_lower == "box":
            if x_col not in df.columns:
                return {"file_path": None, "description": "", "error": f"Column '{x_col}' not found."}
            ax.boxplot(df[x_col].dropna(), patch_artist=True,
                       boxprops=dict(facecolor="steelblue", alpha=0.7))
            ax.set_ylabel(x_col)
            description = f"Box plot of {x_col} showing quartiles and outliers"

        elif chart_type_lower == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            if numeric_df.empty:
                return {"file_path": None, "description": "", "error": "No numeric columns for heatmap."}
            corr = numeric_df.corr()
            im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr.columns)))
            ax.set_yticks(range(len(corr.columns)))
            ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
            ax.set_yticklabels(corr.columns, fontsize=8)
            plt.colorbar(im, ax=ax)
            # Annotate cells
            for i in range(len(corr.columns)):
                for j in range(len(corr.columns)):
                    ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center",
                            fontsize=7, color="black")
            description = "Correlation heatmap of numeric columns"

        else:
            plt.close(fig)
            return {"file_path": None, "description": "", "error": f"Unknown chart_type: '{chart_type}'"}

        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        fig.tight_layout()
        fig.savefig(file_path, dpi=120, bbox_inches="tight")
        plt.close(fig)

        return {"file_path": file_path, "description": description, "error": None}

    except Exception:
        plt.close(fig)
        return {
            "file_path": None,
            "description": "",
            "error": traceback.format_exc(limit=5),
        }


# ---------------------------------------------------------------------------
# Tool 3: stats_calculator
# ---------------------------------------------------------------------------

@tool
def stats_calculator(dataset_path: str, columns: List[str]) -> Dict[str, Any]:
    """
    Compute descriptive statistics, correlations, and skewness for given columns.

    Args:
        dataset_path: Path to the CSV file.
        columns:      List of column names to analyse. Non-numeric columns are
                      included in value-count summaries only.

    Returns:
        Dict with keys:
          descriptive  – describe() output per numeric column
          correlation  – pairwise Pearson correlation matrix (numeric cols)
          skewness     – skewness score per numeric column
          value_counts – top-10 value counts for categorical columns
          error        – error message string or None
    """
    try:
        df = _load_csv(dataset_path)
    except ValueError as exc:
        return {"error": str(exc)}

    # Validate columns
    missing = [c for c in columns if c not in df.columns]
    if missing:
        return {"error": f"Columns not found in dataset: {missing}"}

    subset = df[columns]
    numeric_cols = subset.select_dtypes(include="number").columns.tolist()
    categorical_cols = [c for c in columns if c not in numeric_cols]

    result: Dict[str, Any] = {"error": None}

    # Descriptive statistics
    if numeric_cols:
        desc = subset[numeric_cols].describe().round(4)
        result["descriptive"] = desc.to_dict()

        # Correlation matrix
        if len(numeric_cols) > 1:
            corr = subset[numeric_cols].corr().round(4)
            result["correlation"] = corr.to_dict()
        else:
            result["correlation"] = {}

        # Skewness
        skew = {col: round(float(subset[col].skew()), 4) for col in numeric_cols}
        result["skewness"] = skew
    else:
        result["descriptive"] = {}
        result["correlation"] = {}
        result["skewness"] = {}

    # Value counts for categorical columns
    result["value_counts"] = {}
    for col in categorical_cols:
        vc = df[col].value_counts().head(10)
        result["value_counts"][col] = vc.to_dict()

    return result


# ---------------------------------------------------------------------------
# Tool 4: outlier_detector
# ---------------------------------------------------------------------------

@tool
def outlier_detector(dataset_path: str, column: str) -> Dict[str, Any]:
    """
    Detect outliers in a numeric column using the IQR (interquartile range) method.

    An observation is an outlier if it falls below Q1 - 1.5*IQR
    or above Q3 + 1.5*IQR. This is the standard Tukey fence method.

    WHY IQR over Z-score: IQR is robust to non-normal distributions, which are
    common in real-world datasets (revenue, quantity, web traffic, etc.).

    Args:
        dataset_path: Path to the CSV file.
        column:       Name of the numeric column to check.

    Returns:
        Dict with keys:
          column        – column name
          q1, q3, iqr   – quartile statistics
          lower_fence   – lower bound below which values are outliers
          upper_fence   – upper bound above which values are outliers
          outlier_count – number of outlier rows
          outlier_pct   – percentage of rows that are outliers
          outlier_values – list of outlier values (up to 50)
          severity      – "none" | "mild" | "moderate" | "severe"
          error         – error message or None
    """
    try:
        df = _load_csv(dataset_path)
    except ValueError as exc:
        return {"error": str(exc)}

    if column not in df.columns:
        return {"error": f"Column '{column}' not found in dataset."}

    series = df[column].dropna()
    if not pd.api.types.is_numeric_dtype(series):
        return {"error": f"Column '{column}' is not numeric (dtype: {series.dtype})."}

    if series.empty:
        return {"error": f"Column '{column}' has no non-null values."}

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1

    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    outlier_mask = (series < lower_fence) | (series > upper_fence)
    outlier_count = int(outlier_mask.sum())
    outlier_pct = round(outlier_count / len(series) * 100, 2) if len(series) > 0 else 0.0
    outlier_values = series[outlier_mask].tolist()[:50]

    # Severity classification
    if outlier_pct == 0:
        severity = "none"
    elif outlier_pct < 2:
        severity = "mild"
    elif outlier_pct < 10:
        severity = "moderate"
    else:
        severity = "severe"

    return {
        "column": column,
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "lower_fence": round(lower_fence, 4),
        "upper_fence": round(upper_fence, 4),
        "outlier_count": outlier_count,
        "outlier_pct": outlier_pct,
        "outlier_values": outlier_values,
        "severity": severity,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Tool 5: pattern_finder
# ---------------------------------------------------------------------------

@tool
def pattern_finder(dataset_path: str) -> Dict[str, Any]:
    """
    Automatically discover correlations, value distributions, and trends in the dataset.

    WHY automate pattern discovery: LLMs are good at interpreting patterns but
    slow at computing them. Offloading computation to pandas gives deterministic,
    fast results that the LLM then narrates.

    Finds:
      - Top positive and negative Pearson correlations between numeric columns
      - Top value counts (mode) per categorical column
      - Simple time-series trend detection if a date column is present
      - Columns with high null rates (> 20 %)

    Args:
        dataset_path: Path to the CSV file.

    Returns:
        Dict with keys: correlations, top_categories, trends, high_null_columns, error.
    """
    try:
        df = _load_csv(dataset_path)
    except ValueError as exc:
        return {"error": str(exc)}

    result: Dict[str, Any] = {"error": None}

    numeric_df = df.select_dtypes(include="number")
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # --- Correlations ---
    correlations: List[Dict] = []
    if len(numeric_df.columns) > 1:
        corr_matrix = numeric_df.corr()
        pairs_seen = set()
        for col_a in corr_matrix.columns:
            for col_b in corr_matrix.columns:
                if col_a == col_b:
                    continue
                pair = tuple(sorted([col_a, col_b]))
                if pair in pairs_seen:
                    continue
                pairs_seen.add(pair)
                val = corr_matrix.loc[col_a, col_b]
                if not np.isnan(val):
                    correlations.append({
                        "col_a": col_a,
                        "col_b": col_b,
                        "correlation": round(float(val), 4),
                    })
        # Sort by absolute value, return top 10
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        correlations = correlations[:10]
    result["correlations"] = correlations

    # --- Top categories ---
    top_categories: Dict[str, Any] = {}
    for col in categorical_cols[:8]:  # limit to 8 categorical cols
        vc = df[col].value_counts().head(5)
        top_categories[col] = {
            "top_values": vc.to_dict(),
            "unique_count": int(df[col].nunique()),
        }
    result["top_categories"] = top_categories

    # --- Trend detection (date columns) ---
    trends: List[Dict] = []
    date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "month" in c.lower() or "year" in c.lower()]
    for date_col in date_cols[:2]:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df_sorted = df[[date_col] + numeric_df.columns.tolist()].dropna(subset=[date_col]).sort_values(date_col)
            if len(df_sorted) < 3:
                continue
            for num_col in numeric_df.columns[:4]:
                x = np.arange(len(df_sorted))
                y = df_sorted[num_col].fillna(0).values
                if len(x) > 1:
                    slope, intercept, r_value, p_value, _ = scipy_stats.linregress(x, y)
                    direction = "upward" if slope > 0 else "downward"
                    trends.append({
                        "date_column": date_col,
                        "value_column": num_col,
                        "trend_direction": direction,
                        "slope": round(float(slope), 6),
                        "r_squared": round(float(r_value ** 2), 4),
                        "p_value": round(float(p_value), 4),
                    })
        except Exception:
            continue
    result["trends"] = trends

    # --- High null columns ---
    null_rates = (df.isnull().sum() / len(df) * 100).round(2)
    high_null = {col: float(rate) for col, rate in null_rates.items() if rate > 20}
    result["high_null_columns"] = high_null

    return result
