"""
Vector Databases - Hands-on Exercise

This exercise demonstrates working with vector databases using a simple
in-memory implementation and introduces real database integrations.

Estimated Time: 45 minutes
"""

import math
import hashlib
import random
from typing import List, Dict, Any, Tuple, Optional


# ============================================================================
# PART 1: Simple In-Memory Vector Store
# ============================================================================


class SimpleVectorStore:
    """
    A simple in-memory vector store for demonstration.
    This mimics the core functionality of databases like Pinecone, Chroma, etc.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: List[List[float]] = []
        self.metadata: List[Dict[str, Any]] = []
        self.ids: List[str] = []

    def add(self, id: str, vector: List[float], metadata: Dict[str, Any] = None):
        """Add a vector to the store."""
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension must be {self.dimension}")

        self.ids.append(id)
        self.vectors.append(vector)
        self.metadata.append(metadata or {})

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))

        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot_product / (mag_a * mag_b)

    def search(
        self,
        query_vector: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for k most similar vectors.

        Args:
            query_vector: The query vector
            k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of (id, score, metadata) tuples
        """
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension must be {self.dimension}")

        results = []

        for i, vector in enumerate(self.vectors):
            # Apply metadata filter if specified
            if filter_metadata:
                match = all(
                    self.metadata[i].get(key) == value
                    for key, value in filter_metadata.items()
                )
                if not match:
                    continue

            score = self._cosine_similarity(query_vector, vector)
            results.append((self.ids[i], score, self.metadata[i]))

        # Sort by score (highest first) and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        if id in self.ids:
            index = self.ids.index(id)
            del self.ids[index]
            del self.vectors[index]
            del self.metadata[index]
            return True
        return False

    def count(self) -> int:
        """Return the number of vectors in the store."""
        return len(self.vectors)


# ============================================================================
# PART 2: Mock Embedding Function
# ============================================================================


class MockEmbedding:
    """Mock embedding function for demonstration."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        """Generate a deterministic vector from text."""
        # Use hash to create a pseudo-random but deterministic vector
        hash_input = hashlib.md5(text.encode()).hexdigest()
        seed = int(hash_input[:8], 16)

        random.seed(seed)
        vector = [random.uniform(-1, 1) for _ in range(self.dimension)]

        # Normalize
        magnitude = math.sqrt(sum(x * x for x in vector))
        return [x / magnitude for x in vector]


# ============================================================================
# PART 3: Real Database Integration Examples
# ============================================================================


def example_chroma_usage():
    """
    Example of using Chroma vector database.
    Note: Requires 'pip install chromadb'
    """
    # This is pseudocode to show the API
    """
    import chromadb
    
    # Initialize client
    client = chromadb.Client()
    
    # Create or get collection
    collection = client.create_collection("my_documents")
    
    # Add documents
    collection.add(
        documents=["doc1 text", "doc2 text"],
        ids=["doc1", "doc2"],
        metadatas=[{"source": "pdf"}, {"source": "web"}]
    )
    
    # Query
    results = collection.query(
        query_texts=["search query"],
        n_results=2
    )
    
    return results
    """
    pass


def example_pinecone_usage():
    """
    Example of using Pinecone vector database.
    Note: Requires 'pip install pinecone-client'
    """
    # This is pseudocode
    """
    from pinecone import Pinecone
    
    # Initialize
    pc = Pinecone(api_key="your-api-key")
    index = pc.Index("my-index")
    
    # Upsert vectors
    index.upsert(
        vectors=[
            {"id": "vec1", "values": [0.1, 0.2, ...], "metadata": {"text": "doc1"}},
            {"id": "vec2", "values": [0.3, 0.4, ...], "metadata": {"text": "doc2"}}
        ]
    )
    
    # Query
    results = index.query(
        vector=[0.1, 0.2, ...],
        top_k=5,
        include_metadata=True
    )
    
    return results
    """
    pass


# ============================================================================
# PART 4: Demo the Simple Vector Store
# ============================================================================


def main():
    """Demonstrate the simple vector store."""

    print("=" * 60)
    print("Vector Databases - Hands-on Exercise")
    print("=" * 60)

    # Sample documents
    documents = [
        {
            "id": "doc1",
            "text": "Python is a high-level programming language",
            "metadata": {"source": "tutorial", "topic": "programming"},
        },
        {
            "id": "doc2",
            "text": "Machine learning is a subset of artificial intelligence",
            "metadata": {"source": "tutorial", "topic": "AI"},
        },
        {
            "id": "doc3",
            "text": "Deep learning uses neural networks with multiple layers",
            "metadata": {"source": "article", "topic": "AI"},
        },
        {
            "id": "doc4",
            "text": "JavaScript is used for web development",
            "metadata": {"source": "tutorial", "topic": "programming"},
        },
        {
            "id": "doc5",
            "text": "Natural language processing deals with text data",
            "metadata": {"source": "article", "topic": "NLP"},
        },
    ]

    # Create embedding function and vector store
    embed_fn = MockEmbedding(dimension=384)
    vector_store = SimpleVectorStore(dimension=384)

    # Add documents to vector store
    print("\n[Step 1] Adding documents to vector store...")
    for doc in documents:
        vector = embed_fn.embed(doc["text"])
        vector_store.add(doc["id"], vector, doc["metadata"])

    print(f"Added {vector_store.count()} documents")

    # Test queries
    print("\n[Step 2] Testing similarity search...")

    queries = [
        "What is Python programming?",
        "Tell me about artificial intelligence",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        query_vector = embed_fn.embed(query)
        results = vector_store.search(query_vector, k=3)

        for id, score, metadata in results:
            print(f"  {id} (score: {score:.3f}) - {metadata}")

    # Test metadata filtering
    print("\n[Step 3] Testing metadata filtering...")
    query_vector = embed_fn.embed("Tell me about programming")
    results = vector_store.search(
        query_vector, k=3, filter_metadata={"topic": "programming"}
    )

    print("Filtered by topic=programming:")
    for id, score, metadata in results:
        print(f"  {id} (score: {score:.3f})")

    print("\n[Step 4] Exercise complete!")
    print("Try modifying the documents or adding more queries")


if __name__ == "__main__":
    main()


# ============================================================================
# EXERCISE TASKS
# ============================================================================

"""
EXERCISE TASKS:
1. Implement Euclidean distance as an alternative similarity metric
2. Add support for batch adding of vectors
3. Implement a simple HNSW-like index for faster search
4. Add support for updating existing vectors
5. Add persistence to save/load the vector store

BONUS: Integrate with a real vector database (Chroma or Pinecone)
"""
