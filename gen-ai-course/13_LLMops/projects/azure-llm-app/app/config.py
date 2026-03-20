"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"

    # App Config
    app_name: str = "Azure LLM App"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    max_tokens: int = 1000
    temperature: float = 0.7
    request_timeout: int = 30

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600

    # Azure Application Insights
    applicationinsights_connection_string: str = ""

    # Guardrails
    max_input_length: int = 4000
    max_output_length: int = 8000
    enable_pii_detection: bool = True
    enable_toxicity_filter: bool = True
    toxicity_threshold: float = 0.7

    # Azure Key Vault
    azure_key_vault_url: str = ""

    # Evaluation
    eval_sample_rate: float = 0.1  # 10% of requests evaluated

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
