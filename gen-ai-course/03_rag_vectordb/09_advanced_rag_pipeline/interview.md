# Advanced RAG Pipeline - Interview Questions

## System Design Questions

### Q1: Design a complete RAG pipeline from document ingestion to response generation.

**Answer:** A complete RAG pipeline consists of 5 stages:

1. **Ingestion Layer:**
   - Document loaders (PDF, DOCX, PPT via Unstructured, PyMuPDF)
   - Text extraction and cleaning
   - Multi-modal extraction (images via OCR, tables via table detection)
   - Metadata extraction (source, page number, timestamp)

2. **Processing Layer:**
   - Chunking (semantic, recursive, fixed-size strategies)
   - Embedding generation (Sentence Transformers, OpenAI embeddings)
   - Image captioning (BLIP, ViT-GPT2 models)

3. **Storage Layer:**
   - Vector database (Chroma, Pinecone, Milvus)
   - Metadata storage (PostgreSQL, DynamoDB)
   - Version control for documents

4. **Retrieval Layer:**
   - Vector similarity search (HNSW, IVF indexing)
   - Keyword search (BM25, TF-IDF)
   - Hybrid search (RRF, weighted scoring)
   - Optional: Graph-based retrieval

5. **Generation Layer:**
   - Prompt construction with context
   - LLM inference (OpenAI, Claude, Bedrock)
   - Response formatting and citation

---

### Q2: How would you handle multi-modal content (images, tables) in RAG?

**Answer:** Multi-modal RAG requires specialized processing:

1. **Image Processing:**
   - Extract images using Unstructured.io or PDFPlumber
   - Generate captions with vision-language models (BLIP, CLIP)
   - Store captions as separate text chunks with image metadata

2. **Table Processing:**
   - Extract tables using pdfplumber or Camelot
   - Convert to structured format (JSON, Markdown)
   - Store with semantic description for retrieval

3. **Integration:**
   - Create separate chunks for image captions and table descriptions
   - Tag chunks with content type for filtering
   - Use multi-modal embeddings (CLIP for images)

---

### Q3: Explain hybrid search and its implementation.

**Answer:** Hybrid search combines vector and keyword search:

**Why Hybrid?**
- Vector search: Handles semantic similarity, synonyms
- Keyword search: Handles exact matches, named entities
- Combined: Better recall and precision

**Implementation:**
```
Query 
  │
  ├─▶ Vector Search (FAISS/Pinecone) → Results A
  │
  └─▶ Keyword Search (BM25) → Results B
        │
        ▼
   Reciprocal Rank Fusion (RRF)
        │
        ▼
  Combined Ranked Results
```

**RRF Formula:** Score = Σ(1 / (k + rank)) across result sets

---

### Q4: How would you build a production RAG API with FastAPI?

**Answer:** Production RAG API considerations:

```python
@app.post("/chat")
async def chat(request: QueryRequest):
    # 1. Validate input
    if not request.question.strip():
        raise HTTPException(400, "Empty question")
    
    # 2. Retrieve context (with timeout)
    context = await asyncio.wait_for(
        retrieve_context(request.question),
        timeout=5.0
    )
    
    # 3. Generate response
    response = await llm_complete(request.question, context)
    
    # 4. Log for observability
    log_query(request.question, response)
    
    return {"answer": response.text, "sources": response.sources}
```

Key features:
- Rate limiting and authentication
- Async processing for non-blocking
- Streaming responses for long generations
- Error handling and fallbacks
- Request/response logging

---

### Q5: Compare different vector database choices for production.

**Answer:**

| Database | Scale | Persistence | Managed | Best For |
|----------|-------|-------------|---------|----------|
| **Chroma** | 100K vectors | ✅ | ❌ | Prototypes, small apps |
| **FAISS** | 100M vectors | ❌ (custom) | ❌ | High-performance, in-memory |
| **Pinecone** | Billions | ✅ | ✅ | Production, managed service |
| **Milvus** | Billions | ✅ | ✅/❌ | Enterprise, self-hosted |
| **Weaviate** | Billions | ✅ | ✅/❌ | Graph-enhanced search |

---

## Multi-modal RAG Questions

### Q6: How do you extract and process tables in documents?

**Answer:** Table extraction pipeline:

```python
def extract_tables_from_pdf(pdf_path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Detect tables
            extracted = page.extract_tables()
            for table in extracted:
                # Convert to structured format
                df = pandas.DataFrame(table[1:], columns=table[0])
                
                # Generate description
                description = f"Table with columns: {', '.join(df.columns)}"
                
                tables.append({
                    "markdown": df.to_markdown(),
                    "description": description,
                    "page": page.page_number
                })
    return tables
```

Key considerations:
- Handle merged cells and multi-line rows
- Preserve data types (numbers, dates)
- Generate semantic descriptions for retrieval

---

### Q7: How do you implement image captioning in RAG?

**Answer:** Image captioning workflow:

```python
from transformers import BlipProcessor, BlipForConditionalGeneration

def caption_image(image_path):
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    
    image = Image.open(image_path)
    inputs = processor(images=image, return_tensors="pt")
    
    out = model.generate(**inputs, max_length=50)
    caption = processor.decode(out[0], skip_special_tokens=True)
    
    return caption

# Store caption as chunk with metadata
caption_chunk = Document(
    page_content=caption,
    metadata={
        "type": "image_caption",
        "source_image": image_path,
        "source_page": page_num
    }
)
```

---

## Hybrid Search Questions

### Q8: What is Reciprocal Rank Fusion (RRF) and how does it work?

**Answer:** RRF is a simple yet effective method to combine ranked result sets:

**Formula:** For each document, score = Σ(1 / (k + rank_i)) where rank_i is the rank in each result set.

```python
def rrf_fusion(result_sets, k=60):
    scores = defaultdict(float)
    
    for result_set in result_sets:
        for rank, doc in enumerate(result_set):
            scores[doc.id] += 1 / (k + rank)
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Benefits:**
- No need to normalize scores across different search methods
- Simple, parameter-free combination
- Works well with any number of result sets

---

### Q9: How do you optimize hybrid search performance?

**Answer:** Optimization strategies:

1. **Parallel Execution:** Run vector and keyword search concurrently
2. **Pre-filtering:** Apply metadata filters before vector search
3. **Caching:** Cache frequent query results
4. **Index Optimization:** Tune HNSW parameters (M, efConstruction)
5. **Batch Processing:** Process multiple queries together

---

## API Development Questions

### Q10: How do you implement streaming responses in FastAPI?

**Answer:** Streaming implementation:

```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(request: QueryRequest):
    async def generate():
        context = await retrieve(request.question)
        async for token in llm.astream(request.question, context):
            yield f"data: {json.dumps({'token': token})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

Client-side handling:
```javascript
const eventSource = new EventSource("/chat/stream");
eventSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    appendToken(data.token);
};
```

---

### Q11: How do you handle LLM provider fallbacks?

**Answer:** Multi-provider fallback pattern:

```python
class LLMRouter:
    def __init__(self, providers):
        self.providers = providers
    
    async def complete(self, prompt, **kwargs):
        errors = []
        for provider in self.providers:
            try:
                return await provider.complete(prompt, **kwargs)
            except Exception as e:
                errors.append((provider.name, str(e)))
                continue
        raise Exception(f"All providers failed: {errors}")
```

---

## LLM Integration Questions

### Q12: How do you integrate Claude via AWS Bedrock?

**Answer:** Bedrock integration:

```python
import boto3
import json

def invoke_claude(prompt, max_tokens=1000):
    client = boto3.client('bedrock-runtime')
    
    body = {
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9,
    }
    
    response = client.invoke_model(
        body=json.dumps(body),
        modelId="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    return json.loads(response['body'].read())['completion']
```

---

### Q13: How do you optimize RAG for cost and latency?

**Answer:** Optimization techniques:

1. **Cost Optimization:**
   - Cache frequent queries
   - Use smaller embedding models
   - Limit context length
   - Batch requests

2. **Latency Optimization:**
   - Async processing
   - Connection pooling
   - CDN for static assets
   - Pre-warming cache

---

## Evaluation & Observability Questions

### Q14: How do you evaluate RAG system quality?

**Answer:** Use RAGAS metrics:

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance, context_precision

metrics = [
    faithfulness,      # Answer grounded in context
    answer_relevance,  # Answer addresses question  
    context_precision, # Retrieved context is relevant
]

result = evaluate(test_dataset, metrics=metrics)
```

**Key Metrics:**
- Faithfulness: > 0.8
- Answer Relevance: > 0.75
- Context Precision: > 0.85
- Context Recall: > 0.8

---

### Q15: How do you implement observability in RAG?

**Answer:** Observability setup with Langfuse:

```python
from langfuse import observe

@observe()
def rag_pipeline(question):
    with langfuse.start_as_current_span("retrieval"):
        context = retrieve(question)
    
    with langfuse.start_as_current_span("generation"):
        answer = generate(question, context)
    
    return answer
```

Track:
- Query input and output
- Retrieval scores and sources
- Token usage and costs
- Latency per stage

---

## Agentic AI Questions

### Q16: Explain LangGraph and ReAct patterns.

**Answer:** ReAct pattern combines reasoning and acting:

```
Question
   │
   ▼
Reason ──▶ Plan ──▶ Act
   │          │       │
   └──────────┴───────┘
         Loop until done
```

LangGraph implementation:

```python
workflow = StateGraph(AgentState)
workflow.add_node("reason", reason_node)
workflow.add_node("act", act_node)
workflow.add_edge("reason", "act")
workflow.add_edge("act", "reason")
```

---

### Q17: How do you handle multi-hop reasoning in RAG?

**Answer:** Multi-hop strategies:

1. **Iterative Retrieval:**
   - Retrieve, generate sub-questions
   - Retrieve more context
   - Combine all context

2. **Query Decomposition:**
   - Break complex question into sub-questions
   - Retrieve for each sub-question
   - Combine answers

```python
def multi_hop_rag(question):
    # Decompose
    sub_qs = decompose(question)
    
    # Retrieve for each
    all_context = []
    for sq in sub_qs:
        context = retrieve(sq)
        all_context.extend(context)
    
    # Generate with all context
    return generate(question, all_context)
```

---

## Deployment Questions

### Q18: How do you deploy RAG on AWS?

**Answer:** AWS deployment architecture:

```
Client ──▶ API Gateway ──▶ ECS/Fargate ──▶ Lambda (async tasks)
                                │
                                ├──▶ S3 (documents)
                                ├──▶ RDS/DynamoDB (metadata)  
                                ├──▶ ElastiCache (caching)
                                └──▶ Bedrock (LLM)
```

Key services:
- ECS/Fargate: Container orchestration
- Lambda: Async processing
- S3: Document storage
- RDS/DynamoDB: Metadata storage
- API Gateway: Request routing
- CloudWatch: Monitoring

---

### Q19: How do you handle document versioning?

**Answer:** Versioning strategies:

1. **Simple Version Numbers:**
   ```python
   metadata = {"version": "v1.2.3"}
   ```

2. **Timestamp-based:**
   ```python
   metadata = {"ingested_at": "2025-01-15T10:30:00Z"}
   ```

3. **Hash-based:**
   ```python
   metadata = {"doc_hash": "abc123"}
   ```

Implementation:
- Store version in metadata
- Filter by version in queries
- Migrate old versions to archive

---

### Q20: How do you scale RAG to handle millions of documents?

**Answer:** Scaling strategies:

1. **Database Level:**
   - Sharding by document type/date
   - Index optimization (HNSW parameters)
   - Read replicas for high traffic

2. **Application Level:**
   - Async processing queues
   - Caching frequent queries
   - CDN for static content

3. **Infrastructure:**
   - Auto-scaling groups
   - Load balancers
   - Database connection pooling

```python
# Batch ingestion
async def bulk_ingest(documents, batch_size=100):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        await process_batch(batch)
```