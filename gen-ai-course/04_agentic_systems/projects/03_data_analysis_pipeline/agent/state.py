"""
state.py - Defines the shared state schema for the LangGraph analysis pipeline.

WHY TypedDict: LangGraph requires state to be a TypedDict so the graph runtime
can merge partial state updates from each node without replacing the whole dict.
Each node returns only the keys it modified; the runtime handles merging.

WHY dataclasses for sub-objects: DatasetSummary, AnalysisResult, etc. are
plain data containers that need default factories and easy dict conversion.
They are serialized to Dict before storing in AnalysisState because TypedDict
values must be JSON-serializable for checkpointing.
"""

from typing import TypedDict, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage
from dataclasses import dataclass, field, asdict


@dataclass
class DatasetSummary:
    """
    Snapshot of a loaded CSV dataset used throughout the pipeline.

    WHY capture at profiling time: later nodes (planner, reflector) need shape/dtype
    info without re-reading the file, so we capture it once and pass it forward.
    """

    shape: tuple
    columns: List[str]
    dtypes: Dict[str, str]         # column name → pandas dtype string
    sample_rows: List[Dict]        # first 5 rows as list-of-dicts for LLM context
    null_counts: Dict[str, int]    # column name → count of NaN values
    unique_counts: Dict[str, int]  # column name → count of unique values

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict suitable for JSON / LangGraph state storage."""
        return asdict(self)


@dataclass
class AnalysisResult:
    """
    Output of a single analysis step executed by the analyzer node.

    WHY store both findings (human-readable) and data (machine-readable):
    findings feed the report writer; data feeds the reflector's quality check.
    """

    step: str                    # description of what was analysed
    findings: str                # natural-language summary of what was found
    data: Dict[str, Any]         # raw computed values (stats, counts, etc.)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChartOutput:
    """
    Metadata about a chart image produced by the chart_maker node.

    WHY store file_path separately: the Streamlit UI and API routes need to
    locate chart files on disk without re-running the pipeline.
    """

    title: str
    chart_type: str   # e.g. "histogram", "bar", "scatter", "heatmap"
    file_path: str    # absolute path to the saved PNG
    description: str  # one-line caption used in the markdown report

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReflectionOutput:
    """
    DataCritic verdict on the current analysis depth.

    WHY float score: a 0–10 scale gives the LLM room to express nuance; integer
    thresholds (>= 7 = approved) are applied after parsing.

    WHY approved flag: the conditional edge in graph.py reads this single boolean
    rather than re-parsing the score, keeping edge logic simple and testable.
    """

    quality_score: float          # 0-10, LLM-assigned quality rating
    shallow_areas: List[str]      # aspects the critic found under-explored
    suggestions: List[str]        # concrete suggestions for deeper analysis
    approved: bool                # True if score >= threshold OR max iterations reached

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnalysisState(TypedDict, total=False):
    """
    Shared mutable state passed between every node in the LangGraph pipeline.

    WHY total=False: makes all keys optional so nodes only need to return the
    subset of keys they actually modify. LangGraph merges updates via reducer.

    Key groupings
    -------------
    Input:        dataset_path, follow_up_question, session_id
    Intermediate: dataset_summary, analysis_plan, profiling_results,
                  analysis_results, charts, reflection
    Output:       final_report, follow_up_answer
    Control:      iteration_count, error
    Memory:       conversation_history
    """

    # --- Input ---
    dataset_path: str                          # path to the uploaded CSV file
    session_id: str                            # UUID identifying this analysis session

    # --- Profiling ---
    dataset_summary: Optional[Dict[str, Any]]  # DatasetSummary.to_dict() output

    # --- Planning ---
    analysis_plan: List[str]                   # ordered list of analysis step descriptions

    # --- Analysis ---
    profiling_results: Dict[str, Any]          # raw stats from data_profiler
    analysis_results: List[Dict[str, Any]]     # list of AnalysisResult.to_dict()

    # --- Visualisation ---
    charts: List[Dict[str, Any]]               # list of ChartOutput.to_dict()

    # --- Reflection ---
    reflection: Optional[Dict[str, Any]]       # ReflectionOutput.to_dict()
    iteration_count: int                       # how many analyzer→reflector loops ran

    # --- Report ---
    final_report: str                          # full markdown report text

    # --- Follow-up Q&A ---
    follow_up_question: Optional[str]          # user's follow-up question text
    follow_up_answer: Optional[str]            # agent's answer to follow-up

    # --- Memory ---
    conversation_history: List[BaseMessage]    # short-term message buffer

    # --- Error handling ---
    error: Optional[str]                       # last error message, if any
