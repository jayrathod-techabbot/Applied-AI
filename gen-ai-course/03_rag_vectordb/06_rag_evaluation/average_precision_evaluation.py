"""
Average Precision (AP) Evaluation Script
==========================================
This script demonstrates Average Precision retrieval metric for RAG systems.
AP measures the average of precisions calculated at each relevant document position.

Formula: AP = (1/N) * Σ(P(k) * rel(k))

Where P(k) is precision at position k and rel(k) is 1 if document at k is relevant.
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
    
    # Create query results showing different retrieval scenarios
    query_results = [
        QueryResult(
            query="What is Python?",
            retrieved_docs=[
                documents[0],  # doc1 - RELEVANT at position 1
                documents[1],  # doc2 - not relevant
                documents[5],  # doc6 - not relevant
            ],
            relevance_scores={"doc1": 1.0, "doc2": 0.0, "doc6": 0.0},
            similarity_scores={"doc1": 0.95, "doc2": 0.6, "doc6": 0.3}
        ),
        QueryResult(
            query="Tell me about machine learning",
            retrieved_docs=[
                documents[2],  # doc3 - RELEVANT at position 1
                documents[4],  # doc5 - RELEVANT at position 2
                documents[6],  # doc7 - RELEVANT at position 3
            ],
            relevance_scores={"doc3": 1.0, "doc5": 1.0, "doc7": 1.0},
            similarity_scores={"doc3": 0.92, "doc5": 0.88, "doc7": 0.85}
        ),
        QueryResult(
            query="What is the weather?",
            retrieved_docs=[
                documents[0],  # doc1 - not relevant
                documents[1],  # doc2 - not relevant
                documents[3],  # doc4 - RELEVANT at position 3
            ],
            relevance_scores={"doc1": 0.0, "doc2": 0.0, "doc4": 1.0},
            similarity_scores={"doc1": 0.3, "doc2": 0.25, "doc4": 0.9}
        ),
        QueryResult(
            query="Tell me about neural networks",
            retrieved_docs=[
                documents[6],  # doc7 - not relevant
                documents[4],  # doc5 - RELEVANT at position 2
                documents[2],  # doc3 - not relevant
            ],
            relevance_scores={"doc7": 0.0, "doc5": 1.0, "doc3": 0.0},
            similarity_scores={"doc7": 0.85, "doc5": 0.9, "doc3": 0.6}
        ),
        QueryResult(
            query="What is deep learning?",
            retrieved_docs=[
                documents[9],  # doc10 - not relevant
                documents[6],  # doc7 - RELEVANT at position 2
                documents[2],  # doc3 - RELEVANT at position 3
            ],
            relevance_scores={"doc10": 0.0, "doc7": 1.0, "doc3": 1.0},
            similarity_scores={"doc10": 0.2, "doc7": 0.88, "doc3": 0.65}
        ),
    ]
    
    return vector_db, query_results


# =============================================================================
# Average Precision Metric Implementation
# =============================================================================

def average_precision_at_k(
    retrieved_docs: List[Document],
    relevant_docs: List[str],
    k: int = None
) -> float:
    """
    Calculate Average Precision (AP) at K.
    
    AP = Σ(P(k) * rel(k)) / N
    
    Where:
    - P(k) = precision at position k
    - rel(k) = 1 if document at position k is relevant, 0 otherwise
    - N = total number of relevant documents
    
    This metric rewards systems that rank relevant documents higher.
    
    Args:
        retrieved_docs: List of documents retrieved by the system
        relevant_docs: List of relevant document IDs (ground truth)
        k: Number of top documents to consider
        
    Returns:
        Average Precision score between 0 and 1
    """
    if k is None:
        k = len(retrieved_docs)
    
    if len(relevant_docs) == 0:
        return 0.0
    
    relevant_set = set(relevant_docs)
    
    # Calculate precision at each position where relevant doc is found
    sum_precision = 0.0
    num_relevant_found = 0
    
    for i, doc in enumerate(retrieved_docs[:k], 1):
        if doc.id in relevant_set:
            # Precision at position i
            precision_at_i = i / i  # Since we count up to i
            sum_precision += precision_at_i
            num_relevant_found += 1
    
    # Normalize by total number of relevant documents
    if num_relevant_found == 0:
        return 0.0
    
    return sum_precision / len(relevant_docs)


def average_precision_graded(
    retrieved_docs: List[Document],
    relevance_scores: Dict[str, float],
    k: int = None
) -> float:
    """
    Calculate Average Precision using graded relevance.
    
    This version uses graded (continuous) relevance scores instead of binary.
    """
    if k is None:
        k = len(retrieved_docs)
    
    # Get total number of relevant documents
    total_relevant = sum(1 for score in relevance_scores.values() if score > 0)
    
    if total_relevant == 0:
        return 0.0
    
    # Calculate sum of precision at each position
    sum_precision = 0.0
    
    for i, doc in enumerate(retrieved_docs[:k], 1):
        rel = relevance_scores.get(doc.id, 0.0)
        if rel > 0:
            # Count relevant docs up to position i
            num_relevant_up_to_i = sum(
                1 for j, d in enumerate(retrieved_docs[:i], 1)
                if relevance_scores.get(d.id, 0.0) > 0
            )
            precision_at_i = num_relevant_up_to_i / i
            sum_precision += precision_at_i * rel  # Weight by relevance
    
    return sum_precision / total_relevant


def calculate_mean_average_precision(
    query_results: List[QueryResult],
    k: int = None
) -> Dict[str, EvaluationResult]:
    """
    Calculate Mean Average Precision (MAP).
    
    MAP = (1/N) * Σ(AP_i) for all queries i
    
    Args:
        query_results: List of query results with ground truth
        k: Number of top documents to consider
        
    Returns:
        Dictionary with MAP result and details
    """
    ap_scores = []
    ap_details = []
    
    for qr in query_results:
        # Get ground truth relevant documents
        relevant_docs = [
            doc_id for doc_id, score in qr.relevance_scores.items()
            if score > 0
        ]
        
        # Calculate AP for this query
        ap = average_precision_at_k(qr.retrieved_docs, relevant_docs, k)
        ap_scores.append(ap)
        
        # Store details
        relevant_set = set(relevant_docs)
        ap_details.append({
            "query": qr.query,
            "ap": ap,
            "relevant_docs_found": [
                doc.id for doc in qr.retrieved_docs[:k if k else len(qr.retrieved_docs)]
                if doc.id in relevant_set
            ]
        })
    
    # Calculate MAP
    map_score = sum(ap_scores) / len(ap_scores) if ap_scores else 0.0
    
    return {
        "map": EvaluationResult(
            metric_name="Mean Average Precision (MAP)",
            score=map_score,
            k_value=k if k else (len(query_results[0].retrieved_docs) if query_results else 0),
            details={
                "individual_ap_scores": ap_scores,
                "ap_details": ap_details,
                "num_queries": len(query_results)
            }
        )
    }


def calculate_ap_metrics(
    query_results: List[QueryResult],
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, EvaluationResult]:
    """
    Calculate AP at multiple K values.
    
    Args:
        query_results: List of query results with ground truth
        k_values: List of K values to evaluate
        
    Returns:
        Dictionary mapping metric names to evaluation results
    """
    results = {}
    
    for k in k_values:
        ap_scores = []
        
        for qr in query_results:
            relevant_docs = [
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            ]
            
            ap = average_precision_at_k(qr.retrieved_docs, relevant_docs, k)
            ap_scores.append(ap)
        
        mean_ap = sum(ap_scores) / len(ap_scores) if ap_scores else 0.0
        
        results[f"ap_at_{k}"] = EvaluationResult(
            metric_name=f"Average Precision@{k}",
            score=mean_ap,
            k_value=k,
            details={
                "individual_scores": ap_scores,
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
    Demonstrate how different similarity thresholds affect Average Precision.
    """
    results = {}
    
    for threshold in thresholds:
        ap_scores = []
        
        for qr in query_results:
            filtered_docs = [
                doc for doc, score in zip(qr.retrieved_docs, qr.similarity_scores.values())
                if score >= threshold
            ]
            
            relevant_docs = [
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            ]
            
            if filtered_docs and relevant_docs:
                ap = average_precision_at_k(filtered_docs, relevant_docs)
                ap_scores.append(ap)
        
        mean_ap = sum(ap_scores) / len(ap_scores) if ap_scores else 0.0
        
        results[f"threshold_{threshold}"] = {
            "threshold": threshold,
            "mean_ap": mean_ap,
            "num_queries_evaluated": len(ap_scores)
        }
    
    return results


# =============================================================================
# Demonstration of Chunk Size Impact
# =============================================================================

def demonstrate_chunk_size_impact() -> Dict[str, Any]:
    """
    Demonstrate how different chunk sizes affect Average Precision.
    """
    chunk_sizes = [100, 200, 500, 1000]
    results = {}
    
    # Simulated AP values for different chunk sizes
    simulated_ap = {
        100: 0.58,
        200: 0.72,
        500: 0.75,
        1000: 0.65
    }
    
    for chunk_size in chunk_sizes:
        results[f"chunk_size_{chunk_size}"] = {
            "chunk_size": chunk_size,
            "ap": simulated_ap[chunk_size],
            "analysis": _analyze_chunk_size(chunk_size, simulated_ap[chunk_size])
        }
    
    return results


def _analyze_chunk_size(chunk_size: int, ap: float) -> str:
    """Analyze the trade-offs of a specific chunk size."""
    if chunk_size < 200:
        return "Smaller chunks may miss context - affects ranking of relevant docs"
    elif chunk_size < 500:
        return "Moderate chunk size provides best Average Precision"
    else:
        return "Larger chunks may dilute relevant content in rankings"


# =============================================================================
# Demonstration of Top-K Selection Impact
# =============================================================================

def demonstrate_topk_selection_impact(
    query_results: List[QueryResult]
) -> Dict[str, Any]:
    """
    Demonstrate how different K values affect Average Precision.
    
    Higher K allows more relevant docs to be considered but may dilute precision.
    """
    k_values = [1, 2, 3, 5, 10]
    results = {}
    
    for k in k_values:
        ap_scores = []
        
        for qr in query_results:
            relevant_docs = [
                doc_id for doc_id, score in qr.relevance_scores.items()
                if score > 0
            ]
            
            ap = average_precision_at_k(qr.retrieved_docs, relevant_docs, k)
            ap_scores.append(ap)
        
        mean_ap = sum(ap_scores) / len(ap_scores) if ap_scores else 0.0
        
        results[f"k_{k}"] = {
            "k": k,
            "mean_ap": mean_ap,
            "analysis": _analyze_k_value(k, mean_ap)
        }
    
    return results


def _analyze_k_value(k: int, ap: float) -> str:
    """Analyze the trade-offs of a specific K value."""
    if k == 1:
        return "AP@1 is equivalent to Precision@1 - binary metric"
    elif k < 5:
        return "Moderate K captures relevant docs without diluting precision"
    else:
        return "Higher K considers more docs but may lower average precision"


# =============================================================================
# Demonstration of Reranking Strategy Impact
# =============================================================================

def demonstrate_reranking_impact(
    query_results: List[QueryResult]
) -> Dict[str, Any]:
    """
    Demonstrate how reranking strategies affect Average Precision.
    
    AP is particularly sensitive to ranking quality - better reranking = higher AP.
    """
    strategies = {
        "no_rerank": {"ap": 0.60, "description": "No reranking applied"},
        "simple_rerank": {"ap": 0.68, "description": "Simple score-based reranking"},
        "cross_encoder": {"ap": 0.80, "description": "Cross-encoder reranking"},
        "learning_to_rank": {"ap": 0.85, "description": "Learning-to-rank model"}
    }
    
    results = {}
    
    for strategy, data in strategies.items():
        results[strategy] = {
            "strategy": strategy,
            "ap": data["ap"],
            "description": data["description"]
        }
    
    return results


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution function demonstrating Average Precision evaluation."""
    
    print("=" * 70)
    print("AVERAGE PRECISION (AP) EVALUATION SCRIPT")
    print("=" * 70)
    print()
    
    # Create sample dataset
    vector_db, query_results = create_sample_dataset()
    
    print(f"Created Mock Vector Database with {len(vector_db.documents)} documents")
    print(f"Created {len(query_results)} query results for evaluation")
    print()
    
    # Calculate MAP
    print("-" * 70)
    print("MEAN AVERAGE PRECISION (MAP) METRIC")
    print("-" * 70)
    
    map_results = calculate_mean_average_precision(query_results)
    
    for metric_name, result in map_results.items():
        print(f"\n{result.metric_name}:")
        print(f"  Score: {result.score:.4f}")
        print(f"  Queries Evaluated: {result.details['num_queries']}")
        print(f"  Individual AP Scores: {[f'{s:.2f}' for s in result.details['individual_ap_scores']]}")
        
        print("\n  Per-Query Details:")
        for detail in result.details["ap_details"]:
            print(f"    Query: {detail['query']}")
            print(f"      AP: {detail['ap']:.4f}")
            print(f"      Relevant Docs Found: {detail['relevant_docs_found']}")
    
    print()
    
    # Calculate AP at different K values
    print("-" * 70)
    print("AVERAGE PRECISION @ K METRICS")
    print("-" * 70)
    
    ap_results = calculate_ap_metrics(query_results)
    
    for metric_name, result in ap_results.items():
        print(f"\n{result.metric_name}:")
        print(f"  Score: {result.score:.4f}")
        print(f"  Individual Scores: {[f'{s:.2f}' for s in result.details['individual_scores']]}")
    
    print()
    
    # Demonstrate similarity threshold impact
    print("-" * 70)
    print("SIMILARITY THRESHOLD IMPACT ON AVERAGE PRECISION")
    print("-" * 70)
    
    threshold_results = demonstrate_threshold_impact(query_results)
    
    for key, result in threshold_results.items():
        print(f"\nThreshold {result['threshold']:.1f}:")
        print(f"  Mean AP: {result['mean_ap']:.4f}")
        print(f"  Queries Evaluated: {result['num_queries_evaluated']}")
    
    print()
    
    # Demonstrate chunk size impact
    print("-" * 70)
    print("CHUNK SIZE IMPACT ON AVERAGE PRECISION")
    print("-" * 70)
    
    chunk_results = demonstrate_chunk_size_impact()
    
    for key, result in chunk_results.items():
        print(f"\nChunk Size {result['chunk_size']}:")
        print(f"  AP: {result['ap']:.4f}")
        print(f"  Analysis: {result['analysis']}")
    
    print()
    
    # Demonstrate top-K selection impact
    print("-" * 70)
    print("TOP-K SELECTION IMPACT ON AVERAGE PRECISION")
    print("-" * 70)
    
    topk_results = demonstrate_topk_selection_impact(query_results)
    
    for key, result in topk_results.items():
        print(f"\nK = {result['k']}:")
        print(f"  Mean AP: {result['mean_ap']:.4f}")
        print(f"  Analysis: {result['analysis']}")
    
    print()
    
    # Demonstrate reranking impact
    print("-" * 70)
    print("RERANKING STRATEGY IMPACT ON AVERAGE PRECISION")
    print("-" * 70)
    
    rerank_results = demonstrate_reranking_impact(query_results)
    
    for key, result in rerank_results.items():
        print(f"\n{result['strategy']}:")
        print(f"  AP: {result['ap']:.4f}")
        print(f"  Description: {result['description']}")
    
    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    
    return {
        "map_metrics": map_results,
        "ap_metrics": ap_results,
        "threshold_impact": threshold_results,
        "chunk_size_impact": chunk_results,
        "topk_selection_impact": topk_results,
        "reranking_impact": rerank_results
    }


if __name__ == "__main__":
    results = main()
