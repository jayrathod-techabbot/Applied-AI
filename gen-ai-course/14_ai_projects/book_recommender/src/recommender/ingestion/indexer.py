import logging
import uuid
from pathlib import Path
from typing import List, Optional
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)

from ..config import get_settings
from .chunker import sentence_aware_chunking
from .embedder import BookEmbedder

logger = logging.getLogger(__name__)

class BookIndexer:
    """Handles uploading books to Azure AI Search."""

    EMBEDDING_DIM = 1536  # text-embedding-ada-002 output dimension

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedder = BookEmbedder()
        
        credential = AzureKeyCredential(self.settings.azure_search_key)
        self._index_client = SearchIndexClient(
            endpoint=self.settings.azure_search_endpoint,
            credential=credential,
        )
        self._search_client = SearchClient(
            endpoint=self.settings.azure_search_endpoint,
            index_name=self.settings.azure_search_index,
            credential=credential,
        )

    def ingest_books(self, csv_path: str | Path) -> int:
        """Read *csv_path*, chunk each book, embed chunks, upload to search."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        self._ensure_index_exists()

        df = pd.read_csv(csv_path)

        # Map current column names to standardized ones
        col_map = {
            "authors": "author",
            "categories": "genre",
            "published_year": "year",
        }
        df = df.rename(columns=col_map)

        required_cols = {"title", "author", "genre", "year", "description"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing columns: {missing}")

        text_col = "description"
        total_uploaded = 0

        for _, row in df.iterrows():
            chunks = sentence_aware_chunking(str(row[text_col]))
            if not chunks:
                continue

            embeddings = self.embedder.embed_chunks(chunks)

            try:
                year = int(row["year"])
            except (ValueError, TypeError):
                continue

            documents = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc = {
                    "id": str(uuid.uuid4()),
                    "title": str(row["title"]),
                    "author": str(row["author"]),
                    "genre": str(row["genre"]),
                    "year": year,
                    "description": str(row["description"]),
                    "chunk_index": idx,
                    "chunk_text": chunk,
                    "content_vector": embedding,
                }
                documents.append(doc)

            try:
                results = self._search_client.upload_documents(documents=documents)
                succeeded = sum(1 for r in results if r.succeeded)
                total_uploaded += succeeded
                logger.info(f"Uploaded {succeeded} chunks for '{row['title']}'.")
            except Exception as exc:
                logger.error(f"Failed to upload chunks for '{row['title']}': {exc}")
                raise

        return total_uploaded

    def _ensure_index_exists(self) -> None:
        """Create the Azure AI Search index if it does not already exist."""
        index_name = self.settings.azure_search_index
        existing = list(self._index_client.list_index_names())
        if index_name in existing:
            return

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="author", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="genre", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="year", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
            SearchableField(name="chunk_text", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self.EMBEDDING_DIM,
                vector_search_profile_name="hnsw-profile",
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")],
        )

        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search,
        )

        self._index_client.create_index(index)
        logger.info(f"Created Azure AI Search index '{index_name}'.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest book metadata into Azure AI Search.")
    parser.add_argument("--source", type=str, required=True, help="Path to books.csv")
    args = parser.parse_args()

    # Use basicConfig to see output if run as script
    logging.basicConfig(level=logging.INFO)
    
    indexer = BookIndexer()
    indexer.ingest_books(args.source)
