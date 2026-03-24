"""
Retrieval Techniques - Hands-on Exercises
==========================================

This exercise covers all retrieval techniques from concepts.md:
1. Query Rewriting (LLM-Based, HyDE, Synonym Expansion)
2. Reranking (Cross-Encoder, MMR)
3. Hybrid Search (Vector + Keyword)
4. Multi-Step Retrieval (Query Decomposition)
5. Production Considerations (Caching, Error Handling)

Uses ChromaDB as the vector database.
"""

import os
import json
import hashlib
import pickle
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Third-party imports (install via requirements.txt)
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

# For LLM-based rewriting (using a lightweight model or mock)
try:
    from transformers import pipeline
except ImportError:
    pass

# =============================================================================
# SAMPLE DATA - Tech Documentation Dataset
# =============================================================================

SAMPLE_DOCUMENTS = [
    {
        "id": "doc1",
        "content": """Python is a high-level, interpreted programming language known for its 
        simplicity and readability. It supports multiple programming paradigms including 
        procedural, object-oriented, and functional programming. Python is widely used 
        in web development, data science, machine learning, and automation.""",
        "category": "programming",
        "source": "tech-docs"
    },
    {
        "id": "doc2", 
        "content": """Machine learning is a subset of artificial intelligence that enables 
        systems to learn and improve from experience without being explicitly programmed. 
        Common algorithms include supervised learning, unsupervised learning, and 
        reinforcement learning. Popular frameworks include TensorFlow and PyTorch.""",
        "category": "ai_ml",
        "source": "tech-docs"
    },
    {
        "id": "doc3",
        "content": """REST APIs (Representational State Transfer) are architectural styles 
        for designing networked applications. They use HTTP methods (GET, POST, PUT, DELETE) 
        to perform CRUD operations. REST APIs are stateless and return JSON or XML data.""",
        "category": "web_development",
        "source": "tech-docs"
    },
    {
        "id": "doc4",
        "content": """Docker is a platform for developing, shipping, and running applications 
        in containers. Containers package an application with all its dependencies, ensuring 
        consistent behavior across environments. Docker Hub is a registry for container images.""",
        "category": "devops",
        "source": "tech-docs"
    },
    {
        "id": "doc5",
        "content": """SQL (Structured Query Language) is a domain-specific language used for 
        managing relational databases. Common operations include SELECT, INSERT, UPDATE, 
        and DELETE. Popular databases include PostgreSQL, MySQL, and SQLite.""",
        "category": "databases",
        "source": "tech-docs"
    },
    {
        "id": "doc6",
        "content": """Git is a distributed version control system for tracking changes in 
        source code during software development. It supports branching, merging, and 
        collaborative workflows. GitHub provides hosting for Git repositories.""",
        "category": "devops",
        "source": "tech-docs"
    },
    {
        "id": "doc7",
        "content": """JavaScript is a high-level, dynamic programming language that runs in 
        web browsers and on servers (Node.js). It supports event-driven, functional, and 
        object-oriented programming. Popular frameworks include React, Vue, and Angular.""",
        "category": "web_development",
        "source": "tech-docs"
    },
    {
        "id": "doc8",
        "content": """Neural networks are computing systems inspired by biological neural networks. 
        They consist of interconnected nodes (neurons) organized in layers. Deep learning 
        uses networks with multiple hidden layers. Applications include image recognition 
        and natural language processing.""",
        "category": "ai_ml",
        "source": "tech-docs"
    },
    {
        "id": "doc9",
        "content": """Kubernetes is an open-source container orchestration platform for 
        automating deployment, scaling, and management of containerized applications. 
        It provides features like load balancing, auto-scaling, and self-healing.""",
        "category": "devops",
        "source": "tech-docs"
    },
    {
        "id": "doc10",
        "content": """MongoDB is a NoSQL document database that stores data in flexible, 
        JSON-like documents. It supports horizontal scaling through sharding and provides 
        rich query capabilities. Commonly used with Node.js applications.""",
        "category": "databases",
        "source": "tech-docs"
    }
]


# =============================================================================
# EXERCISE 1: Setup ChromaDB Vector Store
# =============================================================================

def setup_chromadb(collection_name: str = "tech_docs") -> chromadb.Client:
    """
    Setup ChromaDB client with a collection.
    
    TODO: Create a ChromaDB client and collection with the given name.
    Use Settings for persistence.
    
    Returns:
        ChromaDB client
    """
    # Your code here:
    # 1. Create ChromaDB client with persistence
    # 2. Create or get collection with appropriate settings
    # 3. Return the client
    
    raise NotImplementedError("Exercise 1: Implement ChromaDB setup")


def add_documents_to_chromadb(
    client: chromadb.Client, 
    documents: List[Dict[str, Any]],
    embedding_model: SentenceTransformer
) -> None:
    """
    Add documents to ChromaDB collection.
    
    TODO: Implement document addition to ChromaDB:
    - Extract ids, documents, and metadata
    - Generate embeddings for documents
    - Add to collection
    
    Args:
        client: ChromaDB client
        documents: List of document dictionaries
        embedding_model: Sentence transformer model for embeddings
    """
    # Your code here:
    # 1. Get the collection
    # 2. Prepare ids, documents, and metadata
    # 3. Generate embeddings
    # 4. Add to collection
    
    raise NotImplementedError("Exercise 1: Implement document addition")


# =============================================================================
# EXERCISE 2: Query Rewriting Techniques
# =============================================================================

class SynonymExpander:
    """
    Expand queries with synonyms and related terms.
    
    TODO: Implement the synonym expansion logic.
    """
    
    def __init__(self):
        # Define synonym dictionary for common tech terms
        self.synonym_dict = {
            'python': ['python programming', 'python language', 'py'],
            'learn': ['study', 'understand', 'master', 'training'],
            'build': ['create', 'develop', 'make', 'construct'],
            'code': ['program', 'script', 'develop'],
            'web': ['website', 'web application', 'online'],
            'data': ['information', 'dataset', 'records'],
            'app': ['application', 'software', 'program'],
            'run': ['execute', 'start', 'launch'],
            'store': ['save', 'persist', 'keep'],
            'find': ['search', 'lookup', 'discover'],
        }
    
    def expand(self, query: str) -> List[str]:
        """
        Expand query with synonyms.
        
        TODO: Implement synonym expansion:
        1. Tokenize query
        2. Find synonyms for each word
        3. Generate expanded queries
        
        Args:
            query: Original query string
            
        Returns:
            List of expanded queries
        """
        # Your code here:
        # 1. Lowercase and tokenize
        # 2. For each word, find synonyms
        # 3. Create new queries with synonyms
        # 4. Return all variations including original
        
        raise NotImplementedError("Exercise 2a: Implement synonym expansion")


class HyDERetriever:
    """
    HyDE (Hypothetical Document Embeddings) Retriever.
    
    Generate hypothetical documents and use them for retrieval.
    
    TODO: Implement HyDE retrieval using ChromaDB.
    """
    
    def __init__(
        self, 
        chroma_client: chromadb.Client,
        embedding_model: SentenceTransformer,
        llm_generator=None  # Optional LLM for generating hypothetical docs
    ):
        self.chroma_client = chroma_client
        self.embedding_model = embedding_model
        self.llm_generator = llm_generator
        self.collection = chroma_client.get_collection("tech_docs")
    
    def _generate_hypothetical(self, query: str) -> str:
        """
        Generate a hypothetical document for the query.
        
        TODO: Generate a hypothetical document that would answer the query.
        Can use a template-based approach or LLM if available.
        """
        # Simple template-based generation (can be replaced with LLM)
        # Your code here:
        
        # Option 1: Use simple template
        hypothetical = f"""This document provides comprehensive information about {query}. 
        It covers the fundamentals, key concepts, practical applications, 
        and best practices. The content includes detailed explanations, 
        examples, and code snippets for implementation."""
        
        # Option 2: If LLM is available, use it
        # if self.llm_generator:
        #     hypothetical = self.llm_generator(query)
        
        return hypothetical
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve documents using HyDE approach.
        
        TODO: Implement HyDE retrieval:
        1. Generate hypothetical document
        2. Embed the hypothetical document
        3. Search using the hypothetical embedding
        
        Args:
            query: User query
            k: Number of results
            
        Returns:
            List of retrieved documents with scores
        """
        # Your code here:
        # 1. Generate hypothetical document
        # 2. Embed it
        # 3. Query ChromaDB with the hypothetical embedding
        # 4. Return results
        
        raise NotImplementedError("Exercise 2b: Implement HyDE retrieval")


# =============================================================================
# EXERCISE 3: Reranking Techniques
# =============================================================================

class CrossEncoderReranker:
    """
    Rerank results using a cross-encoder model.
    
    TODO: Implement cross-encoder reranking.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize cross-encoder model.
        
        TODO: Load the cross-encoder model from sentence-transformers.
        """
        # Your code here:
        # from sentence_transformers import CrossEncoder
        # self.model = CrossEncoder(model_name)
        
        raise NotImplementedError("Exercise 3a: Initialize cross-encoder")
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Rerank documents based on query-document relevance.
        
        TODO: Implement reranking:
        1. Create query-document pairs
        2. Get cross-encoder scores
        3. Sort by score and return top-k
        
        Args:
            query: The query string
            documents: List of document texts
            top_k: Number of top results to return
            
        Returns:
            List of (document, score) tuples, sorted by relevance
        """
        # Your code here:
        
        raise NotImplementedError("Exercise 3a: Implement reranking")


class MMRReranker:
    """
    Maximal Marginal Relevance (MMR) for diverse results.
    
    TODO: Implement MMR reranking.
    """
    
    def __init__(
        self, 
        embedding_model: SentenceTransformer,
        lambda_mult: float = 0.5
    ):
        """
        Initialize MMR reranker.
        
        Args:
            embedding_model: Sentence transformer for embeddings
            lambda_mult: Balance between relevance (0) and diversity (1)
        """
        self.embedding_model = embedding_model
        self.lambda_mult = lambda_mult
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using MMR to balance relevance and diversity.
        
        TODO: Implement MMR algorithm:
        1. Encode query and documents
        2. Calculate relevance scores (cosine similarity)
        3. Iteratively select documents considering both relevance and diversity
        
        Args:
            query: The query string
            documents: List of document dictionaries with 'content' key
            k: Number of results
            
        Returns:
            List of reranked documents
        """
        # Your code here:
        # 1. Encode query
        # 2. Encode all documents
        # 3. Calculate relevance scores
        # 4. Implement MMR selection loop
        
        raise NotImplementedError("Exercise 3b: Implement MMR reranking")


# =============================================================================
# EXERCISE 4: Hybrid Search (Vector + Keyword)
# =============================================================================

class HybridSearch:
    """
    Combine vector search with keyword search (BM25).
    
    TODO: Implement hybrid search combining ChromaDB with BM25.
    """
    
    def __init__(
        self,
        chroma_client: chromadb.Client,
        embedding_model: SentenceTransformer,
        vector_weight: float = 0.5
    ):
        """
        Initialize hybrid search.
        
        Args:
            chroma_client: ChromaDB client
            embedding_model: Sentence transformer model
            vector_weight: Weight for vector search (1 - vector_weight for keyword)
        """
        self.chroma_client = chroma_client
        self.embedding_model = embedding_model
        self.vector_weight = vector_weight
        self.collection = chroma_client.get_collection("tech_docs")
        
        # Initialize BM25 index
        self._init_bm25()
    
    def _init_bm25(self):
        """Initialize BM25 index from ChromaDB documents."""
        # Your code here:
        # Get all documents from ChromaDB
        # Tokenize and build BM25 index
        
        raise NotImplementedError("Exercise 4: Initialize BM25")
    
    def search(
        self, 
        query: str, 
        k: int = 5,
        alpha: float = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and keyword search.
        
        TODO: Implement hybrid search:
        1. Perform vector search with ChromaDB
        2. Perform BM25 keyword search
        3. Normalize and combine scores
        4. Return top-k results
        
        Args:
            query: Search query
            k: Number of results
            alpha: Override vector weight (optional)
            
        Returns:
            List of combined search results with scores
        """
        # Your code here:
        # 1. Vector search
        # 2. BM25 search  
        # 3. Normalize scores
        # 4. Combine with weighted sum
        # 5. Deduplicate and rank
        
        raise NotImplementedError("Exercise 4: Implement hybrid search")


# =============================================================================
# EXERCISE 5: Query Decomposition
# =============================================================================

class QueryDecomposer:
    """
    Decompose complex queries into simpler sub-queries.
    
    TODO: Implement query decomposition.
    """
    
    def __init__(self, llm=None):
        """
        Initialize query decomposer.
        
        Args:
            llm: Optional LLM for intelligent decomposition
        """
        self.llm = llm
    
    def decompose(self, query: str) -> List[str]:
        """
        Decompose a complex query into simpler sub-queries.
        
        TODO: Implement query decomposition:
        1. Use rules/LLM to break down complex queries
        2. Return list of simpler sub-queries
        
        Common decomposition patterns:
        - "X and Y" -> [X, Y]
        - "X vs Y" -> [X, Y]
        - "How to do X, Y, Z" -> [X, Y, Z]
        
        Args:
            query: Complex query string
            
        Returns:
            List of simpler sub-queries
        """
        # Your code here:
        # Implement rule-based decomposition
        
        raise NotImplementedError("Exercise 5: Implement query decomposition")
    
    def retrieve_decomposed(
        self, 
        query: str, 
        retriever: Any, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents for decomposed queries and combine results.
        
        TODO: Implement retrieval for decomposed queries:
        1. Decompose the query
        2. Retrieve documents for each sub-query
        3. Combine and deduplicate results
        
        Args:
            query: Original complex query
            retriever: Retriever object with retrieve method
            k: Number of results per sub-query
            
        Returns:
            Combined list of relevant documents
        """
        # Your code here:
        
        raise NotImplementedError("Exercise 5: Implement decomposed retrieval")


# =============================================================================
# EXERCISE 6: Production Considerations
# =============================================================================

class RetrievalCache:
    """
    Cache retrieval results for performance.
    
    TODO: Implement a simple in-memory cache for retrieval results.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached entries
        """
        self.cache: Dict[str, Tuple[List[Dict], float]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _hash_query(self, query: str, k: int) -> str:
        """Create a hash key for query + k combination."""
        # Your code here:
        
        raise NotImplementedError("Exercise 6a: Implement cache key generation")
    
    def get(self, query: str, k: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results for a query.
        
        TODO: Implement cache retrieval.
        
        Args:
            query: Query string
            k: Number of results
            
        Returns:
            Cached results or None if not cached
        """
        # Your code here:
        
        raise NotImplementedError("Exercise 6a: Implement cache retrieval")
    
    def set(
        self, 
        query: str, 
        k: int, 
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Cache results for a query.
        
        TODO: Implement cache storage with LRU eviction.
        
        Args:
            query: Query string
            k: Number of results
            results: Results to cache
        """
        # Your code here:
        
        raise NotImplementedError("Exercise 6a: Implement cache storage")


class ResilientRetriever:
    """
    Handle failures gracefully with fallback strategies.
    
    TODO: Implement resilient retrieval with multiple strategies.
    """
    
    def __init__(self, retrievers: List[Any]):
        """
        Initialize with multiple retriever strategies.
        
        Args:
            retrievers: List of retriever objects (tried in order)
        """
        self.retrievers = retrievers
    
    def retrieve(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with fallback to next retriever if one fails.
        
        TODO: Implement resilient retrieval:
        1. Try first retriever
        2. If it fails, try next one
        3. Log errors but continue
        4. Return first successful result
        
        Args:
            query: Query string
            k: Number of results
            
        Returns:
            Retrieved documents
            
        Raises:
            Exception: If all retrievers fail
        """
        # Your code here:
        
        raise NotImplementedError("Exercise 6b: Implement resilient retrieval")


# =============================================================================
# COMPLETE RETRIEVAL PIPELINE
# =============================================================================

class AdvancedRetriever:
    """
    Complete retrieval pipeline combining all techniques.
    
    This demonstrates a production-ready retrieval system.
    """
    
    def __init__(
        self,
        chroma_client: chromadb.Client,
        embedding_model: SentenceTransformer,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        use_mmr: bool = False,
        use_cache: bool = True
    ):
        """
        Initialize advanced retriever with all techniques.
        
        Args:
            chroma_client: ChromaDB client
            embedding_model: Sentence transformer model
            use_hybrid: Enable hybrid search
            use_reranking: Enable cross-encoder reranking
            use_mmr: Use MMR for diversity instead of reranking
            use_cache: Enable result caching
        """
        self.chroma_client = chroma_client
        self.embedding_model = embedding_model
        self.collection = chroma_client.get_collection("tech_docs")
        
        # Initialize components
        self.synonym_expander = SynonymExpander()
        self.hyde = HyDERetriever(chroma_client, embedding_model)
        
        if use_reranking:
            self.cross_encoder = CrossEncoderReranker()
        else:
            self.cross_encoder = None
            
        if use_mmr:
            self.mmr = MMRReranker(embedding_model)
        else:
            self.mmr = None
        
        if use_hybrid:
            self.hybrid = HybridSearch(chroma_client, embedding_model)
        else:
            self.hybrid = None
        
        if use_cache:
            self.cache = RetrievalCache()
        else:
            self.cache = None
        
        self.use_hybrid = use_hybrid
        self.use_reranking = use_reranking
        self.use_mmr = use_mmr
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        use_expansion: bool = True,
        use_hyde: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Main retrieval method with multiple enhancement techniques.
        
        Args:
            query: User query
            k: Number of results
            use_expansion: Use synonym expansion
            use_hyde: Use HyDE retrieval
            
        Returns:
            List of retrieved documents with scores
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(query, k)
            if cached:
                print(f"Cache hit for query: {query}")
                return cached
        
        # Step 1: Query expansion
        if use_expansion:
            expanded_queries = self.synonym_expander.expand(query)
            print(f"Expanded queries: {expanded_queries}")
        else:
            expanded_queries = [query]
        
        # Step 2: Retrieve documents
        all_results = []
        
        for q in expanded_queries:
            if use_hyde:
                results = self.hyde.retrieve(q, k=k*2)
            elif self.hybrid:
                results = self.hybrid.search(q, k=k*2)
            else:
                # Basic vector search
                results = self._vector_search(q, k=k*2)
            
            all_results.extend(results)
        
        # Step 3: Deduplicate
        unique_results = self._deduplicate_results(all_results)
        
        # Step 4: Reranking or MMR
        if self.use_mmr and self.mmr:
            reranked = self.mmr.rerank(query, unique_results, k=k)
        elif self.use_reranking and self.cross_encoder:
            doc_texts = [r['content'] for r in unique_results]
            reranked_scores = self.cross_encoder.rerank(query, doc_texts, top_k=k)
            # Map scores back to documents
            reranked = []
            for doc, score in reranked_scores:
                for r in unique_results:
                    if r['content'] == doc:
                        r['rerank_score'] = score
                        reranked.append(r)
                        break
        else:
            reranked = unique_results[:k]
        
        # Step 5: Cache results
        if self.cache:
            self.cache.set(query, k, reranked)
        
        return reranked
    
    def _vector_search(
        self, 
        query: str, 
        k: int
    ) -> List[Dict[str, Any]]:
        """Basic vector search using ChromaDB."""
        query_embedding = self.embedding_model.encode([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k
        )
        
        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return documents
    
    def _deduplicate_results(
        self, 
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on ID."""
        seen_ids = set()
        unique = []
        
        for r in results:
            if r['id'] not in seen_ids:
                seen_ids.add(r['id'])
                unique.append(r)
        
        return unique


# =============================================================================
# MAIN - DEMONSTRATION
# =============================================================================

def main():
    """
    Main function demonstrating all retrieval techniques.
    """
    print("=" * 60)
    print("Retrieval Techniques - Hands-on Exercise")
    print("=" * 60)
    
    # Initialize embedding model
    print("\n1. Loading embedding model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("   Embedding model loaded successfully!")
    
    # Setup ChromaDB
    print("\n2. Setting up ChromaDB...")
    chroma_client = setup_chromadb("tech_docs")
    print("   ChromaDB setup complete!")
    
    # Add documents
    print("\n3. Adding documents to ChromaDB...")
    add_documents_to_chromadb(chroma_client, SAMPLE_DOCUMENTS, embedding_model)
    print(f"   Added {len(SAMPLE_DOCUMENTS)} documents!")
    
    # Initialize advanced retriever
    print("\n4. Initializing Advanced Retriever...")
    retriever = AdvancedRetriever(
        chroma_client=chroma_client,
        embedding_model=embedding_model,
        use_hybrid=True,
        use_reranking=True,
        use_mmr=False,
        use_cache=True
    )
    print("   Advanced retriever ready!")
    
    # Test queries
    test_queries = [
        "python programming",
        "machine learning and neural networks",
        "web development APIs",
    ]
    
    print("\n" + "=" * 60)
    print("Testing Retrieval Pipeline")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        results = retriever.retrieve(query, k=3)
        
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.get('id', 'N/A')}")
            print(f"   Score: {doc.get('distance', doc.get('rerank_score', 'N/A'))}")
            print(f"   Content: {doc.get('content', '')[:100]}...")
    
    print("\n" + "=" * 60)
    print("Exercise Complete!")
    print("=" * 60)
    print("""
Next Steps:
1. Implement each exercise function
2. Test with different configurations
3. Compare results between techniques
4. Explore hybrid combinations
""")


if __name__ == "__main__":
    main()
