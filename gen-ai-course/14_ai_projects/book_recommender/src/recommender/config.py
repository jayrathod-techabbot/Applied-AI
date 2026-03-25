from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_key: str
    azure_openai_deployment: str = "gpt-4o"
    azure_embedding_deployment: str = "text-embedding-ada-002"

    # Azure AI Search
    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index: str = "books-index"

    # Retrieval settings
    top_k: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
