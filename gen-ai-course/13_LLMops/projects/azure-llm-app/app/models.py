"""Pydantic models for request/response validation."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Message(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_items=1, max_items=20)
    session_id: Optional[str] = None
    stream: bool = False
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    user_id: Optional[str] = None

    @validator("messages")
    def validate_last_message_is_user(cls, v):
        if v and v[-1].role != MessageRole.user:
            raise ValueError("Last message must be from the user")
        return v


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class GuardrailResult(BaseModel):
    passed: bool
    violations: list[str] = []
    redacted_content: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    session_id: Optional[str]
    message: Message
    token_usage: TokenUsage
    latency_ms: float
    model: str
    guardrail_input: GuardrailResult
    guardrail_output: GuardrailResult
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvaluationScore(BaseModel):
    request_id: str
    coherence: float = Field(..., ge=0.0, le=1.0)
    relevance: float = Field(..., ge=0.0, le=1.0)
    fluency: float = Field(..., ge=0.0, le=1.0)
    groundedness: Optional[float] = None
    overall: float = Field(..., ge=0.0, le=1.0)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: dict[str, str] = {}


class MetricsSummary(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    avg_tokens_per_request: float
    total_cost_usd: float
    guardrail_blocks: int
    cache_hit_rate: float
