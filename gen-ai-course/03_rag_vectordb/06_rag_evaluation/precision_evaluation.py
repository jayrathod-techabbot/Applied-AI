"""
Precision@K Evaluation Script
===============================
This script demonstrates precision at K retrieval metric for RAG systems.
Precision@K measures the fraction of retrieved documents that are relevant.

Formula: Precision@K = (# of relevant docs retrieved) / K
"""

import math
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Document:
    """Represents a document with content and metadata."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class QueryResult:
    """Represents the result of a query with retrieved documents."""
    query: str
    retrieved_docs: List[Document]
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    similarity_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Results of retrieval evaluation."""
    metric_name: str
    score: float
    k_value: int
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Mock Vector Database Implementation
# =============================================================================

class MockVectorDatabase:
    """
    Simulates a vector database for testing retrieval scenarios.
    Uses cosine similarity calculations for document retrieval.
    """
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.embeddings: Dict[str, List[float]] = {}
    
    def add_document(self, doc: Document, embedding: List[float]):
        """Add a document with its embedding to the database."""
        self.documents[doc.id] = doc
        self.embeddings[doc.id] = embedding
    
    def search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents using cosine similarity.
        
        Args:
            query_embedding: Embedding vector for the query
            k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score to consider
            
        Returns:
            List of (Document, similarity_score) tuples
        """
        similarities = []
        
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            
            if similarity >= similarity_threshold:
                similarities.append((self.documents[doc_id], similarity))
        
        # Sort by similarity (descending) and take top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]
    
    def _cosine_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


# =============================================================================
# Embedding Model (Mocking nomic-embed-text:latest)
# =============================================================================

class EmbeddingModel:
    """
    Mock embedding model that simulates nomic-embed-text:latest behavior.
    In production, this would connect to the actual model.
    """
    
    def __init__(self):
        # Predefined embeddings for common terms
        self.term_embeddings = {
            "python": [0.9, 0.1, 0.2],
            "programming": [0.85, 0.15, 0.25],
            "language": [0.8, 0.2, 0.3],
            "machine": [0.3, 0.8, 0.1],
            "learning": [0.25, 0.85, 0.15],
            "ai": [0.2, 0.9, 0.1],
            "neural": [0.15, 0.7, 0.8],
            "network": [0.2, 0.65, 0.75],
            "data": [0.4, 0.4, 0.6],
            "science": [0.35, 0.45, 0.55],
            "web": [0.7, 0.3, 0.4],
            "development": [0.65, 0.35, 0.45],
            "database": [0.5, 0.5, 0.3],
            "sql": [0.55, 0.45, 0.35],
            "cloud": [0.3, 0.3, 0.8],
            "container": [0.25, 0.35, 0.85],
        }
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query text."""
        words = text.lower().split()
        embedding = [0.0] * 3
        
        for word in words:
            if word in self.term_embeddings:
                term_emb = self.term_embeddings[word]
                for i in range(len(embedding)):
                    embedding[i] += term_emb[i]
        
        # Normalize
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def embed_documents(self, documents: List[Document]) -> Dict[str, List[float]]:
        """Generate embeddings for documents."""
        embeddings = {}
        
        for doc in documents:
            embeddings[doc.id] = self._embed_text(doc.content)
        
        return embeddings
    
    def _embed_text(self, text: str) -> List[float]:
        """Generate embedding for any text."""
        words = text.lower().split()
        embedding = [0.0] * 3
        
        for word in words:
            if word in self.term_embeddings:
                term_emb = self.term_embeddings[word]
                for i in range(len(embedding)):
                    embedding[i] += term_emb[i]
            else:
                # Random-like embedding for unknown words
                embedding[0] += 0.1
                embedding[1] += 0.1
                embedding[2] += 0.1
        
        # Normalize
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding


# =============================================================================
# LLM Generator (Mocking llama3.1:8b)
# =============================================================================

class LLMGenerator:
    """
    Mock LLM generator that simulates llama3.1:8b behavior.
    In production, this would connect to the actual model.
    """
    
    def __init__(self):
        self.responses = {
            "python": "Python is a high-level programming language known for its readability and simplicity.",
            "machine learning": "Machine learning enables systems to learn from data without explicit programming.",
            "neural networks": "Neural networks are computing systems inspired by biological neural networks.",
        }
    
    def generate(self, prompt: str, context: List[str]) -> str:
        """Generate a response based on prompt and context documents."""
        # Simple keyword-based response generation
        prompt_lower = prompt.lower()
        
        for key, response in self.responses.items():
            if key in prompt_lower:
                return response
        
        return "Based on the retrieved context: " + " ".join(context[:2])


# =============================================================================
# Sample Test Dataset with Ground Truth Relevance
# =============================================================================

def create_sample_dataset() -> Tuple[MockVectorDatabase, List[QueryResult]]:
    """
    Create a sample test dataset with ground truth relevance labels.
    
    Returns:
        Tuple of (vector_db, query_results with ground truth)
    """
    
    # Create sample documents
    documents = [
        Document(
            id="doc1",
            content="Python is a high-level programming language known for its readability and simplicity.",
            metadata={"category": "programming", "is_relevant": True}
        ),
        Document(
            id="doc2",
            content="JavaScript is a programming language used for web development.",
            metadata={"category": "programming", "is_relevant": False}
        ),
        Document(
            id="doc3",
            content="Machine learning enables systems to learn from data without explicit programming.",
            metadata={"category": "ai_ml", "is_relevant": True}
        ),
        Document(
            id="doc4",
            content="The weather today is sunny with a chance of rain in the evening.",
            metadata={"category": "weather", "is_relevant": False}
        ),
        Document(
            id="doc5",
            content="Neural networks are computing systems inspired by biological neural networks.",
            metadata={"category": "ai_ml", "is_relevant": True}
        ),
        Document(
            id="doc6",
            content="SQL is a domain-specific language used for managing relational databases.",
            metadata={"category": "databases", "is_relevant": False}
        ),
        Document(
            id="doc7",
            content="Deep learning is a subset of machine learning using neural networks with multiple layers.",
            metadata={"category": "ai_ml", "is_relevant": True}
        ),
        Document(
            id="doc8",
            content="Docker is a platform for developing applications in containers.",
            metadata={"category": "devops", "is_relevant": False}
        ),
        Document(
            id="doc9",
            content="TensorFlow is an open-source machine learning framework.",
            metadata={"category": "ai_ml", "is_relevant": True}
        ),
        Document(
            id="doc10",
            content="React is a JavaScript library for building user interfaces.",
            metadata={"category": "web_development", "is_relevant": False}
        ),
    ]
    
    # Create vector database
    vector_db = MockVectorDatabase()
    embedding_model = EmbeddingModel()
    
    # Add documents to database
    for doc in documents:
        embedding = embedding_model._embed_text(doc.content)
        vector_db.add_document(doc, embedding)
    
    # Create query results with ground truth
    query_results = [
        QueryResult(
            query="What is Python?",
            retrieved_docs=[
                documents[0],  # doc1 - relevant (Python)
                documents[1],  # doc2 - not relevant
                documents[5],  # doc6 - not relevant
            ],
            relevance_scores={"doc1": 1.0, "doc2": 0.0, "doc6": 0.0},
            similarity_scores={"doc1": 0.95, "doc2": 0.6, "doc6": 0.3}
        ),
        QueryResult(
            query="Tell me about machine learning",
            retrieved_docs=[
                documents[2],  # doc3 - relevant
                documents[4],  # doc5 - relevant
                documents[6],  # doc7 - relevant
            ],
            relevance_scores={"doc3": 1.0, "doc5": 0.9, "doc7": 0.85},
            similarity_scores={"doc3": 0.92, "doc5": 0.88, "doc7": 0.85}
        ),
        QueryResult(
            query="What is the weather?",
            retrieved_docs=[
                documents[3],  # doc4 - relevant (weather)
                documents[0],  # doc1 - not relevant
                documents[1],  # doc2 - not relevant
            ],
            relevance_scores={"doc4": 1.0, "doc1": 0.0, "doc2": 0.0},
            similarity_scores={"doc4": 0.9, "doc1": 0.3, "doc2": 0.25}
        ),
        QueryResult(
            query="Tell me about neural networks",
            retrieved_docs=[
                documents[4],  # doc5 - relevant
                documents[6],  # doc7 - relevant (mentions neural networks)
                documents[2],  # doc3 - partially relevant
            ],
            relevance_scores={"doc5": 1.0, "doc7": 0.8, "doc3": 0.5},
            similarity_scores={"doc5": 0.9, "doc7": 0.85, "doc3": 0.6}
        ),
        QueryResult(
            query="What is deep learning?",
            retrieved_docs=[
                documents[6],  # doc7 - relevant
                documents[2],  # doc3 - relevant
                documents[9],  # doc10 - not relevant
            ],
            relevance_scores={"doc7": 1.0, "doc3": 0.7, "doc10": 0.0},
            similarity_scores={"doc7": 0.88, "doc3": 0.65, "doc10": 0.2}
        ),
    ]
    
    return vector_db, query_results


# =============================================================================
# Precision@K Metric Implementation
# =============================================================================

def precision_at_k(
    retrieved_docs: List[Document],
    relevant_docs: List[str],
    k: int = None
) -> float:
    """
    Calculate Precision@K.
    
    Precision@K = (# of relevant docs retrieved) / K
    
    Args:
        retrieved_docs: List of documents retrieved by the system
        relevant_docs: List of relevant document IDs (ground truth)
        k: Number of top documents to consider (default: len(retrieved_docs))
        
    Returns:
        Precision score between 0 and 1
    """
    if k is None:
        k = len(retrieved_docs)
    
    if k == 0:
        return 0.0
    
    retrieved_ids = [doc.id for doc in retrieved_docs[:k]]
    relevant_set = set(relevant_docs)
    
    relevant_retrieved = len([doc_id for doc_id in retrieved_ids if doc_id in relevant_set])
    
    return relevant_retrieved / k


def calculate_precision_metrics(
    query_results: List[QueryResult],
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, EvaluationResult]:
    """
    Calculate precision at multiple K values.
    
    Args:
        query_results: List of query results with ground truth
        k_values: List of K values to evaluate
        
    Returns:
        Dictionary mapping metric names to evaluation results
    """
    results = {}
    
    for k in k_values:
        precisions = []
        
        for qr in query_results:
            # Get ground truth relevant documents
            relevant_docs = [
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            ]
            
            # Calculate precision at K
            p_at_k = precision_at_k(qr.retrieved_docs, relevant_docs, k)
            precisions.append(p_at_k)
        
        # Calculate mean precision at K
        mean_precision = sum(precisions) / len(precisions) if precisions else 0.0
        
        results[f"precision_at_{k}"] = EvaluationResult(
            metric_name=f"Precision@{k}",
            score=mean_precision,
            k_value=k,
            details={
                "individual_scores": precisions,
                "num_queries": len(query_results)
            }
        )
    
    return results


# =============================================================================
# Demonstration of Similarity Scoring Threshold Impact
# =============================================================================

def demonstrate_threshold_impact(
    query_results: List[QueryResult],
    thresholds: List[float] = [0.0, 0.3, 0.5, 0.7, 0.9]
) -> Dict[str, Any]:
    """
    Demonstrate how different similarity thresholds affect precision.
    
    Higher thresholds may increase precision but reduce recall.
    """
    results = {}
    
    for threshold in thresholds:
        precisions = []
        
        for qr in query_results:
            # Filter documents by similarity threshold
            filtered_docs = [
                doc for doc, score in zip(qr.retrieved_docs, qr.similarity_scores.values())
                if score >= threshold
            ]
            
            # Get ground truth relevant documents
            relevant_docs = [
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            ]
            
            if filtered_docs:
                p_at_k = precision_at_k(filtered_docs, relevant_docs)
                precisions.append(p_at_k)
        
        avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
        
        results[f"threshold_{threshold}"] = {
            "threshold": threshold,
            "mean_precision": avg_precision,
            "num_queries_evaluated": len(precisions)
        }
    
    return results


# =============================================================================
# Demonstration of Chunk Size Impact
# =============================================================================

def demonstrate_chunk_size_impact() -> Dict[str, Any]:
    """
    Demonstrate how different chunk sizes affect retrieval precision.
    
    Smaller chunks may miss context, larger chunks may include noise.
    """
    chunk_sizes = [100, 200, 500, 1000]
    results = {}
    
    # Simulated precision values for different chunk sizes
    # In real scenarios, this would involve actual retrieval experiments
    simulated_precisions = {
        100: 0.72,   # Smaller chunks may miss context
        200: 0.78,   # Good balance
        500: 0.75,   # May include some noise
        1000: 0.68   # Larger chunks include more irrelevant content
    }
    
    for chunk_size in chunk_sizes:
        results[f"chunk_size_{chunk_size}"] = {
            "chunk_size": chunk_size,
            "precision": simulated_precisions[chunk_size],
            "analysis": _analyze_chunk_size(chunk_size, simulated_precisions[chunk_size])
        }
    
    return results


def _analyze_chunk_size(chunk_size: int, precision: float) -> str:
    """Analyze the trade-offs of a specific chunk size."""
    if chunk_size < 200:
        return "Smaller chunks may miss important context but reduce noise"
    elif chunk_size < 500:
        return "Moderate chunk size provides good balance between context and noise"
    else:
        return "Larger chunks include more context but may introduce noise"


# =============================================================================
# Demonstration of Top-K Selection Impact
# =============================================================================

def demonstrate_topk_selection_impact(
    query_results: List[QueryResult]
) -> Dict[str, Any]:
    """
    Demonstrate how different K values affect precision.
    
    Lower K = fewer documents retrieved = potentially higher precision
    """
    k_values = [1, 2, 3, 5, 10]
    results = {}
    
    for k in k_values:
        precisions = []
        
        for qr in query_results:
            relevant_docs = [
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            ]
            
            p_at_k = precision_at_k(qr.retrieved_docs, relevant_docs, k)
            precisions.append(p_at_k)
        
        avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
        
        results[f"k_{k}"] = {
            "k": k,
            "mean_precision": avg_precision,
            "analysis": _analyze_k_value(k, avg_precision)
        }
    
    return results


def _analyze_k_value(k: int, precision: float) -> str:
    """Analyze the trade-offs of a specific K value."""
    if k == 1:
        return "Only top document retrieved - highest precision if correct"
    elif k < 5:
        return "Few documents - good precision with some context"
    else:
        return "More documents - lower precision but more context available"


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution function demonstrating precision evaluation."""
    
    print("=" * 70)
    print("PRECISION@K EVALUATION SCRIPT")
    print("=" * 70)
    print()
    
    # Create sample dataset
    vector_db, query_results = create_sample_dataset()
    
    print(f"Created Mock Vector Database with {len(vector_db.documents)} documents")
    print(f"Created {len(query_results)} query results for evaluation")
    print()
    
    # Calculate precision metrics at different K values
    print("-" * 70)
    print("PRECISION@K METRICS")
    print("-" * 70)
    
    precision_results = calculate_precision_metrics(query_results)
    
    for metric_name, result in precision_results.items():
        print(f"\n{result.metric_name}:")
        print(f"  Score: {result.score:.4f}")
        print(f"  K Value: {result.k_value}")
        print(f"  Queries Evaluated: {result.details['num_queries']}")
        print(f"  Individual Scores: {[f'{s:.2f}' for s in result.details['individual_scores']]}")
    
    print()
    
    # Demonstrate similarity threshold impact
    print("-" * 70)
    print("SIMILARITY THRESHOLD IMPACT ON PRECISION")
    print("-" * 70)
    
    threshold_results = demonstrate_threshold_impact(query_results)
    
    for key, result in threshold_results.items():
        print(f"\nThreshold {result['threshold']:.1f}:")
        print(f"  Mean Precision: {result['mean_precision']:.4f}")
        print(f"  Queries Evaluated: {result['num_queries_evaluated']}")
    
    print()
    
    # Demonstrate chunk size impact
    print("-" * 70)
    print("CHUNK SIZE IMPACT ON PRECISION")
    print("-" * 70)
    
    chunk_results = demonstrate_chunk_size_impact()
    
    for key, result in chunk_results.items():
        print(f"\nChunk Size {result['chunk_size']}:")
        print(f"  Precision: {result['precision']:.4f}")
        print(f"  Analysis: {result['analysis']}")
    
    print()
    
    # Demonstrate top-K selection impact
    print("-" * 70)
    print("TOP-K SELECTION IMPACT ON PRECISION")
    print("-" * 70)
    
    topk_results = demonstrate_topk_selection_impact(query_results)
    
    for key, result in topk_results.items():
        print(f"\nK = {result['k']}:")
        print(f"  Mean Precision: {result['mean_precision']:.4f}")
        print(f"  Analysis: {result['analysis']}")
    
    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    
    return {
        "precision_metrics": precision_results,
        "threshold_impact": threshold_results,
        "chunk_size_impact": chunk_results,
        "topk_selection_impact": topk_results
    }


if __name__ == "__main__":
    results = main()
