# Vector Database Setup Checklist

Complete this checklist to set up everything properly.

---

## ✅ Phase 1: Read Documentation (20 min)

- [ ] Read [README.md](./README.md) - Overview
- [ ] Read [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Fast setup
- [ ] Skim [INSTALLATION.md](./INSTALLATION.md) - Full guide
- [ ] Choose: **Chroma** / **FAISS** / **Milvus** (or all)

**Recommended choice:** Start with **Chroma** (simplest)

---

## ✅ Phase 2: Install Dependencies (5-10 min)

### Option A: Chroma (Simplest, Recommended)
```bash
pip install chromadb sentence-transformers numpy
```

Test installation:
```bash
python -c "import chromadb; print('✓ Chroma OK')"
python -c "from sentence_transformers import SentenceTransformer; print('✓ Sentence Transformers OK')"
```

- [ ] Chroma installed
- [ ] Sentence Transformers installed

### Option B: FAISS (High Performance)
```bash
pip install faiss-cpu sentence-transformers numpy
```

Test installation:
```bash
python -c "import faiss; print('✓ FAISS OK')"
```

- [ ] FAISS installed
- [ ] Sentence Transformers installed

### Option C: Milvus (Enterprise)
```bash
# Start Milvus with Docker
docker run -d -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest

# Install Python client
pip install pymilvus sentence-transformers numpy
```

Test connection:
```bash
python -c "from pymilvus import connections; connections.connect(host='localhost', port=19530); print('✓ Milvus OK')"
```

- [ ] Docker running
- [ ] Milvus installed
- [ ] Connection verified

### Option D: All (Comprehensive)
```bash
pip install chromadb faiss-cpu pymilvus sentence-transformers numpy
```

- [ ] All packages installed

---

## ✅ Phase 3: Run Examples (30 min)

### Step 1: Test Basic Setup
```python
from sentence_transformers import SentenceTransformer

# Download model (one-time, ~120MB)
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f"✓ Model loaded. Dimension: {model.get_sentence_embedding_dimension()}")

# Test embedding
embedding = model.encode("Hello world")
print(f"✓ Embedding shape: {embedding.shape}")
```

- [ ] Model downloads successfully
- [ ] Embedding works

### Step 2: Test Chroma
Create `test_chroma.py`:
```python
from sentence_transformers import SentenceTransformer
import chromadb

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.Client()
collection = client.create_collection("test")

docs = ["Hello world", "Hi there"]
embeddings = embedder.encode(docs).tolist()

collection.add(
    ids=["1", "2"],
    documents=docs,
    embeddings=embeddings
)

results = collection.query(query_texts=["Hi"], n_results=1)
print(f"✓ Found: {results['documents'][0]}")
```

Run: `python test_chroma.py`

- [ ] Chroma collection created
- [ ] Documents added
- [ ] Search works

### Step 3: Run solution.py
```bash
cd gen-ai-course/03_rag_vectordb/03_vector_databases
python solution.py
```

Expected output:
```
============================================================
CHROMA - Simplest Production Option
============================================================
Added 4 documents to Chroma
Search results:
  - Machine learning definition (distance: 0.123)
```

- [ ] `solution.py` runs successfully
- [ ] All 3 databases show (Chroma, FAISS, Milvus)

### Step 4: Run embeddings_examples.py
```bash
python embeddings_examples.py
```

Expected output:
```
🚀 Free Embedding Models Examples
[Various examples...]
✓ All examples completed!
```

- [ ] Multiple embedding models work
- [ ] Integration with Chroma works

---

## ✅ Phase 4: Understand Theory (30 min)

- [ ] Read [concepts.md](./concepts.md)
- [ ] Read [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Compare old vs new
- [ ] Read first 5 examples from [INTEGRATION_EXAMPLES.md](./INTEGRATION_EXAMPLES.md)

**Key concepts to understand:**
- [ ] What are embeddings?
- [ ] What is similarity search?
- [ ] When to use each database?
- [ ] How to choose embedding models?

---

## ✅ Phase 5: Practice with Examples (1 hour)

### Example 1: Simple Q&A
From [INTEGRATION_EXAMPLES.md](./INTEGRATION_EXAMPLES.md), copy "Simple Document Q&A" example.

Create `my_qa.py`:
```python
# (Copy from INTEGRATION_EXAMPLES.md)
```

Run: `python my_qa.py`

- [ ] Successfully copied and ran example
- [ ] Q&A works

### Example 2: Multi-Language Search
From [INTEGRATION_EXAMPLES.md](./INTEGRATION_EXAMPLES.md), copy "Multi-Language Search" example.

- [ ] Example runs
- [ ] Multi-language results visible

### Example 3: Your Own Example
Create a new file `my_example.py` with:
- A knowledge base (3-5 documents)
- At least 2 search queries
- Metadata filtering

- [ ] Created custom example
- [ ] Runs without errors
- [ ] Gets relevant results

---

## ✅ Phase 6: Complete Exercises (1-2 hours)

In the same directory, there's `exercise.py`:
```bash
python exercise.py
```

Complete all exercises in the file:
- [ ] Exercise 1 completed
- [ ] Exercise 2 completed
- [ ] Exercise 3 completed
- [ ] Exercise 4 completed
- [ ] Exercise 5 completed

---

## ✅ Phase 7: Test Knowledge (15 min)

Answer quiz questions in [quiz.md](./quiz.md):

- [ ] All quiz questions answered
- [ ] Score: ___ / 10

**Target:** 8/10 or higher

---

## ✅ Phase 8: Integration (Optional, 1+ hours)

Connect to [04_rag_implementation](../04_rag_implementation/):

- [ ] Read RAG implementation guide
- [ ] Create RAG pipeline using this database
- [ ] Test end-to-end with LLM

---

## 🎯 Summary Checklist

### Understanding
- [ ] Know the 3 databases (Chroma, FAISS, Milvus)
- [ ] Know when to use each
- [ ] Understand free embedding models
- [ ] Know how to install and test

### Practical Skills
- [ ] Can create collection/index
- [ ] Can add documents
- [ ] Can search
- [ ] Can filter by metadata
- [ ] Can persist data

### Code Quality
- [ ] Examples run without errors
- [ ] Custom example created
- [ ] Exercises completed
- [ ] Quiz questions answered

---

## 🚀 Next Steps After Completion

1. **Build a RAG Pipeline**
   - See [04_rag_implementation](../04_rag_implementation/)
   - Integrate vector DB with LLM

2. **Scale Up**
   - Try FAISS for larger datasets
   - Learn about different index types

3. **Optimize**
   - Monitor performance
   - Use batching
   - Consider GPU acceleration

4. **Deploy**
   - Use Milvus for production
   - Set up persistence
   - Monitor in production

---

## 📚 Resource Map

| Task | File |
|------|------|
| Quick setup (2 min) | [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) |
| Full setup (30 min) | [INSTALLATION.md](./INSTALLATION.md) |
| See working code | [solution.py](./solution.py) |
| Learn embedding models | [embeddings_examples.py](./embeddings_examples.py) |
| Copy-paste examples | [INTEGRATION_EXAMPLES.md](./INTEGRATION_EXAMPLES.md) |
| Understand concepts | [concepts.md](./concepts.md) |
| Migrate from old code | [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) |
| Test yourself | [quiz.md](./quiz.md) |
| Hands-on practice | [exercise.py](./exercise.py) |

---

## 💡 Tips for Success

1. **Start with Chroma** - It's the easiest, best for learning
2. **Use `all-MiniLM-L6-v2` embedding model** - Best balanced, widely recommended
3. **Copy examples first** - Don't write from scratch, understand by modifying
4. **Read error messages** - They tell you exactly what's wrong
5. **Test each step** - Don't skip verification steps
6. **Ask questions** - When stuck, check [INSTALLATION.md](./INSTALLATION.md) troubleshooting

---

## ❓ Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'chromadb'"
**Solution:** Run `pip install chromadb`

### Issue: "Port 19530 already in use"
**Solution:** Milvus already running. Stop it: `docker stop milvus`

### Issue: "Model download fails"
**Solution:**
```bash
export HF_HOME="./models"  # Use local cache
pip install sentence-transformers
```

### Issue: "Out of memory"
**Solution:**
- Use smaller model: `all-MiniLM-L6-v2` instead of `all-mpnet-base-v2`
- Process in batches
- Try FAISS with IVF index

### Issue: "Search returns empty results"
**Solution:**
- Check: Are documents added? `print(collection.count())`
- Check: Is query in similar language as docs?
- Try: Simpler query terms

---

## 📊 Progress Tracking

Use this table to track your progress:

| Phase | Task | Status | Date |
|-------|------|--------|------|
| 1 | Read docs | ✓ ☐ | |
| 2 | Install | ✓ ☐ | |
| 3 | Run examples | ✓ ☐ | |
| 4 | Understand theory | ✓ ☐ | |
| 5 | Practice | ✓ ☐ | |
| 6 | Exercises | ✓ ☐ | |
| 7 | Quiz | ✓ ☐ | |
| 8 | Integration | ✓ ☐ | |

---

## 🎓 Completion Certification

When all phases are complete, you can:

✅ Explain how vector databases work
✅ Choose the right database for your use case
✅ Use free embedding models effectively
✅ Write RAG systems with vector search
✅ Scale from prototypes to production

---

**Ready to start?** Begin with Phase 1 - [README.md](./README.md)

**Quick start?** Jump to [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

**Need help?** See [INSTALLATION.md](./INSTALLATION.md) troubleshooting
