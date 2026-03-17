# Exercise 01: Implement Text Chunking Strategies

## Objective

Implement and compare different text chunking strategies for RAG systems.

## Problem Statement

Create a text chunking system that can:
1. Split documents using multiple strategies
2. Preserve chunk boundaries intelligently
3. Handle different document types

## Requirements

### Core Requirements

1. **Fixed-Size Chunker**
   - Split text into chunks of specified size
   - Try to break at natural boundaries (sentences, paragraphs)

2. **Sentence-Based Chunker**
   - Split text at sentence boundaries
   - Combine sentences to fit chunk size

3. **Recursive Chunker**
   - Use multiple separators hierarchically
   - Fall back to smaller separators when needed

### Additional Features

- Chunk overlap to preserve context
- Metadata preservation (page numbers, source)
- Statistics reporting (chunk sizes, count)

## Example Input

```python
text = """
Machine learning is a subset of artificial intelligence. It enables systems 
to learn from data without explicit programming. There are three main types:
supervised, unsupervised, and reinforcement learning.

Supervised learning uses labeled training data. The algorithm learns patterns 
from examples to make predictions on new data. Common applications include 
classification and regression tasks.
"""
```

## Expected Output

```
=== Fixed Size Chunker (chunk_size=150, overlap=20) ===
Chunk 1: "Machine learning is a subset of artificial intelligence. It enables..."
         Length: 142 chars

=== Sentence Chunker (chunk_size=150, overlap=20) ===
Chunk 1: "Machine learning is a subset of artificial intelligence. It enables..."
         Length: 148 chars
```

## Evaluation Criteria

- [ ] Fixed-size chunking works correctly
- [ ] Sentence-based chunking preserves sentence boundaries
- [ ] Recursive chunking handles various separators
- [ ] Overlap is correctly applied
- [ ] Chunk metadata is preserved
- [ ] Code is well-documented

## Time Estimate

- Basic implementation: 45 minutes
- With all features: 1.5 hours
