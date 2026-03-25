from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"

    # Azure AI Search
    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index: str = "books-index"

    # Retrieval settings
    top_k: int = 10
    similarity_threshold: float = 0.72

    model_config = {
        "env_file": str(Path(__file__).parents[2] / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
