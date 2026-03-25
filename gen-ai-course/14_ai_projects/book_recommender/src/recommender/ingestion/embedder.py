from typing import List
import logging
from langchain_openai import AzureOpenAIEmbeddings
from ..config import get_settings

logger = logging.getLogger(__name__)

class BookEmbedder:
    """Uses Azure OpenAI to generate vector embeddings for text chunks."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self._embedder = AzureOpenAIEmbeddings(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            azure_deployment=self.settings.azure_openai_embedding_deployment,
        )

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """Embed a list of text chunks asynchronously."""
        if not chunks:
            return []
            
        logger.info(f"Embedding {len(chunks)} chunks...")
        return self._embedder.embed_documents(chunks)

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string for searching."""
        return self._embedder.embed_query(query)
