# src/market_intel/agents/validation.py
"""
Validation Agent — cross-checks reasoning output against retrieved source chunks.
Uses embedding cosine similarity to assign a confidence score (0.0 - 1.0).
"""
import numpy as np
from langchain_openai import AzureOpenAIEmbeddings
from market_intel.config import settings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


async def validate_and_score(claim: str, source_chunks: list[str]) -> float:
    """
    Compares the claim embedding against each source chunk embedding.
    Returns the average max-similarity score across all sentences in the claim.

    A score >= 0.75 means the claim is well-grounded in retrieved evidence.
    A score < 0.50 is a hallucination risk flag.
    """
    if not source_chunks:
        return 0.0

    embedder = AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_embedding_deployment,
    )

    # Split claim into sentences for granular scoring
    sentences = [s.strip() for s in claim.split(".") if len(s.strip()) > 20]
    if not sentences:
        return 0.0

    claim_embeddings = await embedder.aembed_documents(sentences)
    source_embeddings = await embedder.aembed_documents(source_chunks)

    scores = []
    for claim_emb in claim_embeddings:
        max_sim = max(
            _cosine_similarity(claim_emb, src_emb)
            for src_emb in source_embeddings
        )
        scores.append(max_sim)

    return round(float(np.mean(scores)), 3)
