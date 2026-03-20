"""
graph.py - LangGraph StateGraph definitions for the analysis and follow-up pipelines.

WHY two separate graphs:
  get_analysis_graph() - the main pipeline (profile → plan → analyse → chart →
                         reflect → [loop or report])
  get_followup_graph() - the lightweight Q&A pipeline (route → retrieve → answer)

Separating them keeps each graph small and easy to reason about. The API layer
calls the appropriate graph depending on whether the request is a new analysis
or a follow-up question.

WHY LangGraph over a hand-written loop:
  LangGraph provides built-in state checkpointing, conditional branching,
  and a clear visual graph that matches the architectural diagram in README.md.
  The conditional_edge after reflector is expressed as a Python function
  rather than if/else inside a node, keeping node logic pure.
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

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

load_dotenv()


# ---------------------------------------------------------------------------
# LLM Provider configuration
# ---------------------------------------------------------------------------

class LLMProvider:
    """
    Factory for selecting the LLM backend based on the LLM_PROVIDER env var.

    WHY a class with a classmethod: multiple modules (nodes.py, graph.py) need
    the same LLM instance. A classmethod on a shared class avoids duplicating
    the provider selection logic and makes it easy to mock in tests.

    Supported providers:
      ollama  – local Llama 3.2 via Ollama (default, free, private)
      openai  – OpenAI GPT-4o (higher quality, costs money)
    """

    _instance = None  # module-level singleton cache

    @classmethod
    def get_llm(cls):
        """
        Return a cached LLM instance, creating it on the first call.

        WHY cache: LLM client objects hold HTTP connection pools. Re-creating
        them per node call wastes resources and adds latency.
        """
        if cls._instance is not None:
            return cls._instance

        provider = os.getenv("LLM_PROVIDER", "ollama").lower()

        if provider == "openai":
            cls._instance = cls._build_openai()
        else:
            cls._instance = cls._build_ollama()

        return cls._instance

    @classmethod
    def _build_ollama(cls):
        """Build an Ollama-backed LLM (local, no API key needed)."""
        from langchain_ollama import ChatOllama
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.2,       # Low temperature for factual analysis
            num_predict=2048,      # Enough tokens for a full report section
        )

    @classmethod
    def _build_openai(cls):
        """Build an OpenAI-backed LLM (cloud, requires OPENAI_API_KEY)."""
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Either set it or use LLM_PROVIDER=ollama."
            )
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.2,
            max_tokens=4096,
        )

    @classmethod
    def reset(cls) -> None:
        """Clear the cached instance (useful for testing provider switching)."""
        cls._instance = None


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _should_reanlyze(state: AnalysisState) -> Literal["analyzer", "report_writer"]:
    """
    Decide whether the graph should loop back to analyzer or proceed to report_writer.

    Routing logic:
      - If the reflector approved the analysis (score >= threshold OR max iterations
        reached), continue to report_writer.
      - Otherwise, route back to analyzer for a deeper pass.

    WHY read `approved` from state instead of re-checking score:
      The reflector already applied the threshold and iteration limit when setting
      `approved`. Re-implementing that logic here would duplicate it and create
      a maintenance hazard.
    """
    reflection = state.get("reflection", {})
    if reflection and reflection.get("approved", False):
        return "report_writer"
    return "analyzer"


# ---------------------------------------------------------------------------
# Main analysis graph
# ---------------------------------------------------------------------------

def get_analysis_graph() -> StateGraph:
    """
    Build and compile the main data analysis StateGraph.

    Graph topology:
        data_profiler
            ↓
        planner
            ↓
        analyzer  ←──────────────┐
            ↓                    │ (if approved=False)
        chart_maker              │
            ↓                    │
        reflector ───────────────┘
            ↓ (if approved=True)
        report_writer
            ↓
           END

    WHY chart_maker runs before reflector: generating charts requires knowing
    which columns exist (from profiling), not the final report. Running charts
    early means the reflector can mention "a histogram was generated for revenue"
    in its suggestions, giving the report_writer richer context.

    Returns:
        A compiled CompiledStateGraph ready for .invoke() calls.
    """
    graph = StateGraph(AnalysisState)

    # Register nodes
    graph.add_node("data_profiler", data_profiler)
    graph.add_node("planner", planner)
    graph.add_node("analyzer", analyzer)
    graph.add_node("chart_maker", chart_maker)
    graph.add_node("reflector", reflector)
    graph.add_node("report_writer", report_writer)

    # Entry point
    graph.set_entry_point("data_profiler")

    # Linear edges
    graph.add_edge("data_profiler", "planner")
    graph.add_edge("planner", "analyzer")
    graph.add_edge("analyzer", "chart_maker")
    graph.add_edge("chart_maker", "reflector")

    # Conditional edge: reflector → analyzer (loop) or report_writer (done)
    graph.add_conditional_edges(
        "reflector",
        _should_reanlyze,
        {
            "analyzer": "analyzer",
            "report_writer": "report_writer",
        },
    )

    graph.add_edge("report_writer", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Follow-up Q&A graph
# ---------------------------------------------------------------------------

def get_followup_graph() -> StateGraph:
    """
    Build and compile the lightweight follow-up question-answering graph.

    Graph topology:
        question_router
            ↓
        context_retriever
            ↓
        answerer
            ↓
           END

    WHY not re-run the full analysis graph for follow-ups: the analysis results
    are already stored in DatasetContextMemory. Re-running profiling + planning
    + analysis for each follow-up would take 30-120 seconds. The context_retriever
    pulls only the relevant cached results in milliseconds.

    Returns:
        A compiled CompiledStateGraph ready for .invoke() calls.
    """
    graph = StateGraph(AnalysisState)

    graph.add_node("question_router", question_router)
    graph.add_node("context_retriever", context_retriever)
    graph.add_node("answerer", answerer)

    graph.set_entry_point("question_router")
    graph.add_edge("question_router", "context_retriever")
    graph.add_edge("context_retriever", "answerer")
    graph.add_edge("answerer", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Convenience runner functions
# ---------------------------------------------------------------------------

def run_analysis(
    dataset_path: str,
    session_id: str,
    follow_up_question: str | None = None,
) -> AnalysisState:
    """
    Run the main analysis pipeline and return the final state.

    Args:
        dataset_path:        Absolute path to the CSV file.
        session_id:          Unique session identifier.
        follow_up_question:  Optional initial question (stored for answerer).

    Returns:
        The final AnalysisState dict after all nodes have run.
    """
    initial_state: AnalysisState = {
        "dataset_path": dataset_path,
        "session_id": session_id,
        "dataset_summary": None,
        "analysis_plan": [],
        "profiling_results": {},
        "analysis_results": [],
        "charts": [],
        "reflection": None,
        "final_report": "",
        "follow_up_question": follow_up_question,
        "follow_up_answer": None,
        "conversation_history": [],
        "iteration_count": 0,
        "error": None,
    }

    graph = get_analysis_graph()
    final_state = graph.invoke(initial_state)
    return final_state


def run_followup(
    session_id: str,
    question: str,
    prior_state: AnalysisState,
) -> AnalysisState:
    """
    Run the follow-up Q&A pipeline given a prior analysis state.

    Args:
        session_id:   The session ID from the original analysis run.
        question:     The user's follow-up question.
        prior_state:  The AnalysisState returned by run_analysis().

    Returns:
        Updated state with follow_up_answer populated.
    """
    followup_state: AnalysisState = {
        **prior_state,
        "session_id": session_id,
        "follow_up_question": question,
        "follow_up_answer": None,
    }

    graph = get_followup_graph()
    final_state = graph.invoke(followup_state)
    return final_state
