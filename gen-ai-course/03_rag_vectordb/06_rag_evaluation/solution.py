"""
RAG Evaluation - Solution Code

This is the solution for the RAG Evaluation exercise, implementing
retrieval metrics for RAG systems.
"""

from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass


# ============================================================================
# Document and Query Classes (same as exercise)
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
# Sample Test Data (same as exercise)
# ============================================================================

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
# SOLUTION: Implementation of Retrieval Metrics
# ============================================================================


def precision_at_k(
    retrieved_docs: List[Document], relevant_doc_ids: List[str], k: Optional[int] = None
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
    """
    if not retrieved_docs:
        return 0.0

    # Use k if provided, otherwise use all retrieved docs
    k = k if k is not None else len(retrieved_docs)

    # Get IDs of retrieved documents (up to k)
    retrieved_ids = [doc.id for doc in retrieved_docs[:k]]

    # Create set of relevant document IDs
    relevant_set = set(relevant_doc_ids)

    # Count relevant documents retrieved
    relevant_retrieved = sum(1 for doc_id in retrieved_ids if doc_id in relevant_set)

    # Calculate precision
    return relevant_retrieved / k


def recall_at_k(
    retrieved_docs: List[Document], relevant_doc_ids: List[str], k: Optional[int] = None
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
    """
    if not retrieved_docs or not relevant_doc_ids:
        return 0.0

    # Use k if provided, otherwise use all retrieved docs
    k = k if k is not None else len(retrieved_docs)

    # Get IDs of retrieved documents (up to k)
    retrieved_ids = [doc.id for doc in retrieved_docs[:k]]

    # Create set of relevant document IDs
    relevant_set = set(relevant_doc_ids)

    # Count relevant documents retrieved
    relevant_retrieved = sum(1 for doc_id in retrieved_ids if doc_id in relevant_set)

    # Calculate recall
    return relevant_retrieved / len(relevant_set)


def mean_reciprocal_rank(query_results: List[QueryResult]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).

    MRR = (1/N) * Σ(1/rank_i)

    Where rank_i is the rank of the first relevant document for query i.

    Args:
        query_results: List of QueryResult objects

    Returns:
        MRR score between 0 and 1
    """
    if not query_results:
        return 0.0

    reciprocal_ranks = []

    for result in query_results:
        # Find the rank of the first relevant document
        rank = None
        for i, doc in enumerate(result.retrieved_docs, 1):
            is_relevant = doc.metadata.get("is_relevant", False)
            if is_relevant:
                rank = i
                break

        # Calculate reciprocal rank
        if rank is not None:
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    # Calculate mean
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def average_precision(
    retrieved_docs: List[Document], relevant_doc_ids: List[str]
) -> float:
    """
    Calculate Average Precision (AP).

    AP = Σ(precision at each relevant doc position) / (# of relevant docs)

    Args:
        retrieved_docs: List of retrieved documents in order
        relevant_doc_ids: Set/list of relevant document IDs

    Returns:
        Average precision score
    """
    if not retrieved_docs or not relevant_doc_ids:
        return 0.0

    relevant_set = set(relevant_doc_ids)
    num_relevant = len(relevant_set)

    if num_relevant == 0:
        return 0.0

    precisions_sum = 0.0
    relevant_count = 0

    for i, doc in enumerate(retrieved_docs, 1):
        if doc.id in relevant_set:
            # Calculate precision at this position
            relevant_count += 1
            prec_at_i = relevant_count / i
            precisions_sum += prec_at_i

    return precisions_sum / num_relevant


def ndcg_at_k(
    retrieved_docs: List[Document], relevance_scores: Dict[str, float], k: int = 10
) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG)@K.

    NDCG = DCG / IDCG

    Args:
        retrieved_docs: List of retrieved documents in ranking order
        relevance_scores: Dictionary mapping doc_id to relevance score
        k: Number of documents to consider

    Returns:
        NDCG score between 0 and 1
    """

    def dcg(scores: List[float]) -> float:
        """Calculate DCG."""
        return sum((2**rel - 1) / (i + 1) ** 0.5 for i, rel in enumerate(scores))

    # Get relevance scores for retrieved docs
    retrieved_scores = [relevance_scores.get(doc.id, 0.0) for doc in retrieved_docs[:k]]

    # Calculate DCG
    dcg_value = dcg(retrieved_scores)

    # Calculate IDCG (ideal DCG)
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg_value = dcg(ideal_scores)

    return dcg_value / idcg_value if idcg_value > 0 else 0.0


# ============================================================================
# Evaluation Runner
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
        relevant_ids = all_relevant

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
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RAG Evaluation - Retrieval Metrics Solution")
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
    print(f"  Precision@3: {precision:.4f}")  # Expected: 1/3 = 0.333

    # Test recall_at_k
    recall = recall_at_k(test_retrieved, test_relevant, k=3)
    print(f"  Recall@3: {recall:.4f}")  # Expected: 1/3 = 0.333 (1 out of 3 relevant)

    # Test with more relevant docs
    test_retrieved_2 = [SAMPLE_DOCUMENTS[0], SAMPLE_DOCUMENTS[2], SAMPLE_DOCUMENTS[4]]
    precision_2 = precision_at_k(test_retrieved_2, test_relevant, k=3)
    print(f"  Precision@3 (all relevant): {precision_2:.4f}")  # Expected: 3/3 = 1.0

    # Test NDCG
    test_relevance = {"doc1": 1.0, "doc2": 0.0, "doc3": 0.8, "doc4": 0.5, "doc5": 0.3}
    ndcg = ndcg_at_k(test_retrieved_2, test_relevance, k=3)
    print(f"  NDCG@3: {ndcg:.4f}")

    print("\n--- All Tests Complete! ---")
