# INTERVIEW.md — LLM Semantic Book Recommender

## Q1: How is this different from a keyword search or collaborative filtering recommender?

**A:** Keyword search matches on surface terms — "mystery London" only returns books that literally contain those words. Collaborative filtering needs user interaction data (ratings, clicks) which we didn't have. Semantic search maps both the query and book content into a shared embedding space, so "a melancholy story about memory and loss" correctly retrieves books like The Remains of the Day even if those exact words don't appear in the synopsis. The LLM layer then adds a reasoning step that explains *why* each book is a match, which collaborative filtering can't do at all.

---

## Q2: Walk me through the chunking strategy.

**A:** Book synopses vary from 50 to 2000 words. We used sentence-aware chunking with a target of 512 tokens and a 64-token overlap. The overlap is important because thematic signals often span sentence boundaries — cutting exactly at 512 tokens can split a meaningful phrase. For very short synopses (under 100 tokens), we augmented with the book's genre tags and first chapter description to give the embedding more signal. We experimented with fixed-length chunking first but found it degraded recall by about 12% on our golden test set.

---

## Q3: What does the re-ranking step do and why is it necessary?

**A:** Vector search retrieves by embedding similarity, which captures semantic closeness but can miss nuance — two books might embed similarly because they share a setting, but the user's query is really about emotional tone. We use a cross-encoder re-ranker (sentence-transformers `cross-encoder/ms-marco-MiniLM-L-6-v2`) that takes the (query, candidate) pair together and scores relevance more precisely than the bi-encoder used in retrieval. We over-retrieve at 3× and re-rank down to top-K. This improved MRR by ~18% in our offline evaluation.

---

## Q4: How did you evaluate the system?

**A:** Three layers. (1) Offline: we built a 150-query golden test set with expected books and measured Recall@5 and MRR. (2) LLM-as-judge: GPT-4o scored each recommendation's thematic alignment with the query on a 0–5 scale — this caught cases where cosine similarity was high but the recommendation was thematically off. (3) Online (post-deployment): we tracked recommendation click-through rate and "helpful" ratings from users.

---

## Q5: How is the system deployed?

**A:** FastAPI app on Azure Container Apps. Book index in Azure AI Search with both vector and keyword fields for hybrid retrieval. The ingestion pipeline runs as a scheduled Azure Container Job when new books are added to the catalog. Embeddings are generated with Azure OpenAI ada-002.

---

## Q6: What's the hardest problem you solved in this project?

**A:** Embedding quality for short or vague queries. A query like "something uplifting" is too short for a good embedding. We added a query expansion step — GPT-4o rewrites the short query into 2-3 richer alternative phrasings, we embed all three, and we take the centroid embedding for retrieval. This improved Recall@5 by ~22% for short queries without affecting latency significantly since the embeddings are computed in parallel.

---

## Key Terms to Use

- **Dense embeddings** vs sparse keyword search
- **Sentence-aware chunking** with overlap
- **Hybrid retrieval** (vector + BM25)
- **Cross-encoder re-ranking** vs bi-encoder retrieval
- **Query expansion** for short queries
- **Recall@K and MRR** for offline evaluation
- **LLM-as-judge** scoring
