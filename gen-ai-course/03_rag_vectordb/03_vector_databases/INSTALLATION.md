# Vector Databases - Installation & Setup Guide

This guide covers installing and setting up production-grade vector databases with free embedding models.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Vector Databases](#vector-databases)
3. [Free Embedding Models](#free-embedding-models)
4. [Installation Steps](#installation-steps)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install basic vector database support
pip install chromadb faiss-cpu numpy

# Or with sentence transformers for embeddings
pip install chromadb sentence-transformers
```

---

## Vector Databases

### 1. **Chroma** (Recommended for Beginners)

**Best for:** Small to medium-scale projects, prototyping, local development

**Pros:**
- ✅ Simplest API
- ✅ In-memory and persistent storage options
- ✅ Built-in embedding support
- ✅ No external dependencies
- ✅ Great for learning

**Cons:**
- ❌ Not optimized for massive scale (millions of vectors)

**Installation:**
```bash
pip install chromadb
```

**Quick Example:**
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection(name="my_documents")

collection.add(
    documents=["Hello world", "How are you?"],
    ids=["1", "2"]
)

results = collection.query(
    query_texts=["Greetings"],
    n_results=1
)
```

---

### 2. **FAISS** (Facebook AI Similarity Search)

**Best for:** Large-scale similarity search, high-performance needs

**Pros:**
- ✅ Industry standard (used by Meta, OpenAI, etc.)
- ✅ Extremely fast similarity search
- ✅ Handles millions of vectors efficiently
- ✅ Multiple index types (Flat, IVF, HNSW)
- ✅ GPU support available

**Cons:**
- ❌ More complex API
- ❌ Requires manual vector management

**Installation:**
```bash
# CPU-only (recommended for most users)
pip install faiss-cpu

# GPU support (requires CUDA)
pip install faiss-gpu
```

**Quick Example:**
```python
import faiss
import numpy as np

# Create index
index = faiss.IndexFlatL2(128)  # 128-dimensional vectors

# Add vectors
vectors = np.random.random((1000, 128)).astype('float32')
index.add(vectors)

# Search
query = np.random.random((1, 128)).astype('float32')
distances, indices = index.search(query, k=5)
```

---

### 3. **Milvus** (Enterprise-Grade)

**Best for:** Production systems, distributed deployments, large enterprises

**Pros:**
- ✅ Distributed architecture
- ✅ Supports billions of vectors
- ✅ High availability & reliability
- ✅ Advanced features (partitions, replicas)
- ✅ Multiple index types

**Cons:**
- ❌ Requires server deployment
- ❌ Higher operational complexity
- ❌ Overkill for small projects

**Installation:**

**Option A: Docker (Recommended)**
```bash
# Start Milvus server
docker run -d \
  --name milvus \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest

# Python client
pip install pymilvus
```

**Option B: From Source**
```bash
# See https://milvus.io/docs/install_standalone.md
pip install pymilvus
```

**Quick Example:**
```python
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections

# Connect
connections.connect(host="localhost", port=19530)

# Create collection
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
]
schema = CollectionSchema(fields)
collection = Collection("my_collection", schema=schema)

# Insert
collection.insert([[i for i in range(128)]])

# Search
results = collection.search([[i for i in range(128)]], "vector", limit=5)
```

---

## Free Embedding Models

### Option 1: **Sentence Transformers** (Recommended)

**Model:** `all-MiniLM-L6-v2` - Fast, lightweight, free

```bash
pip install sentence-transformers
```

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # Downloads automatically

# Get embeddings
texts = [
    "Machine learning is great",
    "Deep learning uses neural networks"
]
embeddings = model.encode(texts)
print(embeddings.shape)  # (2, 384)
```

**Popular Free Models:**
- `all-MiniLM-L6-v2` (384 dims, 22M params) - **Best balanced**
- `all-MiniLM-L12-v2` (384 dims, 33M params) - Slightly better, slightly slower
- `distiluse-base-multilingual-cased-v2` (512 dims) - Multilingual
- `all-mpnet-base-v2` (768 dims) - Most powerful but slower

### Option 2: **HuggingFace Transformers**

```bash
pip install transformers torch
```

```python
from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

inputs = tokenizer("Hello world", return_tensors="pt")
outputs = model(**inputs)
embeddings = outputs.last_hidden_state[:, 0]  # CLS token
```

### Option 3: **FastText** (Very Fast, Lightweight)

```bash
pip install fasttext
```

```python
import fasttext

# Load pre-trained model (auto-downloads)
model = fasttext.load_model("cc.en.300.bin")  # 300-dimensional

embedding = model.get_sentence_vector("Machine learning")
print(embedding.shape)  # (300,)
```

### Option 4: **Ollama** (Completely Local)

```bash
# Install Ollama from https://ollama.ai/

# Pull an embedding model
ollama pull nomic-embed-text
```

```python
import ollama

response = ollama.embeddings(
    model="nomic-embed-text",
    prompt="Hello world"
)
print(response["embedding"])  # 768-dimensional vector
```

### Comparison Table

| Model | Dims | Speed | Quality | Size | License |
|-------|------|-------|---------|------|---------|
| all-MiniLM-L6-v2 | 384 | ⚡⚡⚡ | ⭐⭐⭐ | 22M | Apache 2.0 |
| all-MiniLM-L12-v2 | 384 | ⚡⚡ | ⭐⭐⭐ | 33M | Apache 2.0 |
| all-mpnet-base-v2 | 768 | ⚡ | ⭐⭐⭐⭐ | 109M | Apache 2.0 |
| FastText cc.en.300 | 300 | ⚡⚡⚡ | ⭐⭐ | 1GB | CCBY 4.0 |
| nomic-embed-text | 768 | ⚡⚡ | ⭐⭐⭐⭐ | 274M | OpenRail |

---

## Installation Steps

### Step 1: Basic Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Vector Databases

**For Chroma (Easiest):**
```bash
pip install chromadb sentence-transformers numpy
```

**For FAISS (High Performance):**
```bash
pip install faiss-cpu sentence-transformers numpy
```

**For Milvus (Enterprise):**
```bash
# Start Milvus with Docker
docker run -d --name milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest

# Install client
pip install pymilvus numpy
```

**For All (Comprehensive):**
```bash
pip install chromadb faiss-cpu pymilvus sentence-transformers numpy
```

### Step 3: Verify Installation

```python
# Test Chroma
import chromadb
client = chromadb.Client()
print("✓ Chroma installed")

# Test FAISS
import faiss
print("✓ FAISS installed")

# Test Sentence Transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Sentence Transformers installed")
```

---

## Complete Example: Chroma + Sentence Transformers

```python
from sentence_transformers import SentenceTransformer
import chromadb

# 1. Initialize embedding model
embeddings = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Initialize Chroma
client = chromadb.Client()
collection = client.create_collection(name="documents")

# 3. Add documents
documents = [
    "Machine learning is a subset of artificial intelligence",
    "Deep learning uses neural networks with multiple layers",
    "Natural language processing helps computers understand text",
]

# Embed documents
doc_embeddings = embeddings.encode(documents).tolist()

# Add to Chroma
collection.add(
    ids=["1", "2", "3"],
    embeddings=doc_embeddings,
    documents=documents,
    metadatas=[{"source": "wiki"} for _ in documents]
)

# 4. Search
query = "What is machine learning?"
query_embedding = embeddings.encode([query]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=2
)

print("Top results:")
for doc in results["documents"][0]:
    print(f"  - {doc}")
```

---

## Docker Setup (for Milvus)

### Quick Start

```bash
# Start Milvus
docker run -d \
  --name milvus-server \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest

# Check status
docker logs milvus-server

# Stop Milvus
docker stop milvus-server

# Remove container
docker rm milvus-server
```

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  milvus:
    image: milvusdb/milvus:latest
    ports:
      - "19530:19530"
      - "9091:9091"
    volumes:
      - milvus_data:/var/lib/milvus

volumes:
  milvus_data:
```

Run:
```bash
docker-compose up -d
docker-compose down
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'chromadb'"

**Solution:**
```bash
pip install chromadb
```

### Issue: "Cannot import FAISS"

**Solution:**
```bash
# CPU version
pip install faiss-cpu

# Or GPU version (requires CUDA)
pip install faiss-gpu
```

### Issue: "Milvus connection refused"

**Solution:**
```bash
# Verify Milvus is running
docker ps | grep milvus

# If not running, start it
docker run -d --name milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest

# Check connection
python -c "from pymilvus import connections; connections.connect(host='localhost', port=19530); print('Connected!')"
```

### Issue: "Sentence Transformers model download fails"

**Solution:**
```bash
# Set HF_HOME to custom cache directory
export HF_HOME="/path/to/cache"
python your_script.py

# Or manually download
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/custom/path')
```

### Issue: Memory issues with large datasets

**Solution:**
```bash
# For FAISS: Use memory-mapped index
import faiss
index = faiss.IndexIVFFlat(...)  # Use IVF for clustering
index.nprobe = 10  # Adjust search precision

# For Chroma: Use persistent storage
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")

# For Milvus: Batch operations
for i in range(0, len(vectors), 10000):
    collection.insert(vectors[i:i+10000])
```

---

## Choosing the Right Database

| Need | Recommendation |
|------|-----------------|
| Learning/Prototyping | **Chroma** |
| Production (millions of vectors) | **FAISS** or **Milvus** |
| Enterprise/Distributed | **Milvus** |
| Maximum performance | **FAISS** |
| Simplest setup | **Chroma** |
| Multi-language support | **Sentence Transformers** with any DB |

---

## Next Steps

1. Run `solution.py` to see all databases in action
2. Try the examples in `exercise.py`
3. Experiment with different embedding models
4. Integrate with LangChain RAG pipeline (see `04_rag_implementation`)

---

## Resources

- **Chroma:** https://docs.trychroma.com/
- **FAISS:** https://github.com/facebookresearch/faiss/wiki
- **Milvus:** https://milvus.io/docs/
- **Sentence Transformers:** https://www.sbert.net/
- **HuggingFace Models:** https://huggingface.co/models
