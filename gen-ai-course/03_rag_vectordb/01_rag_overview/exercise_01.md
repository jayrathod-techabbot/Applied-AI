# Exercise 01: Build Your First RAG System

## Objective

Build a basic Retrieval-Augmented Generation system that can answer questions about a set of documents.

## Problem Statement

You need to create a simple RAG system that:
1. Stores a collection of documents
2. Allows semantic search (not just keyword matching)
3. Retrieves relevant documents based on user queries
4. Generates context-aware responses

## Requirements

### Core Requirements

1. **Document Storage**
   - Create a system to store at least 5 documents
   - Each document should have an ID and content

2. **Text Embedding**
   - Implement or use a text embedding function
   - Convert documents and queries into vector representations

3. **Similarity Search**
   - Implement cosine similarity or another metric
   - Find top-k most similar documents to a query

4. **Basic RAG Pipeline**
   - Combine retrieval with a mock LLM response
   - Format output with source attribution

### Stretch Goals

- Add metadata support (source, date, author)
- Implement different similarity metrics
- Add document filtering by metadata

## Input/Output Example

### Sample Documents
```python
documents = [
    {"id": "doc1", "content": "Python is a programming language..."},
    {"id": "doc2", "content": "Machine learning is a subset of AI..."},
    # ... more documents
]
```

### Sample Query
```
Query: "Tell me about programming languages"
```

### Expected Output
```
Response: Based on the retrieved context, Python is a programming language...
Sources: [doc1, doc3]
```

## Implementation Hints

1. Start with a simple in-memory vector store
2. Use hash-based vectors for demonstration if no API keys available
3. Structure your code into clear components:
   - `Document` class
   - `Embedding` function
   - `VectorStore` class
   - `RAG` pipeline class

## Evaluation Criteria

- [ ] Documents can be added and stored
- [ ] Query embedding works correctly
- [ ] Similarity search returns relevant results
- [ ] RAG pipeline produces context-aware responses
- [ ] Code is well-structured and commented
- [ ] Sources are cited in output

## Time Estimate

- Basic implementation: 30 minutes
- With stretch goals: 1 hour
