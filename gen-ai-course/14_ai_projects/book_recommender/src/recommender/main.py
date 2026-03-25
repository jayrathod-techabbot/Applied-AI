from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import time
import logging

from .models import RecommendationRequest, RecommendationResponse
from .recommendation.pipeline import recommend
from .utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="LLM Semantic Book Recommender API",
    description="Understanding user intent beyond keyword matching.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response

@app.get("/health")
async def health():
    return {"status": "ok", "service": "book-recommender"}

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Accept a natural-language query and return recommendations.
    """
    try:
        results = await recommend(query=request.query, top_k=request.top_k)
        return RecommendationResponse(
            query=request.query,
            recommendations=results
        )
    except Exception as exc:
        logger.exception(f"Recommendation pipeline failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {str(exc)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
