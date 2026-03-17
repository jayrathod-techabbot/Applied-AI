"""
RAG Overview - Solution Code

This is the solution for the RAG Overview exercise, demonstrating a more
complete implementation with actual OpenAI embeddings.
"""

import os
import math
from typing import List, Tuple, Dict, Any, Optional
import hashlib
import random

# Try to import OpenAI - if not available, use fallback
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Note: OpenAI not installed. Using simulated embeddings.")


# ============================================================================
# Enhanced Document Class
# ============================================================================


class Document:
    """Enhanced document class with metadata support."""

    def __init__(
        self, id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.content = content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Document(id={self.id}, metadata={self.metadata})"

    def to_dict(self) -> Dict:
        return {"id": self.id, "content": self.content, "metadata": self.metadata}


# ============================================================================
# Embedding Implementations
# ============================================================================


class OpenAIEmbedding:
    """OpenAI embedding implementation."""

    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


class FallbackEmbedding:
    """Fallback embedding using hash-based vectors."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to a vector representation."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)

        random.seed(seed)
        vector = [random.uniform(-1, 1) for _ in range(self.dimension)]

        # Normalize
        magnitude = math.sqrt(sum(x**2 for x in vector))
        return [x / magnitude for x in vector] if magnitude > 0 else vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._text_to_vector(text)


def get_embedding_model():
    """Factory function to get the appropriate embedding model."""
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        print("Using OpenAI embeddings")
        return OpenAIEmbedding()
    else:
        print("Using fallback embeddings (for demonstration)")
        return FallbackEmbedding()


# ============================================================================
# Vector Store with Enhanced Features
# ============================================================================


class EnhancedVectorStore:
    """Enhanced vector store with multiple similarity metrics."""

    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model or get_embedding_model()
        self.documents: List[Document] = []
        self.vectors: List[List[float]] = []

    def add_documents(self, docs: List[Dict]):
        """Add documents to the store."""
        documents = [
            Document(d["id"], d["content"], d.get("metadata", {})) for d in docs
        ]
        texts = [doc.content for doc in documents]
        vectors = self.embedding_model.embed_documents(texts)

        self.documents.extend(documents)
        self.vectors.extend(vectors)

        print(f"Added {len(documents)} documents to vector store")

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x**2 for x in a))
        magnitude_b = math.sqrt(sum(x**2 for x in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)

    def _euclidean_distance(self, a: List[float], b: List[float]) -> float:
        """Calculate Euclidean distance."""
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def similarity_search(
        self, query: str, k: int = 3, metric: str = "cosine"
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents."""
        query_vector = self.embedding_model.embed_query(query)

        similarities = []
        for i, doc_vector in enumerate(self.vectors):
            if metric == "cosine":
                score = self._cosine_similarity(query_vector, doc_vector)
            elif metric == "euclidean":
                score = -self._euclidean_distance(
                    query_vector, doc_vector
                )  # Negative for descending sort
            else:
                score = self._cosine_similarity(query_vector, doc_vector)

            similarities.append((self.documents[i], score))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]


# ============================================================================
# Enhanced RAG Pipeline
# ============================================================================


class EnhancedRAG:
    """Enhanced RAG pipeline with better context generation."""

    def __init__(self, documents: List[Dict], use_openai: bool = False):
        embedding_model = None
        if use_openai and OPENAI_AVAILABLE:
            embedding_model = OpenAIEmbedding()

        self.vector_store = EnhancedVectorStore(embedding_model)
        self.vector_store.add_documents(documents)

    def retrieve(
        self, query: str, k: int = 3, filter_metadata: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Retrieve relevant documents with optional metadata filtering."""
        results = self.vector_store.similarity_search(
            query, k=k * 2
        )  # Get more for filtering

        # Apply metadata filters if provided
        if filter_metadata:
            filtered_results = []
            for doc, score in results:
                match = all(
                    doc.metadata.get(key) == value
                    for key, value in filter_metadata.items()
                )
                if match:
                    filtered_results.append((doc, score))
            results = filtered_results[:k]

        return results[:k]

    def generate_context(
        self, query: str, retrieved_docs: List[Tuple[Document, float]]
    ) -> str:
        """Generate context with source attribution."""
        context_parts = []

        for i, (doc, score) in enumerate(retrieved_docs, 1):
            source_info = f"Source {i} (ID: {doc.id}, Score: {score:.3f})"
            if doc.metadata:
                source_info += f" - {doc.metadata}"

            context_parts.append(f"{source_info}:\n{doc.content.strip()}")

        return "\n\n".join(context_parts)

    def answer(self, query: str, k: int = 3, return_sources: bool = True) -> Dict:
        """Answer a query using RAG."""
        # Retrieve
        retrieved_docs = self.retrieve(query, k=k)

        if not retrieved_docs:
            return {
                "query": query,
                "response": "I couldn't find relevant information to answer your query.",
                "retrieved_docs": [],
            }

        # Generate context
        context = self.generate_context(query, retrieved_docs)

        # Format response
        response_parts = [f"Question: {query}", f"\nRelevant Context:\n{context}"]

        if return_sources:
            sources = [
                {"id": doc.id, "score": score, "metadata": doc.metadata}
                for doc, score in retrieved_docs
            ]
            response_parts.append(f"\nSources: {sources}")

        return {
            "query": query,
            "response": "\n".join(response_parts),
            "retrieved_docs": retrieved_docs,
        }


# ============================================================================
# Main Function
# ============================================================================


def main():
    """Demonstrate enhanced RAG implementation."""

    print("=" * 60)
    print("RAG Overview - Enhanced Solution")
    print("=" * 60)

    # Sample documents with metadata
    documents = [
        {
            "id": "doc1",
            "content": "Python is a high-level, interpreted programming language known for its readability and versatility.",
            "metadata": {"topic": "programming", "language": "python"},
        },
        {
            "id": "doc2",
            "content": "Large Language Models (LLMs) are AI systems trained on vast amounts of text data.",
            "metadata": {"topic": "AI", "subtopic": "LLM"},
        },
        {
            "id": "doc3",
            "content": "Retrieval-Augmented Generation combines information retrieval with text generation.",
            "metadata": {"topic": "AI", "subtopic": "RAG"},
        },
        {
            "id": "doc4",
            "content": "Vector databases store high-dimensional embeddings for semantic search.",
            "metadata": {"topic": "databases", "subtopic": "vector"},
        },
        {
            "id": "doc5",
            "content": "Prompt engineering optimizes inputs to LLMs for better outputs.",
            "metadata": {"topic": "AI", "subtopic": "prompting"},
        },
    ]

    # Initialize RAG
    rag = EnhancedRAG(documents)

    # Test queries
    test_queries = [
        "What is RAG?",
        "Tell me about vector databases",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        result = rag.answer(query)
        print(result["response"])
        print()


if __name__ == "__main__":
    main()
