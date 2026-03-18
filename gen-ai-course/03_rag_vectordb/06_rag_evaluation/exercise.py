"""
RAG Evaluation - Hands-on Exercise

This exercise covers implementing retrieval metrics for RAG evaluation:
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG)

Estimated Time: 45 minutes
"""

from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass


# ============================================================================
# PART 1: Document and Query Classes
# ============================================================================


@dataclass
class Document:
    """Represents a document with content and metadata."""

    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QueryResult:
    """Represents the result of a query with retrieved documents."""

    query: str
    retrieved_docs: List[Document]
    relevance_scores: Optional[Dict[str, float]] = None


# ============================================================================
# PART 2: Sample Test Data
# ============================================================================

# Sample documents for testing retrieval
SAMPLE_DOCUMENTS = [
    Document(
        id="doc1",
        content="Python is a high-level programming language known for its readability.",
        metadata={"category": "programming", "is_relevant": True},
    ),
    Document(
        id="doc2",
        content="JavaScript is used for web development and runs in browsers.",
        metadata={"category": "programming", "is_relevant": False},
    ),
    Document(
        id="doc3",
        content="Machine learning enables systems to learn from data without explicit programming.",
        metadata={"category": "ai", "is_relevant": True},
    ),
    Document(
        id="doc4",
        content="The weather today is sunny with a chance of rain in the evening.",
        metadata={"category": "weather", "is_relevant": False},
    ),
    Document(
        id="doc5",
        content="Deep learning is a subset of machine learning using neural networks.",
        metadata={"category": "ai", "is_relevant": True},
    ),
]

# Sample query results for evaluation
SAMPLE_QUERY_RESULTS = [
    QueryResult(
        query="What is Python?",
        retrieved_docs=[
            SAMPLE_DOCUMENTS[0],  # doc1 - relevant
            SAMPLE_DOCUMENTS[1],  # doc2 - not relevant
            SAMPLE_DOCUMENTS[2],  # doc3 - not relevant
        ],
        relevance_scores={"doc1": 1.0, "doc2": 0.0, "doc3": 0.0},
    ),
    QueryResult(
        query="Tell me about machine learning",
        retrieved_docs=[
            SAMPLE_DOCUMENTS[2],  # doc3 - relevant
            SAMPLE_DOCUMENTS[4],  # doc5 - relevant
            SAMPLE_DOCUMENTS[0],  # doc1 - not relevant
        ],
        relevance_scores={"doc3": 1.0, "doc5": 0.8, "doc1": 0.0},
    ),
    QueryResult(
        query="What is the weather like?",
        retrieved_docs=[
            SAMPLE_DOCUMENTS[3],  # doc4 - relevant
            SAMPLE_DOCUMENTS[0],  # doc1 - not relevant
            SAMPLE_DOCUMENTS[1],  # doc2 - not relevant
        ],
        relevance_scores={"doc4": 1.0, "doc1": 0.0, "doc2": 0.0},
    ),
]


# ============================================================================
# PART 3: Exercise - Implement Retrieval Metrics
# ============================================================================


def precision_at_k(
    retrieved_docs: List[Document], relevant_doc_ids: List[str], k: int = None
) -> float:
    """
    Calculate Precision@K.

    Precision@K = (# of relevant docs retrieved) / K

    Args:
        retrieved_docs: List of top K documents from retrieval
        relevant_doc_ids: List of actually relevant document IDs
        k: Number of documents to consider (default: len(retrieved_docs))

    Returns:
        Precision score between 0 and 1

    EXERCISE: Implement this function!
    """
    # TODO: Implement precision_at_k
    # Hint:
    # 1. Get the IDs of retrieved documents (up to k)
    # 2. Create a set of relevant document IDs
    # 3. Count how many relevant docs were retrieved
    # 4. Divide by k (or len(retrieved_docs) if k is None)

    pass  # Remove this and implement


def recall_at_k(
    retrieved_docs: List[Document], relevant_doc_ids: List[str], k: int = None
) -> float:
    """
    Calculate Recall@K.

    Recall@K = (# of relevant docs retrieved) / (total # of relevant docs)

    Args:
        retrieved_docs: List of top K documents from retrieval
        relevant_doc_ids: List of actually relevant document IDs
        k: Number of documents to consider (default: len(retrieved_docs))

    Returns:
        Recall score between 0 and 1

    EXERCISE: Implement this function!
    """
    # TODO: Implement recall_at_k
    # Hint:
    # 1. Get the IDs of retrieved documents (up to k)
    # 2. Create a set of relevant document IDs
    # 3. Count how many relevant docs were retrieved
    # 4. Divide by the total number of relevant docs

    pass  # Remove this and implement


def mean_reciprocal_rank(query_results: List[QueryResult]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).

    MRR = (1/N) * Σ(1/rank_i)

    Where rank_i is the rank of the first relevant document for query i.

    Args:
        query_results: List of QueryResult objects

    Returns:
        MRR score between 0 and 1

    EXERCISE: Implement this function!
    """
    # TODO: Implement mean_reciprocal_rank
    # Hint:
    # 1. For each query result, find the rank of the first relevant doc
    # 2. Calculate reciprocal rank (1/rank) if found, else 0
    # 3. Average all reciprocal ranks

    pass  # Remove this and implement


def average_precision(
    retrieved_docs: List[Document], relevant_doc_ids: List[str]
) -> float:
    """
    Calculate Average Precision (AP).

    AP = Σ(precision at each relevant doc position) / (# of relevant docs)

    Args:
        retrieved_docs: List of retrieved documents in order
        relevant_doc_ids: Set of relevant document IDs

    Returns:
        Average precision score

    EXERCISE: Implement this function!
    """
    # TODO: Implement average_precision
    # Hint:
    # 1. For each relevant doc in retrieved_docs, calculate precision up to that point
    # 2. Sum these precisions
    # 3. Divide by total number of relevant docs

    pass  # Remove this and implement


# ============================================================================
# PART 4: Evaluation Runner
# ============================================================================


def evaluate_retrieval(
    query_results: List[QueryResult], k: int = 3
) -> Dict[str, float]:
    """
    Evaluate retrieval system using multiple metrics.

    Args:
        query_results: List of query results to evaluate
        k: Number of documents to consider

    Returns:
        Dictionary with evaluation metrics
    """
    # Extract relevant doc IDs from metadata
    all_relevant = [
        doc.id for doc in SAMPLE_DOCUMENTS if doc.metadata.get("is_relevant")
    ]

    # Calculate metrics
    precisions = []
    recalls = []

    for result in query_results:
        retrieved_ids = [doc.id for doc in result.retrieved_docs[:k]]
        relevant_ids = all_relevant  # In real scenario, would be query-specific

        # For simplicity, using all relevant docs as ground truth
        # In practice, this would be specific to each query

        prec = precision_at_k(result.retrieved_docs, relevant_ids, k)
        rec = recall_at_k(result.retrieved_docs, relevant_ids, k)

        precisions.append(prec)
        recalls.append(rec)

    mrr = mean_reciprocal_rank(query_results)

    return {
        "precision_at_k": sum(precisions) / len(precisions) if precisions else 0,
        "recall_at_k": sum(recalls) / len(recalls) if recalls else 0,
        "mrr": mrr,
    }


# ============================================================================
# PART 5: Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RAG Evaluation - Retrieval Metrics Exercise")
    print("=" * 60)

    print("\n--- Sample Documents ---")
    for doc in SAMPLE_DOCUMENTS:
        print(
            f"  {doc.id}: {doc.content[:50]}... [relevant: {doc.metadata.get('is_relevant')}]"
        )

    print("\n--- Running Evaluation ---")
    results = evaluate_retrieval(SAMPLE_QUERY_RESULTS, k=3)

    print("\n--- Results ---")
    for metric, value in results.items():
        print(f"  {metric}: {value:.4f}")

    print("\n--- Testing Individual Functions ---")

    # Test precision_at_k
    test_retrieved = [SAMPLE_DOCUMENTS[0], SAMPLE_DOCUMENTS[1], SAMPLE_DOCUMENTS[2]]
    test_relevant = ["doc1", "doc3", "doc5"]
    precision = precision_at_k(test_retrieved, test_relevant, k=3)
    print(f"  Precision@3: {precision}")

    # Expected: 1/3 = 0.333 (only doc1 is relevant in top 3)
