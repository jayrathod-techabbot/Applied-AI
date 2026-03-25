"""
FastAPI entry point for the Book Recommender service.

Endpoints
---------
POST /recommend  — accept a RecommendationRequest, return RecommendationResponse
GET  /health     — liveness probe
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from recommender.config import get_settings
from recommender.models import RecommendationRequest, RecommendationResponse
from recommender.recommender import BookRecommender

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application-level singleton state
# ---------------------------------------------------------------------------
_recommender: BookRecommender | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise expensive resources once at startup."""
    global _recommender
    logger.info("Initialising BookRecommender …")
    _recommender = BookRecommender()
    logger.info("BookRecommender ready.")
    yield
    logger.info("Shutting down BookRecommender service.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Book Recommender API",
    description="LLM-powered semantic book recommendation system backed by Azure AI Search.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware — request timing
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"], summary="Liveness probe")
async def health() -> JSONResponse:
    """Return service health status."""
    return JSONResponse(content={"status": "ok", "service": "book-recommender"})


@app.post(
    "/recommend",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    tags=["recommendations"],
    summary="Get book recommendations",
)
async def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """
    Accept a natural-language query and return ranked book recommendations
    with an LLM-generated explanation.

    - **query**: Free-text book-search query (required).
    - **filters**: Optional metadata filters, e.g. `{"genre": "Fantasy", "year": 2020}`.
    - **top_k**: Number of recommendations to return (1–50, default 5).
    """
    if _recommender is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommender is not initialised yet. Please retry in a moment.",
        )

    try:
        response = await _recommender.recommend(request)
    except Exception as exc:
        logger.exception("Recommendation pipeline failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {exc}",
        )

    return response


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info",
    )
