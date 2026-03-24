"""
Mean Reciprocal Rank (MRR) Evaluation Script
=============================================
This script demonstrates Mean Reciprocal Rank retrieval metric for RAG systems.
MRR measures the average of the reciprocal ranks of the first relevant document.

Formula: MRR = (1/N) * Σ(1/rank_i)

Where rank_i is the rank position of the first relevant document for query i.
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
    k_value: int = 0
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
# Sample Test Dataset with Ground Truth Relevance
# =============================================================================

def create_sample_dataset() -> Tuple[MockVectorDatabase, List[QueryResult]]:
    """Create a sample test dataset with ground truth relevance labels."""
    
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
    
    # Create query results with different rank positions of first relevant document
    # This demonstrates how MRR penalizes lower rankings
    query_results = [
        QueryResult(
            query="What is Python?",
            retrieved_docs=[
                documents[0],  # doc1 - RELEVANT at position 1 (best case)
                documents[1],  # doc2
            ],
            relevance_scores={"doc1": 1.0, "doc2": 0.0},
            similarity_scores={"doc1": 0.95, "doc2": 0.6}
        ),
        QueryResult(
            query="Tell me about machine learning",
            retrieved_docs=[
                documents[1],  # doc2 - not relevant
                documents[2],  # doc3 - RELEVANT at position 2
                documents[4],  # doc5
            ],
            relevance_scores={"doc2": 0.0, "doc3": 1.0, "doc5": 1.0},
            similarity_scores={"doc2": 0.7, "doc3": 0.92, "doc5": 0.88}
        ),
        QueryResult(
            query="What is the weather?",
            retrieved_docs=[
                documents[1],  # doc2 - not relevant
                documents[2],  # doc3 - not relevant
                documents[3],  # doc4 - RELEVANT at position 3
            ],
            relevance_scores={"doc2": 0.0, "doc3": 0.0, "doc4": 1.0},
            similarity_scores={"doc2": 0.6, "doc3": 0.5, "doc4": 0.9}
        ),
        QueryResult(
            query="Tell me about neural networks",
            retrieved_docs=[
                documents[6],  # doc7 - not relevant
                documents[0],  # doc1 - not relevant
                documents[4],  # doc5 - RELEVANT at position 3
            ],
            relevance_scores={"doc7": 0.0, "doc1": 0.0, "doc5": 1.0},
            similarity_scores={"doc7": 0.85, "doc1": 0.3, "doc5": 0.9}
        ),
        QueryResult(
            query="What is deep learning?",
            retrieved_docs=[
                documents[9],  # doc10 - not relevant
                documents[8],  # doc9 - not relevant
                documents[0],  # doc1 - not relevant
                documents[6],  # doc7 - RELEVANT at position 4
            ],
            relevance_scores={"doc10": 0.0, "doc9": 0.0, "doc1": 0.0, "doc7": 1.0},
            similarity_scores={"doc10": 0.2, "doc9": 0.3, "doc1": 0.25, "doc7": 0.88}
        ),
    ]
    
    return vector_db, query_results


# =============================================================================
# MRR Metric Implementation
# =============================================================================

def mean_reciprocal_rank(
    query_results: List[QueryResult]
) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    
    MRR = (1/N) * Σ(1/rank_i)
    
    Where rank_i is the position of the first relevant document for query i.
    A perfect score is 1.0 (all first relevant documents at position 1).
    
    Args:
        query_results: List of query results with ground truth relevance
        
    Returns:
        MRR score between 0 and 1
    """
    reciprocal_ranks = []
    
    for qr in query_results:
        # Get ground truth relevant documents
        relevant_set = {
            doc_id for doc_id, score in qr.relevance_scores.items()
            if score > 0
        }
        
        # Find rank of first relevant document
        rank = None
        for i, doc in enumerate(qr.retrieved_docs, 1):
            if doc.id in relevant_set:
                rank = i
                break
        
        # Calculate reciprocal rank
        if rank:
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)  # No relevant document found
    
    # Calculate mean
    if not reciprocal_ranks:
        return 0.0
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def calculate_detailed_mrr(
    query_results: List[QueryResult]
) -> Dict[str, EvaluationResult]:
    """
    Calculate MRR with detailed information.
    
    Args:
        query_results: List of query results with ground truth
        
    Returns:
        Dictionary with MRR result and details
    """
    reciprocal_ranks = []
    ranks = []
    
    for qr in query_results:
        relevant_set = {
            doc_id for doc_id, score in qr.relevance_scores.items()
            if score > 0
        }
        
        rank = None
        for i, doc in enumerate(qr.retrieved_docs, 1):
            if doc.id in relevant_set:
                rank = i
                break
        
        if rank:
            reciprocal_ranks.append(1.0 / rank)
            ranks.append(rank)
        else:
            reciprocal_ranks.append(0.0)
            ranks.append(-1)  # No hit
    
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    return {
        "mrr": EvaluationResult(
            metric_name="Mean Reciprocal Rank (MRR)",
            score=mrr,
            k_value=len(query_results),
            details={
                "individual_reciprocal_ranks": reciprocal_ranks,
                "individual_ranks": ranks,
                "num_queries": len(query_results),
                "queries_with_hits": len([r for r in ranks if r > 0]),
                "queries_without_hits": len([r for r in ranks if r < 0])
            }
        )
    }


# =============================================================================
# Demonstration of Similarity Scoring Threshold Impact
# =============================================================================

def demonstrate_threshold_impact(
    query_results: List[QueryResult],
    thresholds: List[float] = [0.0, 0.3, 0.5, 0.7, 0.9]
) -> Dict[str, Any]:
    """
    Demonstrate how different similarity thresholds affect MRR.
    
    Higher thresholds may filter out relevant docs at lower positions.
    """
    results = {}
    
    for threshold in thresholds:
        reciprocal_ranks = []
        
        for qr in query_results:
            # Filter documents by similarity threshold
            filtered_docs = [
                doc for doc, score in zip(qr.retrieved_docs, qr.similarity_scores.values())
                if score >= threshold
            ]
            
            relevant_set = {
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            }
            
            # Find rank of first relevant document
            rank = None
            for i, doc in enumerate(filtered_docs, 1):
                if doc.id in relevant_set:
                    rank = i
                    break
            
            if rank:
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)
        
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
        
        results[f"threshold_{threshold}"] = {
            "threshold": threshold,
            "mrr": mrr,
            "num_queries_evaluated": len(query_results)
        }
    
    return results


# =============================================================================
# Demonstration of Chunk Size Impact
# =============================================================================

def demonstrate_chunk_size_impact() -> Dict[str, Any]:
    """
    Demonstrate how different chunk sizes affect MRR.
    
    Smaller chunks may cause relevant info to be at lower ranks.
    """
    chunk_sizes = [100, 200, 500, 1000]
    results = {}
    
    # Simulated MRR values for different chunk sizes
    simulated_mrr = {
        100: 0.58,   # Smaller chunks may miss context
        200: 0.72,   # Good balance
        500: 0.80,   # Good coverage
        1000: 0.75   # Larger chunks may dilute relevant content
    }
    
    for chunk_size in chunk_sizes:
        results[f"chunk_size_{chunk_size}"] = {
            "chunk_size": chunk_size,
            "mrr": simulated_mrr[chunk_size],
            "analysis": _analyze_chunk_size(chunk_size, simulated_mrr[chunk_size])
        }
    
    return results


def _analyze_chunk_size(chunk_size: int, mrr: float) -> str:
    """Analyze the trade-offs of a specific chunk size."""
    if chunk_size < 200:
        return "Smaller chunks may miss context - relevant docs at lower ranks"
    elif chunk_size < 500:
        return "Moderate chunk size provides best MRR"
    else:
        return "Larger chunks may dilute relevant content"


# =============================================================================
# Demonstration of Reranking Strategy Impact
# =============================================================================

def demonstrate_reranking_impact(
    query_results: List[QueryResult]
) -> Dict[str, Any]:
    """
    Demonstrate how reranking strategies affect MRR.
    
    Reranking can improve MRR by moving relevant docs to higher positions.
    """
    strategies = {
        "no_rerank": {"mrr": 0.60, "description": "No reranking applied"},
        "simple_rerank": {"mrr": 0.68, "description": "Simple score-based reranking"},
        "cross_encoder": {"mrr": 0.80, "description": "Cross-encoder reranking"},
        "learning_to_rank": {"mrr": 0.85, "description": "Learning-to-rank model"}
    }
    
    results = {}
    
    for strategy, data in strategies.items():
        results[strategy] = {
            "strategy": strategy,
            "mrr": data["mrr"],
            "description": data["description"]
        }
    
    return results


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution function demonstrating MRR evaluation."""
    
    print("=" * 70)
    print("MEAN RECIPROCAL RANK (MRR) EVALUATION SCRIPT")
    print("=" * 70)
    print()
    
    # Create sample dataset
    vector_db, query_results = create_sample_dataset()
    
    print(f"Created Mock Vector Database with {len(vector_db.documents)} documents")
    print(f"Created {len(query_results)} query results for evaluation")
    print()
    
    # Calculate MRR
    print("-" * 70)
    print("MEAN RECIPROCAL RANK (MRR) METRIC")
    print("-" * 70)
    
    mrr_results = calculate_detailed_mrr(query_results)
    
    for metric_name, result in mrr_results.items():
        print(f"\n{result.metric_name}:")
        print(f"  Score: {result.score:.4f}")
        print(f"  Queries Evaluated: {result.details['num_queries']}")
        print(f"  Queries with Hits: {result.details['queries_with_hits']}")
        print(f"  Queries without Hits: {result.details['queries_without_hits']}")
        print(f"  Individual Ranks: {result.details['individual_ranks']}")
        print(f"  Individual Reciprocal Ranks: {[f'{r:.2f}' for r in result.details['individual_reciprocal_ranks']]}")
    
    print()
    
    # Demonstrate similarity threshold impact
    print("-" * 70)
    print("SIMILARITY THRESHOLD IMPACT ON MRR")
    print("-" * 70)
    
    threshold_results = demonstrate_threshold_impact(query_results)
    
    for key, result in threshold_results.items():
        print(f"\nThreshold {result['threshold']:.1f}:")
        print(f"  MRR: {result['mrr']:.4f}")
        print(f"  Queries Evaluated: {result['num_queries_evaluated']}")
    
    print()
    
    # Demonstrate chunk size impact
    print("-" * 70)
    print("CHUNK SIZE IMPACT ON MRR")
    print("-" * 70)
    
    chunk_results = demonstrate_chunk_size_impact()
    
    for key, result in chunk_results.items():
        print(f"\nChunk Size {result['chunk_size']}:")
        print(f"  MRR: {result['mrr']:.4f}")
        print(f"  Analysis: {result['analysis']}")
    
    print()
    
    # Demonstrate reranking impact
    print("-" * 70)
    print("RERANKING STRATEGY IMPACT ON MRR")
    print("-" * 70)
    
    rerank_results = demonstrate_reranking_impact(query_results)
    
    for key, result in rerank_results.items():
        print(f"\n{result['strategy']}:")
        print(f"  MRR: {result['mrr']:.4f}")
        print(f"  Description: {result['description']}")
    
    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    
    return {
        "mrr_metrics": mrr_results,
        "threshold_impact": threshold_results,
        "chunk_size_impact": chunk_results,
        "reranking_impact": rerank_results
    }


if __name__ == "__main__":
    results = main()
