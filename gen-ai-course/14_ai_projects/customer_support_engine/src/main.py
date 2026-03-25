"""
Customer Support Engine – FastAPI entrypoint.

Endpoints
---------
GET  /health                        – Liveness check.
POST /support/start                 – Start or continue a support conversation.
WS   /ws/{conversation_id}         – Real-time WebSocket interface.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from support.config import settings
from support.graph.builder import build_graph
from support.memory.checkpointer import CosmosDBCheckpointer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared graph instance (initialised at startup)
# ---------------------------------------------------------------------------

_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _graph
    logger.info("Initialising LangGraph with CosmosDB checkpointer …")
    try:
        checkpointer = CosmosDBCheckpointer(
            endpoint=settings.COSMOS_ENDPOINT,
            key=settings.COSMOS_KEY,
            database_name=settings.COSMOS_DB,
            container_name=settings.COSMOS_CONTAINER,
        )
        _graph = build_graph(checkpointer=checkpointer)
        logger.info("Graph ready.")
    except Exception as exc:
        logger.warning(
            "Could not initialise CosmosDB checkpointer (%s); falling back to MemorySaver.",
            exc,
        )
        _graph = build_graph()

    yield

    logger.info("Shutting down Customer Support Engine.")


app = FastAPI(
    title="Customer Support Engine",
    description="Stateful multi-agent customer support system powered by LangGraph + Azure AI.",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class StartRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class StartResponse(BaseModel):
    conversation_id: str
    reply: str
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_graph(conversation_id: str, user_message: str) -> Dict[str, Any]:
    """Invoke the graph synchronously for a given conversation."""
    config = {"configurable": {"thread_id": conversation_id}}

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "conversation_id": conversation_id,
        "kb_chunks": [],
        "resolution_steps": [],
        "retry_count": 0,
        "issue_type": None,
        "severity": None,
        "status": None,
        "feedback_signal": None,
    }

    result = _graph.invoke(initial_state, config=config)
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"])
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "customer-support-engine"}


@app.post("/support/start", response_model=StartResponse, tags=["support"])
async def start_support(body: StartRequest) -> StartResponse:
    """
    Start or continue a support conversation.

    If ``conversation_id`` is omitted a new one is generated automatically.
    """
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialised yet.")

    conversation_id = body.conversation_id or str(uuid.uuid4())

    try:
        result = _run_graph(conversation_id, body.message)
    except Exception as exc:
        logger.error("Graph invocation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Extract the last AI message as the reply
    from langchain_core.messages import AIMessage

    ai_messages = [m for m in result.get("messages", []) if isinstance(m, AIMessage)]
    reply = ai_messages[-1].content if ai_messages else "I'm sorry, I could not process your request."

    return StartResponse(
        conversation_id=conversation_id,
        reply=reply,
        issue_type=result.get("issue_type"),
        severity=result.get("severity"),
        status=result.get("status"),
    )


@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str) -> None:
    """
    WebSocket endpoint for real-time support interactions.

    Message protocol (JSON):
    - Client → Server: ``{"message": "<user text>"}``
    - Server → Client: ``{"reply": "...", "issue_type": "...", "severity": "...", "status": "..."}``
    - Server → Client (error): ``{"error": "<message>"}``
    - Client → Server: ``{"message": "exit"}`` to close the connection gracefully.
    """
    await websocket.accept()
    logger.info("WebSocket connected: conversation_id=%s", conversation_id)

    if _graph is None:
        await websocket.send_json({"error": "Graph not initialised yet."})
        await websocket.close()
        return

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON payload."})
                continue

            user_message: str = payload.get("message", "").strip()
            if not user_message:
                await websocket.send_json({"error": "Empty message."})
                continue

            if user_message.lower() == "exit":
                await websocket.send_json({"reply": "Goodbye! Have a great day."})
                break

            try:
                result = _run_graph(conversation_id, user_message)
            except Exception as exc:
                logger.error("Graph error on WS: %s", exc, exc_info=True)
                await websocket.send_json({"error": str(exc)})
                continue

            from langchain_core.messages import AIMessage

            ai_messages = [
                m for m in result.get("messages", []) if isinstance(m, AIMessage)
            ]
            reply = (
                ai_messages[-1].content
                if ai_messages
                else "I'm sorry, I could not process your request."
            )

            await websocket.send_json(
                {
                    "reply": reply,
                    "issue_type": result.get("issue_type"),
                    "severity": result.get("severity"),
                    "status": result.get("status"),
                }
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: conversation_id=%s", conversation_id)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=False)
