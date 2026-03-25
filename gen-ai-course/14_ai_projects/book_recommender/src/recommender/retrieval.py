"""
Retrieval module — embedding, hybrid search, and cross-encoder re-ranking.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    VectorizedQuery,
    QueryType,
)
from sentence_transformers import CrossEncoder

from .config import get_settings
from .models import BookMetadata, SearchResult

logger = logging.getLogger(__name__)

# Default cross-encoder model — lightweight and effective for passage ranking
_DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class BookRetrieval:
    """Embeds queries, runs hybrid search, and re-ranks results."""

    def __init__(self, cross_encoder_model: str = _DEFAULT_CROSS_ENCODER) -> None:
        self.settings = get_settings()

        self._openai_client = AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_key,
            api_version="2024-02-01",
        )

        self._search_client = SearchClient(
            endpoint=self.settings.azure_search_endpoint,
            index_name=self.settings.azure_search_index,
            credential=AzureKeyCredential(self.settings.azure_search_key),
        )

        logger.info("Loading cross-encoder model: %s", cross_encoder_model)
        self._cross_encoder = CrossEncoder(cross_encoder_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_query(self, query: str) -> List[float]:
        """Return the Ada-002 embedding vector for *query*."""
        try:
            response = self._openai_client.embeddings.create(
                model=self.settings.azure_embedding_deployment,
                input=query,
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.error("Query embedding failed: %s", exc)
            raise

    def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """Execute a hybrid (keyword + vector) search against Azure AI Search.

        Parameters
        ----------
        query_embedding: Vector produced by embed_query().
        query_text:      Original query string for BM25 keyword matching.
        filters:         Optional OData-style field filters, e.g.
                         ``{'genre': 'Fantasy', 'year': 2010}``.
        top_k:           Maximum number of results to return.
        """
        odata_filter = self._build_odata_filter(filters)

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )

        try:
            raw_results = self._search_client.search(
                search_text=query_text,
                vector_queries=[vector_query],
                query_type=QueryType.SIMPLE,
                filter=odata_filter,
                select=[
                    "id",
                    "title",
                    "author",
                    "genre",
                    "year",
                    "description",
                    "thumbnail",
                    "average_rating",
                    "num_pages",
                    "chunk_text",
                ],
                top=top_k,
            )
        except Exception as exc:
            logger.error("Azure AI Search request failed: %s", exc)
            raise

        search_results: List[SearchResult] = []
        for doc in raw_results:
            try:
                book = BookMetadata(
                    title=doc["title"],
                    author=doc["author"],
                    genre=doc["genre"],
                    year=int(doc["year"]),
                    description=doc["description"],
                    thumbnail=doc.get("thumbnail") or None,
                    average_rating=float(doc["average_rating"]) if doc.get("average_rating") is not None else None,
                    num_pages=int(doc["num_pages"]) if doc.get("num_pages") is not None else None,
                )
                result = SearchResult(
                    book=book,
                    score=float(doc.get("@search.score", 0.0)),
                    chunk_text=doc.get("chunk_text", ""),
                )
                search_results.append(result)
            except Exception as exc:
                logger.warning("Skipping malformed search document: %s", exc)

        return search_results

    def rerank(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Re-rank *results* using a cross-encoder model.

        The cross-encoder scores each (query, passage) pair and returns
        results sorted by descending relevance score.
        """
        if not results:
            return []

        pairs = [(query, r.chunk_text) for r in results]

        try:
            scores: List[float] = self._cross_encoder.predict(pairs).tolist()
        except Exception as exc:
            logger.error("Cross-encoder re-ranking failed: %s", exc)
            raise

        scored = sorted(
            zip(scores, results),
            key=lambda x: x[0],
            reverse=True,
        )

        reranked: List[SearchResult] = []
        for score, result in scored:
            reranked.append(
                SearchResult(
                    book=result.book,
                    score=float(score),
                    chunk_text=result.chunk_text,
                )
            )

        return reranked

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_odata_filter(filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Convert a plain dict of field/value pairs to an OData filter string."""
        if not filters:
            return None

        clauses: List[str] = []
        for field, value in filters.items():
            if isinstance(value, str):
                escaped = value.replace("'", "''")
                clauses.append(f"{field} eq '{escaped}'")
            elif isinstance(value, bool):
                clauses.append(f"{field} eq {str(value).lower()}")
            elif isinstance(value, (int, float)):
                clauses.append(f"{field} eq {value}")
            else:
                logger.warning("Unsupported filter type for field '%s': %s", field, type(value))

        return " and ".join(clauses) if clauses else None
