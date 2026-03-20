"""Azure OpenAI client with retry logic, token tracking, and cost estimation."""
import time
import logging
import uuid
from openai import AzureOpenAI, APIConnectionError, RateLimitError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings
from app.models import Message, TokenUsage

logger = logging.getLogger(__name__)
settings = get_settings()

# Cost per 1K tokens (GPT-4o as of 2024 — update as pricing changes)
COST_PER_1K_PROMPT_TOKENS = 0.005
COST_PER_1K_COMPLETION_TOKENS = 0.015


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    prompt_cost = (prompt_tokens / 1000) * COST_PER_1K_PROMPT_TOKENS
    completion_cost = (completion_tokens / 1000) * COST_PER_1K_COMPLETION_TOKENS
    return round(prompt_cost + completion_cost, 6)


class LLMClient:
    """Wrapper around Azure OpenAI with observability and resilience."""

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            timeout=settings.request_timeout,
            max_retries=0,  # We handle retries with tenacity
        )
        self.deployment = settings.azure_openai_deployment

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
        reraise=True,
    )
    def chat(
        self,
        messages: list[Message],
        max_tokens: int | None = None,
        temperature: float | None = None,
        request_id: str | None = None,
    ) -> tuple[str, TokenUsage]:
        """Send chat completion request. Returns (response_text, token_usage)."""
        request_id = request_id or str(uuid.uuid4())
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature if temperature is not None else settings.temperature

        openai_messages = [{"role": m.role.value, "content": m.content} for m in messages]

        logger.info(
            "LLM request",
            extra={
                "request_id": request_id,
                "model": self.deployment,
                "message_count": len(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency_ms = (time.time() - start) * 1000

            usage = response.usage
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                estimated_cost_usd=_estimate_cost(usage.prompt_tokens, usage.completion_tokens),
            )

            content = response.choices[0].message.content or ""

            logger.info(
                "LLM response",
                extra={
                    "request_id": request_id,
                    "latency_ms": round(latency_ms, 2),
                    "prompt_tokens": token_usage.prompt_tokens,
                    "completion_tokens": token_usage.completion_tokens,
                    "cost_usd": token_usage.estimated_cost_usd,
                    "finish_reason": response.choices[0].finish_reason,
                },
            )
            return content, token_usage

        except RateLimitError as e:
            logger.warning("Rate limit hit, will retry", extra={"request_id": request_id, "error": str(e)})
            raise
        except APIConnectionError as e:
            logger.error("Connection error, will retry", extra={"request_id": request_id, "error": str(e)})
            raise
        except APIStatusError as e:
            logger.error(
                "Azure OpenAI API error",
                extra={"request_id": request_id, "status": e.status_code, "error": str(e)},
            )
            raise
