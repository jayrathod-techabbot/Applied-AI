"""Request / response schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_items=1, max_items=20)
    session_id: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)

    @validator("messages")
    def last_message_must_be_user(cls, v):
        if v and v[-1].role != "user":
            raise ValueError("Last message must be from the user")
        return v


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class ChatResponse(BaseModel):
    id: str
    message: Message
    token_usage: TokenUsage
    latency_ms: float
    model: str
    guardrail_passed: bool
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
