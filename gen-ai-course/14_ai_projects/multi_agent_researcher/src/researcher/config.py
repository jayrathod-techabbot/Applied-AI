"""
Configuration settings for the Multi-Agent Researcher platform.
Loads all secrets and endpoints from environment variables (or a .env file).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings resolved from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Azure OpenAI ---
    azure_openai_endpoint: str
    azure_openai_key: str
    azure_openai_deployment: str = "gpt-4o"
    azure_embedding_deployment: str = "text-embedding-ada-002"

    # --- Azure AI Search ---
    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index: str = "research-index"

    # --- Cosmos DB ---
    cosmos_endpoint: str
    cosmos_key: str
    cosmos_db: str = "research-db"
    cosmos_container: str = "reports"

    # --- Optional web-search key (falls back to DuckDuckGo if absent) ---
    serper_api_key: str | None = None


# Module-level singleton so every import gets the same instance.
settings = Settings()
