# src/market_intel/agents/validation_agent.py
"""
Validation Agent — cross-checks the reasoning output against retrieved source
chunks using embedding cosine similarity to produce a confidence score (0.0-1.0).

Score interpretation:
  >= 0.75  Well-grounded — claims are strongly supported by retrieved evidence.
  0.50-0.74  Partially grounded — some claims may extrapolate beyond evidence.
  < 0.50   Low confidence — significant hallucination risk; review recommended.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from langchain_openai import AzureOpenAIEmbeddings

from market_intel.config import settings

logger = logging.getLogger(__name__)

# Thresholds for human-readable confidence labels
_HIGH_CONFIDENCE = 0.75
_MEDIUM_CONFIDENCE = 0.50


@dataclass
class ValidationResult:
    """Output produced by the Validation Agent."""

    confidence_score: float
    confidence_label: str
    sentences_evaluated: int
    sources_compared: int
    sentence_scores: list[float]

    def to_dict(self) -> dict:
        return {
            "confidence_score": self.confidence_score,
            "confidence_label": self.confidence_label,
            "sentences_evaluated": self.sentences_evaluated,
            "sources_compared": self.sources_compared,
            "sentence_scores": self.sentence_scores,
        }


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    va, vb = np.array(a), np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-10))


def _confidence_label(score: float) -> str:
    if score >= _HIGH_CONFIDENCE:
        return "HIGH"
    if score >= _MEDIUM_CONFIDENCE:
        return "MEDIUM"
    return "LOW"


class ValidationAgent:
    """
    Validation Agent that measures how well the reasoning output
    is grounded in the retrieved source chunks.

    Algorithm:
    1. Split the claim into sentences (min 20 chars to skip noise).
    2. Embed each sentence and each source chunk.
    3. For each sentence, find the maximum cosine similarity across all source chunks.
    4. Return the mean of per-sentence max-similarities as the confidence score.
    """

    def __init__(self) -> None:
        self._embedder: AzureOpenAIEmbeddings | None = None

    @property
    def embedder(self) -> AzureOpenAIEmbeddings:
        if self._embedder is None:
            self._embedder = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_embedding_deployment,
            )
        return self._embedder

    def validate(self, claim: str, source_chunks: list[str]) -> ValidationResult:
        """
        Synchronous confidence scoring.

        Args:
            claim: The full analysis text produced by the Reasoning Agent.
            source_chunks: List of raw text strings from the Retrieval Agent.

        Returns:
            ValidationResult with confidence score and diagnostics.
        """
        logger.info(
            "ValidationAgent: scoring claim against %d source chunks", len(source_chunks)
        )

        if not source_chunks:
            logger.warning("ValidationAgent: no source chunks provided — returning 0.0")
            return ValidationResult(
                confidence_score=0.0,
                confidence_label="LOW",
                sentences_evaluated=0,
                sources_compared=0,
                sentence_scores=[],
            )

        sentences = [s.strip() for s in claim.split(".") if len(s.strip()) > 20]
        if not sentences:
            return ValidationResult(
                confidence_score=0.0,
                confidence_label="LOW",
                sentences_evaluated=0,
                sources_compared=len(source_chunks),
                sentence_scores=[],
            )

        claim_embeddings = self.embedder.embed_documents(sentences)
        source_embeddings = self.embedder.embed_documents(source_chunks)

        sentence_scores: list[float] = []
        for claim_emb in claim_embeddings:
            max_sim = max(
                _cosine_similarity(claim_emb, src_emb) for src_emb in source_embeddings
            )
            sentence_scores.append(round(max_sim, 4))

        confidence_score = round(float(np.mean(sentence_scores)), 3)
        label = _confidence_label(confidence_score)

        logger.info(
            "ValidationAgent: confidence_score=%.3f (%s) | sentences=%d",
            confidence_score,
            label,
            len(sentences),
        )

        return ValidationResult(
            confidence_score=confidence_score,
            confidence_label=label,
            sentences_evaluated=len(sentences),
            sources_compared=len(source_chunks),
            sentence_scores=sentence_scores,
        )

    async def avalidate(self, claim: str, source_chunks: list[str]) -> ValidationResult:
        """
        Async confidence scoring.

        Args:
            claim: The full analysis text produced by the Reasoning Agent.
            source_chunks: List of raw text strings from the Retrieval Agent.

        Returns:
            ValidationResult with confidence score and diagnostics.
        """
        logger.info(
            "ValidationAgent (async): scoring claim against %d source chunks", len(source_chunks)
        )

        if not source_chunks:
            return ValidationResult(
                confidence_score=0.0,
                confidence_label="LOW",
                sentences_evaluated=0,
                sources_compared=0,
                sentence_scores=[],
            )

        sentences = [s.strip() for s in claim.split(".") if len(s.strip()) > 20]
        if not sentences:
            return ValidationResult(
                confidence_score=0.0,
                confidence_label="LOW",
                sentences_evaluated=0,
                sources_compared=len(source_chunks),
                sentence_scores=[],
            )

        claim_embeddings = await self.embedder.aembed_documents(sentences)
        source_embeddings = await self.embedder.aembed_documents(source_chunks)

        sentence_scores: list[float] = []
        for claim_emb in claim_embeddings:
            max_sim = max(
                _cosine_similarity(claim_emb, src_emb) for src_emb in source_embeddings
            )
            sentence_scores.append(round(max_sim, 4))

        confidence_score = round(float(np.mean(sentence_scores)), 3)
        label = _confidence_label(confidence_score)

        return ValidationResult(
            confidence_score=confidence_score,
            confidence_label=label,
            sentences_evaluated=len(sentences),
            sources_compared=len(source_chunks),
            sentence_scores=sentence_scores,
        )
