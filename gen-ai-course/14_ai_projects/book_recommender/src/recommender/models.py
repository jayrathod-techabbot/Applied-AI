from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BookMetadata(BaseModel):
    title: str
    author: str
    genre: str
    year: int
    description: str
    thumbnail: Optional[str] = None
    average_rating: Optional[float] = None
    num_pages: Optional[int] = None


class SearchResult(BaseModel):
    book: BookMetadata
    score: float
    chunk_text: str


class RecommendationRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural-language query from the user")
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters, e.g. {'genre': 'Science Fiction', 'year': 2020}",
    )
    top_k: int = Field(default=5, ge=1, le=50, description="Number of recommendations to return")


class RecommendationResponse(BaseModel):
    query: str
    recommendations: List[SearchResult]
    explanation: str
