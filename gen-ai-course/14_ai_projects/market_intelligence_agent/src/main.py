# src/main.py
"""
FastAPI application for the Market Intelligence Agent platform.

Endpoints:
  POST /analyze  — Run the full intelligence pipeline for a given query.
  GET  /health   — Service health check.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from market_intel.agents.orchestrator import OrchestratorAgent
from market_intel.pipelines.rag_chain import RAGChain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan — warm up agents at startup
# ---------------------------------------------------------------------------

_orchestrator: OrchestratorAgent | None = None
_rag_chain: RAGChain | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator, _rag_chain
    logger.info("Starting Market Intelligence Agent platform...")
    _orchestrator = OrchestratorAgent()
    _rag_chain = RAGChain()
    logger.info("Agents initialised and ready.")
    yield
    logger.info("Shutting down Market Intelligence Agent platform.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Market Intelligence Agent",
    description=(
        "Multi-agent market intelligence platform. "
        "Combines hybrid Azure AI Search retrieval, GPT-4o reasoning, "
        "and embedding-based confidence validation."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The market intelligence question to investigate.",
        examples=["What are the latest competitive moves by hyperscalers in the AI chip market?"],
    )
    use_agent: bool = Field(
        default=False,
        description=(
            "If true, use the full AgentExecutor orchestrator (dynamic multi-round retrieval). "
            "If false (default), use the deterministic RAGChain pipeline (faster, more predictable)."
        ),
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Number of chunks to retrieve. Overrides the default setting.",
    )


class ConfidenceDetail(BaseModel):
    confidence_score: float
    confidence_label: str
    sentences_evaluated: int
    sources_compared: int
    sentence_scores: list[float]


class AnalyzeResponse(BaseModel):
    query: str
    analysis: str
    confidence_score: float
    confidence_label: str
    sources_used: int
    latency_ms: float
    validation_details: ConfidenceDetail


class HealthResponse(BaseModel):
    status: str
    version: str
    agents_ready: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    tags=["Operations"],
)
async def health() -> HealthResponse:
    """Returns the current health status of the service."""
    return HealthResponse(
        status="ok",
        version=app.version,
        agents_ready=(_orchestrator is not None and _rag_chain is not None),
    )


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Run market intelligence analysis",
    tags=["Intelligence"],
    status_code=status.HTTP_200_OK,
)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Execute the full market intelligence pipeline for the given query.

    - Retrieves top-k evidence chunks from Azure AI Search (hybrid BM25 + vector).
    - Synthesizes a structured executive briefing using GPT-4o.
    - Scores the output confidence against retrieved embeddings.
    - Returns the report with a confidence score (0.0 - 1.0).
    """
    global _orchestrator, _rag_chain

    if _orchestrator is None or _rag_chain is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agents are not yet initialised. Please retry in a moment.",
        )

    logger.info(
        "POST /analyze | query=%r | use_agent=%s | top_k=%s",
        request.query,
        request.use_agent,
        request.top_k,
    )

    t_start = time.perf_counter()

    try:
        if request.use_agent:
            result = await _orchestrator.run(request.query)
            validation_details = result["validation_details"]
        else:
            chain = RAGChain(top_k=request.top_k) if request.top_k else _rag_chain
            output = await chain.arun(request.query)
            result = output.to_dict()
            validation_details = result["validation_details"]

    except Exception as exc:
        logger.exception("Pipeline error for query=%r: %s", request.query, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {exc}",
        ) from exc

    latency_ms = round((time.perf_counter() - t_start) * 1000, 1)

    logger.info(
        "POST /analyze complete | confidence=%.3f | latency=%.1f ms",
        result["confidence_score"],
        latency_ms,
    )

    return AnalyzeResponse(
        query=result["query"],
        analysis=result["analysis"],
        confidence_score=result["confidence_score"],
        confidence_label=result["confidence_label"],
        sources_used=result["sources_used"],
        latency_ms=latency_ms,
        validation_details=ConfidenceDetail(**validation_details),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
