from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SyncAction(str, Enum):
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    SOURCE_SYNC = "source_sync"


class SyncSource(str, Enum):
    GOOGLE_CALENDAR = "google_calendar"
    GOOGLE_DRIVE = "google_drive"
    GMAIL = "gmail"


class SyncDirection(str, Enum):
    NOTION_TO_SOURCE = "notion_to_source"
    SOURCE_TO_NOTION = "source_to_notion"
    BIDIRECTIONAL = "bidirectional"


class SyncRequest(BaseModel):
    action: SyncAction = Field(..., description="Type of sync to perform")
    sources: Optional[List[SyncSource]] = Field(
        default=None,
        description="Sources to sync",
    )
    direction: SyncDirection = Field(
        default=SyncDirection.BIDIRECTIONAL,
        description="Direction of sync",
    )


class SourceSyncResult(BaseModel):
    status: str
    records_synced: int = 0
    conflicts_resolved: int = 0
    errors: List[str] = []
    last_sync: str


class SyncResponse(BaseModel):
    sync_results: Dict[str, SourceSyncResult]
    health: Dict[str, Any]


class ConflictResolution(BaseModel):
    source: str
    record_id: str
    resolution: str
    reasoning: str
    merged_data: Dict[str, Any]


class HealthStatus(BaseModel):
    all_systems_healthy: bool
    uptime_hours: float
    error_rate: float
    next_sync: Optional[str] = None
    integrations: Dict[str, Dict[str, Any]] = {}
