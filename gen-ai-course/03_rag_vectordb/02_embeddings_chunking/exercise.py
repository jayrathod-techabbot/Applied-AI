"""
Embeddings & Chunking - Hands-on Exercise

This exercise covers different chunking strategies and embedding generation.

Estimated Time: 45 minutes
"""

import re
from typing import List, Dict, Any, Callable


# ============================================================================
# PART 1: Sample Document
# ============================================================================

SAMPLE_DOCUMENT = """
Machine Learning Fundamentals

Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems 
to learn and improve from experience without being explicitly programmed. 
It focuses on developing algorithms that can access data and use it to learn 
for themselves.

Types of Machine Learning

There are three main types of machine learning:

1. Supervised Learning
Supervised learning uses labeled datasets to train algorithms. The algorithm 
learns from example input-output pairs to predict outputs for new inputs. 
Common applications include classification and regression tasks.

2. Unsupervised Learning
Unsupervised learning finds patterns in unlabeled data. The system tries 
to learn the underlying structure without explicit labels. Common techniques 
include clustering and dimensionality reduction.

3. Reinforcement Learning
Reinforcement learning involves an agent learning to make decisions by 
interacting with an environment. The agent receives rewards or penalties 
based on its actions and learns to maximize rewards over time.

Key Concepts

- Features: Individual measurable properties of the data
- Labels: The target variable we want to predict
- Training: The process of learning from data
- Testing: Evaluating the model on unseen data
- Overfitting: When a model learns training data too well
- Underfitting: When a model is too simple to capture patterns

Machine learning is widely used in applications such as image recognition, 
natural language processing, recommendation systems, and autonomous vehicles.
"""


# ============================================================================
# PART 2: Chunking Strategies
# ============================================================================


class TextChunker:
    """Base class for text chunking strategies."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text into smaller pieces. Override in subclasses."""
        raise NotImplementedError


class FixedSizeChunker(TextChunker):
    """
    Split text into fixed-size chunks.
    Simple but may break semantic units.
    """

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Split text into fixed-size chunks."""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                for punct in [". ", "! ", "? ", "\n"]:
                    last_punct = text[start:end].rfind(punct)
                    if last_punct != -1:
                        end = start + last_punct + 1
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "id": f"chunk_{chunk_id}",
                        "text": chunk_text,
                        "start": start,
                        "end": end,
                        "length": len(chunk_text),
                    }
                )
                chunk_id += 1

            # Move start, accounting for overlap
            start = end - self.overlap if end < len(text) else end

        return chunks


class SentenceChunker(TextChunker):
    """
    Split text into sentence-based chunks.
    Preserves semantic meaning better.
    """

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Split text into sentence-based chunks."""
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        start = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + len(sentence) > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    {
                        "id": f"chunk_{chunk_id}",
                        "text": chunk_text,
                        "start": start,
                        "end": start + len(chunk_text),
                        "length": len(chunk_text),
                    }
                )

                # Start new chunk with overlap
                overlap_text = (
                    " ".join(current_chunk)[-self.overlap :]
                    if len(current_chunk) > 1
                    else ""
                )
                current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(" ".join(current_chunk))
                start = start + len(chunk_text) - len(overlap_text)
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1

        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "id": f"chunk_{chunk_id}",
                    "text": chunk_text,
                    "start": start,
                    "end": start + len(chunk_text),
                    "length": len(chunk_text),
                }
            )

        return chunks


class RecursiveChunker(TextChunker):
    """
    Recursive chunking that tries multiple separators.
    Balances semantic preservation with size control.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        super().__init__(chunk_size, overlap)
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Recursively split text using multiple separators."""
        return self._split_text(text, 0)

    def _split_text(self, text: str, separator_index: int) -> List[Dict[str, Any]]:
        """Recursively split text."""
        if separator_index >= len(self.separators):
            # Last resort: return the whole text
            return [
                {
                    "id": "chunk_0",
                    "text": text.strip(),
                    "start": 0,
                    "end": len(text),
                    "length": len(text.strip()),
                }
            ]

        separator = self.separators[separator_index]

        if separator == "":
            # Can't split further
            return [
                {
                    "id": "chunk_0",
                    "text": text.strip(),
                    "start": 0,
                    "end": len(text),
                    "length": len(text.strip()),
                }
            ]

        # Split by current separator
        parts = text.split(separator)

        # If parts are small enough, we're done
        if all(len(p) <= self.chunk_size for p in parts):
            return self._create_chunks(parts, separator)

        # Otherwise, try with next separator for larger parts
        large_parts = [p for p in parts if len(p) > self.chunk_size]

        if not large_parts:
            return self._create_chunks(parts, separator)

        # Recursively split large parts
        result = []
        current_chunk = []
        current_length = 0

        for part in parts:
            if len(part) > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    result.extend(self._create_chunks(current_chunk, separator))
                    current_chunk = []
                    current_length = 0

                # Split large part
                result.extend(self._split_text(part, separator_index + 1))
            else:
                if current_length + len(part) > self.chunk_size:
                    result.extend(self._create_chunks(current_chunk, separator))
                    current_chunk = [part]
                    current_length = len(part)
                else:
                    current_chunk.append(part)
                    current_length += len(part) + len(separator)

        if current_chunk:
            result.extend(self._create_chunks(current_chunk, separator))

        return result

    def _create_chunks(self, parts: List[str], separator: str) -> List[Dict[str, Any]]:
        """Create chunk objects from parts."""
        chunks = []
        chunk_id = 0
        start = 0

        current_text = ""
        for part in parts:
            if not part.strip():
                continue

            test_text = current_text + separator + part if current_text else part

            if len(test_text) > self.chunk_size and current_text:
                chunks.append(
                    {
                        "id": f"chunk_{chunk_id}",
                        "text": current_text.strip(),
                        "start": start,
                        "end": start + len(current_text),
                        "length": len(current_text.strip()),
                    }
                )
                chunk_id += 1

                # Start new chunk with overlap
                overlap_start = max(0, len(current_text) - self.overlap)
                current_text = current_text[overlap_start:] + separator + part
                start = start + overlap_start
            else:
                current_text = test_text

        if current_text.strip():
            chunks.append(
                {
                    "id": f"chunk_{chunk_id}",
                    "text": current_text.strip(),
                    "start": start,
                    "end": start + len(current_text),
                    "length": len(current_text.strip()),
                }
            )

        return chunks


# ============================================================================
# PART 3: Run Chunking Strategies
# ============================================================================


def main():
    """Demonstrate different chunking strategies."""

    print("=" * 60)
    print("Embeddings & Chunking - Hands-on Exercise")
    print("=" * 60)

    strategies = {
        "Fixed Size": FixedSizeChunker(chunk_size=300, overlap=30),
        "Sentence Based": SentenceChunker(chunk_size=300, overlap=30),
        "Recursive": RecursiveChunker(chunk_size=300, overlap=30),
    }

    for name, chunker in strategies.items():
        print(f"\n{name} Chunker")
        print("-" * 40)

        chunks = chunker.chunk(SAMPLE_DOCUMENT)

        print(f"Total chunks: {len(chunks)}")

        # Show first 3 chunks
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1} ({chunk['length']} chars):")
            print(f"  {chunk['text'][:100]}...")

    print("\n" + "=" * 60)
    print("Exercise: Try different chunk sizes and overlap values")
    print("=" * 60)


if __name__ == "__main__":
    main()


# ============================================================================
# EXERCISE TASKS
# ============================================================================

"""
EXERCISE TASKS:
1. Add overlap handling to maintain context between chunks
2. Implement semantic chunking using embeddings
3. Add metadata preservation (page numbers, section headers)
4. Create a function to evaluate chunk quality
5. Implement chunking for code files

BONUS: Use actual embeddings to create semantically coherent chunks
"""
