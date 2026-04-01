# Module 3: RAG & Vector Databases - Concepts

## Table of Contents
- [3.1 What is RAG?](#31-what-is-rag)
- [3.2 Embeddings and Chunking Strategies](#32-embeddings-and-chunking-strategies)
- [3.3 Vector Databases](#33-vector-databases)
- [3.4 Building a RAG Pipeline End-to-End](#34-building-a-rag-pipeline-end-to-end)
- [3.5 Advanced Retrieval Techniques](#35-advanced-retrieval-techniques)
- [3.6 RAG Evaluation and Metrics](#36-rag-evaluation-and-metrics)
- [3.7 Production Challenges and Common Fixes](#37-production-challenges-and-common-fixes)

---

## 3.1 What is RAG? — Overview and Use Cases

### What is Retrieval-Augmented Generation?

Retrieval-Augmented Generation (RAG) is an architecture pattern that enhances Large Language Models (LLMs) by retrieving relevant external knowledge before generating responses. Instead of relying solely on the model's training data, RAG dynamically fetches context from external data sources.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User      │────▶│  Retriever   │────▶│    LLM      │
│   Query     │     │  (Vector DB) │     │  Generator  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                    ┌──────▼──────┐         ┌─────▼─────┐
                    │  Knowledge  │         │  Response │
                    │   Base      │         │           │
                    └─────────────┘         └───────────┘
```

### Why RAG?

| Problem | Traditional LLM | RAG-Enhanced LLM |
|---------|----------------|------------------|
| Knowledge cutoff | Limited to training date | Always up-to-date |
| Hallucination | Prone to fabrication | Grounded in retrieved facts |
| Domain specificity | Generic responses | Domain-specific context |
| Data privacy | Data may leave premises | Keep sensitive data in-house |
| Citations | Cannot cite sources | Can provide source references |

### Core Components

1. **Document Store**: Raw documents (PDFs, text, databases)
2. **Embedding Model**: Converts text to vector representations
3. **Vector Database**: Stores and indexes embeddings for fast retrieval
4. **Retriever**: Finds relevant documents based on query similarity
5. **LLM Generator**: Produces responses using retrieved context

### Common Use Cases

- **Enterprise Knowledge Bases**: Internal documentation search and Q&A
- **Customer Support**: Product-specific intelligent assistants
- **Legal Document Analysis**: Case law retrieval and summarization
- **Medical Research**: Literature review and evidence-based answers
- **Financial Analysis**: Report analysis with current market data
- **Code Assistants**: Repository-specific code generation

### RAG vs Fine-Tuning

| Aspect | RAG | Fine-Tuning |
|--------|-----|-------------|
| Knowledge updates | Instant | Requires retraining |
| Cost | Lower (inference only) | Higher (training + inference) |
| Hallucination | Reduced | Still possible |
| Source attribution | Yes | No |
| Training data needed | None | Large curated dataset |

---

## 3.2 Embeddings and Chunking Strategies

### Understanding Embeddings

Embeddings are dense vector representations of text that capture semantic meaning. Similar texts have vectors that are close together in the embedding space.

```python
from openai import OpenAI
import numpy as np

client = OpenAI()

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

doc_embedding = get_embedding("Machine learning is a subset of AI")
query_embedding = get_embedding("How does AI learn from data?")

similarity = np.dot(doc_embedding, query_embedding) / (
    np.linalg.norm(doc_embedding) * np.linalg.norm(query_embedding)
)
print(f"Similarity: {similarity:.4f}")
```

### Popular Embedding Models

| Model | Dimensions | Max Tokens | Best For |
|-------|-----------|------------|----------|
| text-embedding-3-small | 1536 | 8191 | General purpose |
| text-embedding-3-large | 3072 | 8191 | High accuracy |
| BGE-large-en-v1.5 | 1024 | 512 | Open source |
| E5-large-v2 | 1024 | 512 | Multilingual |
| nomic-embed-text | 768 | 8192 | Long documents |

### Chunking Strategies

#### 1. Fixed-Size Chunking

```python
def fixed_size_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
```

#### 2. Recursive Character Chunking

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def recursive_chunk(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)
```

#### 3. Semantic Chunking

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

def semantic_chunk(text: str) -> list[str]:
    embeddings = OpenAIEmbeddings()
    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=95
    )
    return splitter.split_text(text)
```

### Chunking Best Practices

| Strategy | Chunk Size | Overlap | Best For |
|----------|-----------|---------|----------|
| Fixed-size | 200-500 tokens | 10-20% | Simple documents |
| Recursive | 500-1000 tokens | 100-200 tokens | Mixed content |
| Semantic | Variable | N/A | Complex reasoning |
| Document-specific | Format-dependent | 10% | Code, markdown, LaTeX |

---

## 3.3 Vector Databases — Setup, Integration, and Migration

### Vector Database Comparison

| Feature | Pinecone | Weaviate | Chroma | FAISS |
|---------|----------|----------|--------|-------|
| Type | Cloud | Cloud/Self-hosted | Local/Cloud | Local library |
| Scalability | Billions | Millions-Billions | Thousands-Millions | Millions (RAM) |
| Metadata filtering | Yes | Yes | Yes | Limited |
| Hybrid search | Yes | Yes | Yes | No |
| Open source | No | Yes | Yes | Yes |
| Best for | Production | Production | Development | Research |

### FAISS

```python
import faiss
import numpy as np

dimension = 1536
index = faiss.IndexFlatL2(dimension)

embeddings = np.random.random((1000, dimension)).astype('float32')
index.add(embeddings)
print(f"Index contains {index.ntotal} vectors")

query = np.random.random((1, dimension)).astype('float32')
distances, indices = index.search(query, k=5)

faiss.write_index(index, "my_index.faiss")
```

### Chroma

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection(name="documents", metadata={"hnsw:space": "cosine"})

collection.add(
    documents=["Document 1 content", "Document 2 content"],
    metadatas=[{"source": "file1.pdf"}, {"source": "file2.pdf"}],
    ids=["id1", "id2"]
)

results = collection.query(query_texts=["search query"], n_results=5)
```

### Pinecone

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

pc.create_index(
    name="rag-index",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

index = pc.Index("rag-index")
index.upsert(vectors=[{"id": "doc1", "values": embedding1, "metadata": {"text": "content"}}])

results = index.query(vector=query_embedding, top_k=5, include_metadata=True)
```

### Weaviate

```python
import weaviate
import weaviate.classes as wvc

client = weaviate.connect_to_local()

client.collections.create(
    name="Document",
    vectorizer_config=wvc.config.Configure.Vectorizer.none(),
    properties=[
        wvc.config.Property(name="text", data_type=wvc.config.DataType.TEXT),
        wvc.config.Property(name="source", data_type=wvc.config.DataType.TEXT),
 
