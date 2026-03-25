"""
main.py – FastAPI application for the Multi-Agent Researcher platform.

Endpoints
---------
POST /research
    Accepts a research topic and runs the full CrewAI pipeline.
    Returns a JSON payload containing the markdown report and extracted sources.

GET /health
    Lightweight liveness check.

Run with:
    uvicorn main:app --port 8001 --reload
"""

from __future__ import annotations

import re
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from researcher.crew.crew_builder import build_crew


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    # Eagerly validate configuration at startup so bad env vars surface early.
    try:
        from researcher.config import settings  # noqa: F401
    except Exception as exc:
        raise RuntimeError(f"Configuration error – check your .env file: {exc}") from exc
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Multi-Agent Researcher",
    description=(
        "A CrewAI-powered research platform that uses a Researcher, Critic, and "
        "Writer agent to produce verified, cited markdown reports."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The subject matter to research.",
        examples=["Quantum computing advances in 2025"],
    )


class SourceProvenance(BaseModel):
    index: int
    citation: str


class ResearchResponse(BaseModel):
    topic: str
    report_markdown: str
    sources: list[SourceProvenance]
    elapsed_seconds: float
    cosmos_db_id: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_sources(markdown: str) -> list[SourceProvenance]:
    """
    Parse the References section of the markdown report to build a structured
    source-provenance list.

    Looks for a section that starts with '## References' and extracts numbered
    list items of the form:  1. Title – https://...
    """
    sources: list[SourceProvenance] = []
    in_references = False

    for line in markdown.splitlines():
        stripped = line.strip()

        if re.match(r"^#{1,3}\s+References", stripped, re.IGNORECASE):
            in_references = True
            continue

        if in_references:
            # Stop at the next heading.
            if stripped.startswith("#"):
                break
            # Match numbered list items: "1. ..." or "1) ..."
            m = re.match(r"^(\d+)[.)]\s+(.+)$", stripped)
            if m:
                sources.append(
                    SourceProvenance(index=int(m.group(1)), citation=m.group(2).strip())
                )

    return sources


def _extract_cosmos_id(report: str) -> str | None:
    """Extract the Cosmos DB document ID from the Writer's confirmation line."""
    m = re.search(r"Report saved to Cosmos DB:\s*([^\s\n]+)", report, re.IGNORECASE)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", summary="Liveness check")
async def health() -> JSONResponse:
    return JSONResponse(content={"status": "ok", "service": "multi-agent-researcher"})


@app.post(
    "/research",
    response_model=ResearchResponse,
    summary="Run the multi-agent research pipeline",
    description=(
        "Kicks off the Researcher → Critic → Writer pipeline for the given topic. "
        "The crew runs synchronously; expect 2–5 minutes for a full report."
    ),
)
async def research(request: ResearchRequest) -> ResearchResponse:
    topic = request.topic.strip()

    if not topic:
        raise HTTPException(status_code=422, detail="topic must not be blank.")

    start = time.perf_counter()

    try:
        crew = build_crew(topic)
        # crew.kickoff() returns a CrewOutput object; the final task output is in
        # crew_output.raw (or the last element of crew_output.tasks_output).
        crew_output = crew.kickoff()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline failed: {exc}",
        ) from exc

    elapsed = round(time.perf_counter() - start, 2)

    # Extract the markdown report from the crew output.
    if hasattr(crew_output, "raw"):
        report_markdown: str = crew_output.raw or ""
    else:
        # Fallback: stringify the output.
        report_markdown = str(crew_output)

    sources = _extract_sources(report_markdown)
    cosmos_id = _extract_cosmos_id(report_markdown)

    return ResearchResponse(
        topic=topic,
        report_markdown=report_markdown,
        sources=sources,
        elapsed_seconds=elapsed,
        cosmos_db_id=cosmos_id,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
