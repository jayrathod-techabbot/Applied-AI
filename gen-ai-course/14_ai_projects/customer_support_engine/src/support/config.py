from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"

    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_KEY: str
    AZURE_SEARCH_INDEX: str = "kb-index"

    # Cosmos DB
    COSMOS_ENDPOINT: str
    COSMOS_KEY: str
    COSMOS_DB: str = "support_db"
    COSMOS_CONTAINER: str = "conversations"

    # Agent settings
    MAX_RETRIES: int = 3


settings = Settings()
