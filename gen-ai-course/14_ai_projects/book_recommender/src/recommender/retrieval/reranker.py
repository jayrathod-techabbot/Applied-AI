import logging
from typing import List
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

_DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_cross_encoder_instance = None

def _get_cross_encoder():
    global _cross_encoder_instance
    if _cross_encoder_instance is None:
        logger.info(f"Loading cross-encoder model: {_DEFAULT_CROSS_ENCODER}")
        _cross_encoder_instance = CrossEncoder(_DEFAULT_CROSS_ENCODER)
    return _cross_encoder_instance

def rerank_results(query: str, candidates: List[dict], top_k: int = 5) -> List[dict]:
    """Re-rank *candidates* using a cross-encoder model."""
    if not candidates:
        return []

    cross_encoder = _get_cross_encoder()
    
    # Use chunk_text for scoring (it's what was used for embeddings).
    # If not present, fallback to description (the full book description).
    pairs = [(query, c.get("chunk_text") or c["description"]) for c in candidates]

    try:
        scores: List[float] = cross_encoder.predict(pairs).tolist()
    except Exception as exc:
        logger.error(f"Cross-encoder re-ranking failed: {exc}")
        raise

    scored = sorted(
        zip(scores, candidates),
        key=lambda x: x[0],
        reverse=True,
    )

    reranked: List[dict] = []
    for score, result in scored[:top_k]:
        result["rerank_score"] = float(score)
        reranked.append(result)

    return reranked
