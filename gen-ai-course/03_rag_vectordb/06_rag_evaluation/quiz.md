# Quiz: RAG Evaluation

## Retrieval Metrics

### Question 1
What is Precision@K?

- [ ] A) The fraction of relevant documents retrieved out of total relevant documents
- [ ] B) The fraction of retrieved documents that are relevant
- [ ] C) The average rank of the first relevant document
- [ ] D) The ranking quality considering graded relevance

### Question 2
What does Recall@K measure?

- [ ] A) How many of the retrieved documents are relevant
- [ ] B) What percentage of relevant documents were successfully retrieved
- [ ] C) The position of the first relevant document
- [ ] D) How well the answer uses retrieved context

### Question 3
Mean Reciprocal Rank (MRR) focuses on:

- [ ] A) The average precision across all relevant documents
- [ ] B) The rank position of the first relevant document
- [ ] C) The total number of relevant documents retrieved
- [ ] D) The quality of document ranking

### Question 4
NDCG (Normalized Discounted Cumulative Gain) is different from Precision because:

- [ ] A) It only considers binary relevance
- [ ] B] It considers graded relevance and position in rankings
- [ ] C) It doesn't require relevance scores
- [ ] D) It's faster to calculate

## Generation Metrics

### Question 5
What does Faithfulness measure in RAG evaluation?

- [ ] A) How relevant the answer is to the question
- [ ] B) Whether the answer uses only information from the retrieved context
- [ ] C) How coherent the answer is
- [ ] D) The length of the generated answer

### Question 6
Answer Relevance is typically calculated using:

- [ ] A) BLEU scores
- [ ] B] Embedding similarity between question and answer
- [ ] C) Word overlap metrics
- [ ] D) Token counts

## Evaluation Frameworks

### Question 7
Which framework is specifically designed for RAG evaluation?

- [ ] A) BERTscore
- [ ] B] RAGAs
- [ ] C)ROUGE
- [ ] D) spaCy

### Question 8
What is the purpose of continuous evaluation in RAG systems?

- [ ] A] To evaluate once during development
- [ ] B] To monitor performance over time in production
- [ ] C] To replace human evaluation
- [ ] D] To reduce computational costs

## Answers

1. **B** - Precision@K = (# relevant docs retrieved) / K
2. **B** - Recall@K = (# relevant docs retrieved) / (total relevant docs)
3. **B** - MRR uses the reciprocal of the first relevant document's rank
4. **B** - NDCG considers graded relevance and penalizes lower-position relevant docs
5. **B** - Faithfulness checks if claims in the answer are supported by context
6. **B** - Answer relevance uses embedding similarity (e.g., cosine similarity)
7. **B** - RAGAs is specifically designed for evaluating RAG systems
8. **B** - Continuous evaluation monitors production performance over time
