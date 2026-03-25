# src/market_intel/tools/search_tool.py
"""
AzureSearchTool — LangChain BaseTool wrapper for Azure AI Search hybrid retrieval.
Combines full-text BM25 search with vector similarity for best recall.
"""
from __future__ import annotations

import json
from typing import Any, Optional, Type

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from langchain_core.tools import BaseTool
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import BaseModel, Field

from market_intel.config import settings


class SearchInput(BaseModel):
    query: str = Field(description="The search query to retrieve relevant market intelligence chunks.")


class AzureSearchTool(BaseTool):
    """Hybrid Azure AI Search tool that performs both keyword and vector retrieval."""

    name: str = "azure_market_search"
    description: str = (
        "Search the market intelligence knowledge base using hybrid retrieval "
        "(BM25 + vector similarity). Returns the top relevant chunks with source metadata. "
        "Use this tool to find competitor data, market signals, industry trends, and financial figures."
    )
    args_schema: Type[BaseModel] = SearchInput

    # Declare as Any to satisfy Pydantic v2 (non-serialisable Azure SDK objects)
    _search_client: Any = None
    _embedder: Any = None

    def _get_search_client(self) -> SearchClient:
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index,
                credential=AzureKeyCredential(settings.azure_search_api_key),
            )
        return self._search_client

    def _get_embedder(self) -> AzureOpenAIEmbeddings:
        if self._embedder is None:
            self._embedder = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_embedding_deployment,
            )
        return self._embedder

    def _run(self, query: str) -> str:
        """Synchronous hybrid search."""
        embedder = self._get_embedder()
        query_vector = embedder.embed_query(query)

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=settings.top_k,
            fields="content_vector",
        )

        client = self._get_search_client()
        results = client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "content", "source", "title", "published_date"],
            top=settings.top_k,
        )

        chunks = []
        for doc in results:
            chunks.append({
                "id": doc.get("id", ""),
                "title": doc.get("title", ""),
                "source": doc.get("source", ""),
                "published_date": doc.get("published_date", ""),
                "content": doc.get("content", ""),
            })

        if not chunks:
            return "No relevant documents found for the query."

        return json.dumps(chunks, ensure_ascii=False, indent=2)

    async def _arun(self, query: str) -> str:
        """Async hybrid search — reuses sync client (SDK is synchronous)."""
        return self._run(query)


def build_search_tool() -> AzureSearchTool:
    """Factory function to create a configured AzureSearchTool instance."""
    return AzureSearchTool()
