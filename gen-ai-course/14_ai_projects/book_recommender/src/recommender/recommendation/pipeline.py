import json
import logging
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from ..retrieval.search import hybrid_search
from ..retrieval.reranker import rerank_results
from ..config import settings

logger = logging.getLogger(__name__)

RECOMMENDATION_PROMPT = """
Given the user's reading intent: "{query}"

Here are {n} candidate books retrieved by semantic similarity:
{candidates}

For each book, explain in 1-2 sentences WHY it matches the user's intent.
Focus on thematic alignment, narrative tone, and emotional resonance.
Return as a JSON list: [{{"title": ..., "author": ..., "reason": ..., "score": ...}}]
"""

async def recommend(query: str, top_k: int = 5) -> list[dict]:
    """Execute the end-to-end recommendation pipeline."""
    logger.info(f"Starting recommendation for query: '{query}'")
    
    # Step 1: Embed the query
    embedder = AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_embedding_deployment,
    )
    query_embedding = await embedder.aembed_query(query)

    # Step 2: Hybrid vector + keyword retrieval
    # Over-retrieve for re-ranking
    candidates = await hybrid_search(
        query=query,
        query_embedding=query_embedding,
        top_k=top_k * 3,
    )

    if not candidates:
        logger.warning(f"No search results returned for query '{query}'.")
        return []

    # Step 3: Re-rank candidates
    reranked = rerank_results(query=query, candidates=candidates, top_k=top_k)

    # Step 4: LLM generates explanations
    llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment,
        temperature=0.3,
    )

    candidate_text = "\n".join(
        f"{i+1}. {c['title']} by {c['author']} — {c['description'][:200]}..."
        for i, c in enumerate(reranked)
    )

    response = await llm.ainvoke(
        RECOMMENDATION_PROMPT.format(
            query=query, n=len(reranked), candidates=candidate_text
        )
    )

    try:
        # The LLM is asked for JSON, but sometimes it wraps it in markdown blocks
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        return json.loads(content)
    except Exception as exc:
        logger.error(f"Failed to parse LLM response: {exc}")
        # Fallback to returning reranked results without AI reasons if parsing fails
        return [
            {
                "title": c["title"],
                "author": c["author"],
                "reason": "Match based on thematic search.",
                "score": c.get("rerank_score", 1.0)
            }
            for c in reranked
        ]
