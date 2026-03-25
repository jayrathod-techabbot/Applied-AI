"""
WebSearchTool – CrewAI BaseTool for live web search.

Uses SerperDev when SERPER_API_KEY is configured; otherwise falls back
to the free DuckDuckGo search library (duckduckgo-search).
"""

from __future__ import annotations

import json
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from researcher.config import settings


class _WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the web.")
    max_results: int = Field(default=5, description="Maximum number of web results to return.")


class WebSearchTool(BaseTool):
    """Searches the web for recent information about a query."""

    name: str = "web_search"
    description: str = (
        "Search the live web for up-to-date information on a given query. "
        "Returns titles, URLs, and short snippets for the top results."
    )
    args_schema: Type[BaseModel] = _WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:  # type: ignore[override]
        if settings.serper_api_key:
            return self._serper_search(query, max_results)
        return self._duckduckgo_search(query, max_results)

    # ------------------------------------------------------------------
    # SerperDev backend
    # ------------------------------------------------------------------

    def _serper_search(self, query: str, max_results: int) -> str:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": settings.serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": max_results}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return f"SerperDev search failed: {exc}. Falling back to DuckDuckGo."

        results = []
        for item in data.get("organic", [])[:max_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
            )

        if not results:
            return "No web results found."

        return json.dumps(results, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # DuckDuckGo backend
    # ------------------------------------------------------------------

    def _duckduckgo_search(self, query: str, max_results: int) -> str:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return (
                "duckduckgo-search is not installed. "
                "Install it with: pip install duckduckgo-search"
            )

        results = []
        try:
            with DDGS() as ddgs:
                for hit in ddgs.text(query, max_results=max_results):
                    results.append(
                        {
                            "title": hit.get("title", ""),
                            "url": hit.get("href", ""),
                            "snippet": hit.get("body", ""),
                        }
                    )
        except Exception as exc:
            return f"DuckDuckGo search failed: {exc}"

        if not results:
            return "No web results found."

        return json.dumps(results, ensure_ascii=False, indent=2)
