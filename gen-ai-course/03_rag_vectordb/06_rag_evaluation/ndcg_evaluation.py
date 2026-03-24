"""
Normalized Discounted Cumulative Gain (NDCG) Evaluation Script
================================================================
This script demonstrates NDCG retrieval metric for RAG systems.
NDCG measures ranking quality considering graded relevance.

Formula: 
  DCG = Σ(2^rel_i - 1) / log2(i + 1)  for i = 1 to K
  NDCG = DCG / IDCG

Where rel_i is the relevance score of document at position i.
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
    """Simulates a vector database for testing retrieval scenarios."""
    
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
        """Search for similar documents using cosine similarity."""
        similarities = []
        
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            
            if similarity >= similarity_threshold:
                similarities.append((self.documents[doc_id], similarity))
        
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
    """Mock embedding model that simulates nomic-embed-text:latest behavior."""
    
    def __init__(self):
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
                embedding[0] += 0.1
                embedding[1] += 0.1
                embedding[2] += 0.1
        
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding


# =============================================================================
# LLM Generator (Mocking llama3.1:8b)
# =============================================================================

class LLMGenerator:
    """Mock LLM generator that simulates llama3.1:8b behavior."""
    
    def __init__(self):
        self.responses = {
            "python": "Python is a high-level programming language known for its readability and simplicity.",
            "machine learning": "Machine learning enables systems to learn from data without explicit programming.",
            "neural networks": "Neural networks are computing systems inspired by biological neural networks.",
        }
    
    def generate(self, prompt: str, context: List[str]) -> str:
        """Generate a response based on prompt and context documents."""
        prompt_lower = prompt.lower()
        
        for key, response in self.responses.items():
            if key in prompt_lower:
                return response
        
        return "Based on the retrieved context: " + " ".join(context[:2])


# =============================================================================
# Sample Test Dataset with Graded Relevance
# =============================================================================

def create_sample_dataset() -> Tuple[MockVectorDatabase, List[QueryResult]]:
    """
    Create a sample test dataset with graded relevance scores.
    
    Unlike binary relevance, NDCG uses graded relevance (0.0 to 1.0)
    to measure how well highly relevant documents are ranked.
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
    
    # Create query results with GRADED relevance scores
    # This is critical for NDCG - it uses continuous relevance scores
    query_results = [
        QueryResult(
            query="What is Python?",
            retrieved_docs=[
                documents[0],  # doc1 - highly relevant
                documents[1],  # doc2 - not relevant
                documents[5],  # doc6 - not relevant
            ],
            # Graded relevance: 1.0 = most relevant, 0.0 = not relevant
            relevance_scores={"doc1": 1.0, "doc2": 0.0, "doc6": 0.0},
            similarity_scores={"doc1": 0.95, "doc2": 0.6, "doc6": 0.3}
        ),
        QueryResult(
            query="Tell me about machine learning",
            retrieved_docs=[
                documents[2],  # doc3 - highly relevant
                documents[4],  # doc5 - relevant
                documents[6],  # doc7 - relevant
            ],
            # Graded relevance - different levels of relevance
            relevance_scores={"doc3": 1.0, "doc5": 0.8, "doc7": 0.6},
            similarity_scores={"doc3": 0.92, "doc5": 0.88, "doc7": 0.85}
        ),
        QueryResult(
            query="What is the weather?",
            retrieved_docs=[
                documents[3],  # doc4 - relevant
                documents[0],  # doc1 - not relevant
                documents[1],  # doc2 - not relevant
            ],
            relevance_scores={"doc4": 1.0, "doc1": 0.0, "doc2": 0.0},
            similarity_scores={"doc4": 0.9, "doc1": 0.3, "doc2": 0.25}
        ),
        QueryResult(
            query="Tell me about neural networks",
            retrieved_docs=[
                documents[4],  # doc5 - highly relevant
                documents[6],  # doc7 - relevant
                documents[2],  # doc3 - partially relevant
            ],
            relevance_scores={"doc5": 1.0, "doc7": 0.7, "doc3": 0.4},
            similarity_scores={"doc5": 0.9, "doc7": 0.85, "doc3": 0.6}
        ),
        QueryResult(
            query="What is deep learning?",
            retrieved_docs=[
                documents[6],  # doc7 - highly relevant
                documents[2],  # doc3 - relevant
                documents[9],  # doc10 - not relevant
            ],
            relevance_scores={"doc7": 1.0, "doc3": 0.9, "doc10": 0.0},
            similarity_scores={"doc7": 0.88, "doc3": 0.65, "doc10": 0.2}
        ),
    ]
    
    return vector_db, query_results


# =============================================================================
# NDCG Metric Implementation
# =============================================================================

def dcg_at_k(scores: List[float], k: int = None) -> float:
    """
    Calculate Discounted Cumulative Gain (DCG) at K.
    
    DCG = Σ(2^rel_i - 1) / log2(i + 1) for i = 1 to K
    
    Args:
        scores: List of relevance scores for retrieved documents
        k: Number of top documents to consider
        
    Returns:
        DCG score
    """
    if k is None:
        k = len(scores)
    else:
        k = min(k, len(scores))
    
    dcg = 0.0
    for i, rel in enumerate(scores[:k], 1):
        # Use the graded relevance directly
        dcg += (2 ** rel - 1) / math.log2(i + 1)
    
    return dcg


def ndcg_at_k(
    retrieved_docs: List[Document],
    relevance_scores: Dict[str, float],
    k: int = None
) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG) at K.
    
    NDCG = DCG / IDCG
    
    IDCG is the DCG of an ideal ranking (documents sorted by relevance descending).
    A perfect NDCG is 1.0.
    
    Args:
        retrieved_docs: List of documents retrieved by the system
        relevance_scores: Dictionary of document IDs to relevance scores
        k: Number of top documents to consider
        
    Returns:
        NDCG score between 0 and 1
    """
    if k is None:
        k = len(retrieved_docs)
    
    # Get relevance scores for retrieved documents
    retrieved_scores = [
        relevance_scores.get(doc.id, 0.0) 
        for doc in retrieved_docs[:k]
    ]
    
    # Calculate DCG
    dcg = dcg_at_k(retrieved_scores, k)
    
    # Calculate IDCG (Ideal DCG)
    # Sort all relevance scores in descending order
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = dcg_at_k(ideal_scores, k)
    
    # Handle edge case
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def calculate_ndcg_metrics(
    query_results: List[QueryResult],
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, EvaluationResult]:
    """
    Calculate NDCG at multiple K values.
    
    Args:
        query_results: List of query results with graded relevance
        k_values: List of K values to evaluate
        
    Returns:
        Dictionary mapping metric names to evaluation results
    """
    results = {}
    
    for k in k_values:
        ndcg_scores = []
        
        for qr in query_results:
            # Calculate NDCG at K
            ndcg = ndcg_at_k(qr.retrieved_docs, qr.relevance_scores, k)
            ndcg_scores.append(ndcg)
        
        # Calculate mean NDCG at K
        mean_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
        
        results[f"ndcg_at_{k}"] = EvaluationResult(
            metric_name=f"NDCG@{k}",
            score=mean_ndcg,
            k_value=k,
            details={
                "individual_scores": ndcg_scores,
                "num_queries": len(query_results)
            }
        )
    
    return results


# =============================================================================
# Alternative NDCG Implementations
# =============================================================================

def ndcg_at_k_binary(
    retrieved_docs: List[Document],
    relevant_docs: List[str],
    k: int = None
) -> float:
    """
    Calculate NDCG using binary relevance (1 or 0).
    
    This is a simplified version when only binary relevance is available.
    """
    if k is None:
        k = len(retrieved_docs)
    
    relevance_scores = {
        doc.id: 1.0 if doc.id in relevant_docs else 0.0
        for doc in retrieved_docs[:k]
    }
    
    return ndcg_at_k(retrieved_docs, relevance_scores, k)


def average_ndcg(
    query_results: List[QueryResult],
    k: int = 10
) -> float:
    """
    Calculate average NDCG across all queries at a given K.
    
    This is often called "Mean NDCG" (or just NDCG).
    """
    ndcg_scores = []
    
    for qr in query_results:
        ndcg = ndcg_at_k(qr.retrieved_docs, qr.relevance_scores, k)
        ndcg_scores.append(ndcg)
    
    return sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0


# =============================================================================
# Demonstration of Similarity Scoring Threshold Impact
# =============================================================================

def demonstrate_threshold_impact(
    query_results: List[QueryResult],
    thresholds: List[float] = [0.0, 0.3, 0.5, 0.7, 0.9]
) -> Dict[str, Any]:
    """
    Demonstrate how different similarity thresholds affect NDCG.
    """
    results = {}
    
    for threshold in thresholds:
        ndcg_scores = []
        
        for qr in query_results:
            filtered_docs = [
                doc for doc, score in zip(qr.retrieved_docs, qr.similarity_scores.values())
                if score >= threshold
            ]
            
            if filtered_docs:
                ndcg = ndcg_at_k(filtered_docs, qr.relevance_scores)
                ndcg_scores.append(ndcg)
        
        avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
        
        results[f"threshold_{threshold}"] = {
            "threshold": threshold,
            "mean_ndcg": avg_ndcg,
            "num_queries_evaluated": len(ndcg_scores)
        }
    
    return results


# =============================================================================
# Demonstration of Chunk Size Impact
# =============================================================================

def demonstrate_chunk_size_impact() -> Dict[str, Any]:
    """
    Demonstrate how different chunk sizes affect NDCG.
    """
    chunk_sizes = [100, 200, 500, 1000]
    results = {}
    
    # Simulated NDCG values for different chunk sizes
    simulated_ndcg = {
        100: 0.62,
        200: 0.75,
        500: 0.78,
        1000: 0.70
    }
    
    for chunk_size in chunk_sizes:
        results[f"chunk_size_{chunk_size}"] = {
            "chunk_size": chunk_size,
            "ndcg": simulated_ndcg[chunk_size],
            "analysis": _analyze_chunk_size(chunk_size, simulated_ndcg[chunk_size])
        }
    
    return results


def _analyze_chunk_size(chunk_size: int, ndcg: float) -> str:
    """Analyze the trade-offs of a specific chunk size."""
    if chunk_size < 200:
        return "Smaller chunks may miss context - affects ranking quality"
    elif chunk_size < 500:
        return "Moderate chunk size provides best NDCG"
    else:
        return "Larger chunks may dilute relevant content in rankings"


# =============================================================================
# Demonstration of Reranking Strategy Impact
# =============================================================================

def demonstrate_reranking_impact(
    query_results: List[QueryResult]
) -> Dict[str, Any]:
    """
    Demonstrate how reranking strategies affect NDCG.
    
    NDCG is particularly sensitive to reranking because it measures
    the quality of document ranking.
    """
    strategies = {
        "no_rerank": {"ndcg": 0.65, "description": "No reranking applied"},
        "simple_rerank": {"ndcg": 0.72, "description": "Simple score-based reranking"},
        "cross_encoder": {"ndcg": 0.82, "description": "Cross-encoder reranking"},
        "learning_to_rank": {"ndcg": 0.88, "description": "Learning-to-rank model"}
    }
    
    results = {}
    
    for strategy, data in strategies.items():
        results[strategy] = {
            "strategy": strategy,
            "ndcg": data["ndcg"],
            "description": data["description"]
        }
    
    return results


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution function demonstrating NDCG evaluation."""
    
    print("=" * 70)
    print("NORMALIZED DISCOUNTED CUMULATIVE GAIN (NDCG) EVALUATION SCRIPT")
    print("=" * 70)
    print()
    
    # Create sample dataset
    vector_db, query_results = create_sample_dataset()
    
    print(f"Created Mock Vector Database with {len(vector_db.documents)} documents")
    print(f"Created {len(query_results)} query results for evaluation")
    print("Note: Using GRADED relevance scores (0.0 to 1.0)")
    print()
    
    # Calculate NDCG metrics at different K values
    print("-" * 70)
    print("NDCG METRICS")
    print("-" * 70)
    
    ndcg_results = calculate_ndcg_metrics(query_results)
    
    for metric_name, result in ndcg_results.items():
        print(f"\n{result.metric_name}:")
        print(f"  Score: {result.score:.4f}")
        print(f"  K Value: {result.k_value}")
        print(f"  Queries Evaluated: {result.details['num_queries']}")
        print(f"  Individual Scores: {[f'{s:.2f}' for s in result.details['individual_scores']]}")
    
    print()
    
    # Calculate average NDCG at K=10
    avg_ndcg = average_ndcg(query_results, k=10)
    print(f"Average NDCG@10: {avg_ndcg:.4f}")
    print()
    
    # Demonstrate similarity threshold impact
    print("-" * 70)
    print("SIMILARITY THRESHOLD IMPACT ON NDCG")
    print("-" * 70)
    
    threshold_results = demonstrate_threshold_impact(query_results)
    
    for key, result in threshold_results.items():
        print(f"\nThreshold {result['threshold']:.1f}:")
        print(f"  Mean NDCG: {result['mean_ndcg']:.4f}")
        print(f"  Queries Evaluated: {result['num_queries_evaluated']}")
    
    print()
    
    # Demonstrate chunk size impact
    print("-" * 70)
    print("CHUNK SIZE IMPACT ON NDCG")
    print("-" * 70)
    
    chunk_results = demonstrate_chunk_size_impact()
    
    for key, result in chunk_results.items():
        print(f"\nChunk Size {result['chunk_size']}:")
        print(f"  NDCG: {result['ndcg']:.4f}")
        print(f"  Analysis: {result['analysis']}")
    
    print()
    
    # Demonstrate reranking impact
    print("-" * 70)
    print("RERANKING STRATEGY IMPACT ON NDCG")
    print("-" * 70)
    
    rerank_results = demonstrate_reranking_impact(query_results)
    
    for key, result in rerank_results.items():
        print(f"\n{result['strategy']}:")
        print(f"  NDCG: {result['ndcg']:.4f}")
        print(f"  Description: {result['description']}")
    
    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    
    return {
        "ndcg_metrics": ndcg_results,
        "threshold_impact": threshold_results,
        "chunk_size_impact": chunk_results,
        "reranking_impact": rerank_results
    }


if __name__ == "__main__":
    results = main()
