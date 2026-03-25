# LLM Semantic Book Recommender

## Overview

An LLM-powered semantic recommendation system that understands user intent beyond keyword matching. Leverages dense embeddings, vector similarity search, and contextual LLM reasoning to recommend books based on semantic similarity and user preferences.

---

## Architecture Diagram

```
User Query (natural language)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Azure Container Apps                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               Query Processing Pipeline               │  │
│  │                                                       │  │
│  │   Input ──▶ Intent Extraction ──▶ Query Embedding    │  │
│  │              (GPT-4o)             (ada-002)           │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │              Retrieval Layer                           │  │
│  │   Vector Search (Azure AI Search) → Top-K Candidates  │  │
│  │   + Metadata Filter (genre, length, era)              │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │              Re-Ranking + LLM Explanation              │  │
│  │   Cross-encoder re-rank → GPT-4o generates reason     │  │
│  │   why each book matches the user's intent             │  │
│  └────────────────────────┬──────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────┘
                            │
                   Final Recommendations
                (book + reason + similarity score)
```

### Data Ingestion Pipeline
```
Book Metadata (CSV/API)
    │
    ▼
Chunking (synopsis → sentence-aware, 512 tokens, 64 overlap)
    │
    ▼
Embedding (Azure OpenAI ada-002)
    │
    ▼
Azure AI Search Index (vector + metadata fields)
```

---

## Project Structure

```
book_recommender/
├── .env.example
├── pyproject.toml
├── README.md
├── INTERVIEW.md
│
├── infra/
│   ├── main.bicep
│   ├── container_app.bicep
│   └── ai_search.bicep
│
├── data/
│   └── sample_books.csv          # Book metadata for local dev/testing
│
├── src/
│   └── recommender/
│       ├── __init__.py
│       ├── main.py               # FastAPI app
│       ├── config.py
│       │
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── chunker.py        # Sentence-aware chunking
│       │   ├── embedder.py       # Azure OpenAI embeddings
│       │   └── indexer.py        # Pushes to Azure AI Search
│       │
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── search.py         # Vector + hybrid search
│       │   └── reranker.py       # Cross-encoder re-ranking
│       │
│       ├── recommendation/
│       │   ├── __init__.py
│       │   └── pipeline.py       # End-to-end recommendation chain
│       │
│       └── utils/
│           ├── __init__.py
│           └── logger.py
│
├── notebooks/
│   └── explore_embeddings.ipynb  # Visualize embedding clusters
│
└── tests/
    ├── test_chunker.py
    ├── test_search.py
    └── test_pipeline.py
```

---

## Setup Instructions

### 1. Environment Setup

```bash
git clone <repo-url>
cd book_recommender
uv venv
uv sync
cp .env.example .env
```

### 2. Ingest Book Data

```bash
# Index sample books into Azure AI Search
uv run python -m recommender.ingestion.indexer --source data/sample_books.csv
```

### 3. Deploy Azure Infrastructure

```bash
cd infra
az group create --name rg-book-recommender --location eastus
az deployment group create \
  --resource-group rg-book-recommender \
  --template-file main.bicep
```

### 4. Run Locally

```bash
uv run uvicorn src.recommender.main:app --reload --port 8002
```

### 5. Test a Recommendation

```bash
curl -X POST http://localhost:8002/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "a melancholy story about memory and loss set in post-war Europe", "top_k": 5}'
```

### 6. Deploy to Azure Container Apps

```bash
az acr build --registry <your-acr> --image book-recommender:latest .
az containerapp update \
  --name book-recommender-app \
  --resource-group rg-book-recommender \
  --image <your-acr>.azurecr.io/book-recommender:latest
```

---

## Core Code: Recommendation Pipeline

```python
# src/recommender/recommendation/pipeline.py
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from recommender.retrieval.search import hybrid_search
from recommender.retrieval.reranker import rerank_results
from recommender.config import settings

RECOMMENDATION_PROMPT = """
Given the user's reading intent: "{query}"

Here are {n} candidate books retrieved by semantic similarity:
{candidates}

For each book, explain in 1-2 sentences WHY it matches the user's intent.
Focus on thematic alignment, narrative tone, and emotional resonance.
Return as a JSON list: [{{"title": ..., "author": ..., "reason": ..., "score": ...}}]
"""

async def recommend(query: str, top_k: int = 5) -> list[dict]:
    # Step 1: Embed the query
    embedder = AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_embedding_deployment,
    )
    query_embedding = await embedder.aembed_query(query)

    # Step 2: Hybrid vector + keyword retrieval
    candidates = await hybrid_search(
        query=query,
        query_embedding=query_embedding,
        top_k=top_k * 3,  # Over-retrieve for re-ranking
    )

    # Step 3: Re-rank candidates
    reranked = rerank_results(query=query, candidates=candidates, top_k=top_k)

    # Step 4: LLM generates explanations
    llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        temperature=0.3,
    )

    candidate_text = "\n".join(
        f"{i+1}. {c['title']} by {c['author']} — {c['synopsis'][:200]}"
        for i, c in enumerate(reranked)
    )

    response = await llm.ainvoke(
        RECOMMENDATION_PROMPT.format(
            query=query, n=len(reranked), candidates=candidate_text
        )
    )

    import json
    return json.loads(response.content)
```

---

## Evaluation Strategy

| Metric | Method |
|---|---|
| **Recall@K** | Golden test set of (query → expected book) pairs |
| **MRR** | Mean Reciprocal Rank across test queries |
| **LLM-as-judge** | GPT-4o scores semantic relevance of each recommendation (0–5) |
| **Embedding coverage** | % of top-k results above cosine similarity threshold |

---

## Environment Variables

```env
# .env.example
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

AZURE_SEARCH_ENDPOINT=https://<search>.search.windows.net
AZURE_SEARCH_KEY=<key>
AZURE_SEARCH_INDEX=books-index

APP_ENV=development
LOG_LEVEL=INFO
TOP_K_DEFAULT=5
SIMILARITY_THRESHOLD=0.72
```
