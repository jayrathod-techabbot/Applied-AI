# src/market_intel/config.py
"""
Application settings loaded from environment variables via pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"

    # Azure AI Search
    azure_search_endpoint: str
    azure_search_api_key: str
    azure_search_index: str = "market-intel-index"

    # Azure Blob Storage
    azure_storage_connection_string: str
    azure_storage_container: str = "reports"

    # Retrieval settings
    top_k: int = 10


settings = Settings()
