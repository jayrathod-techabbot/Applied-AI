# src/market_intel/agents/retrieval_agent.py
"""
Retrieval Agent — performs hybrid Azure AI Search (BM25 + vector) to fetch
the top-k most relevant market intelligence chunks for a given query.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from langchain_openai import AzureOpenAIEmbeddings

from market_intel.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A single document chunk returned by the retrieval agent."""

    id: str
    title: str
    source: str
    published_date: str
    content: str
    search_score: float = 0.0


@dataclass
class RetrievalResult:
    """Container for the retrieval agent output."""

    query: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    total_retrieved: int = 0

    def to_context_string(self) -> str:
        """Format chunks as a numbered context block for LLM consumption."""
        if not self.chunks:
            return "No relevant context found."

        parts = []
        for i, chunk in enumerate(self.chunks, start=1):
            parts.append(
                f"[{i}] Source: {chunk.source} | Title: {chunk.title} | Date: {chunk.published_date}\n"
                f"{chunk.content}"
            )
        return "\n\n---\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "total_retrieved": self.total_retrieved,
            "chunks": [
                {
                    "id": c.id,
                    "title": c.title,
                    "source": c.source,
                    "published_date": c.published_date,
                    "content": c.content,
                    "search_score": c.search_score,
                }
                for c in self.chunks
            ],
        }


class RetrievalAgent:
    """
    Retrieval Agent that performs hybrid Azure AI Search.

    Combines BM25 full-text ranking with dense vector similarity for
    superior recall over either approach alone.
    """

    def __init__(self) -> None:
        self._search_client: SearchClient | None = None
        self._embedder: AzureOpenAIEmbeddings | None = None

    @property
    def search_client(self) -> SearchClient:
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index,
                credential=AzureKeyCredential(settings.azure_search_api_key),
            )
        return self._search_client

    @property
    def embedder(self) -> AzureOpenAIEmbeddings:
        if self._embedder is None:
            self._embedder = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_embedding_deployment,
            )
        return self._embedder

    def retrieve(self, query: str, top_k: int | None = None) -> RetrievalResult:
        """
        Synchronous hybrid retrieval.

        Args:
            query: Natural language query string.
            top_k: Number of chunks to return. Defaults to settings.top_k.

        Returns:
            RetrievalResult containing ranked document chunks.
        """
        k = top_k or settings.top_k
        logger.info("RetrievalAgent: hybrid search | query=%r | top_k=%d", query, k)

        query_vector = self.embedder.embed_query(query)

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=k,
            fields="content_vector",
        )

        raw_results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "content", "source", "title", "published_date"],
            top=k,
        )

        chunks: list[RetrievedChunk] = []
        for doc in raw_results:
            chunks.append(
                RetrievedChunk(
                    id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    source=doc.get("source", ""),
                    published_date=doc.get("published_date", ""),
                    content=doc.get("content", ""),
                    search_score=doc.get("@search.score", 0.0),
                )
            )

        logger.info("RetrievalAgent: retrieved %d chunks", len(chunks))
        return RetrievalResult(query=query, chunks=chunks, total_retrieved=len(chunks))

    async def aretrieve(self, query: str, top_k: int | None = None) -> RetrievalResult:
        """
        Async-compatible retrieval (wraps synchronous Azure SDK).

        The Azure AI Search SDK is synchronous; this method is provided for
        consistent async interface usage in the pipeline.
        """
        return self.retrieve(query, top_k=top_k)
