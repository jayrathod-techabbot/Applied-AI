# Module 14: Production AI Projects — Core Concepts

## Table of Contents
- [14.1 Capstone Project Methodology](#141-capstone-project-methodology)
- [14.2 Project 1: Book Recommender](#142-project-1-book-recommender)
- [14.3 Project 2: Customer Support Engine](#143-project-2-customer-support-engine)
- [14.4 Project 3: Market Intelligence Agent](#144-project-3-market-intelligence-agent)
- [14.5 Project 4: Multi-Agent Researcher](#145-project-4-multi-agent-researcher)
- [14.6 Production Readiness Checklist](#146-production-readiness-checklist)

---

## 14.1 Capstone Project Methodology

Building production-grade AI systems requires a disciplined approach that spans from initial requirements gathering through deployment and ongoing monitoring. This section outlines a methodology that applies to all four capstone projects.

### End-to-End Project Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Discover │───►│  2. Design  │───►│  3. Build   │───►│  4. Test    │
│  Requirements │    │ Architecture │    │ Implement   │    │ Validate    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                                                        │
       │                                                        ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  7. Iterate  │◄───│  6. Monitor │◄───│  5. Deploy  │◄───│  4.5 Secure │
│  Improve     │    │  Observe    │    │  Release    │    │  Harden     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Phase 1: Requirements Gathering

| Activity | Deliverable | Tools |
|----------|-------------|-------|
| Stakeholder interviews | User stories, success criteria | Miro, Notion |
| Data audit | Data inventory, quality assessment | Pandas Profiling, Great Expectations |
| Constraint mapping | Latency, cost, compliance requirements | Architecture Decision Records |
| Baseline metrics | Current performance benchmarks | LangSmith, custom evals |

**Key Questions:**
- What is the primary user problem?
- What data sources are available?
- What are the latency and throughput requirements?
- What compliance constraints apply (GDPR, HIPAA, etc.)?
- What is the acceptable hallucination rate?

### Phase 2: Architecture Design

| Decision Point | Options | Selection Criteria |
|----------------|---------|-------------------|
| **Model** | GPT-4o, Claude 3.5, Llama 3 | Cost, quality, latency, availability |
| **Orchestration** | LangChain, LangGraph, CrewAI | Workflow complexity, state needs |
| **Vector Store** | Azure AI Search, Cosmos DB, Pinecone | Scale, query patterns, integration |
| **Storage** | Blob Storage, Cosmos DB, SQL | Data type, access patterns |
| **Deployment** | Azure Container Apps, AKS, Functions | Scale, cost, management overhead |

**Architecture Decision Record (ADR) Template:**

```yaml
# ADR-001: Vector Store Selection
status: accepted
context: >
  Need semantic search over 500K book descriptions with metadata filtering.
  Must integrate with Azure ecosystem. Support hybrid search (keyword + semantic).
decision: >
  Use Azure AI Search with semantic ranking and vector search.
  Embeddings via text-embedding-3-large.
consequences:
  - Pros: Native Azure integration, hybrid search, managed service
  - Cons: Vendor lock-in, limited customization vs open-source
  - Trade-offs: Cost ~$200/month at scale vs self-hosted Weaviate
```

### Phase 3: Implementation

**Sprint Structure (2-week cycles):**

| Sprint | Focus | Deliverable |
|--------|-------|-------------|
| Sprint 1 | Data pipeline, embeddings | Ingested data, vector index |
| Sprint 2 | Core retrieval, RAG pipeline | Working search, basic RAG |
| Sprint 3 | Agent logic, orchestration | Functional agent workflow |
| Sprint 4 | Frontend integration, streaming | End-to-end user experience |
| Sprint 5 | Testing, evaluation, hardening | Eval reports, security audit |
| Sprint 6 | Deployment, monitoring | Production deployment, dashboards |

### Phase 4: Testing & Evaluation

| Test Type | Method | Tools |
|-----------|--------|-------|
| **Unit Tests** | Component-level assertions | pytest, unittest |
| **Integration Tests** | End-to-end workflow validation | pytest-asyncio, mock services |
| **LLM Evaluation** | Quality metrics (faithfulness, relevance) | RAGAS, LangSmith, DeepEval |
| **Load Testing** | Throughput, latency under load | Locust, k6 |
| **Security Testing** | Prompt injection, data leakage | Promptfoo, manual pen testing |

**RAG Evaluation Metrics:**

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

dataset = {
    "question": ["What themes appear in Dune?", "Who wrote 1984?"],
    "answer": ["Political intrigue, ecology, religion", "George Orwell"],
    "contexts": [["Dune explores political...", "The novel examines..."], ["Orwell published..."]],
    "ground_truth": ["Politics, ecology, religion, messianism", "George Orwell"]
}

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)
print(results)
# faithfulness: 0.87, answer_relevancy: 0.92, context_precision: 0.85, context_recall: 0.78
```

### Phase 5: Deployment

**Deployment Checklist:**
- [ ] Infrastructure as Code (Bicep/Terraform) reviewed
- [ ] CI/CD pipeline configured (GitHub Actions / Azure DevOps)
- [ ] Environment variables and secrets in Azure Key Vault
- [ ] Container images scanned for vulnerabilities
- [ ] Health check endpoints implemented
- [ ] Logging and tracing configured (Application Insights)
- [ ] Alerting rules defined (latency, error rate, cost)
- [ ] Rollback strategy documented

### Phase 6: Monitoring & Observability

| Pillar | Implementation | Alerts |
|--------|---------------|--------|
| **Metrics** | Azure Monitor, Application Insights | Latency > 5s, Error rate > 5% |
| **Traces** | OpenTelemetry → Application Insights | Failed LLM calls, timeout chains |
| **Logs** | Structured JSON logs → Log Analytics | Security events, anomalous patterns |
| **Quality** | LangSmith evals, custom dashboards | Hallucination rate drift > 10% |
| **Cost** | Azure Cost Management, token tracking | Daily spend > budget threshold |

#### Key Takeaways — Capstone Project Methodology

- Follow a **structured lifecycle**: Discover → Design → Build → Test → Deploy → Monitor → Iterate
- Document **architecture decisions** with ADRs to capture rationale and trade-offs
- Evaluate RAG systems with **standardized metrics**: faithfulness, relevancy, precision, recall
- Implement **comprehensive monitoring** across metrics, traces, logs, quality, and cost
- Plan for **iterative improvement** — production AI systems require continuous refinement

---

## 14.2 Project 1: Book Recommender

A production-grade book recommendation system that combines semantic search, embedding-based retrieval, re-ranking, and LLM-powered explanations. Built on Azure AI Search with a LangChain orchestration layer.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Book Recommender System                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │  React   │    │              API Gateway (FastAPI)           │  │
│  │  Frontend│◄──►│  • Auth  • Rate Limit  • Request Validation │  │
│  └──────────┘    └──────────────────┬───────────────────────────┘  │
│                                     │                               │
│              ┌──────────────────────┼──────────────────────┐       │
│              ▼                      ▼                      ▼       │
│     ┌────────────────┐   ┌────────────────┐   ┌────────────────┐  │
│     │  Embedding     │   │  Vector Search │   │  Re-Ranking    │  │
│     │  Pipeline      │   │  (Azure AI     │   │  (Cross-       │  │
│     │                │   │   Search)      │   │   Encoder)     │  │
│     │  • Chunk       │   │                │   │                │  │
│     │  • Embed       │   │  • Hybrid      │   │  • Score       │  │
│     │  • Index       │   │  • Semantic    │   │  • Re-order    │  │
│     └────────┬───────┘   │  • Filter      │   │  • Top-K       │  │
│              │           └────────┬───────┘   └────────┬───────┘  │
│              │                    │                     │          │
│              ▼                    ▼                     ▼          │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │              LLM Explanation Generator                    │  │
│     │  • Generate personalized recommendations                 │  │
│     │  • Explain why each book matches user preferences        │  │
│     │  • Format response with metadata (rating, genre, year)   │  │
│     └──────────────────────┬───────────────────────────────────┘  │
│                            │                                       │
│              ┌─────────────┼─────────────┐                        │
│              ▼             ▼             ▼                        │
│     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│     │ Azure AI    │ │ Cosmos DB   │ │ Blob Storage│              │
│     │ Search      │ │ (User       │ │ (Book       │              │
│     │ (Vectors +  │ │  Profiles)  │ │  Metadata)  │              │
│     │  Semantic)  │ │             │ │             │              │
│     └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | GPT-4o / GPT-4o-mini | Recommendation generation, explanations |
| **Embeddings** | text-embedding-3-large | Semantic representation of book descriptions |
| **Vector Search** | Azure AI Search | Hybrid search (BM25 + vector + semantic ranking) |
| **Re-Ranking** | Cross-encoder (ms-marco-MiniLM-L-6-v2) | Precision re-ranking of top candidates |
| **User Profiles** | Azure Cosmos DB | Store preferences, reading history, ratings |
| **Book Metadata** | Azure Blob Storage + SQL | Book details, covers, reviews |
| **Backend** | FastAPI + LangChain | API, orchestration, RAG pipeline |
| **Frontend** | React + TypeScript | User interface, real-time updates |
| **Deployment** | Azure Container Apps | Scalable container hosting |

### Key Components

#### 1. Embedding Pipeline

```python
from langchain_openai import OpenAIEmbeddings
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType,
    SearchableField, SearchField, VectorSearch,
    HnswAlgorithmConfiguration, VectorSearchProfile
)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=3072)

def create_book_index(index_name: str, endpoint: str, key: str):
    """Create Azure AI Search index with vector support."""
    index_client = SearchIndexClient(endpoint=endpoint, credential=key)
    
    index = SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="book_id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="author", type=SearchFieldDataType.String),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchableField(name="genre", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="publication_year", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="avg_rating", type=SearchFieldDataType.Double, filterable=True),
            SearchField(
                name="description_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=3072,
                vector_search_profile_name="hnsw-profile"
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
            profiles=[VectorSearchProfile(
                name="hnsw-profile",
                algorithm_configuration_name="hnsw-config"
            )]
        )
    )
    
    index_client.create_or_update_index(index)

def embed_and_index_books(books: list[dict], index_name: str):
    """Process books through embedding pipeline."""
    for book in books:
        vector = embeddings.embed_query(book["description"])
        doc = {
            "book_id": book["id"],
            "title": book["title"],
            "author": book["author"],
            "description": book["description"],
            "genre": book["genre"],
            "publication_year": book["publication_year"],
            "avg_rating": book["avg_rating"],
            "description_vector": vector,
        }
        upload_to_search_index(doc, index_name)
```

#### 2. Hybrid Search with Re-Ranking

```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from sentence_transformers import CrossEncoder

class BookSearchEngine:
    def __init__(self, search_endpoint: str, search_key: str, index_name: str):
        self.search_client = SearchClient(search_endpoint, index_name, key=search_key)
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    def search(self, query: str, user_prefs: dict, top_k: int = 20) -> list[dict]:
        """Hybrid search with vector, keyword, and semantic ranking."""
        query_vector = embeddings.embed_query(query)
        
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=50,
            fields="description_vector"
        )
        
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"genre eq '{user_prefs.get('preferred_genre', '')}'" if user_prefs.get('preferred_genre') else None,
            top=top_k,
            query_type="semantic",
            semantic_configuration_name="book-config"
        )
        
        candidates = []
        for result in results:
            candidates.append({
                "book_id": result["book_id"],
                "title": result["title"],
                "author": result["author"],
                "description": result["description"],
                "score": result["@search.score"],
                "genre": result["genre"],
                "avg_rating": result["avg_rating"],
            })
        
        # Re-rank with cross-encoder
        if len(candidates) > 5:
            pairs = [(query, c["description"]) for c in candidates]
            scores = self.reranker.predict(pairs)
            for i, score in enumerate(scores):
                candidates[i]["rerank_score"] = float(score)
            candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return candidates[:10]
```

#### 3. LLM Recommendation Generator

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

recommendation_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a book recommendation engine. Given a user query, their reading preferences, and candidate books, generate personalized recommendations with explanations for why each book matches their interests."""),
    ("user", """User Query: {query}
User Preferences: {favorite_genres}, Previously Liked: {liked_books}
Candidate Books: {candidates}
Generate recommendations for the top 5 most relevant books in JSON format.""")
])

parser = JsonOutputParser()
chain = recommendation_prompt | llm | parser

def generate_recommendations(query: str, user_profile: dict, candidates: list[dict]) -> dict:
    candidates_text = "\n".join([
        f"- {c['title']} by {c['author']} ({c['genre']}, {c['avg_rating']}★): {c['description'][:200]}..."
        for c in candidates[:10]
    ])
    return chain.invoke({
        "query": query,
        "favorite_genres": ", ".join(user_profile.get("genres", [])),
        "liked_books": ", ".join(user_profile.get("liked_books", [])),
        "candidates": candidates_text
    })
```

#### 4. Azure Infrastructure (Bicep)

```bicep
// book-recommender-infra.bicep
param location string = resourceGroup().location
param environment string = 'prod'

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: 'book-search-${environment}'
  location: location
  sku: { name: 'standard' }
  properties: {
    hostingMode: 'default'
    semanticSearch: 'free'
  }
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: 'book-cosmos-${environment}'
  location: location
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0 }]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'UserProfiles'
  properties: { resource: { id: 'UserProfiles' } }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'bookmetadata${environment}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: { accessTier: 'Hot' }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'book-recommender-env-${environment}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'book-recommender-logs-${environment}'
  location: location
  properties: { retentionInDays: 30 }
}

output searchEndpoint string = searchService.properties.endpoint
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
```

#### Key Takeaways — Book Recommender

- **Hybrid search** (BM25 + vector + semantic) outperforms pure vector search for book recommendations
- **Re-ranking** with cross-encoders improves precision by 15–25% over initial retrieval scores
- **User profiles** in Cosmos DB enable personalization without rebuilding the vector index
- **LLM explanations** increase user trust and engagement with recommendations
- **Azure AI Search** provides managed vector search with semantic ranking and filtering

---

## 14.3 Project 2: Customer Support Engine

A real-time, stateful customer support system built with LangGraph, WebSockets, and React. Features intent classification, knowledge retrieval, resolution reasoning, and streaming responses.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Customer Support Engine                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │  React   │◄──►│           WebSocket Gateway                  │  │
│  │  Chat UI │    │  • Connection management                     │  │
│  │          │    │  • Message streaming (SSE/WebSocket)         │  │
│  └──────────┘    │  • Session routing                           │  │
│                  └──────────────────┬───────────────────────────┘  │
│                                     │                               │
│              ┌──────────────────────▼──────────────────────┐       │
│              │           LangGraph State Machine            │       │
│              │                                              │       │
│              │  ┌──────────┐    ┌──────────┐    ┌────────┐ │       │
│              │  │ Classify │───►│ Retrieve │───►│Resolve │ │       │
│              │  │ Intent   │    │ Knowledge│    │ Reason │ │       │
│              │  └──────────┘    └──────────┘    └────────┘ │       │
│              │       │                                      │       │
│              │       ▼                                      │       │
│              │  ┌──────────┐    ┌──────────┐    ┌────────┐ │       │
│              │  │ Escalate │◄───│ Validate │◄───│Generate│ │       │
│              │  │ to Human │    │ Response │    │ Reply  │ │       │
│              │  └──────────┘    └──────────┘    └────────┘ │       │
│              └──────────────────────┬───────────────────────┘       │
│                                     │                               │
│              ┌──────────────────────┼───────────────────────┐       │
│              ▼                      ▼                       ▼       │
│     ┌─────────────┐         ┌─────────────┐         ┌─────────────┐│
│     │ Azure AI    │         │ Cosmos DB   │         │ Application ││
│     │ Search      │         │ (Session    │         │ Insights    ││
│     │ (Knowledge  │         │  State)     │         │ (Tracing)   ││
│     │  Base)      │         │             │         │             ││
│     └─────────────┘         └─────────────┘         └─────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### LangGraph State Machine

```python
from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver

class SupportState(TypedDict):
    messages: Annotated[List, add_messages]
    intent: str
    confidence: float
    retrieved_docs: List[dict]
    resolution: str
    escalation_needed: bool
    session_id: str
    customer_id: str
    retry_count: int

def classify_intent(state: SupportState) -> dict:
    """Classify customer intent using LLM."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""Classify the customer's intent: billing, technical, account, product_info, complaint, or general.
    Customer message: {state['messages'][-1].content}
    Respond with ONLY the category name."""
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    valid_intents = ["billing", "technical", "account", "product_info", "complaint", "general"]
    if intent not in valid_intents:
        intent = "general"
    return {"intent": intent, "confidence": 0.9 if intent != "general" else 0.5}

def retrieve_knowledge(state: SupportState) -> dict:
    """Retrieve relevant knowledge base articles."""
    search_client = SearchClient(
        endpoint=os.environ["SEARCH_ENDPOINT"],
        index_name="knowledge-base",
        credential=os.environ["SEARCH_KEY"]
    )
    query = state["messages"][-1].content
    vector = embeddings.embed_query(query)
    results = search_client.search(
        search_text=query,
        vector_queries=[VectorizedQuery(vector=vector, k_nearest_neighbors=5, fields="content_vector")],
        filter=f"category eq '{state['intent']}'",
        top=5,
        query_type="semantic"
    )
    docs = [{"title": r["title"], "content": r["content"], "url": r["url"]} for r in results]
    return {"retrieved_docs": docs}

def resolve_issue(state: SupportState) -> dict:
    """Determine if the issue can be resolved automatically."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    context = "\n".join([f"### {d['title']}\n{d['content']}" for d in state["retrieved_docs"]])
    prompt = f"""Based on the customer's issue and retrieved knowledge, determine:
    1. Can this be resolved automatically? (yes/no)
    2. If yes, what is the resolution?
    3. Should this be escalated? (yes/no)
    Customer Issue: {state['messages'][-1].content}
    Knowledge: {context}
    Respond in JSON: {{"resolvable": true/false, "resolution": "...", "escalate": true/false}}"""
    result = json.loads(llm.invoke(prompt).content)
    return {"resolution": result.get("resolution", ""), "escalation_needed": result.get("escalate", False)}

def generate_response(state: SupportState) -> dict:
    """Generate a customer-friendly response."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
    context = "\n".join([f"- {d['title']}: {d['content'][:200]}..." for d in state["retrieved_docs"]])
    prompt = f"""You are a helpful customer support agent. Generate a response.
    Customer Issue: {state['messages'][-1].content}
    Resolution: {state['resolution']}
    Context: {context}
    Guidelines: Be empathetic, provide specific steps, include relevant links."""
    response = llm.stream([{"role": "system", "content": prompt}, *state["messages"]])
    return {"messages": [response]}

def validate_response(state: SupportState) -> dict:
    """Validate the generated response for quality and safety."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response_text = state["messages"][-1].content if state["messages"] else ""
    prompt = f"""Validate this response: 1. Addresses issue? 2. Polite? 3. Safe? 4. Supported?
    Response: {response_text}
    Respond in JSON: {{"addresses_issue": true, "polite": true, "safe": true, "supported": true}}"""
    result = json.loads(llm.invoke(prompt).content)
    if not all(result.values()):
        return {"retry_count": state.get("retry_count", 0) + 1}
    return {"retry_count": 0}

def escalate_to_human(state: SupportState) -> dict:
    """Route to human agent when needed."""
    ticket = {"customer_id": state["customer_id"], "intent": state["intent"],
              "conversation": [m.content for m in state["messages"]],
              "priority": "high" if state["intent"] == "complaint" else "medium"}
    ticket_id = create_support_ticket(ticket)
    return {"messages": [AIMessage(
        content=f"I've created ticket #{ticket_id}. A human agent will contact you within 2 hours."
    )]}

# Routing Logic
def route_after_resolve(state: SupportState) -> Literal["generate", "escalate"]:
    return "escalate" if state.get("escalation_needed") else "generate"

def route_after_generate(state: SupportState) -> Literal["validate", "escalate"]:
    return "escalate" if state.get("retry_count", 0) >= 2 else "validate"

def route_after_validate(state: SupportState) -> Literal["end", "generate"]:
    return END if state.get("retry_count", 0) == 0 else "generate"

# Build Graph
graph = StateGraph(SupportState)
graph.add_node("classify", classify_intent)
graph.add_node("retrieve", retrieve_knowledge)
graph.add_node("resolve", resolve_issue)
graph.add_node("generate", generate_response)
graph.add_node("validate", validate_response)
graph.add_node("escalate", escalate_to_human)

graph.set_entry_point("classify")
graph.add_edge("classify", "retrieve")
graph.add_edge("retrieve", "resolve")
graph.add_conditional_edges("resolve", route_after_resolve, {"generate": "generate", "escalate": "escalate"})
graph.add_conditional_edges("generate", route_after_generate, {"validate": "validate", "escalate": "escalate"})
graph.add_conditional_edges("validate", route_after_validate, {END: END, "generate": "generate"})
graph.add_edge("escalate", END)

checkpointer = PostgresSaver(conn_string=os.environ["DATABASE_URL"])
app = graph.compile(checkpointer=checkpointer)
```

### Real-Time Streaming with WebSockets

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)
    
    async def send_chunk(self, session_id: str, chunk: str):
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_text(json.dumps({"type": "chunk", "content": chunk}))
    
    async def send_complete(self, session_id: str, metadata: dict):
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_text(json.dumps({"type": "complete", **metadata}))

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message["type"] == "user_message":
                config = {"configurable": {"thread_id": session_id}}
                async for event in app.astream_events(
                    {"messages": [HumanMessage(content=message["content"])], "session_id": session_id},
                    config=config, version="v2"
                ):
                    if event["event"] == "on_chat_model_stream":
                        chunk = event["data"]["chunk"].content
                        if chunk:
                            await manager.send_chunk(session_id, chunk)
                    elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                        await manager.send_complete(session_id, {
                            "intent": event["data"]["output"].get("intent", ""),
                            "escalated": event["data"]["output"].get("escalation_needed", False),
                        })
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

### Frontend Integration (React)

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function useChatWebSocket(sessionId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const currentResponse = useRef('');

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chunk') {
        currentResponse.current += data.content;
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, content: currentResponse.current }];
          }
          return [...prev, { role: 'assistant', content: currentResponse.current, timestamp: new Date() }];
        });
      }
      if (data.type === 'complete') {
        setIsStreaming(false);
        currentResponse.current = '';
      }
    };
    return () => ws.close();
  }, [sessionId]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || isStreaming) return;
    setMessages(prev => [...prev, { role: 'user', content, timestamp: new Date() }]);
    setIsStreaming(true);
    currentResponse.current = '';
    wsRef.current.send(JSON.stringify({ type: 'user_message', content }));
  }, [isStreaming]);

  return { messages, sendMessage, isStreaming };
}
```

#### Key Takeaways — Customer Support Engine

- **LangGraph state machine** provides explicit control flow for complex support workflows
- **Intent classification** routes queries to appropriate knowledge domains
- **Re-ranking** knowledge base results improves answer accuracy
- **Response validation** prevents hallucinated or inappropriate answers
- **WebSocket streaming** enables real-time token-by-token responses
- **Postgres checkpointer** persists session state for multi-turn conversations

---

## 14.4 Project 3: Market Intelligence Agent

A multi-agent system that scrapes web sources, extracts market insights, summarizes findings, and produces intelligence reports. Built with LangChain, RAG, and Azure Blob Storage.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Market Intelligence Agent                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │  User    │    │            Orchestrator Agent                │  │
│  │  Query   │───►│  • Parse research request                    │  │
│  │          │    │  • Decompose into sub-tasks                  │  │
│  └──────────┘    │  • Coordinate agent execution                │  │
│                  └──────────┬───────────────────────────────────┘  │
│                             │                                       │
│              ┌──────────────┼──────────────┐                       │
│              ▼              ▼              ▼                       │
│     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│     │  Web        │ │  Retrieval  │ │  Reasoning  │               │
│     │  Scraper    │ │  Agent      │ │  Agent      │               │
│     │  Agent      │ │             │ │             │               │
│     │             │ │  • Query    │ │  • Analyze  │               │
│     │  • Crawl    │ │    vectors  │ │    findings │               │
│     │  • Extract  │ │  • Filter   │ │  • Synthesize│              │
│     │  • Clean    │ │  • Rank     │ │  • Cross-ref│               │
│     └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │
│             │              │               │                       │
│             ▼              ▼               ▼                       │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │              Validation Agent                             │  │
│     │  • Fact-check claims                                    │  │
│     │  • Detect bias or hallucination                         │  │
│     │  • Score confidence                                     │  │
│     └──────────────────────┬───────────────────────────────────┘  │
│                            │                                       │
│              ┌─────────────┼─────────────┐                        │
│              ▼             ▼             ▼                        │
│     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│     │ Blob Storage│ │ Azure AI    │ │ Cosmos DB   │              │
│     │ (Raw HTML,  │ │ Search      │ │ (Reports,   │              │
│     │  Cleaned    │ │ (Indexed    │ │  Metadata)  │              │
│     │  Text)      │ │  Content)   │ │             │              │
│     └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Implementation

```python
from langchain_openai import ChatOpenAI
from playwright.async_api import async_playwright
import asyncio

class IntelligenceState(TypedDict):
    query: str
    sources: List[str]
    raw_content: List[dict]
    extracted_insights: List[dict]
    analysis: str
    validated_report: str
    confidence_score: float

class WebScraperAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    async def scrape(self, urls: List[str]) -> List[dict]:
        """Scrape and clean content from URLs."""
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            for url in urls:
                try:
                    page = await browser.new_page()
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state("networkidle")
                    content = await page.evaluate("""() => {
                        document.querySelectorAll('nav, footer, script, style, .ad, .sidebar').forEach(el => el.remove());
                        return document.body.innerText;
                    }""")
                    summary = await self.llm.ainvoke(f"Summarize this content in 3-5 bullet points focusing on market trends, numbers, and company names:\n{content[:4000]}")
                    results.append({
                        "url": url, "title": await page.title(),
                        "content": content[:5000], "summary": summary.content,
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    results.append({"url": url, "error": str(e)})
                finally:
                    await page.close()
            await browser.close()
        return results

class RetrievalAgent:
    def __init__(self, search_client, embeddings):
        self.search_client = search_client
        self.embeddings = embeddings
    
    def retrieve(self, query: str, category: str, top_k: int = 10) -> List[dict]:
        """Retrieve relevant documents from vector store."""
        vector = self.embeddings.embed_query(query)
        results = self.search_client.search(
            search_text=query,
            vector_queries=[VectorizedQuery(vector=vector, k_nearest_neighbors=top_k, fields="content_vector")],
            filter=f"category eq '{category}'" if category else None,
            top=top_k, query_type="semantic"
        )
        return [{"title": r["title"], "content": r["content"], "source": r["source"], "score": r["@search.score"]} for r in results]

class ReasoningAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    def analyze(self, query: str, scraped: List[dict], retrieved: List[dict]) -> str:
        """Synthesize insights from multiple sources."""
        scraped_text = "\n\n".join([f"Source: {s['url']}\nSummary: {s['summary']}" for s in scraped if 'error' not in s])
        retrieved_text = "\n\n".join([f"Source: {r['title']} ({r['source']})\n{r['content'][:300]}" for r in retrieved])
        prompt = f"""Research Query: {query}
SCRAPED WEB CONTENT:\n{scraped_text}
RETRIEVED KNOWLEDGE BASE:\n{retrieved_text}
Produce a comprehensive market intelligence report:
1. KEY FINDINGS (3-5 bullets) 2. MARKET TRENDS 3. COMPETITIVE LANDSCAPE
4. RISKS & OPPORTUNITIES 5. RECOMMENDED ACTIONS
Cite sources inline. Flag conflicting information."""
        return self.llm.invoke(prompt).content

class ValidationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    def validate(self, query: str, report: str, sources: List[dict]) -> dict:
        """Validate report quality and confidence."""
        sources_text = "\n".join([f"- {s.get('url', s.get('title', 'Unknown'))}" for s in sources])
        prompt = f"""Validate this report:
Query: {query}\nSources: {sources_text}\nReport:\n{report}
Evaluate: 1. Claims supported by sources? 2. Unsupported assertions? 3. Conflicting info? 4. Confidence score (0.0-1.0) 5. Improvements
Respond in JSON."""
        result = json.loads(self.llm.invoke(prompt).content)
        return {"validated_report": report, "confidence_score": result.get("confidence_score", 0.5), "validation_notes": result}

class MarketIntelligenceOrchestrator:
    def __init__(self):
        self.scraper = WebScraperAgent()
        self.retrieval = RetrievalAgent(search_client, embeddings)
        self.reasoner = ReasoningAgent()
        self.validator = ValidationAgent()
    
    async def run(self, query: str, urls: List[str], category: str = "") -> dict:
        """Execute full market intelligence pipeline."""
        scraped, retrieved = await asyncio.gather(
            self.scraper.scrape(urls),
            asyncio.to_thread(self.retrieval.retrieve, query, category)
        )
        analysis = self.reasoner.analyze(query, scraped, retrieved)
        all_sources = scraped + retrieved
        validated = self.validator.validate(query, analysis, all_sources)
        self._store_report(query, validated, all_sources)
        return validated
    
    def _store_report(self, query: str, report: dict, sources: List[dict]):
        """Store report in Cosmos DB and sources in Blob Storage."""
        for source in sources:
            if 'content' in source:
                blob_client = BlobClient.from_connection_string(
                    conn_str=os.environ["BLOB_CONN_STRING"],
                    container_name="market-intel-raw",
                    blob_name=f"{datetime.utcnow().strftime('%Y%m%d')}/{hash(source.get('url', ''))}.txt"
                )
                blob_client.upload_blob(source['content'], overwrite=True)
        cosmos_client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
        container = cosmos_client.get_database_client("MarketIntel").get_container_client("Reports")
        container.upsert_item({
            "id": str(uuid.uuid4()), "query": query,
            "confidence": report["confidence_score"], "source_count": len(sources),
            "created_at": datetime.utcnow().isoformat(),
            "report_summary": report["validated_report"][:500],
        })
```

### Summarization Pipeline

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

class SummarizationPipeline:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    
    def summarize_document(self, content: str, summary_type: str = "detailed") -> str:
        """Summarize long documents using map-reduce."""
        docs = self.splitter.create_documents([content])
        if summary_type == "detailed":
            chain = load_summarize_chain(self.llm, chain_type="map_reduce",
                map_prompt="Write a detailed summary:\n{text}\nDETAILED SUMMARY:",
                combine_prompt="Write a comprehensive summary:\n{text}\nCOMPREHENSIVE SUMMARY:")
        else:
            chain = load_summarize_chain(self.llm, chain_type="map_reduce",
                map_prompt="Summarize in 2-3 sentences: {text}",
                combine_prompt="Create a concise summary: {text}")
        return chain.invoke(docs)
    
    def extract_key_entities(self, content: str) -> dict:
        """Extract companies, people, metrics from content."""
        prompt = f"""Extract key entities from: {content[:3000]}
        Return JSON with: companies, people, metrics (with context), dates, products."""
        return json.loads(self.llm.invoke(prompt).content)
```

#### Key Takeaways — Market Intelligence Agent

- **Multi-agent decomposition** separates concerns: scraping, retrieval, reasoning, validation
- **Async scraping** with Playwright handles dynamic JavaScript-rendered pages
- **Map-reduce summarization** handles documents exceeding context windows
- **Validation agent** provides confidence scoring and fact-checking
- **Blob Storage** stores raw scraped content for audit trails
- **Cosmos DB** tracks report metadata for search and analytics

---

## 14.5 Project 4: Multi-Agent Researcher

A collaborative research system using CrewAI with LangChain orchestration and Cosmos DB for shared memory. Features sequential delegation between researcher, critic, and writer agents.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Multi-Agent Researcher                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │  User    │    │              CrewAI Orchestrator             │  │
│  │  Topic   │───►│  • Define crew and tasks                     │  │
│  │          │    │  • Manage agent handoffs                     │  │
│  └──────────┘    │  • Aggregate final deliverable               │  │
│                  └──────────────────┬───────────────────────────┘  │
│                                     │                               │
│              ┌──────────────────────┼──────────────────────┐       │
│              ▼                      ▼                      ▼       │
│     ┌─────────────┐         ┌─────────────┐         ┌─────────────┐│
│     │ Researcher  │────────►│   Critic    │────────►│   Writer    ││
│     │  Agent      │         │   Agent     │         │   Agent     ││
│     │             │         │             │         │             ││
│     │ • Search    │         │ • Review    │         │ • Compose   ││
│     │ • Gather    │         │ • Fact-check│         │ • Format    ││
│     │ • Analyze   │         │ • Suggest   │         │ • Polish    ││
│     │ • Synthesize│         │ • Approve   │         │ • Publish   ││
│     └──────┬──────┘         └──────┬──────┘         └──────┬──────┘│
│            │                       │                       │       │
│            └───────────────────────┼───────────────────────┘       │
│                                    │                                │
│                     ┌──────────────▼──────────────┐                │
│                     │    Cosmos DB (Shared Memory) │                │
│                     │                              │                │
│                     │  • Research artifacts         │                │
│                     │  • Critique feedback          │                │
│                     │  • Draft versions             │                │
│                     │  • Agent conversation history  │                │
│                     └──────────────────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### CrewAI Implementation

```python
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()
file_tool = FileReadTool()

researcher = Agent(
    role="Senior Research Analyst",
    goal="Conduct thorough research on {topic} and gather comprehensive, accurate information from multiple sources",
    backstory="""You are a senior research analyst with 10+ years of experience in market research
    and academic analysis. You excel at finding credible sources, extracting key insights,
    and synthesizing complex information into structured findings.""",
    tools=[search_tool, scrape_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

critic = Agent(
    role="Critical Review Editor",
    goal="Review research findings for accuracy, completeness, bias, and logical consistency",
    backstory="""You are a meticulous review editor with expertise in fact-checking and
    editorial standards. You identify gaps in research, question unsupported claims,
    detect potential bias, and ensure all assertions are backed by credible sources.""",
    tools=[search_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

writer = Agent(
    role="Senior Content Writer",
    goal="Produce a polished, well-structured research report on {topic} that is engaging and authoritative",
    backstory="""You are a senior content writer specializing in research reports and
    analytical pieces. You transform raw research and editorial feedback into compelling
    narratives with clear structure, smooth transitions, and actionable insights.""",
    tools=[file_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

research_task = Task(
    description="""Research the topic: {topic}
    Focus areas: 1. Current state and recent developments 2. Key players and thought leaders
    3. Market size, growth trends 4. Challenges and risks 5. Future outlook
    Requirements: Use at least 10 credible sources, include data points, note conflicting views.""",
    expected_output="""Comprehensive research document with:
    - Executive summary, key findings by focus area, data points with citations,
    - List of all sources with URLs, identified gaps.""",
    agent=researcher, output_file="research_findings.md",
)

review_task = Task(
    description="""Review the research findings on {topic} for quality and accuracy.
    Checklist: 1. Claims backed by sources? 2. Logical gaps? 3. Data current? 4. Biases?
    5. Conflicting viewpoints acknowledged? 6. Comprehensive enough?
    For each issue: describe it, suggest improvements, provide additional sources.""",
    expected_output="""Review document with: Quality score (1-10), issues with severity,
    improvement suggestions, additional sources, approval status.""",
    agent=critic, context=[research_task], output_file="review_feedback.md",
)

writing_task = Task(
    description="""Write a comprehensive research report on {topic}.
    Structure: 1. Title and Executive Summary 2. Introduction 3. Current State Analysis
    4. Key Findings 5. Market Dynamics 6. Challenges and Risks 7. Future Outlook
    8. Conclusions and Recommendations 9. References
    Style: Professional tone, clear headings, inline citations, actionable recommendations.""",
    expected_output="""Polished research report in Markdown: 2000-3000 words, all sections,
    sources cited, ready for publication.""",
    agent=writer, context=[research_task, review_task], output_file="final_report.md",
)

crew = Crew(
    agents=[researcher, critic, writer],
    tasks=[research_task, review_task, writing_task],
    process=Process.sequential, verbose=2, memory=True, cache=True, max_rpm=100, share_crew=True,
)

result = crew.kickoff(inputs={"topic": "The impact of AI on software development in 2026"})
```

### Shared Memory with Cosmos DB

```python
from azure.cosmos import CosmosClient, PartitionKey

class CrewMemoryManager:
    """Manages shared memory for CrewAI agents using Cosmos DB."""
    
    def __init__(self, endpoint: str, key: str, database: str = "CrewMemory"):
        self.client = CosmosClient(endpoint, {"masterKey": key})
        self.db = self.client.create_database_if_not_exists(id=database)
        self.artifacts = self.db.create_container_if_not_exists(id="artifacts", partition_key=PartitionKey(path="/research_id"))
        self.feedback = self.db.create_container_if_not_exists(id="feedback", partition_key=PartitionKey(path="/research_id"))
        self.conversations = self.db.create_container_if_not_exists(id="conversations", partition_key=PartitionKey(path="/research_id"))
    
    def store_artifact(self, research_id: str, agent_name: str, content: str, metadata: dict = None):
        """Store research artifacts (findings, drafts, etc.)."""
        item = {
            "id": f"{research_id}-{agent_name}-{datetime.utcnow().isoformat()}",
            "research_id": research_id, "agent": agent_name,
            "content": content, "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self.artifacts.upsert_item(item)
        return item["id"]
    
    def store_feedback(self, research_id: str, from_agent: str, to_agent: str, feedback: str):
        """Store inter-agent feedback."""
        item = {
            "id": f"fb-{research_id}-{datetime.utcnow().isoformat()}",
            "research_id": research_id, "from_agent": from_agent, "to_agent": to_agent,
            "feedback": feedback, "created_at": datetime.utcnow().isoformat(),
        }
        self.feedback.upsert_item(item)
    
    def get_conversation_history(self, research_id: str, agent_name: str = None) -> list[dict]:
        """Retrieve conversation history for context."""
        query = "SELECT * FROM c WHERE c.research_id = @rid"
        params = [{"name": "@rid", "value": research_id}]
        if agent_name:
            query += " AND c.agent = @agent"
            params.append({"name": "@agent", "value": agent_name})
        query += " ORDER BY c.created_at ASC"
        return list(self.conversations.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    
    def get_latest_artifact(self, research_id: str, agent_name: str) -> dict | None:
        """Get the most recent artifact from a specific agent."""
        query = "SELECT TOP 1 * FROM c WHERE c.research_id = @rid AND c.agent = @agent ORDER BY c.created_at DESC"
        results = list(self.artifacts.query_items(query=query, parameters=[
            {"name": "@rid", "value": research_id}, {"name": "@agent", "value": agent_name}
        ], enable_cross_partition_query=True))
        return results[0] if results else None
```

#### Key Takeaways — Multi-Agent Researcher

- **CrewAI sequential process** enables clean handoffs between specialized agents
- **Shared memory** via Cosmos DB persists artifacts, feedback, and conversation history
- **Critics improve quality** by fact-checking and identifying gaps before final output
- **Agent memory** enables context-aware decisions across multiple tasks
- **Output files** provide audit trails for each stage of the research pipeline

---

## 14.6 Production Readiness Checklist

### Testing

| Category | Checklist Item | Status |
|----------|---------------|--------|
| **Unit Tests** | All utility functions have >90% coverage | ☐ |
| **Unit Tests** | Mock LLM calls in unit tests | ☐ |
| **Integration Tests** | End-to-end workflow tests pass | ☐ |
| **Integration Tests** | External service mocks configured | ☐ |
| **LLM Evaluation** | RAGAS/LangSmith evals run on test set | ☐ |
| **LLM Evaluation** | Hallucination rate < 5% | ☐ |
| **LLM Evaluation** | Answer relevancy > 0.8 | ☐ |
| **Load Testing** | System handles expected peak load | ☐ |
| **Load Testing** | p99 latency within SLA | ☐ |
| **Security** | Prompt injection tests pass | ☐ |
| **Security** | PII detection in outputs | ☐ |
| **Security** | Rate limiting configured | ☐ |

### Deployment

| Category | Checklist Item | Status |
|----------|---------------|--------|
| **Infrastructure** | Bicep/Terraform templates reviewed | ☐ |
| **Infrastructure** | All resources tagged (env, owner, cost-center) | ☐ |
| **Infrastructure** | Network security groups configured | ☐ |
| **Infrastructure** | Private endpoints for Azure services | ☐ |
| **CI/CD** | Pipeline includes lint, test, build, deploy | ☐ |
| **CI/CD** | Container image scanning enabled | ☐ |
| **CI/CD** | Rollback strategy documented | ☐ |
| **Secrets** | All secrets in Azure Key Vault | ☐ |
| **Secrets** | No hardcoded credentials | ☐ |
| **Secrets** | Managed identities used where possible | ☐ |

### Monitoring

| Category | Checklist Item | Status |
|----------|---------------|--------|
| **Metrics** | Application Insights configured | ☐ |
| **Metrics** | Custom business metrics tracked | ☐ |
| **Metrics** | Token usage and cost tracking | ☐ |
| **Tracing** | OpenTelemetry instrumentation | ☐ |
| **Tracing** | Distributed tracing across services | ☐ |
| **Logging** | Structured JSON logs | ☐ |
| **Logging** | Log retention policy set | ☐ |
| **Alerting** | Latency alerts configured | ☐ |
| **Alerting** | Error rate alerts configured | ☐ |
| **Alerting** | Cost anomaly alerts configured | ☐ |
| **Quality** | Periodic LLM evaluation scheduled | ☐ |
| **Quality** | Drift detection for model outputs | ☐ |

### Security

| Category | Checklist Item | Status |
|----------|---------------|--------|
| **Auth** | Azure AD / Entra ID authentication | ☐ |
| **Auth** | RBAC configured for all resources | ☐ |
| **Auth** | API keys rotated regularly | ☐ |
| **Data** | Encryption at rest enabled | ☐ |
| **Data** | TLS 1.2+ for all communications | ☐ |
| **Data** | Data retention policy defined | ☐ |
| **Input** | Input validation and sanitization | ☐ |
| **Input** | Prompt injection guardrails | ☐ |
| **Input** | Output filtering for sensitive data | ☐ |
| **Compliance** | GDPR/data residency requirements met | ☐ |
| **Compliance** | Audit logging enabled | ☐ |
| **Compliance** | Data processing agreement in place | ☐ |

#### Key Takeaways — Production Readiness

- **Testing** must cover unit, integration, LLM evaluation, load, and security dimensions
- **Deployment** requires infrastructure as code, CI/CD pipelines, and secret management
- **Monitoring** spans metrics, tracing, logging, alerting, and quality evaluation
- **Security** encompasses authentication, encryption, input validation, and compliance
- Use this checklist as a **living document** — update it as new risks and requirements emerge

---

## Summary

| Project | Core Concept | Key Technologies | Azure Services |
|---------|-------------|-----------------|----------------|
| **Book Recommender** | Hybrid search + re-ranking + personalization | LangChain, Cross-encoders, FastAPI | AI Search, Cosmos DB, Blob Storage |
| **Customer Support** | State machine + streaming + validation | LangGraph, WebSockets, React | AI Search, Cosmos DB, App Insights |
| **Market Intelligence** | Multi-agent scraping + summarization | LangChain, Playwright, asyncio | Blob Storage, AI Search, Cosmos DB |
| **Multi-Agent Researcher** | Sequential delegation + shared memory | CrewAI, LangChain | Cosmos DB, Container Apps |

All four projects demonstrate production-grade patterns:
- **Modular architecture** with clear component boundaries
- **Infrastructure as Code** for reproducible deployments
- **Evaluation-driven development** with standardized metrics
- **Observability** across metrics, traces, logs, and quality
- **Security-first design** with authentication, encryption, and guardrails
