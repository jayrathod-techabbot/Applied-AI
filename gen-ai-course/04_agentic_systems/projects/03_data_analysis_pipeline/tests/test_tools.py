"""
test_tools.py - Unit tests for the data analysis tools.

Test strategy:
- Each tool is tested with a known CSV so results are deterministic.
- Dangerous code blocks are verified to return error strings without executing.
- File creation tests check disk presence so we don't just trust the return value.

WHY use tmp_path (pytest fixture) instead of tempfile.mkdtemp:
  tmp_path is automatically cleaned up after the test; mkdtemp requires manual
  cleanup and can leave artefacts on failure.
"""

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Ensure project root is on sys.path so 'agent' package resolves correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tools import (
    pandas_executor,
    chart_generator,
    stats_calculator,
    outlier_detector,
    pattern_finder,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_csv(tmp_path: Path) -> str:
    """Create a small CSV file with known values and return its path."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Carol", "Dave", "Eve"] * 20,
            "revenue": [100.0, 200.0, 150.0, 300.0, 250.0] * 20,
            "quantity": [10, 20, 15, 30, 25] * 20,
            "region": ["North", "South", "North", "East", "West"] * 20,
            "date": pd.date_range("2024-01-01", periods=100, freq="D").astype(str),
        }
    )
    csv_path = str(tmp_path / "sample.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def outlier_csv(tmp_path: Path) -> str:
    """Create a CSV with obvious outliers in the 'value' column."""
    import numpy as np

    normal_values = list(np.random.normal(loc=50, scale=5, size=95).round(2))
    outlier_values = [500.0, 600.0, -200.0, 700.0, 800.0]  # clear outliers
    all_values = normal_values + outlier_values

    df = pd.DataFrame({"value": all_values, "category": ["A"] * 100})
    csv_path = str(tmp_path / "outliers.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


# ---------------------------------------------------------------------------
# Test: pandas_executor
# ---------------------------------------------------------------------------

class TestPandasExecutor:
    """Tests for the sandboxed pandas code execution tool."""

    def test_basic_computation(self, sample_csv: str) -> None:
        """Running a simple expression returns a non-null result."""
        result = pandas_executor.invoke({
            "code": "df.shape",
            "dataset_path": sample_csv,
        })
        assert result["error"] is None, f"Unexpected error: {result['error']}"
        assert result["result"] is not None
        assert "100" in result["result"]  # 100 rows

    def test_aggregate_computation(self, sample_csv: str) -> None:
        """Mean computation on a numeric column returns a float string."""
        result = pandas_executor.invoke({
            "code": "df['revenue'].mean()",
            "dataset_path": sample_csv,
        })
        assert result["error"] is None
        # Mean of [100,200,150,300,250] repeated 20 times = 200.0
        assert "200.0" in result["result"]

    def test_groupby_computation(self, sample_csv: str) -> None:
        """Group-by aggregation executes without error."""
        code = "df.groupby('region')['revenue'].sum()"
        result = pandas_executor.invoke({"code": code, "dataset_path": sample_csv})
        assert result["error"] is None
        assert result["result"] is not None

    def test_print_statement_captured(self, sample_csv: str) -> None:
        """print() output is captured in the stdout field."""
        code = "print('hello from sandbox')"
        result = pandas_executor.invoke({"code": code, "dataset_path": sample_csv})
        assert result["error"] is None
        assert "hello from sandbox" in (result["stdout"] or result["result"] or "")

    def test_blocks_os_import(self, sample_csv: str) -> None:
        """Code containing 'import os' is blocked before execution."""
        code = "import os; os.system('echo pwned')"
        result = pandas_executor.invoke({"code": code, "dataset_path": sample_csv})
        assert result["error"] is not None
        assert "Blocked" in result["error"] or "blocked" in result["error"].lower()

    def test_blocks_subprocess(self, sample_csv: str) -> None:
        """Code containing 'import subprocess' is blocked."""
        code = "import subprocess; subprocess.run(['ls'])"
        result = pandas_executor.invoke({"code": code, "dataset_path": sample_csv})
        assert result["error"] is not None
        assert result["error"] is not None  # any error is acceptable

    def test_blocks_open(self, sample_csv: str) -> None:
        """Code containing open() is blocked."""
        code = "open('/etc/passwd', 'r').read()"
        result = pandas_executor.invoke({"code": code, "dataset_path": sample_csv})
        assert result["error"] is not None

    def test_blocks_eval(self, sample_csv: str) -> None:
        """Code containing eval() is blocked."""
        code = "eval('__import__(\"os\").system(\"echo pwned\")')"
        result = pandas_executor.invoke({"code": code, "dataset_path": sample_csv})
        assert result["error"] is not None

    def test_invalid_dataset_path(self, tmp_path: Path) -> None:
        """Non-existent dataset path returns an error."""
        result = pandas_executor.invoke({
            "code": "df.shape",
            "dataset_path": str(tmp_path / "nonexistent.csv"),
        })
        assert result["error"] is not None
        assert "not found" in result["error"].lower() or "no such" in result["error"].lower()

    def test_syntax_error_in_code(self, sample_csv: str) -> None:
        """Syntax errors in code are caught and returned as error strings."""
        result = pandas_executor.invoke({
            "code": "df[ (this is not valid python",
            "dataset_path": sample_csv,
        })
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Test: chart_generator
# ---------------------------------------------------------------------------

class TestChartGenerator:
    """Tests for chart generation and file creation."""

    def test_histogram_creates_file(self, sample_csv: str, tmp_path: Path) -> None:
        """Histogram chart is saved as a PNG file on disk."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "histogram",
            "x_col": "revenue",
            "y_col": "",
            "title": "Revenue Distribution",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is None, f"Chart error: {result['error']}"
        assert result["file_path"] is not None
        assert Path(result["file_path"]).exists(), "Chart file not found on disk."
        assert result["file_path"].endswith(".png")

    def test_bar_chart_creates_file(self, sample_csv: str, tmp_path: Path) -> None:
        """Bar chart for a categorical column is created successfully."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "bar",
            "x_col": "region",
            "y_col": "",
            "title": "Region Distribution",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is None
        assert Path(result["file_path"]).exists()

    def test_scatter_chart_creates_file(self, sample_csv: str, tmp_path: Path) -> None:
        """Scatter plot between two numeric columns is created successfully."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "scatter",
            "x_col": "revenue",
            "y_col": "quantity",
            "title": "Revenue vs Quantity",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is None
        assert Path(result["file_path"]).exists()

    def test_heatmap_creates_file(self, sample_csv: str, tmp_path: Path) -> None:
        """Correlation heatmap is generated from numeric columns."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "heatmap",
            "x_col": "",
            "y_col": "",
            "title": "Correlation Heatmap",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is None
        assert Path(result["file_path"]).exists()

    def test_box_chart_creates_file(self, sample_csv: str, tmp_path: Path) -> None:
        """Box plot for a numeric column is created successfully."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "box",
            "x_col": "revenue",
            "y_col": "",
            "title": "Revenue Box Plot",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is None
        assert Path(result["file_path"]).exists()

    def test_unknown_chart_type_returns_error(self, sample_csv: str, tmp_path: Path) -> None:
        """Unknown chart types return an error without crashing."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "pie_chart_that_doesnt_exist",
            "x_col": "region",
            "y_col": "",
            "title": "Test",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is not None
        assert result["file_path"] is None

    def test_missing_column_returns_error(self, sample_csv: str, tmp_path: Path) -> None:
        """Referencing a non-existent column returns an error."""
        result = chart_generator.invoke({
            "dataset_path": sample_csv,
            "chart_type": "histogram",
            "x_col": "nonexistent_column",
            "y_col": "",
            "title": "Test",
            "output_dir": str(tmp_path),
        })
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Test: stats_calculator
# ---------------------------------------------------------------------------

class TestStatsCalculator:
    """Tests for the descriptive statistics tool."""

    def test_returns_expected_keys(self, sample_csv: str) -> None:
        """Result dict contains all expected top-level keys."""
        result = stats_calculator.invoke({
            "dataset_path": sample_csv,
            "columns": ["revenue", "quantity"],
        })
        assert result.get("error") is None
        assert "descriptive" in result
        assert "correlation" in result
        assert "skewness" in result

    def test_descriptive_stats_values(self, sample_csv: str) -> None:
        """Descriptive stats for 'revenue' contain the correct mean."""
        result = stats_calculator.invoke({
            "dataset_path": sample_csv,
            "columns": ["revenue"],
        })
        desc = result.get("descriptive", {})
        assert "revenue" in desc
        revenue_stats = desc["revenue"]
        # Mean of [100,200,150,300,250] * 20 = 200.0
        assert abs(revenue_stats.get("mean", 0) - 200.0) < 0.01

    def test_correlation_present_for_two_numeric_cols(self, sample_csv: str) -> None:
        """Correlation matrix is present when two numeric columns are supplied."""
        result = stats_calculator.invoke({
            "dataset_path": sample_csv,
            "columns": ["revenue", "quantity"],
        })
        corr = result.get("correlation", {})
        assert "revenue" in corr
        assert "quantity" in corr["revenue"]

    def test_value_counts_for_categorical(self, sample_csv: str) -> None:
        """Value counts are computed for categorical columns."""
        result = stats_calculator.invoke({
            "dataset_path": sample_csv,
            "columns": ["region"],
        })
        vc = result.get("value_counts", {})
        assert "region" in vc
        assert len(vc["region"]) > 0

    def test_missing_column_returns_error(self, sample_csv: str) -> None:
        """Supplying a non-existent column returns an error."""
        result = stats_calculator.invoke({
            "dataset_path": sample_csv,
            "columns": ["does_not_exist"],
        })
        assert result.get("error") is not None


# ---------------------------------------------------------------------------
# Test: outlier_detector
# ---------------------------------------------------------------------------

class TestOutlierDetector:
    """Tests for the IQR-based outlier detection tool."""

    def test_finds_obvious_outliers(self, outlier_csv: str) -> None:
        """The detector identifies the artificially injected outliers."""
        result = outlier_detector.invoke({
            "dataset_path": outlier_csv,
            "column": "value",
        })
        assert result.get("error") is None
        assert result["outlier_count"] >= 5, (
            f"Expected at least 5 outliers, got {result['outlier_count']}"
        )
        assert result["severity"] in ("moderate", "severe")

    def test_no_outliers_in_normal_data(self, sample_csv: str) -> None:
        """Revenue column in sample data has zero or very few outliers."""
        result = outlier_detector.invoke({
            "dataset_path": sample_csv,
            "column": "revenue",
        })
        assert result.get("error") is None
        # Revenue values are [100,200,150,300,250] — no IQR outliers expected
        assert result["outlier_count"] == 0
        assert result["severity"] == "none"

    def test_returns_fence_values(self, sample_csv: str) -> None:
        """Lower and upper fence values are present and numerically valid."""
        result = outlier_detector.invoke({
            "dataset_path": sample_csv,
            "column": "revenue",
        })
        assert "lower_fence" in result
        assert "upper_fence" in result
        assert result["lower_fence"] < result["upper_fence"]

    def test_non_numeric_column_returns_error(self, sample_csv: str) -> None:
        """Applying outlier detection to a text column returns an error."""
        result = outlier_detector.invoke({
            "dataset_path": sample_csv,
            "column": "region",
        })
        assert result.get("error") is not None

    def test_missing_column_returns_error(self, sample_csv: str) -> None:
        """Referencing a missing column returns an error."""
        result = outlier_detector.invoke({
            "dataset_path": sample_csv,
            "column": "no_such_col",
        })
        assert result.get("error") is not None


# ---------------------------------------------------------------------------
# Test: pattern_finder
# ---------------------------------------------------------------------------

class TestPatternFinder:
    """Tests for the automatic pattern discovery tool."""

    def test_returns_expected_keys(self, sample_csv: str) -> None:
        """Result contains all expected top-level keys."""
        result = pattern_finder.invoke({"dataset_path": sample_csv})
        assert result.get("error") is None
        for key in ("correlations", "top_categories", "trends", "high_null_columns"):
            assert key in result, f"Missing key: {key}"

    def test_finds_correlations_between_numeric_cols(self, sample_csv: str) -> None:
        """Correlations list is non-empty when 2+ numeric columns exist."""
        result = pattern_finder.invoke({"dataset_path": sample_csv})
        corrs = result.get("correlations", [])
        assert len(corrs) > 0, "Expected at least one correlation pair."
        first = corrs[0]
        assert "col_a" in first and "col_b" in first and "correlation" in first

    def test_top_categories_for_categorical_col(self, sample_csv: str) -> None:
        """Top categories are computed for the 'region' column."""
        result = pattern_finder.invoke({"dataset_path": sample_csv})
        cats = result.get("top_categories", {})
        assert "region" in cats or "name" in cats

    def test_no_high_null_columns_in_clean_data(self, sample_csv: str) -> None:
        """Clean sample CSV should have no high-null columns."""
        result = pattern_finder.invoke({"dataset_path": sample_csv})
        assert result.get("high_null_columns") == {}
