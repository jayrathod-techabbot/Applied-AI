# Exercise: Advanced Retrieval Techniques

## Overview

This hands-on exercise covers all retrieval techniques from the concepts.md file using ChromaDB and open-source libraries. You will implement query rewriting, reranking, hybrid search, query decomposition, and production considerations.

## Prerequisites

Install required dependencies:

```bash
pip install chromadb sentence-transformers rank-bm25 numpy scikit-learn
```

## Exercises

### Exercise 1: Setup ChromaDB Vector Store

Implement the following functions to set up ChromaDB with sample documents:

1. **[`setup_chromadb()`](exercise.py:79)** - Create ChromaDB client with persistent storage
2. **[`add_documents_to_chromadb()`](exercise.py:95)** - Add documents with embeddings to ChromaDB

**Expected Output:** A ChromaDB collection containing the tech documentation dataset.

---

### Exercise 2: Query Rewriting

Implement two query rewriting techniques:

#### 2a. Synonym Expansion ([`SynonymExpander.expand()`](exercise.py:140))

- Tokenize the query
- Look up synonyms from the dictionary
- Generate multiple query variations
- Return list of expanded queries

**Test:**
```python
expander = SynonymExpander()
queries = expander.expand("learn python")
print(queries)  # Should include: ["learn python", "study python", "understand python", ...]
```

#### 2b. HyDE Retrieval ([`HyDERetriever.retrieve()`](exercise.py:181))

- Generate a hypothetical document that answers the query
- Embed the hypothetical document
- Search ChromaDB using the hypothetical embedding

**Test:**
```python
hyde = HyDERetriever(chroma_client, embedding_model)
results = hyde.retrieve("machine learning frameworks", k=3)
```

---

### Exercise 3: Reranking Techniques

#### 3a. Cross-Encoder Reranking ([`CrossEncoderReranker.rerank()`](exercise.py:230))

- Load cross-encoder model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Create query-document pairs
- Get relevance scores
- Sort and return top-k results

**Test:**
```python
reranker = CrossEncoderReranker()
documents = ["doc1 content", "doc2 content", "doc3 content"]
results = reranker.rerank("python programming", documents, top_k=2)
```

#### 3b. MMR Reranking ([`MMRReranker.rerank()`](exercise.py:278))

- Encode query and documents
- Calculate relevance scores (cosine similarity)
- Implement MMR selection algorithm to balance relevance vs diversity

**Test:**
```python
mmr = MMRReranker(embedding_model, lambda_mult=0.5)
docs = [{"content": "python is a programming language", "id": "1"},
        {"content": "java is also a programming language", "id": "2"}]
results = mmr.rerank("programming language", docs, k=2)
```

---

### Exercise 4: Hybrid Search ([`HybridSearch.search()`](exercise.py:344))

Combine vector search (ChromaDB) with keyword search (BM25):

1. Initialize BM25 index from ChromaDB documents
2. Perform vector search
3. Perform BM25 search
4. Normalize scores
5. Combine using weighted sum

**Test:**
```python
hybrid = HybridSearch(chroma_client, embedding_model, vector_weight=0.5)
results = hybrid.search("python programming", k=5)
```

---

### Exercise 5: Query Decomposition

#### 5a. Decompose Queries ([`QueryDecomposer.decompose()`](exercise.py:404))

Break down complex queries into simpler sub-queries:
- "X and Y" → [X, Y]
- "How to do X, Y, Z" → [X, Y, Z]

#### 5b. Retrieve Decomposed ([`QueryDecomposer.retrieve_decomposed()`](exercise.py:436))

- Decompose query
- Retrieve for each sub-query
- Combine and deduplicate results

**Test:**
```python
decomposer = QueryDecomposer()
sub_queries = decomposer.decompose("python and machine learning")
# Should return: ["python", "machine learning"]
```

---

### Exercise 6: Production Considerations

#### 6a. Retrieval Cache ([`RetrievalCache`](exercise.py:477))

Implement LRU cache with:
- Query hashing
- Get/Set operations
- Cache size limits
- Hit/miss statistics

**Test:**
```python
cache = RetrievalCache(max_size=100)
cache.set("python", 5, [{"id": "1", "content": "test"}])
result = cache.get("python", 5)
print(result)  # Should return cached result
```

#### 6b. Resilient Retriever ([`ResilientRetriever.retrieve()`](exercise.py:535))

Implement fallback strategy:
- Try first retriever
- If fails, try next
- Log errors
- Return first successful result

---

## Complete Pipeline Test

After implementing all exercises, test the complete pipeline:

```python
# Initialize
retriever = AdvancedRetriever(
    chroma_client=chroma_client,
    embedding_model=embedding_model,
    use_hybrid=True,
    use_reranking=True,
    use_cache=True
)

# Test retrieval
results = retriever.retrieve("machine learning", k=3)

for r in results:
    print(f"{r['id']}: {r['content'][:100]}...")
```

## Expected Results

| Technique | Purpose | Key Benefit |
|-----------|---------|-------------|
| Synonym Expansion | Expand queries with synonyms | Better recall |
| HyDE | Generate hypothetical docs | Handle complex queries |
| Cross-Encoder | Re-score with cross-encoder | Higher precision |
| MMR | Balance relevance/diversity | Diverse results |
| Hybrid Search | Vector + Keyword | Robust retrieval |
| Query Decomposition | Break complex queries | Handle multi-part questions |
| Caching | Store results | Performance |
| Resilient Retriever | Fallback strategies | Reliability |

## Additional Challenges

1. **Compare Techniques**: Test each technique separately and compare results
2. **Parameter Tuning**: Experiment with `lambda_mult` for MMR, `vector_weight` for hybrid
3. **Combine Techniques**: Try different combinations (e.g., HyDE + Reranking)
4. **Add Custom Synonyms**: Extend the synonym dictionary with domain-specific terms
5. **Benchmark Performance**: Measure latency for each technique
