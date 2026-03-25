"""
AzureDocSearchTool – CrewAI BaseTool wrapper around Azure AI Search.

Returns the top-k document chunks most relevant to the query, including
their source metadata so the Writer can build provenance citations.
"""

from __future__ import annotations

import json
from typing import Any, Type

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from crewai.tools import BaseTool
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import BaseModel, Field

from researcher.config import settings


class _AzureSearchInput(BaseModel):
    query: str = Field(description="Natural-language query to search for in the document index.")
    top_k: int = Field(default=5, description="Maximum number of document chunks to return.")


class AzureDocSearchTool(BaseTool):
    """Retrieves relevant document chunks from an Azure AI Search index."""

    name: str = "azure_doc_search"
    description: str = (
        "Search the Azure AI Search index for documents relevant to the given query. "
        "Returns up to top_k text chunks with their source file name and page number."
    )
    args_schema: Type[BaseModel] = _AzureSearchInput

    # Private attributes (not part of the Pydantic model exported to CrewAI).
    _search_client: SearchClient | None = None
    _embeddings: AzureOpenAIEmbeddings | None = None

    def _get_search_client(self) -> SearchClient:
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index,
                credential=AzureKeyCredential(settings.azure_search_key),
            )
        return self._search_client

    def _get_embeddings(self) -> AzureOpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                azure_deployment=settings.azure_embedding_deployment,
            )
        return self._embeddings

    def _run(self, query: str, top_k: int = 5) -> str:  # type: ignore[override]
        """Execute hybrid (keyword + vector) search and return formatted results."""
        client = self._get_search_client()

        # Build a vectorized query for semantic relevance.
        try:
            embeddings = self._get_embeddings()
            query_vector = embeddings.embed_query(query)
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="content_vector",
            )
            results = client.search(
                search_text=query,
                vector_queries=[vector_query],
                select=["id", "content", "source_file", "page_number"],
                top=top_k,
            )
        except Exception:
            # Fall back to keyword-only search if vector fields are unavailable.
            results = client.search(
                search_text=query,
                select=["id", "content", "source_file", "page_number"],
                top=top_k,
            )

        chunks: list[dict[str, Any]] = []
        for result in results:
            chunks.append(
                {
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "source_file": result.get("source_file", "unknown"),
                    "page_number": result.get("page_number", ""),
                }
            )

        if not chunks:
            return "No relevant documents found in the index for this query."

        return json.dumps(chunks, ensure_ascii=False, indent=2)
