"""
Retrieval Techniques - Solutions
=================================

Complete implementations for all exercises using ChromaDB and open-source libraries.
"""

import os
import json
import hashlib
import pickle
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from collections import OrderedDict

# Third-party imports
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

# For LLM-based rewriting
try:
    from sentence_transformers import CrossEncoder
except ImportError:
    pass


# =============================================================================
# SAMPLE DATA
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
# SOLUTION 1: Setup ChromaDB
# =============================================================================

def setup_chromadb(collection_name: str = "tech_docs") -> chromadb.Client:
    """
    Setup ChromaDB client with a collection.
    """
    # Create persistent ChromaDB client
    client = chromadb.Client(Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    ))
    
    # Delete existing collection if exists
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Tech documentation collection"}
    )
    
    return client


def add_documents_to_chromadb(
    client: chromadb.Client, 
    documents: List[Dict[str, Any]],
    embedding_model: SentenceTransformer
) -> None:
    """
    Add documents to ChromaDB collection.
    """
    collection = client.get_collection("tech_docs")
    
    # Extract data
    ids = [doc["id"] for doc in documents]
    texts = [doc["content"] for doc in documents]
    metadatas = [
        {"category": doc.get("category", ""), "source": doc.get("source", "")}
        for doc in documents
    ]
    
    # Generate embeddings
    embeddings = embedding_model.encode(texts).tolist()
    
    # Add to ChromaDB
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )


# =============================================================================
# SOLUTION 2: Query Rewriting
# =============================================================================

class SynonymExpander:
    """Expand queries with synonyms and related terms."""
    
    def __init__(self):
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
            'db': ['database', 'databases'],
            'ml': ['machine learning'],
            'ai': ['artificial intelligence'],
            'deep': ['deep learning'],
        }
    
    def expand(self, query: str) -> List[str]:
        """Expand query with synonyms."""
        words = query.lower().split()
        expanded = [query]  # Keep original
        
        for i, word in enumerate(words):
            if word in self.synonym_dict:
                for synonym in self.synonym_dict[word]:
                    # Replace word with synonym
                    new_words = words.copy()
                    new_words[i] = synonym
                    expanded.append(' '.join(new_words))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_expanded = []
        for q in expanded:
            if q not in seen:
                seen.add(q)
                unique_expanded.append(q)
        
        return unique_expanded


class HyDERetriever:
    """HyDE (Hypothetical Document Embeddings) Retriever."""
    
    def __init__(
        self, 
        chroma_client: chromadb.Client,
        embedding_model: SentenceTransformer,
        llm_generator=None
    ):
        self.chroma_client = chroma_client
        self.embedding_model = embedding_model
        self.llm_generator = llm_generator
        self.collection = chroma_client.get_collection("tech_docs")
    
    def _generate_hypothetical(self, query: str) -> str:
        """Generate a hypothetical document that would answer the query."""
        # Template-based generation
        hypothetical = f"""This document provides comprehensive information about {query}. 
        It covers the fundamentals, key concepts, practical applications, 
        and best practices. The content includes detailed explanations, 
        examples, and implementation guidance for developers."""
        
        return hypothetical
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve documents using HyDE approach."""
        # Step 1: Generate hypothetical document
        hypothetical_doc = self._generate_hypothetical(query)
        
        # Step 2: Embed the hypothetical document
        hypo_embedding = self.embedding_model.encode([hypothetical_doc])[0]
        
        # Step 3: Search using the hypothetical embedding
        results = self.collection.query(
            query_embeddings=[hypo_embedding.tolist()],
            n_results=k
        )
        
        # Format results
        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return documents


# =============================================================================
# SOLUTION 3: Reranking
# =============================================================================

class CrossEncoderReranker:
    """Rerank results using a cross-encoder model."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Rerank documents based on query-document relevance."""
        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]
        
        # Get cross-encoder scores
        scores = self.model.predict(pairs)
        
        # Sort by score (descending)
        scored_docs = sorted(
            zip(documents, scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return scored_docs[:top_k]


class MMRReranker:
    """Maximal Marginal Relevance for diverse results."""
    
    def __init__(
        self, 
        embedding_model: SentenceTransformer,
        lambda_mult: float = 0.5
    ):
        self.embedding_model = embedding_model
        self.lambda_mult = lambda_mult
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Rerank documents using MMR to balance relevance and diversity."""
        if not documents:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Encode all documents
        doc_contents = [doc['content'] for doc in documents]
        doc_embeddings = self.embedding_model.encode(doc_contents)
        
        # Calculate relevance scores (cosine similarity)
        relevance_scores = cosine_similarity(
            [query_embedding], doc_embeddings
        )[0]
        
        # MMR selection
        selected = []
        selected_indices = []
        
        for _ in range(min(k, len(documents))):
            best_score = -float('inf')
            best_idx = None
            
            for idx, doc in enumerate(documents):
                if idx in selected_indices:
                    continue
                
                # Relevance component
                rel = relevance_scores[idx]
                
                # Diversity component
                if selected:
                    selected_embs = [doc_embeddings[i] for i in selected_indices]
                    div = max(
                        cosine_similarity([doc_embeddings[idx]], [emb])[0][0]
                        for emb in selected_embs
                    )
                else:
                    div = 0
                
                # MMR score
                mmr_score = self.lambda_mult * rel - (1 - self.lambda_mult) * div
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
            
            if best_idx is not None:
                selected.append(documents[best_idx])
                selected_indices.append(best_idx)
        
        return selected


# =============================================================================
# SOLUTION 4: Hybrid Search
# =============================================================================

class HybridSearch:
    """Combine vector search with keyword search (BM25)."""
    
    def __init__(
        self,
        chroma_client: chromadb.Client,
        embedding_model: SentenceTransformer,
        vector_weight: float = 0.5
    ):
        self.chroma_client = chroma_client
        self.embedding_model = embedding_model
        self.vector_weight = vector_weight
        self.collection = chroma_client.get_collection("tech_docs")
        
        # Initialize BM25 index
        self._init_bm25()
    
    def _init_bm25(self):
        """Initialize BM25 index from ChromaDB documents."""
        # Get all documents from ChromaDB
        results = self.collection.get()
        
        self.doc_ids = results['ids']
        self.documents = results['documents']
        
        # Tokenize documents for BM25
        self.tokenized_docs = [doc.lower().split() for doc in self.documents]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_docs)
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to 0-1 range."""
        if len(scores) == 0:
            return scores
        
        min_score = scores.min()
        max_score = scores.max()
        
        if max_score - min_score == 0:
            return np.ones_like(scores) * 0.5
        
        return (scores - min_score) / (max_score - min_score)
    
    def search(
        self, 
        query: str, 
        k: int = 5,
        alpha: float = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and keyword search."""
        alpha = alpha if alpha is not None else self.vector_weight
        
        # Step 1: Vector search
        query_embedding = self.embedding_model.encode([query])[0]
        vector_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k * 3
        )
        
        # Extract vector scores (convert distance to similarity)
        vector_docs = {}
        for i, doc_id in enumerate(vector_results['ids'][0]):
            distance = vector_results['distances'][0][i]
            # Convert distance to similarity (lower distance = higher similarity)
            vector_docs[doc_id] = 1 / (1 + distance)
        
        # Step 2: BM25 keyword search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Map BM25 scores to documents
        bm25_docs = {}
        for i, doc_id in enumerate(self.doc_ids):
            bm25_docs[doc_id] = bm25_scores[i]
        
        # Step 3: Get all unique document IDs
        all_doc_ids = list(set(vector_docs.keys()) | set(bm25_docs.keys()))
        
        # Step 4: Normalize and combine scores
        combined_scores = {}
        
        for doc_id in all_doc_ids:
            vec_score = vector_docs.get(doc_id, 0)
            bm25_score = bm25_docs.get(doc_id, 0)
            
            # Normalize individual scores
            vec_score_norm = vec_score  # Already in 0-1 range
            bm25_score_norm = bm25_score / (max(bm25_scores) + 1e-10)  # Normalize
            
            # Weighted combination
            combined = alpha * vec_score_norm + (1 - alpha) * bm25_score_norm
            combined_scores[doc_id] = combined
        
        # Step 5: Sort by combined score
        sorted_docs = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Step 6: Build result list
        results = []
        doc_id_to_content = dict(zip(self.doc_ids, self.documents))
        
        for doc_id, score in sorted_docs[:k]:
            results.append({
                'id': doc_id,
                'content': doc_id_to_content[doc_id],
                'score': score,
                'vector_score': vector_docs.get(doc_id, 0),
                'bm25_score': bm25_docs.get(doc_id, 0)
            })
        
        return results


# =============================================================================
# SOLUTION 5: Query Decomposition
# =============================================================================

class QueryDecomposer:
    """Decompose complex queries into simpler sub-queries."""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def decompose(self, query: str) -> List[str]:
        """Decompose a complex query into simpler sub-queries."""
        query = query.lower().strip()
        
        # Common decomposition patterns
        sub_queries = []
        
        # Pattern 1: "X and Y"
        if ' and ' in query:
            parts = query.split(' and ')
            sub_queries.extend([p.strip() for p in parts if p.strip()])
        
        # Pattern 2: "X vs Y" or "X versus Y"
        elif ' vs ' in query or ' versus ' in query:
            if ' vs ' in query:
                parts = query.split(' vs ')
            else:
                parts = query.split(' versus ')
            sub_queries.extend([p.strip() for p in parts if p.strip()])
        
        # Pattern 3: "X, Y, Z" (comma separated)
        elif ',' in query:
            parts = query.split(',')
            sub_queries.extend([p.strip() for p in parts if p.strip()])
        
        # If no pattern matched, return original
        if not sub_queries:
            sub_queries = [query]
        
        # Remove duplicates
        sub_queries = list(dict.fromkeys(sub_queries))
        
        return sub_queries
    
    def retrieve_decomposed(
        self, 
        query: str, 
        retriever: Any, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve documents for decomposed queries and combine results."""
        # Decompose query
        sub_queries = self.decompose(query)
        
        # Retrieve for each sub-query
        all_docs = []
        for sq in sub_queries:
            docs = retriever.retrieve(sq, k=k)
            all_docs.extend(docs)
        
        # Deduplicate based on ID
        seen_ids = set()
        unique_docs = []
        for doc in all_docs:
            if doc['id'] not in seen_ids:
                seen_ids.add(doc['id'])
                unique_docs.append(doc)
        
        # Sort by score (if available)
        if 'distance' in unique_docs[0]:
            unique_docs.sort(key=lambda x: x.get('distance', float('inf')))
        elif 'score' in unique_docs[0]:
            unique_docs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return unique_docs[:k*len(sub_queries)]


# =============================================================================
# SOLUTION 6: Production Considerations
# =============================================================================

class RetrievalCache:
    """Cache retrieval results for performance."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _hash_query(self, query: str, k: int) -> str:
        """Create a hash key for query + k combination."""
        key_string = f"{query}:{k}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, k: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached results for a query."""
        key = self._hash_query(query, k)
        
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, query: str, k: int, results: List[Dict[str, Any]]) -> None:
        """Cache results for a query."""
        key = self._hash_query(query, k)
        
        # If cache is full, remove oldest item
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)
        
        self.cache[key] = results
        # Move to end (most recently used)
        self.cache.move_to_end(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }


class ResilientRetriever:
    """Handle failures gracefully with fallback strategies."""
    
    def __init__(self, retrievers: List[Any]):
        self.retrievers = retrievers
        self.errors = []
    
    def retrieve(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve with fallback to next retriever if one fails."""
        for i, retriever in enumerate(self.retrievers):
            try:
                results = retriever.retrieve(query, k=k)
                if results:
                    return results
            except Exception as e:
                error_msg = f"Retriever {i} failed: {str(e)}"
                self.errors.append(error_msg)
                print(f"Warning: {error_msg}")
                continue
        
        # All retrievers failed
        if self.errors:
            raise RuntimeError(f"All retrievers failed: {self.errors}")
        
        return []


# =============================================================================
# COMPLETE RETRIEVAL PIPELINE
# =============================================================================

class AdvancedRetriever:
    """Complete retrieval pipeline combining all techniques."""
    
    def __init__(
        self,
        chroma_client: chromadb.Client,
        embedding_model: SentenceTransformer,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        use_mmr: bool = False,
        use_cache: bool = True
    ):
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
        """Main retrieval method with multiple enhancement techniques."""
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
    
    def _vector_search(self, query: str, k: int) -> List[Dict[str, Any]]:
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
    """Main function demonstrating all retrieval techniques."""
    print("=" * 60)
    print("Retrieval Techniques - Solution Demonstration")
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
    
    # Test each technique
    print("\n" + "=" * 60)
    print("Testing Individual Techniques")
    print("=" * 60)
    
    # Test Synonym Expansion
    print("\n--- Synonym Expansion ---")
    expander = SynonymExpander()
    expanded = expander.expand("learn python")
    print(f"Original: 'learn python'")
    print(f"Expanded: {expanded}")
    
    # Test HyDE
    print("\n--- HyDE Retrieval ---")
    hyde = HyDERetriever(chroma_client, embedding_model)
    hyde_results = hyde.retrieve("machine learning frameworks", k=3)
    for r in hyde_results:
        print(f"  {r['id']}: {r['content'][:60]}...")
    
    # Test Hybrid Search
    print("\n--- Hybrid Search ---")
    hybrid = HybridSearch(chroma_client, embedding_model, vector_weight=0.5)
    hybrid_results = hybrid.search("python programming", k=3)
    for r in hybrid_results:
        print(f"  {r['id']}: score={r['score']:.4f}")
    
    # Test Cross-Encoder Reranking
    print("\n--- Cross-Encoder Reranking ---")
    reranker = CrossEncoderReranker()
    test_docs = [SAMPLE_DOCUMENTS[0]["content"], SAMPLE_DOCUMENTS[1]["content"]]
    reranked = reranker.rerank("python programming", test_docs, top_k=2)
    for doc, score in reranked:
        print(f"  Score: {score:.4f} - {doc[:60]}...")
    
    # Test Query Decomposition
    print("\n--- Query Decomposition ---")
    decomposer = QueryDecomposer()
    sub_queries = decomposer.decompose("python and machine learning")
    print(f"Original: 'python and machine learning'")
    print(f"Sub-queries: {sub_queries}")
    
    # Test Cache
    print("\n--- Retrieval Cache ---")
    cache = RetrievalCache(max_size=100)
    test_results = [{"id": "1", "content": "test"}]
    cache.set("test query", 5, test_results)
    cached = cache.get("test query", 5)
    print(f"Cache set/get: {cached is not None}")
    print(f"Cache stats: {cache.get_stats()}")
    
    # Test Complete Pipeline
    print("\n" + "=" * 60)
    print("Complete Retrieval Pipeline")
    print("=" * 60)
    
    retriever = AdvancedRetriever(
        chroma_client=chroma_client,
        embedding_model=embedding_model,
        use_hybrid=True,
        use_reranking=True,
        use_cache=True
    )
    
    test_queries = [
        "machine learning",
        "web development",
        "database"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        results = retriever.retrieve(query, k=3)
        
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.get('id', 'N/A')} - {doc.get('content', '')[:50]}...")
    
    print("\n" + "=" * 60)
    print("Solution Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
