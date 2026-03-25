# src/market_intel/pipelines/rag_chain.py
"""
RAGChain — wires together the Retrieval → Reasoning → Validation pipeline
without the overhead of a full AgentExecutor loop.

Use this class when you want a deterministic, non-agentic pipeline
(no tool-use loop) for maximum predictability and speed.
Use OrchestratorAgent when you need the agent to dynamically decide
how many retrieval rounds to perform.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from market_intel.agents.retrieval_agent import RetrievalAgent, RetrievalResult
from market_intel.agents.reasoning_agent import ReasoningAgent, ReasoningResult
from market_intel.agents.validation_agent import ValidationAgent, ValidationResult
from market_intel.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RAGChainOutput:
    """Full output from a single RAGChain execution."""

    query: str
    retrieval: RetrievalResult
    reasoning: ReasoningResult
    validation: ValidationResult

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "analysis": self.reasoning.analysis,
            "confidence_score": self.validation.confidence_score,
            "confidence_label": self.validation.confidence_label,
            "sources_used": self.retrieval.total_retrieved,
            "model_used": self.reasoning.model_used,
            "token_usage": {
                "prompt_tokens": self.reasoning.prompt_tokens,
                "completion_tokens": self.reasoning.completion_tokens,
            },
            "validation_details": self.validation.to_dict(),
        }


class RAGChain:
    """
    Deterministic RAG pipeline: Retrieval → Reasoning → Validation.

    This pipeline executes each stage in a fixed sequence without
    agent-loop overhead, making it faster and more predictable than
    the OrchestratorAgent for straightforward Q&A workloads.

    Args:
        top_k: Number of chunks to retrieve. Defaults to settings.top_k.
        reasoning_temperature: Temperature for the Reasoning Agent LLM call.
    """

    def __init__(
        self,
        top_k: int | None = None,
        reasoning_temperature: float = 0.2,
    ) -> None:
        self.top_k = top_k or settings.top_k
        self._retrieval_agent = RetrievalAgent()
        self._reasoning_agent = ReasoningAgent(temperature=reasoning_temperature)
        self._validation_agent = ValidationAgent()

    # ------------------------------------------------------------------
    # Synchronous interface
    # ------------------------------------------------------------------

    def run(self, query: str) -> RAGChainOutput:
        """
        Execute the full pipeline synchronously.

        Args:
            query: The market intelligence question.

        Returns:
            RAGChainOutput with analysis, confidence score, and diagnostics.
        """
        logger.info("RAGChain.run: starting | query=%r | top_k=%d", query, self.top_k)

        # Stage 1 — Retrieval
        retrieval_result = self._retrieval_agent.retrieve(query, top_k=self.top_k)
        context = retrieval_result.to_context_string()
        logger.info("RAGChain.run: retrieved %d chunks", retrieval_result.total_retrieved)

        # Stage 2 — Reasoning
        reasoning_result = self._reasoning_agent.reason(query=query, context=context)
        logger.info("RAGChain.run: reasoning complete")

        # Stage 3 — Validation
        source_texts = [chunk.content for chunk in retrieval_result.chunks]
        validation_result = self._validation_agent.validate(
            claim=reasoning_result.analysis,
            source_chunks=source_texts,
        )
        logger.info(
            "RAGChain.run: validation complete | confidence=%.3f (%s)",
            validation_result.confidence_score,
            validation_result.confidence_label,
        )

        return RAGChainOutput(
            query=query,
            retrieval=retrieval_result,
            reasoning=reasoning_result,
            validation=validation_result,
        )

    # ------------------------------------------------------------------
    # Async interface
    # ------------------------------------------------------------------

    async def arun(self, query: str) -> RAGChainOutput:
        """
        Execute the full pipeline asynchronously.

        Args:
            query: The market intelligence question.

        Returns:
            RAGChainOutput with analysis, confidence score, and diagnostics.
        """
        logger.info("RAGChain.arun: starting | query=%r | top_k=%d", query, self.top_k)

        # Stage 1 — Retrieval (async wrapper over sync Azure SDK)
        retrieval_result = await self._retrieval_agent.aretrieve(query, top_k=self.top_k)
        context = retrieval_result.to_context_string()
        logger.info("RAGChain.arun: retrieved %d chunks", retrieval_result.total_retrieved)

        # Stage 2 — Reasoning (async LLM call)
        reasoning_result = await self._reasoning_agent.areason(query=query, context=context)
        logger.info("RAGChain.arun: reasoning complete")

        # Stage 3 — Validation (async embeddings)
        source_texts = [chunk.content for chunk in retrieval_result.chunks]
        validation_result = await self._validation_agent.avalidate(
            claim=reasoning_result.analysis,
            source_chunks=source_texts,
        )
        logger.info(
            "RAGChain.arun: validation complete | confidence=%.3f (%s)",
            validation_result.confidence_score,
            validation_result.confidence_label,
        )

        return RAGChainOutput(
            query=query,
            retrieval=retrieval_result,
            reasoning=reasoning_result,
            validation=validation_result,
        )
