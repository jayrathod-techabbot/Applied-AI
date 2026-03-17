"""
RAG Overview - Hands-on Exercise

This exercise demonstrates the basic RAG workflow using a simple in-memory
vector store. You'll build a basic question-answering system over documents.

Estimated Time: 30 minutes
"""

import os
from typing import List, Tuple

# ============================================================================
# PART 1: Setup and Imports
# ============================================================================

# For this exercise, we'll use a simple in-memory approach
# In production, you'd use libraries like langchain, pinecone, etc.

# Sample documents for our knowledge base
SAMPLE_DOCUMENTS = [
    {
        "id": "doc1",
        "content": """
        Python is a high-level, interpreted programming language known for its
        readability and versatility. It supports multiple programming paradigms
        including procedural, object-oriented, and functional programming.
        Python is widely used in web development, data science, machine learning,
        and automation. The language emphasizes code readability with its use
        of significant whitespace.
        """,
    },
    {
        "id": "doc2",
        "content": """
        Large Language Models (LLMs) are artificial intelligence systems trained
        on vast amounts of text data. They can understand and generate human-like
        text. Examples include GPT-4, Claude, and Gemini. LLMs use transformer
        architectures and are capable of tasks like translation, summarization,
        question answering, and creative writing. They have revolutionized
        natural language processing applications.
        """,
    },
    {
        "id": "doc3",
        "content": """
        Retrieval-Augmented Generation (RAG) is a technique that combines
        information retrieval with text generation. RAG systems first retrieve
        relevant documents from a knowledge base, then use them to augment
        the prompt sent to an LLM. This helps reduce hallucinations and provides
        source attribution. RAG is essential for building accurate AI systems
        that can access up-to-date or domain-specific information.
        """,
    },
    {
        "id": "doc4",
        "content": """
        Vector databases are specialized database systems designed to store
        and query high-dimensional vector embeddings. They enable semantic
        similarity search, where documents can be found based on meaning
        rather than exact keyword matching. Popular vector databases include
        Pinecone, Weaviate, Chroma, and Milvus. They are fundamental to RAG
        systems for efficient document retrieval.
        """,
    },
    {
        "id": "doc5",
        "content": """
        Prompt engineering is the practice of designing and optimizing prompts
        for large language models. Effective prompts clearly specify the desired
        output format, provide relevant context, and use techniques like
        few-shot learning. Key concepts include role prompting, chain-of-thought
        reasoning, and temperature settings. Good prompt engineering can
        significantly improve LLM output quality without changing the model.
        """,
    },
]


# ============================================================================
# PART 2: Simple Embedding Simulation
# ============================================================================


class SimpleEmbedding:
    """
    A simple embedding simulation for educational purposes.
    In production, use actual embedding models like:
    - OpenAI's text-embedding-ada-002
    - HuggingFace's sentence-transformers
    - Google's text-embedding-004
    """

    def __init__(self):
        # Simulate embeddings with hash-based vectors
        self.dimension = 384

    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to a simple vector representation."""
        import hashlib
        import math

        # Create a deterministic but pseudo-random vector based on text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)

        # Generate pseudo-random values based on seed
        import random

        random.seed(seed)
        vector = [random.uniform(-1, 1) for _ in range(self.dimension)]

        # Normalize the vector
        magnitude = math.sqrt(sum(x**2 for x in vector))
        return [x / magnitude for x in vector]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return [self._text_to_vector(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query."""
        return self._text_to_vector(text)


# ============================================================================
# PART 3: Simple Vector Store
# ============================================================================


class SimpleVectorStore:
    """
    A simple in-memory vector store for demonstration.
    In production, use: Pinecone, Weaviate, Chroma, Milvus, etc.
    """

    def __init__(self):
        self.embeddings = SimpleEmbedding()
        self.documents = []
        self.vectors = []

    def add_documents(self, docs: List[dict]):
        """Add documents to the vector store."""
        texts = [doc["content"] for doc in docs]
        vectors = self.embeddings.embed_documents(texts)

        self.documents.extend(docs)
        self.vectors.extend(vectors)

        print(f"Added {len(docs)} documents to the vector store")

    def similarity_search(self, query: str, k: int = 3) -> List[Tuple[dict, float]]:
        """Find k most similar documents to the query."""
        query_vector = self.embeddings.embed_query(query)

        # Calculate cosine similarity
        similarities = []
        for i, doc_vector in enumerate(self.vectors):
            similarity = sum(a * b for a, b in zip(query_vector, doc_vector))
            similarities.append((self.documents[i], similarity))

        # Sort by similarity (highest first) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]


# ============================================================================
# PART 4: Simple RAG Pipeline
# ============================================================================


class SimpleRAG:
    """
    A simple RAG pipeline demonstration.
    In production, use LangChain's RAG implementations.
    """

    def __init__(self, documents: List[dict]):
        self.vector_store = SimpleVectorStore()
        self.vector_store.add_documents(documents)

    def retrieve(self, query: str, k: int = 3) -> List[dict]:
        """Retrieve relevant documents for a query."""
        results = self.vector_store.similarity_search(query, k)
        return [doc for doc, score in results]

    def generate_context(self, query: str, retrieved_docs: List[dict]) -> str:
        """Generate augmented context from retrieved documents."""
        context_parts = []

        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(
                f"Document {i} (ID: {doc['id']}):\n{doc['content'].strip()}"
            )

        return "\n\n".join(context_parts)

    def answer(self, query: str) -> dict:
        """Answer a query using RAG."""
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.retrieve(query, k=2)

        # Step 2: Generate context
        context = self.generate_context(query, retrieved_docs)

        # Step 3: In production, you would send this to an LLM
        # For demo, we'll create a simulated response
        response = f"""
Based on the retrieved context, here is my answer to: "{query}"

[In a real RAG system, this would be generated by an LLM using the context below]

Retrieved Context:
{context}

Source Documents: {[doc['id'] for doc in retrieved_docs]}
"""
        return {"query": query, "response": response, "retrieved_docs": retrieved_docs}


# ============================================================================
# PART 5: Run the Exercise
# ============================================================================


def main():
    """Main function to demonstrate RAG workflow."""

    print("=" * 60)
    print("RAG Overview - Hands-on Exercise")
    print("=" * 60)

    # Initialize RAG system with sample documents
    print("\n[Step 1] Initializing RAG system with sample documents...")
    rag = SimpleRAG(SAMPLE_DOCUMENTS)

    # Test queries
    test_queries = [
        "What is Python programming language?",
        "How do LLMs work?",
        "What is vector database?",
    ]

    print("\n[Step 2] Testing RAG with sample queries...\n")

    for query in test_queries:
        print("-" * 60)
        print(f"Query: {query}")
        print("-" * 60)

        result = rag.answer(query)
        print(result["response"])
        print()

    print("\n[Step 3] Exercise Complete!")
    print("\nTry modifying the test_queries or adding your own documents")
    print("to explore the RAG workflow further.")


if __name__ == "__main__":
    main()


# ============================================================================
# EXERCISE TASKS
# ============================================================================

"""
EXERCISE TASKS:
1. Add more documents to the SAMPLE_DOCUMENTS list related to AI/ML
2. Modify the similarity_search to use different similarity metrics
3. Add document metadata (source, date, author) and include in retrieval
4. Implement a simple reranking of retrieved documents
5. Add support for document deletion or updates

BONUS: Replace SimpleEmbedding with actual OpenAI embeddings
(requires: pip install openai)
"""
