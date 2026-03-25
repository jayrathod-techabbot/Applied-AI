import logging
from typing import List
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from ..config import settings

logger = logging.getLogger(__name__)


async def hybrid_search(
    query: str,
    query_embedding: List[float],
    top_k: int = 15,
) -> List[dict]:
    """Perform hybrid (vector + keyword) search against Azure AI Search."""

    credential = AzureKeyCredential(settings.azure_search_key)
    async with SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index,
        credential=credential,
    ) as client:
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )

        results = await client.search(
            search_text=query,
            vector_queries=[vector_query],
            top=top_k,
            select=["title", "author", "description", "genre", "chunk_text"],
        )

        documents: List[dict] = []
        async for result in results:
            documents.append({
                "title": result.get("title", ""),
                "author": result.get("author", ""),
                "description": result.get("description", ""),
                "genre": result.get("genre", ""),
                "chunk_text": result.get("chunk_text", ""),
                "search_score": result.get("@search.score", 0.0),
            })

        logger.info(f"Hybrid search returned {len(documents)} results for query: '{query}'")
        return documents
