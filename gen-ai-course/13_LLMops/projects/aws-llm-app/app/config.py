"""Application configuration via environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Bedrock
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # App
    app_name: str = "AWS LLM App"
    app_version: str = "1.0.0"
    environment: str = "development"
    max_tokens: int = 1000
    temperature: float = 0.7

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Cache (ElastiCache Redis)
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600

    # Guardrails
    max_input_length: int = 4000
    enable_pii_detection: bool = True

    # AWS
    aws_secrets_manager_secret_name: str = "llm-app/secrets"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
