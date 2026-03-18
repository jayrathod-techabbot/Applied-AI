"""
Free Embedding Models Examples

This file demonstrates using various free embedding models with vector databases.
No API keys required - all models are completely free to use locally.
"""

from typing import List, Dict, Any


# ============================================================================
# 1. SENTENCE TRANSFORMERS (Recommended)
# ============================================================================


class SentenceTransformerEmbedder:
    """
    Free embeddings using Sentence Transformers.
    Models automatically download on first use.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize with a free model.

        Popular models:
        - all-MiniLM-L6-v2 (384 dims, fast, balanced) ← RECOMMENDED
        - all-MiniLM-L12-v2 (384 dims, slightly better quality)
        - all-mpnet-base-v2 (768 dims, best quality, slower)
        - distiluse-base-multilingual-cased-v2 (512 dims, multilingual)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "Install sentence-transformers: pip install sentence-transformers"
            )

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def embed_single(self, text: str) -> List[float]:
        """Get embedding for single text."""
        return self.embed([text])[0]

    def info(self) -> Dict[str, Any]:
        """Get model info."""
        return {
            "model": self.model_name,
            "dimension": self.dimension,
            "framework": "Sentence Transformers",
        }


# ============================================================================
# 2. HUGGINGFACE TRANSFORMERS
# ============================================================================


class HuggingFaceEmbedder:
    """
    Direct embeddings using HuggingFace transformers.
    More control, but slightly more setup.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize with HuggingFace model.

        Other options:
        - distiluse-base-multilingual-cased-v2
        - paraphrase-MiniLM-L6-v2
        - all-mpnet-base-v2
        """
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
        except ImportError:
            raise ImportError("Install transformers: pip install transformers torch")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model_name = model_name

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        import torch

        embeddings = []
        for text in texts:
            inputs = self.tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Use CLS token embedding
            embedding = outputs.last_hidden_state[:, 0].cpu().numpy()
            embeddings.append(embedding[0].tolist())

        return embeddings

    def embed_single(self, text: str) -> List[float]:
        """Get embedding for single text."""
        return self.embed([text])[0]


# ============================================================================
# 3. OLLAMA (Completely Local, No Downloads)
# ============================================================================


class OllamaEmbedder:
    """
    Free embeddings using Ollama - completely local execution.
    Requires: ollama pull nomic-embed-text
    """

    def __init__(
        self, model_name: str = "nomic-embed-text", host: str = "localhost:11434"
    ):
        """
        Initialize Ollama embedder.

        Setup:
        1. Install Ollama from https://ollama.ai/
        2. Run: ollama pull nomic-embed-text
        3. Then use this embedder
        """
        try:
            import ollama
        except ImportError:
            raise ImportError(
                "Install ollama: pip install ollama (and ollama CLI from ollama.ai)"
            )

        self.client = ollama
        self.model_name = model_name
        self.host = host

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        embeddings = []
        for text in texts:
            try:
                response = self.client.embeddings(model=self.model_name, prompt=text)
                embeddings.append(response["embedding"])
            except Exception as e:
                raise RuntimeError(
                    f"Ollama error: {e}. Make sure ollama is running: " f"ollama serve"
                )
        return embeddings

    def embed_single(self, text: str) -> List[float]:
        """Get embedding for single text."""
        return self.embed([text])[0]


# ============================================================================
# 4. FASTTEXT (Very Fast, Lightweight)
# ============================================================================


class FastTextEmbedder:
    """
    Free embeddings using FastText.
    Very fast, but lower quality than neural models.
    """

    def __init__(self, language: str = "en"):
        """
        Initialize FastText.

        Supported languages:
        - 'en' for English (cc.en.300.bin)
        - 'es' for Spanish
        - 'fr' for French
        - etc.
        """
        try:
            import fasttext
        except ImportError:
            raise ImportError("Install fasttext: pip install fasttext")

        # Auto-download model
        model_path = f"cc.{language}.300.bin"
        print(f"Loading FastText model (may take a minute on first run)...")
        self.model = fasttext.load_model(model_path)
        self.dimension = 300

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        return [self.model.get_sentence_vector(text).tolist() for text in texts]

    def embed_single(self, text: str) -> List[float]:
        """Get embedding for single text."""
        return self.model.get_sentence_vector(text).tolist()


# ============================================================================
# INTEGRATION WITH CHROMA
# ============================================================================


def demo_with_chroma():
    """Demonstrate embeddings with Chroma vector database."""
    print("\n" + "=" * 70)
    print("Sentence Transformers + Chroma")
    print("=" * 70)

    try:
        import chromadb
    except ImportError:
        print("Skipped: pip install chromadb")
        return

    # Initialize embedder
    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    print(f"✓ Loaded model: {embedder.model_name}")
    print(f"  Embedding dimension: {embedder.dimension}")

    # Initialize database
    client = chromadb.Client()
    collection = client.create_collection(name="documents")

    # Sample documents
    documents = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks with multiple layers",
        "Natural language processing helps computers understand text",
        "Computer vision enables machines to interpret images",
        "Reinforcement learning uses rewards and penalties",
    ]

    # Embed and add
    embeddings = embedder.embed(documents)
    collection.add(
        ids=[str(i) for i in range(len(documents))],
        embeddings=embeddings,
        documents=documents,
        metadatas=[{"source": "ml_basics"} for _ in documents],
    )
    print(f"✓ Added {len(documents)} documents")

    # Search
    queries = [
        "What is deep learning?",
        "Tell me about computer vision",
        "Explain machine learning",
    ]

    for query in queries:
        query_embedding = embedder.embed([query])
        results = collection.query(query_embeddings=query_embedding, n_results=2)

        print(f"\n📌 Query: '{query}'")
        for i, doc in enumerate(results["documents"][0], 1):
            print(f"   {i}. {doc}")


# ============================================================================
# COMPARISON DEMO
# ============================================================================


def compare_embedders():
    """Compare different free embedding models."""
    print("\n" + "=" * 70)
    print("Free Embedding Models Comparison")
    print("=" * 70)

    test_text = "Machine learning is transforming technology"

    models_to_try = [
        ("Sentence Transformers (MiniLM)", SentenceTransformerEmbedder, {}),
        (
            "Sentence Transformers (MPNet)",
            SentenceTransformerEmbedder,
            {"model_name": "all-mpnet-base-v2"},
        ),
        ("FastText", FastTextEmbedder, {"language": "en"}),
    ]

    results = {}

    for name, embedder_class, kwargs in models_to_try:
        try:
            print(f"\n🔄 Loading {name}...")
            embedder = embedder_class(**kwargs)

            embedding = embedder.embed_single(test_text)
            results[name] = {
                "dimension": len(embedding),
                "model": (
                    embedder.model_name if hasattr(embedder, "model_name") else "N/A"
                ),
                "status": "✓ Success",
            }
            print(f"   ✓ Dimension: {len(embedding)}")
        except Exception as e:
            results[name] = {"status": f"✗ Failed: {str(e)[:50]}"}
            print(f"   ✗ {str(e)[:50]}")

    print("\n" + "=" * 70)
    print("Summary:")
    for name, info in results.items():
        print(f"  {name}: {info['status']}")


# ============================================================================
# PRACTICAL EXAMPLE
# ============================================================================


def practical_rag_example():
    """
    Complete RAG example using free embeddings.
    """
    print("\n" + "=" * 70)
    print("Practical RAG Example - Document Q&A")
    print("=" * 70)

    try:
        import chromadb
    except ImportError:
        print("Skipped: pip install chromadb")
        return

    # 1. Initialize
    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    client = chromadb.Client()
    collection = client.create_collection(name="knowledge_base")

    # 2. Add knowledge base
    knowledge_base = [
        {
            "text": "Python is a high-level programming language known for its simplicity.",
            "source": "Python docs",
        },
        {
            "text": "Machine learning requires large amounts of data for training.",
            "source": "ML guide",
        },
        {
            "text": "Vector databases store embeddings for fast similarity search.",
            "source": "VectorDB docs",
        },
        {
            "text": "Large language models are trained on billions of tokens.",
            "source": "LLM research",
        },
    ]

    docs = [kb["text"] for kb in knowledge_base]
    embeddings = embedder.embed(docs)

    collection.add(
        ids=[str(i) for i in range(len(docs))],
        embeddings=embeddings,
        documents=docs,
        metadatas=[{"source": kb["source"]} for kb in knowledge_base],
    )

    # 3. Answer questions
    questions = [
        "What is Python?",
        "How much data do machine learning models need?",
        "What are vector databases?",
    ]

    for question in questions:
        query_embedding = embedder.embed([question])
        results = collection.query(query_embeddings=query_embedding, n_results=1)

        print(f"\n❓ {question}")
        print(f"📄 {results['documents'][0][0]}")
        print(f"📌 Source: {results['metadatas'][0][0]['source']}")


# ============================================================================
# MAIN
# ============================================================================


if __name__ == "__main__":
    print("\n🚀 Free Embedding Models Examples\n")

    # Run demos
    demo_with_chroma()
    compare_embedders()
    practical_rag_example()

    print("\n" + "=" * 70)
