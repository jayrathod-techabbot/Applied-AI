from typing import List
import logging

logger = logging.getLogger(__name__)

def sentence_aware_chunking(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> List[str]:
    """Split *text* into overlapping word-level chunks.
    
    This is a simplified version of sentence-aware chunking.
    In a real-world scenario, you might want to use something like Spacy
    or NLTK to identify sentence boundaries.
    """
    if not text or not text.strip():
        return []

    words = text.split()
    step = max(chunk_size - overlap, 1)
    chunks: List[str] = []

    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks
