# Production Issues - Quiz

## Test Your Knowledge

### Question 1

What is the primary purpose of a circuit breaker pattern in RAG systems?

A) To speed up vector database queries
B) To prevent cascading failures from external service outages
C) To improve embedding quality
D) To reduce LLM costs

### Question 2

Which metric would you use to measure if the generated answer is supported by the retrieved context?

A) Precision@K
B) MRR
C) Faithfulness
D) Recall@K

### Question 3

In the DEBUG framework for debugging, what does the "E" stand for?

A) Execute
B) Examine
C) Error
D) Evaluate

### Question 4

What is the main advantage of hybrid search over pure vector search?

A) It's faster
B) It combines keyword and semantic matching
C) It uses less memory
D) It's easier to implement

### Question 5

Which component in a RAG pipeline is most likely to cause latency spikes?

A) Document storage
B) LLM generation
C) Text chunking
D) Metadata indexing

### Question 6

What is the purpose of the Maximal Marginal Relevance (MMR) reranking approach?

A) To maximize precision
B) To balance relevance with diversity in results
C) To minimize computational cost
D) To improve recall

### Question 7

What type of caching would help most with repeated queries in a RAG system?

A) CPU cache
B) Response cache
C) GPU cache
D) Network cache

### Question 8

Which evaluation metric is best for measuring if relevant documents appear early in results?

A) Precision@K
B) Recall@K
C) NDCG
D) MRR

### Question 9

What is a hallucination in the context of RAG generation?

A) A vector database error
B) Generated content not grounded in the retrieved context
C) An embedding vector with all zeros
D) A retrieval timeout

### Question 10

What should be the first step when debugging poor retrieval quality?

A) Change the LLM
B) Check the embedding model and query preprocessing
C) Increase the number of documents retrieved
D) Add more data sources

---

## Answers

1. **B** - Circuit breakers prevent cascading failures by stopping requests to failing services
2. **C** - Faithfulness measures if the answer is supported by the retrieved context
3. **B** - DEBUG stands for Define, Examine, Break down, Understand, Apply, Prove
4. **B** - Hybrid search combines keyword (BM25) and semantic (vector) search
5. **B** - LLM generation is typically the slowest component
6. **B** - MMR balances relevance with diversity to avoid redundant results
7. **B** - Response caching avoids recomputation for repeated queries
8. **C** - NDCG specifically measures ranking quality with graded relevance
9. **B** - Hallucinations are generated content not supported by the context
10. **B** - Always check embeddings and preprocessing first when debugging retrieval
