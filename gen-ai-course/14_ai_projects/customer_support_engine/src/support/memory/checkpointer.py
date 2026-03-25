"""Cosmos DB-backed checkpointer for LangGraph conversation state."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
)

logger = logging.getLogger(__name__)


class CosmosDBCheckpointer(BaseCheckpointSaver):
    """
    LangGraph checkpoint saver that persists graph state to Azure Cosmos DB.

    Each checkpoint is stored as a Cosmos document whose ``id`` is built from
    the thread_id (conversation_id) and the checkpoint's ``ts`` timestamp so
    that multiple checkpoints per conversation are supported.

    Parameters
    ----------
    endpoint:
        Cosmos DB account URI.
    key:
        Primary or secondary master key.
    database_name:
        Database name (created on first use if it does not exist).
    container_name:
        Container name (created on first use if it does not exist).
    serde:
        Optional custom serializer; falls back to JSON.
    """

    def __init__(
        self,
        endpoint: str,
        key: str,
        database_name: str,
        container_name: str,
        serde: Optional[SerializerProtocol] = None,
    ) -> None:
        super().__init__(serde=serde)

        client = CosmosClient(url=endpoint, credential=key)

        db = client.create_database_if_not_exists(id=database_name)
        self._container = db.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/thread_id"),
            offer_throughput=400,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _doc_id(thread_id: str, ts: str) -> str:
        # Cosmos id must not contain '/' – replace with '-'
        safe_ts = ts.replace("/", "-").replace(":", "-")
        return f"{thread_id}_{safe_ts}"

    def _to_doc(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> Dict[str, Any]:
        thread_id = config["configurable"]["thread_id"]
        ts = checkpoint["ts"]
        return {
            "id": self._doc_id(thread_id, ts),
            "thread_id": thread_id,
            "ts": ts,
            "checkpoint": self.serde.dumps(checkpoint).decode("utf-8")
            if isinstance(self.serde.dumps(checkpoint), bytes)
            else json.dumps(checkpoint),
            "metadata": json.dumps(metadata) if metadata else "{}",
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

    def _from_doc(
        self, doc: Dict[str, Any]
    ) -> Tuple[Checkpoint, CheckpointMetadata]:
        raw_cp = doc["checkpoint"]
        checkpoint: Checkpoint = (
            self.serde.loads(raw_cp.encode("utf-8"))
            if hasattr(self.serde, "loads")
            else json.loads(raw_cp)
        )
        metadata: CheckpointMetadata = json.loads(doc.get("metadata", "{}"))
        return checkpoint, metadata

    # ------------------------------------------------------------------
    # BaseCheckpointSaver interface
    # ------------------------------------------------------------------

    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """Return the latest (or specific) checkpoint for a thread."""
        thread_id = config["configurable"]["thread_id"]
        thread_ts: Optional[str] = config["configurable"].get("thread_ts")

        try:
            if thread_ts:
                doc_id = self._doc_id(thread_id, thread_ts)
                doc = self._container.read_item(item=doc_id, partition_key=thread_id)
                checkpoint, metadata = self._from_doc(doc)
                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                )

            # No specific ts → fetch the most recent checkpoint
            query = (
                "SELECT TOP 1 * FROM c WHERE c.thread_id = @tid "
                "ORDER BY c.ts DESC"
            )
            items = list(
                self._container.query_items(
                    query=query,
                    parameters=[{"name": "@tid", "value": thread_id}],
                    enable_cross_partition_query=False,
                )
            )
            if not items:
                return None

            checkpoint, metadata = self._from_doc(items[0])
            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "thread_ts": items[0]["ts"],
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
            )

        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as exc:
            logger.error("get_tuple failed: %s", exc, exc_info=True)
            return None

    def list(
        self,
        config: Dict[str, Any],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Yield checkpoints for a thread, newest first."""
        thread_id = config["configurable"]["thread_id"]
        top_clause = f"TOP {limit}" if limit else ""

        query = (
            f"SELECT {top_clause} * FROM c WHERE c.thread_id = @tid "
            "ORDER BY c.ts DESC"
        )
        try:
            items = self._container.query_items(
                query=query,
                parameters=[{"name": "@tid", "value": thread_id}],
                enable_cross_partition_query=False,
            )
            for doc in items:
                checkpoint, metadata = self._from_doc(doc)
                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "thread_ts": doc["ts"],
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                )
        except Exception as exc:
            logger.error("list checkpoints failed: %s", exc, exc_info=True)

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist a checkpoint and return the updated config."""
        doc = self._to_doc(config, checkpoint, metadata)
        try:
            self._container.upsert_item(doc)
        except Exception as exc:
            logger.error("put checkpoint failed: %s", exc, exc_info=True)

        thread_id = config["configurable"]["thread_id"]
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            }
        }
