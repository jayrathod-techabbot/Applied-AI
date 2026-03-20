"""Amazon Bedrock client (Claude 3) with retry and cost tracking."""
import json
import logging
import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings
from app.models import TokenUsage

logger = logging.getLogger(__name__)
settings = get_settings()

# Claude 3 Haiku pricing per 1K tokens (update as AWS pricing changes)
_INPUT_COST_PER_1K  = 0.00025
_OUTPUT_COST_PER_1K = 0.00125

SYSTEM_PROMPT = """You are a helpful, accurate, and professional AI assistant.
- Provide clear and concise answers
- Acknowledge uncertainty when you are unsure
- Decline requests that are harmful or unethical"""


class BedrockClient:
    def __init__(self):
        self._client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(ClientError),
        reraise=True,
    )
    def chat(self, messages: list[dict], max_tokens: int | None = None) -> tuple[str, TokenUsage]:
        max_tokens = max_tokens or settings.max_tokens

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        })

        try:
            response = self._client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            text = result["content"][0]["text"]
            usage = result.get("usage", {})

            input_tokens  = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cost = round(
                (input_tokens / 1000) * _INPUT_COST_PER_1K +
                (output_tokens / 1000) * _OUTPUT_COST_PER_1K, 6
            )
            token_usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost,
            )
            logger.info("Bedrock response", extra={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            })
            return text, token_usage

        except ClientError as e:
            logger.error("Bedrock error", extra={"error": str(e)})
            raise
