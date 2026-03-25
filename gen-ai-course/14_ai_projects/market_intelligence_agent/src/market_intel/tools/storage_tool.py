# src/market_intel/tools/storage_tool.py
"""
BlobStorageTool — LangChain BaseTool that saves final intelligence reports
to Azure Blob Storage as JSON files.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Type

from azure.storage.blob import BlobServiceClient
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from market_intel.config import settings


class StorageInput(BaseModel):
    content: str = Field(
        description=(
            "The report content to save. Must be a JSON string with keys: "
            "'query', 'analysis', 'confidence_score', and optionally 'sources_used'."
        )
    )


class BlobStorageTool(BaseTool):
    """Saves structured intelligence reports to Azure Blob Storage."""

    name: str = "save_report_to_blob"
    description: str = (
        "Persist the final intelligence report to Azure Blob Storage. "
        "Call this tool after you have completed your analysis to save the report. "
        "Pass the full report as a JSON string."
    )
    args_schema: Type[BaseModel] = StorageInput

    _blob_service_client: Any = None

    def _get_client(self) -> BlobServiceClient:
        if self._blob_service_client is None:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
        return self._blob_service_client

    def _run(self, content: str) -> str:
        """Upload report blob and return the blob URL."""
        try:
            report_data = json.loads(content)
        except json.JSONDecodeError:
            # Wrap plain text in a report envelope
            report_data = {"raw_content": content}

        report_data["saved_at"] = datetime.now(timezone.utc).isoformat()
        blob_name = f"reports/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{uuid.uuid4()}.json"

        client = self._get_client()
        container_client = client.get_container_client(settings.azure_storage_container)

        # Ensure container exists
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            json.dumps(report_data, ensure_ascii=False, indent=2),
            overwrite=True,
            content_settings=None,
        )

        blob_url = blob_client.url
        return json.dumps({"status": "saved", "blob_name": blob_name, "url": blob_url})

    async def _arun(self, content: str) -> str:
        """Async wrapper — reuses synchronous Azure SDK client."""
        return self._run(content)


def build_storage_tool() -> BlobStorageTool:
    """Factory function to create a configured BlobStorageTool instance."""
    return BlobStorageTool()
