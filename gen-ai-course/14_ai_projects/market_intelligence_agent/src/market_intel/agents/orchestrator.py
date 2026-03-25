# src/market_intel/agents/orchestrator.py
"""
Orchestrator Agent — master coordinator using LangChain AgentExecutor.

Coordinates the full intelligence pipeline:
  1. Uses AzureSearchTool to retrieve relevant market intelligence chunks.
  2. Synthesizes a structured analysis grounded in the retrieved evidence.
  3. Persists the final report to Azure Blob Storage via BlobStorageTool.
  4. Validation Agent scores the output (handled in run_intelligence_pipeline).
"""
from __future__ import annotations

import logging
from datetime import date

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI

from market_intel.config import settings
from market_intel.tools.search_tool import build_search_tool
from market_intel.tools.storage_tool import build_storage_tool
from market_intel.agents.validation_agent import ValidationAgent

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a market intelligence orchestrator responsible for \
producing accurate, evidence-backed executive briefings.

Your workflow:
1. Call `azure_market_search` with a focused query to retrieve relevant market data.
2. Synthesize the retrieved chunks into a structured analysis — do NOT fabricate facts.
3. Call `azure_market_search` again with refined queries if you need additional evidence.
4. Once you have sufficient evidence, produce the final structured report:

## Executive Summary
2-3 sentences capturing the most critical insight.

## Key Market Signals
Bulleted list with [Source: ...] attribution for each signal.

## Competitive Landscape
Analysis of competitive dynamics visible in the evidence.

## Strategic Implications
Actionable takeaways for strategy, investment, or risk management.

## Evidence Gaps
Important questions the retrieved evidence could not fully answer.

5. Call `save_report_to_blob` with a JSON string containing your complete analysis.

Today's date: {date}
Query focus: {query}

IMPORTANT: Every factual claim must trace back to a retrieved chunk. \
If context is insufficient, say so explicitly rather than extrapolating.
"""


def build_orchestrator() -> AgentExecutor:
    """
    Construct and return a configured LangChain AgentExecutor
    that drives the full market intelligence pipeline.
    """
    llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        api_version="2024-02-01",
        temperature=0.2,
    )

    tools = [
        build_search_tool(),
        build_storage_tool(),
    ]

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )


class OrchestratorAgent:
    """
    High-level wrapper around the LangChain AgentExecutor orchestrator.

    Manages the full pipeline including post-hoc validation scoring.
    """

    def __init__(self) -> None:
        self._executor: AgentExecutor | None = None
        self._validator = ValidationAgent()

    @property
    def executor(self) -> AgentExecutor:
        if self._executor is None:
            self._executor = build_orchestrator()
        return self._executor

    async def run(self, query: str) -> dict:
        """
        Execute the full intelligence pipeline asynchronously.

        Args:
            query: The market intelligence question to investigate.

        Returns:
            dict with keys: query, analysis, confidence_score,
            confidence_label, sources_used, validation_details.
        """
        logger.info("OrchestratorAgent: starting pipeline | query=%r", query)

        result = await self.executor.ainvoke({
            "input": query,
            "date": str(date.today()),
            "query": query,
        })

        analysis: str = result["output"]

        # Collect text returned by tool calls (search results used as evidence)
        source_chunks: list[str] = []
        for action, observation in result.get("intermediate_steps", []):
            if isinstance(observation, str) and len(observation) > 50:
                source_chunks.append(observation)

        # Validation scoring
        validation = await self._validator.avalidate(
            claim=analysis,
            source_chunks=source_chunks,
        )

        logger.info(
            "OrchestratorAgent: pipeline complete | confidence=%.3f (%s)",
            validation.confidence_score,
            validation.confidence_label,
        )

        return {
            "query": query,
            "analysis": analysis,
            "confidence_score": validation.confidence_score,
            "confidence_label": validation.confidence_label,
            "sources_used": len(source_chunks),
            "validation_details": validation.to_dict(),
        }


async def run_intelligence_pipeline(query: str) -> dict:
    """
    Module-level convenience function for running the full pipeline.

    Args:
        query: The market intelligence question.

    Returns:
        Pipeline output dict (see OrchestratorAgent.run).
    """
    agent = OrchestratorAgent()
    return await agent.run(query)
