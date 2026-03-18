# Exercise: Implement RAG Evaluation Metrics

## Objective

Implement key retrieval metrics for evaluating RAG systems, including:
- Precision@K
- Recall@K  
- Mean Reciprocal Rank (MRR)
- Average Precision (AP)

## Background

Evaluating RAG systems requires measuring both retrieval and generation quality. This exercise focuses on implementing core retrieval metrics that assess how well the system finds relevant documents.

## Tasks

1. **Implement `precision_at_k()`**: Calculate the fraction of retrieved documents that are relevant
2. **Implement `recall_at_k()`**: Calculate the fraction of relevant documents that were retrieved
3. **Implement `mean_reciprocal_rank()`**: Calculate the average of reciprocal ranks of first relevant documents
4. **Implement `average_precision()`**: Calculate precision at each relevant document position

## Input Format

- `retrieved_docs`: List of Document objects (ordered by relevance)
- `relevant_doc_ids`: List of document IDs that are actually relevant

## Expected Output

Each function should return a float between 0 and 1.

## Example

```python
retrieved = [doc1, doc2, doc3]  # doc1 and doc3 are relevant
relevant = ["doc1", "doc3"]

precision_at_k(retrieved, relevant, k=3)  # Returns 0.67 (2/3)
recall_at_k(retrieved, relevant, k=3)      # Returns 1.0 (all relevant retrieved)
```

## References

- See `concepts.md` for detailed metric definitions
- See `solution.py` for implementation hints
