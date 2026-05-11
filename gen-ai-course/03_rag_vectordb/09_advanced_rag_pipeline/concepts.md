# Advanced RAG Pipeline - Technical Concepts

## 1. RAG Pipeline Architecture

### End-to-End Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│   Ingest    │────▶│   Index &    │────▶│   Retrieve   │────▶│  Generate   │
│  Documents  │     │   Store      │     │   Context    │     │   Output    │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
       │                   │                     │                    │
       ▼                   ▼                     ▼                    ▼
  Document Load        Create Vector        Similarity Search    LLM Completion
  Parse & Clean        Store + Metadata     Apply Filters        With Context
  Chunk & Tag          Embed with Model       Top-K Results        Return Response
```

### Pipeline Components

1. **Ingestion Layer**
   - Document loaders (PDF, DOCX, PPT, HTML, etc.)
   - Text extraction and cleaning
   - Image/table extraction
   - Metadata extraction and tagging

2. **Processing Layer**
   - Chunking strategies (semantic, recursive, fixed-size)
   - Embedding generation
   - Multi-modal processing (images, tables)

3. **Storage Layer**
   - Vector database (Pinecone, Chroma, Milvus, etc.)
   - Metadata storage
   - Version control

4. **Retrieval Layer**
   - Vector similarity search
   - Keyword search (BM25, TF-IDF)
   - Hybrid search combining both
   - Optional graph-based retrieval

5. **Generation Layer**
   - Prompt construction
   - LLM inference
   - Response post-processing

## 2. Data Ingestion Pipelines

### Document Processing Pipeline

```python
class IngestionPipeline:
    def __init__(self):
        self.loaders = {
            'pdf': PyMuPDFLoader,
            'docx': Docx2txtLoader,
            'ppt': UnstructuredPowerPointLoader,
            'html': UnstructuredHTMLLoader,
            'image': UnstructuredImageLoader
        }
    
    def process_document(self, file_path):
        # 1. Load document
        loader = self.get_loader(file_path)
        documents = loader.load()
        
        # 2. Parse and extract
        parsed = self.parse_documents(documents)
        
        # 3. Extract multi-modal content
        text_chunks, tables, images = self.extract_multimodal(parsed)
        
        # 4. Chunk semantically
        chunks = self.semantic_chunk(text_chunks)
        
        # 5. Add metadata
        enriched_chunks = self.add_metadata(chunks, file_path)
        
        return enriched_chunks
```

### Chunking Strategies

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| Fixed-size | Simple documents | Predictable | May break semantic units |
| Recursive | Mixed content | Hierarchical | Complex |
| Semantic | Quality retrieval | Context-aware | Slower |
| Markdown-aware | Technical docs | Structure preserved | Limited formats |

### Metadata Tagging System

```python
metadata = {
    'source': 'document.pdf',
    'page': 1,
    'chunk_index': 0,
    'version': 'v1.2',
    'timestamp': '2025-01-15T10:30:00Z',
    'doc_type': 'technical_manual',
    'tags': ['api', 'reference'],
    'author': 'Engineering Team'
}
```

## 3. Multi-modal RAG

### Supported Content Types

1. **Text** - Standard document text
2. **Images** - Captions via vision models
3. **Tables** - Structured data extraction
4. **Charts/Graphs** - Data extraction and analysis

### Image Captioning Pipeline

```python
from transformers import VisionEncoderDecoderModel, ViTFeatureExtractor

def caption_image(image_path):
    model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
    feature_extractor = ViTFeatureExtractor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
    
    image = Image.open(image_path)
    pixel_values = feature_extractor(images=[image], return_tensors="pt").pixel_values
    output_ids = model.generate(pixel_values, max_length=16, num_beams=4)
    caption = feature_extractor.batch_decode(output_ids, skip_special_tokens=True)[0]
    
    return caption
```

### Table Extraction

```python
def extract_tables(pdf_path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables()
            for table in extracted:
                df = pd.DataFrame(table[1:], columns=table[0])
                tables.append({
                    'content': df.to_markdown(),
                    'metadata': {'page': page.page_number}
                })
    return tables
```

## 4. Hybrid Search

### Architecture

```
Query
   │
   ▼
┌─────────────────────────────┐
│  Query Expansion / Reform   │
└─────────────────────────────┘
   │
   ▼
┌─────────────────┐  ┌─────────────────┐
│  Vector Search  │  │  Keyword Search │
│   (FAISS/Chroma)│  │   (BM25/TF-IDF) │
└─────────────────┘  └─────────────────┘
   │                      │
   └──────────┬───────────┘
              ▼
   ┌────────────────────┐
   │  Reciprocal Rank   │
   │     Fusion (RRF)   │
   └────────────────────┘
              │
              ▼
      Ranked Results
```

### Implementation

```python
class HybridSearch:
    def __init__(self, vector_db, keyword_searcher):
        self.vector_db = vector_db
        self.keyword_searcher = keyword_searcher
    
    def search(self, query, k=10, alpha=0.5):
        # Vector search
        vector_results = self.vector_db.similarity_search(query, k=k*2)
        
        # Keyword search
        keyword_results = self.keyword_searcher.search(query, k=k*2)
        
        # RRF fusion
        combined = self.reciprocal_rank_fusion(vector_results, keyword_results)
        
        return combined[:k]
    
    def reciprocal_rank_fusion(self, results_list, k=60):
        fused_scores = {}
        for results in results_list:
            for rank, result in enumerate(results):
                doc_id = result.metadata.get('id')
                score = 1 / (k + rank)
                fused_scores[doc_id] = fused_scores.get(doc_id, 0) + score
        return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
```

## 5. FastAPI Implementation

### Basic Chat Endpoint

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    question: str
    session_id: Optional[str] = None
    top_k: int = 5

@app.post("/chat")
async def chat(query: Query):
    # Retrieve context
    context = rag_system.retrieve(query.question, k=query.top_k)
    
    # Generate response
    response = rag_system.generate(query.question, context)
    
    return {"answer": response, "sources": response.metadata}

@app.post("/ingest")
async def ingest(files: List[UploadFile]):
    results = []
    for file in files:
        chunks = ingestion_pipeline.process(file)
        vector_db.upsert(chunks)
        results.append({"file": file.filename, "chunks": len(chunks)})
    return results
```

### Streaming Response

```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(query: Query):
    async def generate():
        context = rag_system.retrieve(query.question, k=query.top_k)
        async for chunk in rag_system.generate_stream(query.question, context):
            yield json.dumps({"chunk": chunk}) + "\n"
    
    return StreamingResponse(generate(), media_type="text/plain")
```

## 6. LLM Integration Patterns

### Provider Abstraction

```python
class LLMProvider:
    def __init__(self, provider: str, config: dict):
        self.provider = provider
        self.config = config
    
    def complete(self, prompt: str, **kwargs) -> str:
        if self.provider == "openai":
            return self._openai_complete(prompt, **kwargs)
        elif self.provider == "bedrock":
            return self._bedrock_complete(prompt, **kwargs)
        elif self.provider == "anthropic":
            return self._anthropic_complete(prompt, **kwargs)
    
    def _bedrock_complete(self, prompt: str, **kwargs):
        import boto3
        client = boto3.client('bedrock-runtime')
        body = {"prompt": prompt, "max_tokens": kwargs.get('max_tokens', 1000)}
        response = client.invoke_model(
            body=json.dumps(body),
            modelId="anthropic.claude-3-sonnet-20240229-v1:0"
        )
        return json.loads(response['body'].read())['completion']
```

### Cost Optimization Strategies

1. **Model Selection** - Choose appropriate model size for task
2. **Caching** - Cache frequent queries and responses
3. **Chunk Limiting** - Restrict context to reduce tokens
4. **Rate Limiting** - Batch requests when possible

## 7. Evaluation & Observability

### RAGAS Evaluation

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance, context_precision

def evaluate_rag(dataset):
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevance,
            context_precision
        ]
    )
    return result
```

### Langfuse Integration

```python
from langfuse import Langfuse

langfuse = Langfuse()

@observe()
def rag_pipeline(question: str):
    with langfuse.start_as_current_span(name="rag-pipeline") as span:
        span.update(
            input=question,
            metadata={"model": "gpt-4", "k": 5}
        )
        
        context = retrieve(question)
        span.add_event("retrieval", {"num_chunks": len(context)})
        
        answer = generate(question, context)
        span.update(output=answer)
        
        return answer
```

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Faithfulness | Answer grounded in context | > 0.8 |
| Answer Relevance | Answer addresses question | > 0.75 |
| Context Precision | Relevant context retrieved | > 0.85 |
| Latency | End-to-end response time | < 2s |
| Cost per Query | Token usage cost | < $0.01 |

## 8. Agentic Workflows (LangGraph)

### ReAct Pattern

```python
from langgraph.graph import StateGraph

class RAGState(TypedDict):
    question: str
    context: List[str]
    answer: str
    next_action: str

def retrieve_node(state: RAGState):
    context = retriever.search(state["question"])
    return {"context": context, "next_action": "generate"}

def generate_node(state: RAGState):
    answer = llm.generate(state["question"], state["context"])
    return {"answer": answer, "next_action": "evaluate"}

def evaluate_node(state: RAGState):
    score = evaluator.score(state["question"], state["answer"], state["context"])
    if score < 0.8:
        return {"next_action": "rewrite"}
    return {"next_action": "end"}

workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "evaluate")
workflow.add_conditional_edges("evaluate", lambda s: s["next_action"])
```