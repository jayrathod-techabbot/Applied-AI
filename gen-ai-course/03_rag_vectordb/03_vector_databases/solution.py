"""
Vector Databases - Production Solutions

Demonstrates using production-grade vector databases:
- Chroma (simplest, in-memory/persistent)
- FAISS (high-performance, scalable)
- Milvus (enterprise-grade)
"""

from typing import List, Dict, Any, Optional
import numpy as np


# ============================================================================
# 1. CHROMA - Simplest Production Option
# ============================================================================


class ChromaVectorStore:
    """Chroma vector database wrapper - great for small-medium scale."""

    def __init__(self, collection_name: str = "documents", persist_dir: str = "./chroma_db"):
        """
        Initialize Chroma vector store.

        Args:
            collection_name: Name of the collection
            persist_dir: Directory to persist the database
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("Install chromadb: pip install chromadb")

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ):
        """Add documents to the vector store."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        self.collection.add(
            documents=documents,
            metadatas=metadatas or [{"source": "unknown"} for _ in documents],
            ids=ids,
        )
        print(f"Added {len(documents)} documents to Chroma")

    def search(self, query_text: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        return [
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]

    def delete_all(self):
        """Delete all documents."""
        count = self.collection.count()
        self.client.delete_collection(name=self.collection.name)
        print(f"Deleted collection with {count} documents")


# ============================================================================
# 2. FAISS - High-Performance Vector Search
# ============================================================================


class FAISSVectorStore:
    """FAISS vector database - optimized for large-scale similarity search."""

    def __init__(self, dimension: int = 384):
        """
        Initialize FAISS vector store.

        Args:
            dimension: Dimension of the embeddings
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("Install faiss: pip install faiss-cpu")

        self.faiss = faiss
        self.dimension = dimension
        self.index = self.faiss.IndexFlatIP(dimension)  # Inner product (cosine with normalized vectors)
        self.id_to_doc = {}
        self.id_to_meta = {}
        self.doc_id = 0

    def add_vectors(
        self,
        vectors: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ):
        """Add vectors and documents to the index."""
        vectors_array = np.array(vectors, dtype=np.float32)

        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
        vectors_array = vectors_array / (norms + 1e-10)

        self.index.add(vectors_array)

        for i, doc in enumerate(documents):
            self.id_to_doc[self.doc_id] = doc
            self.id_to_meta[self.doc_id] = metadatas[i] if metadatas else {}
            self.doc_id += 1

        print(f"Added {len(documents)} documents to FAISS")

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        query_array = np.array([query_vector], dtype=np.float32)

        # Normalize query
        norm = np.linalg.norm(query_array, axis=1, keepdims=True)
        query_array = query_array / (norm + 1e-10)

        distances, indices = self.index.search(query_array, k)

        return [
            {
                "id": int(idx),
                "document": self.id_to_doc.get(int(idx), ""),
                "metadata": self.id_to_meta.get(int(idx), {}),
                "score": float(distances[0][i]),
            }
            for i, idx in enumerate(indices[0])
            if idx != -1
        ]

    def save(self, path: str):
        """Save index to disk."""
        self.faiss.write_index(self.index, path)
        print(f"Saved FAISS index to {path}")

    def load(self, path: str):
        """Load index from disk."""
        self.index = self.faiss.read_index(path)
        print(f"Loaded FAISS index from {path}")


# ============================================================================
# 3. MILVUS - Enterprise-Grade Vector Database
# ============================================================================


class MilvusVectorStore:
    """Milvus vector database - enterprise-grade, distributed."""

    def __init__(
        self,
        collection_name: str = "documents",
        host: str = "localhost",
        port: int = 19530,
        dimension: int = 384,
    ):
        """
        Initialize Milvus vector store.

        Args:
            collection_name: Name of the collection
            host: Milvus server host
            port: Milvus server port
            dimension: Dimension of the embeddings
        """
        try:
            from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections
        except ImportError:
            raise ImportError("Install pymilvus: pip install pymilvus")

        self.Collection = Collection
        self.FieldSchema = FieldSchema
        self.CollectionSchema = CollectionSchema
        self.DataType = DataType
        self.collection_name = collection_name
        self.dimension = dimension

        # Connect to Milvus
        connections.connect(host=host, port=port)

        # Create collection if not exists
        self._create_collection()

    def _create_collection(self):
        """Create collection in Milvus."""
        from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

        try:
            self.collection = Collection(self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                FieldSchema(name="document", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=256),
            ]
            schema = CollectionSchema(fields, description="Document embeddings")
            self.collection = Collection(self.collection_name, schema=schema)

    def add_vectors(
        self,
        vectors: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ):
        """Add vectors and documents to Milvus."""
        data = {
            "vector": vectors,
            "document": documents,
            "source": [m.get("source", "unknown") for m in (metadatas or [{}] * len(documents))],
        }

        self.collection.insert(data)
        self.collection.flush()
        print(f"Added {len(documents)} documents to Milvus")

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=k,
            output_fields=["document", "source"],
        )

        return [
            {
                "id": hit.id,
                "document": hit.entity.get("document", ""),
                "metadata": {"source": hit.entity.get("source", "")},
                "score": float(hit.score),
            }
            for hit in results[0]
        ]


# ============================================================================
# DEMO
# ============================================================================


def demo_chroma():
    """Demonstrate Chroma vector store."""
    print("\n" + "=" * 60)
    print("CHROMA - Simplest Production Option")
    print("=" * 60)

    try:
        store = ChromaVectorStore(collection_name="demo")

        documents = [
            "Machine learning is a subset of artificial intelligence.",
            "Deep learning uses neural networks with multiple layers.",
            "Natural language processing helps computers understand text.",
            "Computer vision enables machines to interpret images.",
        ]

        metadatas = [
            {"topic": "AI", "type": "definition"},
            {"topic": "ML", "type": "definition"},
            {"topic": "NLP", "type": "definition"},
            {"topic": "CV", "type": "definition"},
        ]

        store.add_documents(documents, metadatas)

        results = store.search("What is deep learning?", k=2)
        print("\nSearch results:")
        for r in results:
            print(f"  - {r['document'][:60]}... (distance: {r['distance']:.3f})")

        store.delete_all()
    except ImportError as e:
        print(f"Skipped: {e}")


def demo_faiss():
    """Demonstrate FAISS vector store."""
    print("\n" + "=" * 60)
    print("FAISS - High-Performance Vector Search")
    print("=" * 60)

    try:
        import numpy as np

        store = FAISSVectorStore(dimension=4)

        # Simple 4D vectors for demo
        vectors = [
            [1.0, 0.0, 0.0, 0.0],
            [0.9, 0.1, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ]

        documents = ["Vector A", "Vector A-similar", "Vector B", "Vector C"]
        store.add_vectors(vectors, documents)

        query = [1.0, 0.0, 0.0, 0.0]
        results = store.search(query, k=2)
        print("\nSearch results:")
        for r in results:
            print(f"  - {r['document']} (score: {r['score']:.3f})")
    except ImportError as e:
        print(f"Skipped: {e}")


def demo_milvus():
    """Demonstrate Milvus vector store."""
    print("\n" + "=" * 60)
    print("MILVUS - Enterprise-Grade Vector Database")
    print("=" * 60)

    try:
        store = MilvusVectorStore(dimension=4)

        vectors = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ]

        documents = ["Doc A", "Doc B", "Doc C"]
        store.add_vectors(vectors, documents)

        query = [1.0, 0.0, 0.0, 0.0]
        results = store.search(query, k=2)
        print("\nSearch results:")
        for r in results:
            print(f"  - {r['document']} (score: {r['score']:.3f})")
    except Exception as e:
        print(f"Skipped: {e} (Milvus requires server running)")


if __name__ == "__main__":
    demo_chroma()
    demo_faiss()
    demo_milvus()
