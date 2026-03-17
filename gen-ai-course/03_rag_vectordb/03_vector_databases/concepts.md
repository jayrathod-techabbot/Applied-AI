# Vector Databases - Concepts

## What is a Vector Database?

A vector database is a specialized database system designed to store and efficiently search high-dimensional vector embeddings. Unlike traditional databases that store structured data in rows and columns, vector databases are optimized for similarity-based searches.

## Why Vector Databases?

### Traditional Database Limitations
- Keyword-based search only
- Exact match queries
- Poor semantic search capabilities

### Vector Database Advantages
- Semantic similarity search
- Fast approximate nearest neighbor (ANN) search
- Scalable to billions of vectors
- Support for metadata filtering

## How Vector Search Works

```
Query Vector: [0.1, -0.3, 0.5, ...]
                    ↓
           Vector Database
                    ↓
Nearest Vectors: [0.12, -0.29, 0.48, ...]
                  [0.09, -0.31, 0.52, ...]
                  [0.11, -0.28, 0.51, ...]
```

## Popular Vector Databases

| Database | Type | Key Features | Best For |
|----------|------|--------------|----------|
| **Pinecone** | Cloud-native | Managed service, serverless | Production, scaling |
| **Weaviate** | Open source | Graph API, hybrid search | Flexibility, features |
| **Chroma** | Open source | Embeddings-focused, local | Prototyping, small scale |
| **Milvus** | Open source | Scalable, cloud-native | Large-scale |
| **Qdrant** | Open source | Rust-based, fast | Performance |
| **pgvector** | Extension | PostgreSQL-based | Existing Postgres users |

## Key Concepts

### 1. Embeddings
Numerical representations of data (text, images, audio) in vector form.

### 2. Similarity Metrics

#### Cosine Similarity
```
cosine(A, B) = (A · B) / (||A|| × ||B||)
```
- Range: -1 to 1
- Most common for text embeddings

#### Euclidean Distance
```
dist(A, B) = √(Σ(Ai - Bi)²)
```
- Lower is more similar
- Good for normalized vectors

#### Dot Product
```
dot(A, B) = Σ(Ai × Bi)
```
- For normalized vectors, equivalent to cosine

### 3. Indexing Algorithms

#### HNSW (Hierarchical Navigable Small World)
- Graph-based indexing
- Fast search with good recall
- Higher memory usage
- Default for many databases

#### IVF (Inverted File)
- Clustering-based
- Good balance of speed and recall
- Lower memory than HNSW

#### PQ (Product Quantization)
- Compresses vectors
- Good for very large datasets
- Trade-off: speed vs accuracy

### 4. Metadata Filtering
Filter results by metadata before or after vector search:
- Pre-filter: Filter then search (slower)
- Post-filter: Search then filter (may return fewer than k results)

## Architecture Considerations

### Cloud vs Self-Hosted

**Cloud-managed (Pinecone, etc.)**
- Easy setup
- Automatic scaling
- Less control

**Self-hosted (Weaviate, Milvus, etc.)**
- Full control
- Cost-effective at scale
- Requires DevOps expertise

### Hybrid Search
Combines vector search with keyword search for better results.

## Performance Metrics

### Recall
Fraction of true nearest neighbors found.

### Latency
Time to return search results.

### Throughput
Queries per second (QPS).

### Memory Usage
RAM required to store indices.

## Best Practices

1. **Choose the right index type** based on your recall/latency requirements
2. **Normalize your embeddings** for consistent similarity scores
3. **Use metadata filtering** to reduce the search space
4. **Monitor performance** and tune parameters regularly
5. **Consider hybrid search** for better results
