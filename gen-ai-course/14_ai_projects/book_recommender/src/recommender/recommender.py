"""
BookRecommender — orchestrates the full recommendation pipeline.

Pipeline
--------
1. Extract structured intent from the user query via GPT-4o.
2. Embed the (refined) query with Ada-002.
3. Run hybrid search + metadata filtering on Azure AI Search.
4. Re-rank results with a cross-encoder.
5. Generate a natural-language explanation with GPT-4o.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

from .config import get_settings
from .models import (
    BookMetadata,
    RecommendationRequest,
    RecommendationResponse,
    SearchResult,
)
from .retrieval import BookRetrieval

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_INTENT_SYSTEM_PROMPT = """\
You are a librarian assistant. Given a user's book-search query, extract:
1. A refined semantic search query (improve clarity, expand synonyms).
2. Any explicit metadata filters the user mentioned (genre, year, author).

Respond ONLY with a valid JSON object in this exact schema:
{
  "refined_query": "<string>",
  "filters": {
    "genre": "<string or null>",
    "year": <integer or null>,
    "author": "<string or null>"
  }
}
Do not include any text outside the JSON object.
"""

_EXPLANATION_SYSTEM_PROMPT = """\
You are a knowledgeable librarian. Given a user's query and a list of book
recommendations, write a concise, engaging explanation (3-5 sentences) of why
these books were selected and what makes them a good match.
"""


class BookRecommender:
    """End-to-end LLM-powered book recommendation orchestrator."""

    def __init__(self) -> None:
        self.settings = get_settings()

        self._openai_client = AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_key,
            api_version="2024-02-01",
        )

        self._retrieval = BookRetrieval()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def recommend(
        self, request: RecommendationRequest
    ) -> RecommendationResponse:
        """Run the full recommendation pipeline asynchronously.

        Parameters
        ----------
        request: RecommendationRequest with query, optional filters, and top_k.

        Returns
        -------
        RecommendationResponse containing ranked recommendations and explanation.
        """
        logger.info("Starting recommendation pipeline for query: '%s'", request.query)

        # Step 1 — extract intent (refined query + structured filters)
        refined_query, extracted_filters = await self._extract_intent(request.query)

        # Merge caller-supplied filters with LLM-extracted filters
        # (caller filters take precedence)
        merged_filters = {**_drop_nulls(extracted_filters), **(request.filters or {})}
        logger.debug("Merged filters: %s", merged_filters)

        # Step 2 — embed the refined query
        query_embedding = await asyncio.to_thread(
            self._retrieval.embed_query, refined_query
        )

        # Step 3 — hybrid search
        top_k_search = min(self.settings.top_k, request.top_k * 3)  # over-fetch for reranking
        raw_results: List[SearchResult] = await asyncio.to_thread(
            self._retrieval.hybrid_search,
            query_embedding,
            refined_query,
            merged_filters or None,
            top_k_search,
        )

        if not raw_results:
            logger.warning("No search results returned for query '%s'.", request.query)
            return RecommendationResponse(
                query=request.query,
                recommendations=[],
                explanation="No matching books were found for your query. Try broadening your search.",
            )

        # Step 4 — re-rank with cross-encoder
        reranked: List[SearchResult] = await asyncio.to_thread(
            self._retrieval.rerank, refined_query, raw_results
        )

        # Trim to the requested top_k
        final_results = reranked[: request.top_k]

        # Step 5 — generate LLM explanation
        explanation = await self._generate_explanation(request.query, final_results)

        return RecommendationResponse(
            query=request.query,
            recommendations=final_results,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _extract_intent(
        self, query: str
    ) -> tuple[str, Dict[str, Any]]:
        """Use GPT-4o to refine the query and extract metadata filters."""

        def _call_llm() -> tuple[str, Dict[str, Any]]:
            response = self._openai_client.chat.completions.create(
                model=self.settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                max_tokens=256,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.error("Intent extraction returned invalid JSON: %s", exc)
                return query, {}

            refined = parsed.get("refined_query", query)
            filters = parsed.get("filters", {})
            return refined, filters

        try:
            refined_query, filters = await asyncio.to_thread(_call_llm)
        except Exception as exc:
            logger.error("Intent extraction LLM call failed: %s", exc)
            refined_query, filters = query, {}

        return refined_query, filters

    async def _generate_explanation(
        self, original_query: str, results: List[SearchResult]
    ) -> str:
        """Ask GPT-4o to explain why these books were recommended."""

        book_list = "\n".join(
            f"- \"{r.book.title}\" by {r.book.author} ({r.book.year}) [{r.book.genre}]"
            + (f" — rated {r.book.average_rating}/5" if r.book.average_rating else "")
            for r in results
        )
        user_message = (
            f"User query: {original_query}\n\n"
            f"Recommended books:\n{book_list}"
        )

        def _call_llm() -> str:
            response = self._openai_client.chat.completions.create(
                model=self.settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": _EXPLANATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=512,
            )
            return response.choices[0].message.content or ""

        try:
            explanation = await asyncio.to_thread(_call_llm)
        except Exception as exc:
            logger.error("Explanation generation failed: %s", exc)
            explanation = "Here are the most relevant books based on your query."

        return explanation.strip()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _drop_nulls(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *d* with None / null values removed."""
    return {k: v for k, v in d.items() if v is not None}
