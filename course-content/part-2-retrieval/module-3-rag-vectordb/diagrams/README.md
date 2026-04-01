# Module 3: RAG & Vector Databases — Diagrams

Visual reference for RAG architecture, embedding pipelines, vector databases, chunking strategies, retrieval flows, and evaluation frameworks.

---

## 1. RAG Architecture Overview

### High-Level RAG Pipeline

```
+---------------------------------------------------------------------------+
|                           RAG SYSTEM ARCHITECTURE                          |
+---------------------------------------------------------------------------+
|                                                                            |
|  OFFLINE (Indexing) PIPELINE              ONLINE (Query) PIPELINE          |
|                                                                            |
|  +----------+                             +--------------+                 |
|  | Raw Docs |                             |  User Query  |                 |
|  | PDF/HTML |                             |  "What is X?"|                 |
|  | Markdown |                             +------+-------+                 |
|  +----+-----+                                    |                         |
|       |                                   +------v-------+                 |
|  +----v-----+                             |   Embedding  |                 |
|  |  Loader  |                             |    Model     |                 |
|  |& Parser  |                             +------+-------+                 |
|  +----+-----+                                    |                         |
|       |                                    Query Vector                     |
|  +----v-----+                                    |                         |
|  | Chunking |                             +------v-------+                 |
|  | Strategy |                             |    Vector    |                 |
|  +----+-----+                             |  Similarity  |                 |
|       |                                   |    Search    |                 |
|  +----v-----+                             +------+-------+                 |
|  |Embedding |                                    |                         |
|  |  Model   |                             +------v-------+                 |
|  +----+-----+                             |  Top-K Docs  |                 |
|       |                                   +------+-------+                 |
|  +----v-------------+                           |                         |
|  |   Vector Store   |+------- stored ----- +----v--------------+          |
|  |  (Chroma/FAISS/  |      embeddings      |   LLM Generator   |          |
|  |   Pinecone)      |                      |  "Given context,  |          |
|  +------------------+                      |   answer the Q"   |          |
|                                            +----+--------------+          |
|                                                 |                         |
|                                            +----v-------+                 |
|                                            |  Response  |                 |
|                                            | + Citations |                 |
|                                            +------------+                 |
+---------------------------------------------------------------------------+
```

### Mermaid — RAG System Architecture

```mermaid
graph TB
    subgraph Offline["Offline Indexing Pipeline"]
        A[Raw Documents] --> B[Document Loader & Parser]
        B --> C[Text Chunking]
        C --> D[Embedding Model]
        D --> E[Vector Store]
    end

    subgraph Online["Online Query Pipeline"]
        F[User Query] --> G[Query Embedding]
        G --> H[Vector Similarity Search]
        H --> I[Top-K Retrieved Chunks]
        I --> J[Prompt Construction]
        J --> K[LLM Generation]
        K --> L[Response + Citations]
    end

    E -.-> H

    style Offline fill:#e8f4f8,stroke:#2196F3
    style Online fill:#f3e8f8,stroke:#9C27B0
    style E fill:#fff3e0,stroke:#FF9800
```

---

## 2. Embedding Pipeline

### Text to Vector Conversion

```
+--------------------------------------------------------------+
|                   EMBEDDING PIPELINE                          |
+--------------------------------------------------------------+
|                                                               |
|  "Machine learning is a subset      +---------------------+  |
|   of artificial intelligence"  ---> |  Tokenizer          |  |
|                                     |  [Machine, learning, |  |
|                                     |   is, a, subset,     |  |
|                                     |   of, artificial,    |  |
|                                     |   intelligence]      |  |
|                                     +----------+----------+  |
|                                                |              |
|                                     +----------v----------+  |
|                                     |  Transformer Encoder |  |
|                                     |  +----------------+  |  |
|                                     |  | Self-Attention  |  |  |
|                                     |  | Feed-Forward    |  |  |
|                                     |  | Layer Norm      |  |  |
|                                     |  +----------------+  |  |
|                                     +----------+----------+  |
|                                                |              |
|                                     +----------v----------+  |
|                                     |  Pooling Layer       |  |
|                                     |  (Mean/CLS Token)    |  |
|                                     +----------+----------+  |
|                                                |              |
|  Vector: [0.023, -0.187, 0.451,               v              |
|           ..., 0.089]         <---- Dense Vector (1536-d)    |
|                                                               |
+--------------------------------------------------------------+
```

### Mermaid — Embedding Generation Flow

```mermaid
flowchart LR
    A[Raw Text] --> B[Tokenizer]
    B --> C[Token IDs]
    C --> D[Token Embeddings]
    D --> E[Transformer Layers]
    E --> F[Hidden States]
    F --> G{Pooling Strategy}
    G -->|Mean Pooling| H[Average all tokens]
    G -->|CLS Token| I[First token output]
    H --> J[Normalized Embedding Vector]
    I --> J
    J --> K[Store in Vector DB]

    style A fill:#e3f2fd
    style J fill:#e8f5e9
    style K fill:#fff3e0
```

### Embedding Model Comparison

```
+-----------------------------------------------------------------------+
|                    EMBEDDING MODEL COMPARISON                          |
+-------------------+--------+-----------+--------+--------------------+
| Model             | Dims   | Max Tokens| Type   | Best For           |
+-------------------+--------+-----------+--------+--------------------+
| text-embed-3-sm   | 1536   | 8191      | Cloud  | General purpose    |
| text-embed-3-lg   | 3072   | 8191      | Cloud  | High accuracy      |
| BGE-large-en      | 1024   | 512       | Local  | Open source        |
| E5-large-v2       | 1024   | 512       | Local  | Multilingual       |
| nomic-embed-text  | 768    | 8192      | Local  | Long documents     |
| all-MiniLM-L6-v2  | 384    | 256       | Local  | Fast/speed         |
+-------------------+--------+-----------+--------+--------------------+
| Higher dimensions = richer representation, more storage/compute        |
| Longer max tokens = can embed larger chunks without truncation         |
+-----------------------------------------------------------------------+
```

---

## 3. Vector Database Comparison

### Feature Matrix

```
+------------------------------------------------------------------------------+
|                     VECTOR DATABASE COMPARISON                                |
+--------------+----------+----------+----------+----------+------------------+
| Feature      | FAISS    | Chroma   | Pinecone | Weaviate | Milvus           |
+--------------+----------+----------+----------+----------+------------------+
| Type         | Library  | DB       | Cloud    | Hybrid   | DB               |
| Deployment   | Local    | Local    | SaaS     | Either   | Self-hosted      |
| Scalability  | RAM      | Millions | Billions | Millions | Billions         |
| Index Types  | 10+      | HNSW     | Proprietary| HNSW   | 7+               |
| Metadata     | Limited  | Yes      | Yes      | Yes      | Yes              |
| Hybrid Search| No       | Yes      | Yes      | Yes      | Yes              |
| GPU Support  | Yes      | No       | N/A      | No       | Yes              |
| License      | MIT      | Apache   | Proprietary| BSD    | Apache           |
+--------------+----------+----------+----------+----------+------------------+
| Setup Effort | Medium   | Low      | Low      | Medium   | High             |
| Cost         | Free     | Free     | $$       | Free/$   | Free/$           |
+--------------+----------+----------+----------+----------+------------------+
|                                                                            |
| Use FAISS: Research, large local datasets, need GPU acceleration           |
| Use Chroma: Prototyping, small apps, learning RAG                          |
| Use Pinecone: Production, managed, zero-ops                                |
| Use Weaviate: Production, hybrid search, self-hosted option                |
| Use Milvus: Massive scale, distributed, enterprise                         |
+------------------------------------------------------------------------------+
```

### Mermaid — Vector DB Selection Decision Tree

```mermaid
flowchart TD
    A[Need a Vector DB?] --> B{Scale?}
    B -->|< 100K vectors| C{Prototyping?}
    B -->|100K - 10M| D{Cloud or Self-hosted?}
    B -->|> 10M| E[Consider Milvus or Pinecone]

    C -->|Yes| F[Chroma]
    C -->|No| G[FAISS or Chroma]

    D -->|Cloud Managed| H[Pinecone]
    D -->|Self-hosted| I{Need hybrid search?}
    I -->|Yes| J[Weaviate]
    I -->|No| K[FAISS or Qdrant]

    E -->|Managed| L[Pinecone Enterprise]
    E -->|Self-hosted| M[Milvus Cluster]

    style F fill:#e8f5e9
    style H fill:#e3f2fd
    style J fill:#fff3e0
    style M fill:#fce4ec
```

---

## 4. Chunking Strategies

### Strategy Comparison

```
+---------------------------------------------------------------------------+
|                        CHUNKING STRATEGIES                                 |
+---------------------------------------------------------------------------+
|                                                                            |
|  FIXED-SIZE CHUNKING                                                       |
|  +------------+------------+------------+------------+                    |
|  | Chunk 1    | Chunk 2    | Chunk 3    | Chunk 4    |                    |
|  | ########## | oo######## | oo######## | oo######## |                    |
|  | 500 chars  | 500 chars  | 500 chars  | 500 chars  |                    |
|  +------------+------------+------------+------------+                    |
|  oo = overlap (50 chars)                                                   |
|  + Simple, fast  x Breaks sentences/paragraphs                            |
|                                                                            |
|  RECURSIVE CHARACTER CHUNKING                                              |
|  +------------------+------------------+------------------+               |
|  | Paragraph 1      | Paragraph 2+3    | Paragraph 4      |               |
|  | + Sentence split | + Word boundary  | + Remainder      |               |
|  +------------------+------------------+------------------+               |
|  Splits: \n\n -> \n -> . -> " " -> ""                                     |
|  + Respects structure  x May still split mid-idea                         |
|                                                                            |
|  SEMANTIC CHUNKING                                                         |
|  +-----------------------+  +----------------+  +------------------+      |
|  | Topic A               |  | Topic B        |  | Topic C          |      |
|  | (high internal sim)   |  | (boundary)     |  | (high internal)  |      |
|  +-----------------------+  +----------------+  +------------------+      |
|  Splits where embedding similarity drops below threshold                   |
|  + Topically coherent  x Variable sizes, slower, costs embeddings        |
|                                                                            |
|  DOCUMENT-SPECIFIC CHUNKING                                                |
|  +----------+----------+----------+----------+                            |
|  | Function | Function | Class    | Method   |                            |
|  | def foo  | def bar  | class X  | def m1   |                            |
|  +----------+----------+----------+----------+                            |
|  + Preserves code/docs structure  x Requires custom parsers               |
|                                                                            |
+---------------------------------------------------------------------------+
```

### Mermaid — Chunking Decision Flow

```mermaid
flowchart TD
    A[Document to Chunk] --> B{Content Type?}

    B -->|Code| C[Document-Specific]
    C --> C1[Split by function/class]

    B -->|Markdown/LaTeX| D[Format-Aware Recursive]
    D --> D1[Split on headers, then paragraphs]

    B -->|Mixed prose| E{Need semantic accuracy?}
    E -->|High| F[Semantic Chunking]
    F --> F1[Split at meaning boundaries]
    E -->|Standard| G[Recursive Character]
    G --> G1[Split on \n\n -> \n -> . -> space]

    B -->|Simple/plain text| H[Fixed-Size]
    H --> H1[Every N tokens with overlap]

    C1 --> I[Set overlap 0-10%]
    D1 --> J[Set overlap 10-15%]
    F1 --> K[No overlap needed]
    G1 --> L[Set overlap 10-20%]
    H1 --> M[Set overlap 10-20%]

    style F fill:#e8f5e9
    style G fill:#e3f2fd
    style H fill:#fff3e0
```

---

## 5. Retrieval Flow

### Standard vs. Advanced Retrieval

```
+---------------------------------------------------------------------------+
|                      STANDARD RAG RETRIEVAL                                |
+---------------------------------------------------------------------------+
|                                                                            |
|  Query --> Embed --> Vector Search --> Top-K --> LLM --> Answer           |
|                                                                            |
|  Simple but limited: may miss relevant docs, no re-ranking               |
|                                                                            |
+---------------------------------------------------------------------------+

+---------------------------------------------------------------------------+
|                      ADVANCED RAG RETRIEVAL                                |
+---------------------------------------------------------------------------+
|                                                                            |
|                    +--- Dense Search (embeddings) ---+                     |
|                    |                                  |                     |
|  Query --> Query --+                                  +--> Reciprocal -->  |
|           Transform|                                  |    Rank Fusion     |
|                    +--- Sparse Search (BM25) ---------+        |           |
|                                                                |           |
|                                                           +----v----+      |
|                                                           | Top 20  |      |
|                                                           |candidates|     |
|                                                           +----+----+      |
|                                                                |           |
|                                                           +----v----+      |
|                                                           |Re-ranker|      |
|                                                           |(cross-  |      |
|                                                           |encoder) |      |
|                                                           +----+----+      |
|                                                                |           |
|                                                           +----v----+      |
|                                                           | Top 5   |      |
|                                                           | final   |      |
|                                                           +----+----+      |
|                                                                |           |
|                                                    +-----------v--------+  |
|                                                    |  Compression       |  |
|                                                    |  (extract key      |  |
|                                                    |   sentences)       |  |
|                                                    +-----------+--------+  |
|                                                                |           |
|                                                    +-----------v--------+  |
|                                                    |  LLM Generate      |  |
|                                                    |  + Faithfulness    |  |
|                                                    |    Check           |  |
|                                                    +-----------+--------+  |
|                                                                |           |
|                                                           +----v----+      |
|                                                           | Answer  |      |
|                                                           +---------+      |
+---------------------------------------------------------------------------+
```

### Mermaid — Retrieval Strategies

```mermaid
flowchart TD
    Q[User Query] --> QT[Query Transformation]
    QT --> Q1[Original Query]
    QT --> Q2[Expanded Query 1]
    QT --> Q3[Expanded Query 2]

    Q1 --> D1[Dense Search]
    Q2 --> D1
    Q3 --> D1
    Q1 --> S1[Sparse BM25 Search]

    D1 --> RRF[Reciprocal Rank Fusion]
    S1 --> RRF

    RRF --> TOP20[Top 20 Candidates]
    TOP20 --> RE[Re-Ranker Cross-Encoder]
    RE --> TOP5[Top 5 Final Chunks]
    TOP5 --> COMP[Contextual Compression]
    COMP --> LLM[LLM Generation]
    LLM --> FC[Faithfulness Check]
    FC --> ANS[Final Answer]

    style QT fill:#fff3e0
    style RE fill:#e8f5e9
    style FC fill:#fce4ec
```

---

## 6. Evaluation Framework

### RAG Evaluation Dimensions

```
+------------------------------------------------------------------------------+
|                      RAG EVALUATION FRAMEWORK                                 |
+------------------------------------------------------------------------------+
|                                                                               |
|                         +------------------+                                  |
|                         |    User Query    |                                  |
|                         +--------+---------+                                  |
|                                  |                                            |
|                    +-------------v--------------+                             |
|                    |                            |                             |
|           +--------v---------+        +--------v---------+                   |
|           |  RETRIEVAL       |        |  GENERATION      |                   |
|           |  EVALUATION      |        |  EVALUATION      |                   |
|           +--------+---------+        +--------+---------+                   |
|                    |                            |                             |
|  +-----------------+------------+   +----------+-----------+                 |
|  |                 |            |   |         |            |                 |
|  v                 v            v   v         v            v                 |
| +------+  +----------+  +------+  +--------+  +----------+  +--------+      |
| |Preci-|  |          |  |      |  |Faithful|  | Answer   |  |        |      |
| |sion  |  | Recall   |  | MRR  |  | ness   |  |Relevance |  |Correct |      |
| |  @k  |  |   @k     |  |      |  |        |  |          |  |  ness  |      |
| +--+---+  +----+-----+  +--+---+  +---+----+  +----+-----+  +---+----+      |
|    |           |           |           |            |            |           |
|    v           v           v           v            v            v           |
|  "Are the   "Did we     "Is the    "Is the      "Does the    "Is the        |
|   retrieved  find all   first      answer       answer       answer         |
|   docs       relevant   relevant   grounded     relevant     factually      |
|   relevant?" docs?"     result     in context?" to query?"   correct?"      |
|                          first?"                                             |
|                                                                               |
+------------------------------------------------------------------------------+
|                                                                               |
|  METRIC FORMULAS                                                             |
|                                                                               |
|  Precision@k = |relevant intersection retrieved| / k                         |
|  Recall@k    = |relevant intersection retrieved| / |all relevant|            |
|  MRR         = 1/N x 1/rank_i                                                |
|  F1          = 2 x (Precision x Recall) / (Precision + Recall)               |
|  NDCG        = DCG / IDCG (position-weighted relevance)                      |
|                                                                               |
|  RAGAS Framework:                                                            |
|  +-- Context Precision: Are retrieved chunks relevant?                       |
|  +-- Context Recall: Do chunks cover the ground truth?                       |
|  +-- Faithfulness: Is answer supported by context?                           |
|  +-- Answer Relevancy: Does answer address the question?                     |
|                                                                               |
+------------------------------------------------------------------------------+
```

### Mermaid — Evaluation Pipeline

```mermaid
flowchart LR
    subgraph Dataset["Evaluation Dataset"]
        Q[Questions]
        GT[Ground Truth Answers]
        CT[Relevant Contexts]
    end

    subgraph Retrieval["Retrieval Metrics"]
        P[Precision@k]
        R[Recall@k]
        M[MRR]
        N[NDCG]
    end

    subgraph Generation["Generation Metrics"]
        F[Faithfulness]
        AR[Answer Relevancy]
        CR[Context Relevancy]
    end

    subgraph EndToEnd["End-to-End"]
        E2E[Correctness + Fluency]
    end

    Q --> RAG[RAG System]
    RAG --> Retrieved[Retrieved Chunks]
    RAG --> Answer[Generated Answer]

    Retrieved --> P
    Retrieved --> R
    CT --> P
    CT --> R
    Retrieved --> M
    GT --> N

    Answer --> F
    CT --> F
    Answer --> AR
    Q --> AR
    Retrieved --> CR
    Q --> CR

    Answer --> E2E
    GT --> E2E

    style Retrieval fill:#e3f2fd
    style Generation fill:#e8f5e9
    style EndToEnd fill:#fff3e0
```

### Evaluation Metrics Summary Table

```
+-----------------------------------------------------------------------+
|                    EVALUATION METRICS SUMMARY                          |
+-------------------+---------------+----------------+-----------------+
| Metric            | Component     | Measures       | Target          |
+-------------------+---------------+----------------+-----------------+
| Precision@k       | Retrieval     | Relevant/total | > 0.8           |
| Recall@k          | Retrieval     | Found/all      | > 0.9           |
| MRR               | Retrieval     | First relevant | > 0.7           |
| NDCG              | Retrieval     | Rank quality   | > 0.8           |
| Faithfulness      | Generation    | Groundedness   | > 0.9           |
| Answer Relevancy  | Generation    | Topic match    | > 0.85          |
| Context Relevancy | Retrieval+Gen | Chunk quality  | > 0.8           |
| Correctness       | End-to-End    | Factual match  | Task-dependent  |
+-------------------+---------------+----------------+-----------------+
| Use RAGAS, DeepEval, or custom LLM-as-Judge for automated eval       |
+-----------------------------------------------------------------------+
```
