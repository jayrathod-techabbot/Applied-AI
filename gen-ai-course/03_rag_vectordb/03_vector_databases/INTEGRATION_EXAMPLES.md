# Vector Database Integration Examples

Complete, copy-paste ready examples for common use cases.

## 1. Simple Document Q&A (Chroma + Sentence Transformers)

**Best for:** Prototyping, learning, small projects

```python
from sentence_transformers import SentenceTransformer
import chromadb

# 1. Initialize
embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./qa_db")
collection = client.get_or_create_collection(name="documents")

# 2. Load documents
documents = [
    "Python is a high-level programming language.",
    "Machine learning enables computers to learn from data.",
    "Neural networks are inspired by biological neurons.",
    "Embeddings map text to high-dimensional vectors.",
]

# 3. Embed and add
embeddings = embedder.encode(documents).tolist()
collection.add(
    ids=[str(i) for i in range(len(documents))],
    embeddings=embeddings,
    documents=documents,
)

# 4. Answer questions
questions = [
    "What is Python?",
    "How does machine learning work?",
    "What are embeddings?",
]

for question in questions:
    q_embedding = embedder.encode([question]).tolist()
    results = collection.query(
        query_embeddings=q_embedding,
        n_results=1
    )
    print(f"Q: {question}")
    print(f"A: {results['documents'][0][0]}\n")
```

**Output:**
```
Q: What is Python?
A: Python is a high-level programming language.

Q: How does machine learning work?
A: Machine learning enables computers to learn from data.

Q: What are embeddings?
A: Embeddings map text to high-dimensional vectors.
```

---

## 2. Multi-Source Document Search

**Best for:** Combining documents from multiple sources with metadata filtering

```python
from sentence_transformers import SentenceTransformer
import chromadb

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./multi_source_db")
collection = client.get_or_create_collection(name="docs")

# Documents from different sources
documents = [
    # Wikipedia
    {"text": "Python is a programming language", "source": "wikipedia"},
    {"text": "Machine learning is subset of AI", "source": "wikipedia"},

    # News
    {"text": "New AI breakthrough announced", "source": "news"},
    {"text": "Python gains popularity", "source": "news"},

    # Blog
    {"text": "Deep learning tutorial", "source": "blog"},
    {"text": "How to use Python", "source": "blog"},
]

# Add with source metadata
embeddings = embedder.encode([d["text"] for d in documents]).tolist()
collection.add(
    ids=[str(i) for i in range(len(documents))],
    embeddings=embeddings,
    documents=[d["text"] for d in documents],
    metadatas=[{"source": d["source"]} for d in documents],
)

# Search only in Wikipedia
query = "What is machine learning?"
q_emb = embedder.encode([query]).tolist()

results = collection.query(
    query_embeddings=q_emb,
    n_results=2,
    where={"source": "wikipedia"}
)

print(f"Results from Wikipedia:")
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"  - {doc} ({meta['source']})")
```

---

## 3. High-Performance Search (FAISS)

**Best for:** Large collections, high-speed retrieval

```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Create index
dimension = embedder.get_sentence_embedding_dimension()
index = faiss.IndexFlatIP(dimension)

# Normalize vectors (required for cosine similarity)
documents = [
    "Machine learning algorithms learn from data",
    "Deep learning uses neural networks",
    "NLP processes human language",
    "Computer vision interprets images",
    "Reinforcement learning uses rewards",
] * 1000  # Simulate larger dataset

embeddings = embedder.encode(documents)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

# Add to index
embeddings_32 = embeddings.astype('float32')
index.add(embeddings_32)

print(f"Index contains {index.ntotal} vectors")

# Search
query = "How do neural networks work?"
query_emb = embedder.encode([query])
query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)

distances, indices = index.search(
    query_emb.astype('float32'),
    k=5
)

print(f"\nTop results for '{query}':")
for i, idx in enumerate(indices[0]):
    print(f"  {i+1}. {documents[idx]} (score: {distances[0][i]:.3f})")

# Save for later
faiss.write_index(index, "./faiss_index.bin")
```

---

## 4. Real-Time Document Streaming

**Best for:** Adding documents incrementally as they arrive

```python
from sentence_transformers import SentenceTransformer
import chromadb
from datetime import datetime

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./stream_db")
collection = client.get_or_create_collection(name="stream")

class DocumentStream:
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
        self.batch_docs = []
        self.batch_ids = []
        self.doc_counter = 0

    def add_document(self, text, metadata=None):
        """Add document and auto-flush when batch is full"""
        self.batch_docs.append(text)
        self.batch_ids.append(f"doc_{self.doc_counter}")
        self.doc_counter += 1

        if len(self.batch_docs) >= self.batch_size:
            self.flush()

    def flush(self):
        """Flush batch to database"""
        if not self.batch_docs:
            return

        embeddings = embedder.encode(self.batch_docs).tolist()
        collection.add(
            ids=self.batch_ids,
            embeddings=embeddings,
            documents=self.batch_docs,
        )
        print(f"✓ Flushed {len(self.batch_docs)} documents")
        self.batch_docs = []
        self.batch_ids = []

# Simulate streaming data
stream = DocumentStream(batch_size=50)

# Add documents as they come
for i in range(150):
    stream.add_document(
        f"This is document {i} about topic {i % 5}"
    )

# Flush remaining
stream.flush()

# Search
results = collection.query(
    query_texts=["topic 2"],
    n_results=5
)
print(f"Found {len(results['ids'][0])} documents matching 'topic 2'")
```

---

## 5. Semantic Search with Re-ranking

**Best for:** Better accuracy with lightweight ranking

```python
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
import numpy as np

# Models
embedder = SentenceTransformer('all-MiniLM-L6-v2')
ranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

client = chromadb.PersistentClient(path="./rerank_db")
collection = client.get_or_create_collection(name="docs")

# Documents
documents = [
    "The capital of France is Paris",
    "Paris is known for the Eiffel Tower",
    "France is a country in Europe",
    "The Louvre museum is in Paris",
    "French cuisine is famous worldwide",
]

# Index
embeddings = embedder.encode(documents).tolist()
collection.add(
    ids=[str(i) for i in range(len(documents))],
    embeddings=embeddings,
    documents=documents,
)

# Search with re-ranking
query = "Where is the Eiffel Tower?"

# Step 1: Retrieve candidates (fast, approximate)
q_emb = embedder.encode([query]).tolist()
candidates = collection.query(
    query_embeddings=q_emb,
    n_results=5  # Get more candidates
)

# Step 2: Re-rank with cross-encoder (slower, more accurate)
query_doc_pairs = [
    [query, doc] for doc in candidates["documents"][0]
]
scores = ranker.predict(query_doc_pairs)

# Sort by re-ranked scores
ranked = sorted(
    zip(candidates["documents"][0], scores),
    key=lambda x: x[1],
    reverse=True
)

print(f"Re-ranked results for '{query}':")
for i, (doc, score) in enumerate(ranked, 1):
    print(f"  {i}. {doc} (score: {score:.3f})")
```

---

## 6. RAG with LLM Integration

**Best for:** Complete RAG pipeline with Claude/OpenAI

```python
from sentence_transformers import SentenceTransformer
import chromadb
from anthropic import Anthropic

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./rag_db")
collection = client.get_or_create_collection(name="knowledge")

# Claude client
llm = Anthropic()

# Knowledge base
documents = [
    "Python is a dynamically-typed, high-level programming language.",
    "Machine learning is a subset of artificial intelligence focused on algorithms that learn from data.",
    "Deep learning uses neural networks with many layers to process complex patterns.",
    "Natural language processing helps computers understand and generate human language.",
]

# Index knowledge
embeddings = embedder.encode(documents).tolist()
collection.add(
    ids=[str(i) for i in range(len(documents))],
    embeddings=embeddings,
    documents=documents,
)

def rag_query(question):
    """Answer question using RAG pipeline"""

    # 1. Retrieve relevant documents
    q_emb = embedder.encode([question]).tolist()
    retrieved = collection.query(
        query_embeddings=q_emb,
        n_results=2
    )

    context = "\n".join(retrieved["documents"][0])

    # 2. Generate answer with Claude
    message = llm.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Answer the question based on the provided context.

Context:
{context}

Question: {question}

Answer:"""
            }
        ]
    )

    return {
        "answer": message.content[0].text,
        "sources": retrieved["documents"][0],
    }

# Use it
result = rag_query("What is machine learning?")
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
```

---

## 7. Multi-Language Search

**Best for:** Content in multiple languages

```python
from sentence_transformers import SentenceTransformer
import chromadb

# Multilingual model
embedder = SentenceTransformer('distiluse-base-multilingual-cased-v2')

client = chromadb.PersistentClient(path="./multi_lang_db")
collection = client.get_or_create_collection(name="docs")

# Documents in different languages
documents = [
    # English
    {"text": "The cat is sleeping", "lang": "en"},
    {"text": "Dogs are loyal animals", "lang": "en"},

    # Spanish
    {"text": "El gato está durmiendo", "lang": "es"},
    {"text": "Los perros son animales leales", "lang": "es"},

    # French
    {"text": "Le chat dort", "lang": "fr"},
    {"text": "Les chiens sont des animaux fidèles", "lang": "fr"},
]

# Index
embeddings = embedder.encode([d["text"] for d in documents]).tolist()
collection.add(
    ids=[str(i) for i in range(len(documents))],
    embeddings=embeddings,
    documents=[d["text"] for d in documents],
    metadatas=[{"lang": d["lang"]} for d in documents],
)

# Search in English
results = collection.query(
    query_texts=["Sleeping cat"],
    n_results=6
)

print("Multilingual search results:")
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"  [{meta['lang'].upper()}] {doc}")
```

---

## 8. Chunked Document Search

**Best for:** Searching within long documents

```python
from sentence_transformers import SentenceTransformer
import chromadb

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chunked_db")
collection = client.get_or_create_collection(name="chunks")

# Long document
long_doc = """
Python Programming Basics

Chapter 1: Introduction
Python is a high-level programming language created by Guido van Rossum.
It emphasizes code readability and simplicity.

Chapter 2: Data Types
Python supports various data types including integers, floats, strings, lists, and dictionaries.
Lists are ordered collections that can contain multiple data types.

Chapter 3: Functions
Functions are reusable blocks of code that perform specific tasks.
Functions can accept arguments and return values.

Chapter 4: Libraries
Python has a rich ecosystem of libraries like NumPy, Pandas, and Scikit-learn.
These libraries extend Python's capabilities for scientific computing and data analysis.
"""

# Chunk the document
chunks = [c.strip() for c in long_doc.split('\n\n') if c.strip()]

# Index chunks
embeddings = embedder.encode(chunks).tolist()
collection.add(
    ids=[f"chunk_{i}" for i in range(len(chunks))],
    embeddings=embeddings,
    documents=chunks,
    metadatas=[{"doc": "Python Basics", "chunk": i} for i in range(len(chunks))],
)

# Search
query = "What are Python libraries?"
q_emb = embedder.encode([query]).tolist()

results = collection.query(
    query_embeddings=q_emb,
    n_results=2
)

print(f"Relevant chunks for '{query}':")
for i, (chunk, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
    print(f"\n{i}. {meta['doc']} - Chunk {meta['chunk']}")
    print(f"   {chunk}")
```

---

## 9. Semantic Caching

**Best for:** Reducing LLM calls with semantic search

```python
from sentence_transformers import SentenceTransformer
import chromadb
from anthropic import Anthropic

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./cache_db")
collection = client.get_or_create_collection(name="cache")
llm = Anthropic()

def semantic_cache_query(question, similarity_threshold=0.95):
    """Answer using LLM, cache results semantically"""

    # 1. Check cache for similar questions
    q_emb = embedder.encode([question]).tolist()
    cached = collection.query(
        query_embeddings=q_emb,
        n_results=1,
        include=["documents", "metadatas", "distances"]
    )

    # Check if similar enough (distance < threshold = high similarity)
    if cached["distances"][0] and 1 - cached["distances"][0][0] > similarity_threshold:
        print("✓ Using cached answer")
        return cached["metadatas"][0][0]["answer"]

    # 2. Generate new answer (no cache hit)
    print("✗ Cache miss, generating new answer...")
    message = llm.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[{"role": "user", "content": question}]
    )

    answer = message.content[0].text

    # 3. Cache the answer
    collection.add(
        ids=[f"q_{collection.count()}"],
        embeddings=q_emb,
        documents=[question],
        metadatas=[{"answer": answer}],
    )

    return answer

# Try it
q1 = "What is machine learning?"
print(semantic_cache_query(q1))

q2 = "Tell me about machine learning"  # Similar, cached!
print(semantic_cache_query(q2))
```

---

## 10. Performance Monitoring

**Best for:** Production systems

```python
from sentence_transformers import SentenceTransformer
import chromadb
import time
import statistics

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./perf_db")
collection = client.get_or_create_collection(name="docs")

# Sample data
documents = [f"Document {i} with content about topic {i % 5}" for i in range(10000)]

class PerformanceMonitor:
    def __init__(self):
        self.embed_times = []
        self.search_times = []
        self.add_times = []

    def monitor_embedding(self, texts):
        start = time.time()
        embeddings = embedder.encode(texts)
        elapsed = (time.time() - start) / len(texts)
        self.embed_times.append(elapsed)
        return embeddings

    def monitor_add(self, ids, docs, embeddings):
        start = time.time()
        collection.add(ids=ids, documents=docs, embeddings=embeddings)
        elapsed = time.time() - start
        self.add_times.append(elapsed)

    def monitor_search(self, query_emb):
        start = time.time()
        results = collection.query(query_embeddings=query_emb, n_results=5)
        elapsed = time.time() - start
        self.search_times.append(elapsed)
        return results

    def report(self):
        print("\n📊 Performance Report")
        print(f"Embedding: {statistics.mean(self.embed_times)*1000:.2f}ms per doc")
        print(f"Add: {statistics.mean(self.add_times)*1000:.2f}ms per batch")
        print(f"Search: {statistics.mean(self.search_times)*1000:.2f}ms")

# Monitor operations
monitor = PerformanceMonitor()

# Add documents
embeddings_data = monitor.monitor_embedding(documents)
for i in range(0, len(documents), 1000):
    batch = documents[i:i+1000]
    batch_ids = [str(j) for j in range(i, i+len(batch))]
    batch_embs = embeddings_data[i:i+1000].tolist()
    monitor.monitor_add(batch_ids, batch, batch_embs)

# Search
for _ in range(10):
    query_emb = monitor.monitor_embedding(["test query"])
    monitor.monitor_search(query_emb.tolist())

monitor.report()
```

---

## Key Takeaways

1. **Start simple** - Chroma is easiest for learning
2. **Scale up** - FAISS when you need speed
3. **Free models** - Sentence Transformers always recommended
4. **Real production** - Use Milvus for enterprise
5. **Monitor** - Track performance in production

---

**For more examples:** See `embeddings_examples.py` in the course materials
