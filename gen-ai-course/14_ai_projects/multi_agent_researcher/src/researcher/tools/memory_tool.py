"""
CosmosMemoryTool – CrewAI BaseTool for persisting and retrieving research
reports in Azure Cosmos DB (NoSQL API).

Two operations are exposed via the `operation` field:
  - "save"     – upsert a report document.
  - "retrieve" – fetch a previously saved report by topic slug.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Literal, Type

from azure.cosmos import CosmosClient, PartitionKey, exceptions as cosmos_exc
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from researcher.config import settings


class _CosmosInput(BaseModel):
    operation: Literal["save", "retrieve"] = Field(
        description='Either "save" to persist a report or "retrieve" to fetch one.'
    )
    topic: str = Field(description="The research topic (used as the document key).")
    content: str | None = Field(
        default=None,
        description='Markdown report content. Required when operation is "save".',
    )
    sources: list[str] | None = Field(
        default=None,
        description='List of source URLs / citations. Used when operation is "save".',
    )


def _slugify(text: str) -> str:
    """Convert a topic string to a URL-safe identifier."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:120]


class CosmosMemoryTool(BaseTool):
    """Saves and retrieves research reports in Azure Cosmos DB."""

    name: str = "cosmos_memory"
    description: str = (
        "Persist a finished research report to Cosmos DB (operation='save') or "
        "retrieve a previously saved report by topic (operation='retrieve'). "
        "Use this after the Writer produces the final markdown."
    )
    args_schema: Type[BaseModel] = _CosmosInput

    # Lazy-initialised client handles.
    _cosmos_client: CosmosClient | None = None
    _container = None  # azure.cosmos.ContainerProxy

    def _get_container(self):
        if self._container is None:
            if self._cosmos_client is None:
                self._cosmos_client = CosmosClient(
                    url=settings.cosmos_endpoint,
                    credential=settings.cosmos_key,
                )
            db = self._cosmos_client.create_database_if_not_exists(settings.cosmos_db)
            self._container = db.create_container_if_not_exists(
                id=settings.cosmos_container,
                partition_key=PartitionKey(path="/topic_slug"),
                offer_throughput=400,
            )
        return self._container

    def _run(  # type: ignore[override]
        self,
        operation: Literal["save", "retrieve"],
        topic: str,
        content: str | None = None,
        sources: list[str] | None = None,
    ) -> str:
        container = self._get_container()
        slug = _slugify(topic)

        if operation == "save":
            return self._save(container, slug, topic, content, sources)
        return self._retrieve(container, slug)

    # ------------------------------------------------------------------

    def _save(self, container, slug: str, topic: str, content: str | None, sources: list[str] | None) -> str:
        if not content:
            return "Error: 'content' is required for the save operation."

        document = {
            "id": slug,
            "topic_slug": slug,
            "topic": topic,
            "content": content,
            "sources": sources or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            container.upsert_item(document)
            return f"Report for topic '{topic}' successfully saved to Cosmos DB (id={slug})."
        except Exception as exc:
            return f"Failed to save report to Cosmos DB: {exc}"

    def _retrieve(self, container, slug: str) -> str:
        try:
            item = container.read_item(item=slug, partition_key=slug)
            return json.dumps(
                {
                    "topic": item.get("topic", ""),
                    "content": item.get("content", ""),
                    "sources": item.get("sources", []),
                    "created_at": item.get("created_at", ""),
                },
                ensure_ascii=False,
                indent=2,
            )
        except cosmos_exc.CosmosResourceNotFoundError:
            return f"No saved report found for slug '{slug}'."
        except Exception as exc:
            return f"Failed to retrieve report from Cosmos DB: {exc}"
