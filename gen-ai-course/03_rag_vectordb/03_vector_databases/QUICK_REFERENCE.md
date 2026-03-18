# Quick Reference Card

## 1-Minute Setup

### Option A: Simplest (Recommended)
```bash
pip install chromadb sentence-transformers
```

```python
from sentence_transformers import SentenceTransformer
import chromadb

# Setup
embedder = SentenceTransformer('all-MiniLM-L6-v2')
db = chromadb.Client()
col = db.create_collection("docs")

# Add
docs = ["Machine learning", "Deep learning"]
embeddings = embedder.encode(docs).tolist()
col.add(ids=["1", "2"], documents=docs, embeddings=embeddings)

# Search
results = col.query(query_texts=["What is ML?"], n_results=1)
print(results["documents"][0])
```

---

### Option B: High Performance
```bash
pip install faiss-cpu sentence-transformers
```

```python
from sentence_transformers import SentenceTransformer
from solution import FAISSVectorStore

embedder = SentenceTransformer('all-MiniLM-L6-v2')
store = FAISSVectorStore(dimension=384)

# Add
docs = ["Machine learning", "Deep learning"]
vectors = embedder.encode(docs)
store.add_vectors(vectors.tolist(), docs)

# Search
q_vec = embedder.encode(["What is ML?"])[0]
results = store.search(q_vec, k=1)
for r in results:
    print(r['document'])
```

---

## Free Embedding Models Comparison

| Model | Command | Dims | Speed | Quality |
|-------|---------|------|-------|---------|
| **Sentence Transformers** | `pip install sentence-transformers` | 384 | ⚡⚡⚡ | ⭐⭐⭐ |
| **FastText** | `pip install fasttext` | 300 | ⚡⚡⚡ | ⭐⭐ |
| **Ollama** | `ollama pull nomic-embed-text` | 768 | ⚡⚡ | ⭐⭐⭐⭐ |
| **HuggingFace** | `pip install transformers` | varies | ⚡ | ⭐⭐⭐⭐ |

**Recommended:** `all-MiniLM-L6-v2` from Sentence Transformers

---

## Vector DB Comparison

| Task | Best Choice | Install |
|------|-------------|---------|
| **Learn** | Chroma | `pip install chromadb` |
| **Prototype** | Chroma | `pip install chromadb` |
| **Production (1M vectors)** | FAISS | `pip install faiss-cpu` |
| **Enterprise (1B+ vectors)** | Milvus | `docker run milvusdb/milvus` |
| **Local/Private** | Chroma/Ollama | Local only |

---

## Common Patterns

### Pattern 1: Add Text Documents
```python
docs = ["text1", "text2"]
embeddings = embedder.encode(docs).tolist()

# Chroma
collection.add(ids=["1", "2"], documents=docs, embeddings=embeddings)

# FAISS
store.add_vectors(embeddings, docs)
```

### Pattern 2: Search by Text
```python
# Chroma (takes text directly!)
results = collection.query(query_texts=["search query"], n_results=5)

# FAISS (requires embedding)
query_vec = embedder.encode(["search query"])[0]
results = store.search(query_vec, k=5)
```

### Pattern 3: Filter by Metadata
```python
# Chroma
results = collection.query(
    query_texts=["query"],
    n_results=5,
    where={"category": "AI"}
)

# FAISS (manual filtering)
results = [r for r in results if r["metadata"]["category"] == "AI"]
```

### Pattern 4: Persistent Storage
```python
# Chroma (automatic)
client = chromadb.PersistentClient(path="./db")
col = client.get_or_create_collection("docs")
# Data survives restart!

# FAISS (manual)
store.save("./faiss.bin")
# Later...
store.load("./faiss.bin")
```

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install chromadb  # Or faiss-cpu or pymilvus
```

### "Wrong dimension"
```python
# Always check dimension
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print(embedder.get_sentence_embedding_dimension())  # 384
```

### "Connection refused (Milvus)"
```bash
# Start Milvus
docker run -d -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
```

### "Out of memory"
```python
# Use FAISS IVF for large data
index = faiss.IndexIVFFlat(quantizer, dim, 100)
index.nprobe = 10
```

---

## Complete Working Example (10 minutes)

```python
#!/usr/bin/env python3
"""Complete working RAG example"""

from sentence_transformers import SentenceTransformer
import chromadb

# 1. Setup
embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.Client()
collection = client.create_collection("knowledge")

# 2. Add knowledge
docs = [
    "Python is a high-level programming language",
    "Machine learning enables computers to learn from data",
    "Deep learning uses neural networks",
]

embeddings = embedder.encode(docs).tolist()
collection.add(
    ids=[str(i) for i in range(len(docs))],
    documents=docs,
    embeddings=embeddings,
)

# 3. Answer questions
questions = [
    "What is Python?",
    "Tell me about machine learning",
    "Explain deep learning",
]

for q in questions:
    results = collection.query(
        query_texts=[q],
        n_results=1
    )
    print(f"Q: {q}")
    print(f"A: {results['documents'][0][0]}\n")
```

**Run it:**
```bash
pip install sentence-transformers chromadb
python script.py
```

---

## Performance Tips

### Fast Embedding
```python
# Batch processing (faster)
embeddings = embedder.encode(documents, batch_size=32)

# GPU acceleration
embedder = SentenceTransformer('...', device='cuda')
```

### Fast Search
```python
# Chroma: use persistent mode
client = chromadb.PersistentClient(path="./db")

# FAISS: use IVF index for large datasets
index = faiss.IndexIVFFlat(quantizer, dim, 100)

# Milvus: enable GPU search
```

### Memory Efficient
```python
# Stream process documents
for batch in batches:
    embeddings = embedder.encode(batch)
    collection.add(documents=batch, embeddings=embeddings)
```

---

## When to Use Each

```
"I'm learning"
    → Chroma + Sentence Transformers
    → pip install chromadb sentence-transformers

"I have 10K+ documents"
    → FAISS + Sentence Transformers
    → pip install faiss-cpu sentence-transformers

"I need production enterprise system"
    → Milvus + Sentence Transformers
    → docker + pip install pymilvus sentence-transformers

"I need zero internet/cloud"
    → Chroma/FAISS + Ollama
    → Local only, completely private
```

---

## Reading Order

1. 📖 This page (you are here)
2. 📖 [INSTALLATION.md](./INSTALLATION.md) - Full setup
3. 🔧 [solution.py](./solution.py) - Working code
4. 💻 [embeddings_examples.py](./embeddings_examples.py) - Free models
5. 📚 [INTEGRATION_EXAMPLES.md](./INTEGRATION_EXAMPLES.md) - 10 use cases
6. 💻 [exercise.py](./exercise.py) - Hands-on

---

## Cheat Sheet

```python
# One-liner: Simple search
from sentence_transformers import SentenceTransformer
import chromadb

e = SentenceTransformer('all-MiniLM-L6-v2')
c = chromadb.Client().create_collection("x")
c.add(ids=["1"], documents=["text"], embeddings=e.encode(["text"]).tolist())
r = c.query(query_texts=["search"], n_results=1)
print(r["documents"][0])  # Output: ["text"]
```

---

**Need help?** See [INSTALLATION.md](./INSTALLATION.md)

**Want examples?** See [INTEGRATION_EXAMPLES.md](./INTEGRATION_EXAMPLES.md)

**Want to understand?** See [concepts.md](./concepts.md)
