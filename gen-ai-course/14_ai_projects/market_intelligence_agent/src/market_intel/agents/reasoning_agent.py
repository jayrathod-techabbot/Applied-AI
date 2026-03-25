# src/market_intel/agents/reasoning_agent.py
"""
Reasoning Agent — uses GPT-4o to synthesize a structured market intelligence
analysis grounded in the retrieved context chunks.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

from market_intel.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a senior market intelligence analyst with expertise in \
competitive strategy, industry dynamics, and financial analysis.

Your task is to synthesize the retrieved market intelligence context into a \
structured, evidence-backed executive briefing.

STRICT RULES:
- Every claim must be grounded in the provided context snippets.
- If the context is insufficient to make a claim, explicitly state the limitation.
- Do NOT fabricate statistics, company names, dates, or financial figures.
- Always attribute key facts to their source (use the [Source: ...] notation).

OUTPUT FORMAT:
## Executive Summary
2-3 sentences capturing the most important insight.

## Key Market Signals
- Bulleted list of discrete signals extracted from the context, each with [Source: ...]

## Competitive Landscape
Analysis of competitive dynamics visible in the retrieved data.

## Strategic Implications
What this means for strategy, investment, or risk management.

## Evidence Gaps
Any important questions the retrieved context could not answer.
"""

HUMAN_TEMPLATE = """Query: {query}

Retrieved Context:
{context}

Please produce the structured market intelligence analysis."""


@dataclass
class ReasoningResult:
    """Output produced by the Reasoning Agent."""

    query: str
    analysis: str
    model_used: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "analysis": self.analysis,
            "model_used": self.model_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }


class ReasoningAgent:
    """
    Reasoning Agent that calls GPT-4o to synthesize analysis
    from retrieved context chunks.
    """

    def __init__(self, temperature: float = 0.2) -> None:
        self._llm: AzureChatOpenAI | None = None
        self.temperature = temperature

    @property
    def llm(self) -> AzureChatOpenAI:
        if self._llm is None:
            self._llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_deployment,
                api_version="2024-02-01",
                temperature=self.temperature,
            )
        return self._llm

    def reason(self, query: str, context: str) -> ReasoningResult:
        """
        Synchronous reasoning call.

        Args:
            query: The original user query.
            context: Formatted context string from the RetrievalAgent.

        Returns:
            ReasoningResult with structured analysis text.
        """
        logger.info("ReasoningAgent: synthesizing analysis for query=%r", query)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_TEMPLATE.format(query=query, context=context)),
        ]

        response = self.llm.invoke(messages)
        analysis = response.content

        usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        logger.info(
            "ReasoningAgent: analysis complete | prompt_tokens=%d | completion_tokens=%d",
            prompt_tokens,
            completion_tokens,
        )

        return ReasoningResult(
            query=query,
            analysis=analysis,
            model_used=settings.azure_openai_deployment,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    async def areason(self, query: str, context: str) -> ReasoningResult:
        """
        Async reasoning call using LangChain's async invoke.

        Args:
            query: The original user query.
            context: Formatted context string from the RetrievalAgent.

        Returns:
            ReasoningResult with structured analysis text.
        """
        logger.info("ReasoningAgent (async): synthesizing analysis for query=%r", query)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_TEMPLATE.format(query=query, context=context)),
        ]

        response = await self.llm.ainvoke(messages)
        analysis = response.content

        usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        return ReasoningResult(
            query=query,
            analysis=analysis,
            model_used=settings.azure_openai_deployment,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
