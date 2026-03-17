"""
Embeddings & Chunking - Solution Code

This is an enhanced solution with multiple chunking strategies and metadata support.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""

    id: str
    text: str
    start: int
    end: int
    length: int
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "length": self.length,
            "metadata": self.metadata or {},
        }


class EnhancedChunker:
    """Enhanced chunker with multiple strategies and metadata support."""

    def __init__(
        self, chunk_size: int = 500, overlap: int = 50, preserve_metadata: bool = True
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_metadata = preserve_metadata
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]

    def chunk(
        self,
        text: str,
        strategy: str = "recursive",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Chunk text using the specified strategy."""
        if strategy == "fixed":
            return self._fixed_chunk(text, metadata)
        elif strategy == "sentence":
            return self._sentence_chunk(text, metadata)
        elif strategy == "recursive":
            return self._recursive_chunk(text, metadata)
        elif strategy == "paragraph":
            return self._paragraph_chunk(text, metadata)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _create_chunk(
        self,
        chunk_id: int,
        text: str,
        start: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Chunk:
        """Create a Chunk object."""
        return Chunk(
            id=f"chunk_{chunk_id}",
            text=text.strip(),
            start=start,
            end=start + len(text),
            length=len(text.strip()),
            metadata=metadata or {},
        )

    def _fixed_chunk(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Fixed-size chunking with boundary detection."""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to break at natural boundaries
            if end < len(text):
                # Look for sentence or paragraph boundaries
                for sep in [". ", "! ", "? ", "\n\n", "\n"]:
                    boundary = text[start:end].rfind(sep)
                    if boundary != -1:
                        end = start + boundary + len(sep)
                        break

            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append(self._create_chunk(chunk_id, chunk_text, start, metadata))
                chunk_id += 1

            # Move with overlap
            new_start = end - self.overlap
            if new_start <= start:
                start = end
            else:
                start = new_start

        return chunks

    def _sentence_chunk(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Sentence-based chunking."""
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_text = ""
        start = 0
        chunk_id = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_text) + len(sentence) > self.chunk_size and current_text:
                chunks.append(
                    self._create_chunk(chunk_id, current_text, start, metadata)
                )
                chunk_id += 1

                # Handle overlap
                overlap_text = (
                    current_text[-self.overlap :]
                    if len(current_text) > self.overlap
                    else current_text
                )
                current_text = (
                    overlap_text + " " + sentence if overlap_text else sentence
                )
                start = (
                    start + len(current_text) - len(sentence) - len(overlap_text) - 1
                )
            else:
                current_text = (
                    current_text + " " + sentence if current_text else sentence
                )

        if current_text.strip():
            chunks.append(self._create_chunk(chunk_id, current_text, start, metadata))

        return chunks

    def _recursive_chunk(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Recursive chunking with multiple separators."""
        chunks = []

        def split_with_separator(text: str, sep_index: int, start: int) -> List[Chunk]:
            if sep_index >= len(self.separators):
                if text.strip():
                    return [
                        Chunk(
                            id=f"chunk_{len(chunks)}",
                            text=text.strip(),
                            start=start,
                            end=start + len(text),
                            length=len(text.strip()),
                            metadata=metadata or {},
                        )
                    ]
                return []

            separator = self.separators[sep_index]
            parts = text.split(separator)

            # If parts are small enough, create chunks
            if all(len(p) <= self.chunk_size for p in parts if p.strip()):
                return _create_chunks_from_parts(parts, separator, start, metadata)

            # Recursively split large parts
            result = []
            current = ""
            current_start = start

            for part in parts:
                test = current + separator + part if current else part

                if len(test) > self.chunk_size and current:
                    result.extend(
                        _create_chunks_from_parts(
                            [current], separator, current_start, metadata
                        )
                    )
                    current_start = current_start + len(current) - self.overlap
                    current = (
                        part[-self.overlap :] if len(part) > self.overlap else part
                    )
                else:
                    current = test

            if current.strip():
                result.extend(
                    _create_chunks_from_parts(
                        [current], separator, current_start, metadata
                    )
                )

            return result

        def _create_chunks_from_parts(
            parts: List[str],
            separator: str,
            start: int,
            metadata: Optional[Dict[str, Any]],
        ) -> List[Chunk]:
            chunks_list = []
            current_text = ""
            chunk_id = 0
            current_start = start

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                test = current_text + separator + part if current_text else part

                if len(test) > self.chunk_size and current_text:
                    chunks_list.append(
                        Chunk(
                            id=f"chunk_{chunk_id}",
                            text=current_text.strip(),
                            start=current_start,
                            end=current_start + len(current_text),
                            length=len(current_text.strip()),
                            metadata=metadata or {},
                        )
                    )
                    chunk_id += 1
                    overlap = (
                        current_text[-self.overlap :]
                        if len(current_text) > self.overlap
                        else ""
                    )
                    current_text = overlap + separator + part if overlap else part
                    current_start = current_start + len(current_text) - len(part)
                else:
                    current_text = test

            if current_text.strip():
                chunks_list.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        text=current_text.strip(),
                        start=current_start,
                        end=current_start + len(current_text),
                        length=len(current_text.strip()),
                        metadata=metadata or {},
                    )
                )

            return chunks_list

        return split_with_separator(text, 0, 0)

    def _paragraph_chunk(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Paragraph-based chunking."""
        # Split by double newlines
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        current_text = ""
        start = 0
        chunk_id = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Add newline if not first paragraph
            para_with_newline = "\n" + para if current_text else para

            if (
                len(current_text) + len(para_with_newline) > self.chunk_size
                and current_text
            ):
                chunks.append(
                    self._create_chunk(chunk_id, current_text, start, metadata)
                )
                chunk_id += 1

                # Handle overlap
                overlap = current_text[-self.overlap :]
                current_text = overlap + "\n" + para if overlap else para
                start = start + len(current_text) - len(para) - 1
            else:
                current_text = (
                    current_text + para_with_newline if current_text else para
                )

        if current_text.strip():
            chunks.append(self._create_chunk(chunk_id, current_text, start, metadata))

        return chunks


def main():
    """Demonstrate enhanced chunking."""

    print("=" * 60)
    print("Embeddings & Chunking - Enhanced Solution")
    print("=" * 60)

    sample_text = """
    Introduction to Machine Learning
    
    Machine learning is a subset of artificial intelligence that enables systems 
    to learn and improve from experience without being explicitly programmed.
    
    Types of Machine Learning
    
    There are three main types:
    1. Supervised Learning - Uses labeled data
    2. Unsupervised Learning - Finds patterns in unlabeled data
    3. Reinforcement Learning - Learns through rewards and penalties
    """

    chunker = EnhancedChunker(chunk_size=200, overlap=30)

    strategies = ["fixed", "sentence", "recursive", "paragraph"]

    for strategy in strategies:
        print(f"\n{strategy.upper()} Strategy")
        print("-" * 40)

        chunks = chunker.chunk(sample_text, strategy=strategy)

        print(f"Created {len(chunks)} chunks")

        for chunk in chunks[:2]:
            print(f"\n{chunk.id} ({chunk.length} chars):")
            print(f"  {chunk.text[:80]}...")


if __name__ == "__main__":
    main()
