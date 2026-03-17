# Embeddings & Chunking Concepts

## Text Embeddings

### What are Embeddings?

Embeddings are dense numerical representations of text that capture semantic meaning. They transform words, sentences, or documents into vectors in a high-dimensional space where similar items are close together.

```
Text → "The cat sat on the mat"
        ↓
Vector → [0.12, -0.34, 0.56, ..., 0.89]  (1536 dimensions for ada-002)
```

### Why Embeddings Matter in RAG

1. **Semantic Search**: Find meaning, not just keywords
2. **Efficient Retrieval**: Fast similarity search in vector space
3. **Context Preservation**: Similar concepts cluster together

### Types of Embeddings

#### Word Embeddings
- Word2Vec, GloVe, FastText
- Capture word-level semantics

#### Sentence Embeddings
- sentence-transformers, SBERT
- Capture sentence-level meaning

#### Document Embeddings
- Document-level semantic representation
- Good for long documents

### Popular Embedding Models

| Model | Dimensions | Provider | Use Case |
|-------|------------|----------|----------|
| text-embedding-ada-002 | 1536 | OpenAI | General purpose |
| text-embedding-3-small | 1536/256 | OpenAI | Fast, cheaper |
| text-embedding-3-large | 3072 | OpenAI | Higher quality |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | HuggingFace | Free, local |
| Cohere-embed-multilingual-v3.0 | 1024 | Cohere | Multilingual |

### Choosing an Embedding Model

Consider:
- **Dimension**: Higher isn't always better
- **Cost**: API calls vs hosting locally
- **Language**: Multilingual support needed?
- **Task**: General vs domain-specific

## Document Chunking

### Why Chunking?

LLMs have limited context windows. Chunking allows you to:
1. Fit documents into the LLM's context
2. Improve retrieval precision
3. Enable parallel processing
4. Manage costs effectively

### Chunking Strategies

#### 1. Fixed-Size Chunking
```
Text: "Hello world. This is a test. More text here."
Chunks: ["Hello world.", "This is a test.", "More text here."]
```

**Pros**: Simple, predictable
**Cons**: May break semantic units

#### 2. Sentence-Based Chunking
Split by sentences using NLP libraries

**Pros**: Preserves semantic meaning
**Cons**: May vary significantly in size

#### 3. Paragraph-Based Chunking
Split at paragraph boundaries

**Pros**: Natural semantic units
**Cons**: Variable sizes

#### 4. Recursive Chunking
Hierarchical splitting (paragraphs → sentences → words)

**Pros**: Flexible, maintains context
**Cons**: More complex

#### 5. Semantic Chunking
Split based on semantic similarity

**Pros**: Cohesive chunks
**Cons**: Computationally expensive

### Chunk Size Considerations

| Chunk Size | Pros | Cons |
|------------|------|------|
| Small (100-200) | Precise retrieval | May lose context |
| Medium (500-1000) | Balanced | May include noise |
| Large (1500+) | More context | May exceed context limit |

### Overlap Strategy

Add overlap between chunks to maintain context:

```
Chunk 1: "The quick brown fox"
Chunk 2: "brown fox jumps over"
           ↑ overlap ↑
```

Typical overlap: 10-20% of chunk size

### Handling Special Content

#### Code Files
- Split by function/class definitions
- Preserve indentation
- Use language-aware parsers

#### Tables
- Extract as structured data
- Chunk by rows or logical sections

#### Long Documents
- Use hierarchical chunking
- Maintain section structure in metadata

## Best Practices

1. **Start with 500-1000 character chunks** and adjust based on results
2. **Use overlap** to prevent context loss
3. **Preserve metadata** (source, page number, section)
4. **Test different strategies** on your specific data
5. **Consider your retrieval approach** when choosing chunk size
