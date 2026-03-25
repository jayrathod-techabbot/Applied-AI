"""Azure AI Search wrapper for knowledge base retrieval."""

from __future__ import annotations

import logging
from typing import List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

logger = logging.getLogger(__name__)


class KnowledgeBaseSearch:
    """
    Thin wrapper around Azure AI Search for retrieving KB chunks.

    Parameters
    ----------
    endpoint:
        Azure AI Search service endpoint URL.
    api_key:
        Admin or query API key.
    index_name:
        Name of the search index to query.
    """

    def __init__(self, endpoint: str, api_key: str, index_name: str) -> None:
        self._client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Run a semantic / keyword search against the knowledge base index.

        Parameters
        ----------
        query:
            The search query (typically the customer's message or a
            reformulated version of it).
        top_k:
            Maximum number of documents to return.

        Returns
        -------
        List[str]
            A list of plain-text content chunks ordered by relevance score.
        """
        if not query.strip():
            return []

        try:
            results = self._client.search(
                search_text=query,
                top=top_k,
                query_type=QueryType.SIMPLE,
                include_total_count=False,
            )

            chunks: List[str] = []
            for doc in results:
                # Support both 'content' and 'chunk' field names
                content = doc.get("content") or doc.get("chunk") or ""
                if content:
                    chunks.append(str(content))

            logger.debug("KB search returned %d chunks for query: %.60s", len(chunks), query)
            return chunks

        except Exception as exc:
            logger.error("KB search failed: %s", exc, exc_info=True)
            return []
