"""
Vector Databases - Solution Code

Enhanced implementation with multiple similarity metrics and batch operations.
"""

import math
from typing import List, Dict, Any, Tuple, Optional, Literal


class EnhancedVectorDB:
    """Enhanced vector database with multiple features."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def add(
        self, id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a single vector."""
        if len(vector) != self.dimension:
            raise ValueError(f"Vector must have {self.dimension} dimensions")

        self.vectors[id] = vector
        self.metadata[id] = metadata or {}

    def add_batch(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ):
        """Add multiple vectors at once."""
        for i, id in enumerate(ids):
            metadata = metadatas[i] if metadatas else {}
            self.add(id, vectors[i], metadata)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        return dot / (mag_a * mag_b) if mag_a > 0 and mag_b > 0 else 0.0

    def _euclidean_distance(self, a: List[float], b: List[float]) -> float:
        """Calculate Euclidean distance (returns negative for sorting)."""
        return -math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def search(
        self,
        query: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        metric: Literal["cosine", "euclidean"] = "cosine",
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors."""
        if len(query) != self.dimension:
            raise ValueError(f"Query must have {self.dimension} dimensions")

        # Choose similarity function
        if metric == "cosine":
            similarity_fn = self._cosine_similarity
        else:
            similarity_fn = self._euclidean_distance

        results = []
        for id, vector in self.vectors.items():
            # Apply filter
            if filter_metadata:
                if not all(
                    self.metadata[id].get(k) == v for k, v in filter_metadata.items()
                ):
                    continue

            score = similarity_fn(query, vector)
            results.append((id, score, self.metadata[id]))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        if id in self.vectors:
            del self.vectors[id]
            del self.metadata[id]
            return True
        return False

    def get(self, id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get vector and metadata by ID."""
        if id in self.vectors:
            return self.vectors[id], self.metadata[id]
        return None

    def count(self) -> int:
        """Return number of vectors."""
        return len(self.vectors)

    def exists(self, id: str) -> bool:
        """Check if ID exists."""
        return id in self.vectors


def main():
    """Demonstrate the enhanced vector database."""

    print("=" * 50)
    print("Vector Database - Enhanced Solution")
    print("=" * 50)

    # Create database
    db = EnhancedVectorDB(dimension=4)

    # Add vectors
    vectors = [
        [1.0, 0.0, 0.0, 0.0],
        [0.9, 0.1, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    ids = ["vec1", "vec2", "vec3", "vec4", "vec5"]
    metadatas = [
        {"topic": "AI"},
        {"topic": "ML"},
        {"topic": "data"},
        {"topic": "code"},
        {"topic": "data"},
    ]

    db.add_batch(ids, vectors, metadatas)
    print(f"Added {db.count()} vectors")

    # Search
    query = [1.0, 0.0, 0.0, 0.0]
    results = db.search(query, k=3)

    print("\nSearch results (cosine):")
    for id, score, meta in results:
        print(f"  {id}: {score:.3f} - {meta}")

    # Filtered search
    results = db.search(query, k=3, filter_metadata={"topic": "data"})
    print("\nFiltered by topic=data:")
    for id, score, meta in results:
        print(f"  {id}: {score:.3f}")


if __name__ == "__main__":
    main()
