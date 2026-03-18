# Vector Databases

## Introduction

This topic covers production-grade vector databases with **zero cost** using free embedding models and open-source databases.

## What You'll Learn

- ✅ Using **Chroma** (simplest, beginner-friendly)
- ✅ Using **FAISS** (high-performance, scalable)
- ✅ Using **Milvus** (enterprise-grade, distributed)
- ✅ Free embedding models (Sentence Transformers, FastText, Ollama)
- ✅ Complete RAG pipeline integration
- ✅ Search optimization and filtering

## Key Concepts

1. **Vector Databases** - Specialized databases for embedding storage and search
2. **Similarity Search** - Finding semantically similar content fast
3. **Embeddings** - Numerical representations of text/images
4. **Metadata Filtering** - Combining vector and structured search
5. **Indexing** - Optimizing search performance

## Quick Start

### 1️⃣ Installation (Choose One)

**Simplest (Chroma + Sentence Transformers):**
```bash
pip install chromadb sentence-transformers numpy
```

**High Performance (FAISS):**
```bash
pip install faiss-cpu sentence-transformers numpy
```

**Enterprise (Milvus):**
```bash
docker run -d -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
pip install pymilvus sentence-transformers numpy
```

**All options:**
```bash
pip install chromadb faiss-cpu pymilvus sentence-transformers numpy
```

### 2️⃣ Try It Now (5 minutes)

```python
from sentence_transformers import SentenceTransformer
import chromadb

# Get embedder
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Create database
client = chromadb.Client()
collection = client.create_collection(name="docs")

# Add documents
docs = ["Machine learning is great", "Deep learning uses neural networks"]
embeddings = embedder.encode(docs).tolist()

collection.add(
    ids=["1", "2"],
    embeddings=embeddings,
    documents=docs
)

# Search
query_emb = embedder.encode(["What is deep learning?"]).tolist()
results = collection.query(query_embeddings=query_emb, n_results=1)
print(results["documents"][0])
```

## Recommended Learning Path

1. **Start Here:** [INSTALLATION.md](./INSTALLATION.md) - Setup & free models guide
2. **Theory:** [concepts.md](./concepts.md) - Understand vector databases
3. **Examples:**
   - `solution.py` - Chroma, FAISS, Milvus implementations
   - `embeddings_examples.py` - Free embedding models demo
4. **Hands-On:** [exercise.py](./exercise.py) - Try it yourself
5. **Test Yourself:** [quiz.md](./quiz.md)

## What's Included

| File | Purpose |
|------|---------|
| `INSTALLATION.md` | 📖 Complete setup guide (START HERE) |
| `solution.py` | 🔧 Working implementations of all 3 databases |
| `embeddings_examples.py` | 🎯 Free embedding models showcase |
| `exercise.py` | 💻 Hands-on exercises |
| `concepts.md` | 📚 Theory and concepts |
| `quiz.md` | ❓ Test your knowledge |

## Free Resources Used

### Vector Databases (All Free & Open Source)
- **Chroma** - Simplest API, perfect for learning
- **FAISS** - Industry standard, used by Meta/OpenAI
- **Milvus** - Enterprise-grade, supports 100M+ vectors

### Embedding Models (All Free)
- **Sentence Transformers** - Best balanced (recommended)
- **FastText** - Ultra-fast, lightweight
- **Ollama** - Completely local, private
- **HuggingFace** - Thousands of free models

## Comparison: Which One Should You Use?

### For Learning/Prototyping
→ **Chroma + Sentence Transformers**
```bash
pip install chromadb sentence-transformers
```

### For Production (Million+ vectors)
→ **FAISS + Sentence Transformers**
```bash
pip install faiss-cpu sentence-transformers
```

### For Enterprise/Distributed Systems
→ **Milvus + Sentence Transformers**
```bash
docker run -d -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
pip install pymilvus sentence-transformers
```

### For Maximum Privacy (Local Execution)
→ **Ollama + Any Local Vector DB**
```bash
ollama pull nomic-embed-text
pip install chromadb
```

## Key Features of Each Database

| Feature | Chroma | FAISS | Milvus |
|---------|--------|-------|--------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Scalability** | ~100K vectors | ~100M vectors | ~1B+ vectors |
| **Performance** | Good | Excellent | Excellent |
| **Memory Efficiency** | Low | Low | Medium |
| **Distributed** | No | No | Yes |
| **Best For** | Learning | Production | Enterprise |

## Free Embedding Models Comparison

| Model | Dimensions | Speed | Quality | Size | Best For |
|-------|-----------|-------|---------|------|----------|
| all-MiniLM-L6-v2 | 384 | ⚡⚡⚡ | ⭐⭐⭐ | 22MB | **START HERE** |
| all-mpnet-base-v2 | 768 | ⚡ | ⭐⭐⭐⭐ | 109MB | Best quality |
| FastText | 300 | ⚡⚡⚡ | ⭐⭐ | 1GB | Ultra-fast |
| nomic-embed-text | 768 | ⚡⚡ | ⭐⭐⭐⭐ | 274MB | Local/private |

## Prerequisites

- Understanding of embeddings from [02_embeddings_chunking](../02_embeddings_chunking/)
- Python 3.8+
- ~5GB disk space (for models and databases)

## Estimated Time

- 📖 Reading: 30 minutes
- 💻 Hands-on: 1-2 hours
- 🚀 Full setup: 10-15 minutes

## Next Steps

1. 📖 Read [INSTALLATION.md](./INSTALLATION.md)
2. 🔧 Run `solution.py` to see all options
3. 🎯 Try `embeddings_examples.py` with free models
4. 💻 Complete `exercise.py`
5. 🏗️ Build your RAG pipeline (see [04_rag_implementation](../04_rag_implementation/))

## Resources

- 📚 **Chroma Docs:** https://docs.trychroma.com/
- 📚 **FAISS Guide:** https://github.com/facebookresearch/faiss/wiki
- 📚 **Milvus Docs:** https://milvus.io/docs/
- 📚 **Sentence Transformers:** https://www.sbert.net/
- 🔗 **HuggingFace Models:** https://huggingface.co/models
- 🎓 **Vector DB Benchmarks:** https://ann-benchmarks.com/

## Common Questions

**Q: Do I need to pay for anything?**
A: No! Everything here is completely free and open-source.

**Q: Which embedding model should I use?**
A: Start with `all-MiniLM-L6-v2` - it's the best balanced.

**Q: Can I use this with LLMs like GPT/Claude?**
A: Yes! See [04_rag_implementation](../04_rag_implementation/) for complete RAG examples.

**Q: How many vectors can I store?**
A: Chroma: ~100K, FAISS: ~100M, Milvus: 1B+

**Q: Do I need a GPU?**
A: No, CPU is fine for most use cases. GPU speeds up embedding generation.

---

**Ready to start?** → [Go to INSTALLATION.md](./INSTALLATION.md)
