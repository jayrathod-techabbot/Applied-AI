"""
Advanced RAG Pipeline - Hands-on Exercises
"""

import os
from typing import List, Dict
from dataclasses import dataclass


# Exercise 1: Document Ingestion Pipeline
def exercise_ingestion():
    """
    Exercise 1: Build a document ingestion pipeline
    
    Tasks:
    1. Load a PDF document
    2. Extract text and metadata
    3. Chunk the document
    4. Add metadata including version
    """
    
    # TODO: Implement document loading
    # loader = PyMuPDFLoader("sample.pdf")
    # documents = loader.load()
    
    # TODO: Implement chunking
    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=500,
    #     chunk_overlap=50
    # )
    # chunks = splitter.split_documents(documents)
    
    # TODO: Add metadata
    # for chunk in chunks:
    #     chunk.metadata['version'] = 'v1.0'
    #     chunk.metadata['processed_at'] = datetime.now().isoformat()
    
    # print(f"Processed {len(chunks)} chunks")
    pass


# Exercise 2: Multi-modal Processing
def exercise_multimodal():
    """
    Exercise 2: Extract and process images/tables
    
    Tasks:
    1. Extract images from a document
    2. Generate captions using BLIP
    3. Extract tables using pdfplumber
    4. Store as retrievable chunks
    """
    
    # TODO: Extract images
    # images = extract_images_from_pdf("doc.pdf")
    
    # TODO: Generate captions
    # for img in images:
    #     caption = generate_caption(img['path'])
    #     store_caption_chunk(caption, img['metadata'])
    
    # TODO: Extract tables
    # tables = extract_tables_with_pdfplumber("doc.pdf")
    
    # TODO: Convert to markdown and store
    pass


# Exercise 3: Hybrid Search
def exercise_hybrid_search():
    """
    Exercise 3: Implement hybrid search with RRF
    
    Tasks:
    1. Perform vector search
    2. Perform keyword search (BM25)
    3. Combine using RRF
    4. Compare with vector-only results
    """
    
    query = "What are the key benefits?"
    
    # TODO: Vector search
    # vector_results = vector_db.similarity_search(query, k=10)
    
    # TODO: Keyword search (using rank-bm25)
    # keyword_results = bm25_search(query, k=10)
    
    # TODO: RRF fusion
    # combined = reciprocal_rank_fusion([vector_results, keyword_results])
    
    # TODO: Compare results
    pass


# Exercise 4: FastAPI Endpoint
def exercise_api():
    """
    Exercise 4: Create FastAPI endpoints
    
    Tasks:
    1. Create /chat endpoint
    2. Create /ingest endpoint  
    3. Add streaming support
    4. Add error handling
    """
    
    # TODO: Implement endpoints
    # @app.post("/chat")
    # async def chat(query: QueryRequest):
    #     ...
    
    # @app.post("/ingest")
    # async def ingest(files: List[UploadFile]):
    #     ...
    
    pass


# Exercise 5: Evaluation
def exercise_evaluation():
    """
    Exercise 5: Implement RAG evaluation
    
    Tasks:
    1. Create test dataset
    2. Run RAGAS evaluation
    3. Log results to Langfuse
    4. Generate evaluation report
    """
    
    # TODO: Create test dataset
    # test_questions = [...]
    # ground_truth = [...]
    
    # TODO: Run evaluation
    # from ragas import evaluate
    # results = evaluate(dataset, metrics=[faithfulness, answer_relevance])
    
    # TODO: Log to Langfuse
    # langfuse.create_dataset(...)
    
    pass


# Exercise 6: LangGraph Agent
def exercise_langgraph():
    """
    Exercise 6: Build agentic RAG workflow
    
    Tasks:
    1. Create state graph
    2. Implement retrieve node
    3. Implement generate node
    4. Implement evaluate node
    5. Add conditional routing
    """
    
    # TODO: Define state
    # class AgentState(TypedDict):
    #     question: str
    #     context: List[str]
    #     answer: str
    #     next_action: str
    
    # TODO: Create workflow
    # workflow = StateGraph(AgentState)
    # workflow.add_node("retrieve", retrieve_node)
    # workflow.add_node("generate", generate_node)
    # workflow.add_node("evaluate", evaluate_node)
    
    pass


# Exercise 7: Bedrock Integration
def exercise_bedrock():
    """
    Exercise 7: Integrate with AWS Bedrock
    
    Tasks:
    1. Set up Bedrock client
    2. Implement Claude invocation
    3. Handle streaming responses
    4. Add error handling
    """
    
    # TODO: Implement Bedrock client
    # import boto3
    # client = boto3.client('bedrock-runtime')
    
    # TODO: Implement Claude call
    # def invoke_claude(prompt):
    #     ...
    
    pass


# Exercise 8: Cost Optimization
def exercise_optimization():
    """
    Exercise 8: Optimize RAG for cost and latency
    
    Tasks:
    1. Implement caching layer
    2. Add request batching
    3. Optimize chunk sizes
    4. Monitor token usage
    """
    
    # TODO: Add Redis caching
    # @lru_cache(maxsize=1000)
    # def cached_query(query):
    #     ...
    
    # TODO: Batch requests
    # async def batch_process(queries):
    #     ...
    
    pass


# Exercise 9: Docker Deployment
def exercise_deployment():
    """
    Exercise 9: Dockerize the RAG application
    
    Tasks:
    1. Write Dockerfile
    2. Create docker-compose.yml
    3. Configure environment variables
    4. Test container locally
    """
    
    # Dockerfile:
    # FROM python:3.10-slim
    # WORKDIR /app
    # COPY requirements.txt .
    # RUN pip install -r requirements.txt
    # COPY . .
    # CMD ["uvicorn", "solution:app", "--host", "0.0.0.0", "--port", "8000"]
    
    pass


# Exercise 10: Monitoring
def exercise_monitoring():
    """
    Exercise 10: Implement observability
    
    Tasks:
    1. Set up logging
    2. Add Langfuse tracing
    3. Monitor performance metrics
    4. Create dashboards
    """
    
    # TODO: Basic logging
    # import logging
    # logging.basicConfig(level=logging.INFO)
    
    # TODO: Langfuse setup
    # langfuse = Langfuse()
    
    # TODO: Custom metrics
    # LATENCY = Histogram('rag_latency_seconds')
    # TOKENS = Counter('rag_tokens_used')
    
    pass


def run_exercises():
    """Run all exercises"""
    exercises = [
        ("Ingestion Pipeline", exercise_ingestion),
        ("Multi-modal Processing", exercise_multimodal),
        ("Hybrid Search", exercise_hybrid_search),
        ("API Development", exercise_api),
        ("Evaluation", exercise_evaluation),
        ("LangGraph Agent", exercise_langgraph),
        ("Bedrock Integration", exercise_bedrock),
        ("Optimization", exercise_optimization),
        ("Deployment", exercise_deployment),
        ("Monitoring", exercise_monitoring),
    ]
    
    print("Advanced RAG Pipeline Exercises")
    print("=" * 50)
    
    for name, exercise in exercises:
        print(f"\n[ ] {name}")
        # exercise()


if __name__ == "__main__":
    run_exercises()