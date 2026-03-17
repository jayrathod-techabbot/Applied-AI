# Exercise 01: Build a Vector Database Wrapper

## Objective

Create a wrapper class that abstracts vector database operations.

## Problem Statement

Build a Python class that provides a unified interface for vector storage and search operations.

## Requirements

### Core Features

1. **Add vectors** - Store vectors with IDs and metadata
2. **Search** - Find similar vectors by cosine similarity
3. **Delete** - Remove vectors by ID
4. **Metadata filtering** - Filter results by metadata fields

### Additional Features

- Batch operations for efficiency
- Multiple similarity metrics
- Basic statistics (count, dimensions)

## Expected API

```python
class VectorDB:
    def __init__(self, dimension: int = 384):
        ...
    
    def add(self, id: str, vector: List[float], metadata: dict = None):
        ...
    
    def search(self, query: List[float], k: int = 5, filter: dict = None):
        ...
    
    def delete(self, id: str) -> bool:
        ...
    
    def count(self) -> int:
        ...
```

## Evaluation

- [ ] Add vectors works
- [ ] Search returns correct results
- [ ] Delete removes vectors
- [ ] Metadata filtering works
- [ ] Code is documented

## Time Estimate

45 minutes
