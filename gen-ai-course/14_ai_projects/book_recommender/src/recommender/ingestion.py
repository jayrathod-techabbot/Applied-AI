"""
Book ingestion pipeline.

Reads books.csv and uploads chunked, embedded documents to Azure AI Search.

Expected CSV columns (from books.csv / Google Books dataset)
-------------------------------------------------------------
isbn13, isbn10, title, subtitle, authors, categories, thumbnail,
description, published_year, average_rating, num_pages, ratings_count
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import List

import pandas as pd
from openai import AzureOpenAI
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
    SearchIndex,
)

from .config import get_settings

logger = logging.getLogger(__name__)


class BookIngestion:
    """Handles chunking, embedding, and uploading books to Azure AI Search."""

    EMBEDDING_DIM = 1536  # text-embedding-ada-002 output dimension

    def __init__(self) -> None:
        self.settings = get_settings()

        self._openai_client = AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_key,
            api_version="2024-02-01",
        )

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_book_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 64,
    ) -> List[str]:
        """Split *text* into overlapping word-level chunks.

        Parameters
        ----------
        text:       Full book / passage text.
        chunk_size: Number of words per chunk.
        overlap:    Number of words shared between consecutive chunks.
        """
        if not text or not text.strip():
            return []

        words = text.split()
        step = max(chunk_size - overlap, 1)
        chunks: List[str] = []

        for start in range(0, len(words), step):
            chunk_words = words[start : start + chunk_size]
            chunks.append(" ".join(chunk_words))
            if start + chunk_size >= len(words):
                break

        return chunks

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """Embed a list of text chunks using Azure OpenAI Ada-002.

        Batches requests to stay within API limits (max 2048 texts per call).
        """
        if not chunks:
            return []

        embeddings: List[List[float]] = []
        batch_size = 16  # conservative batch size

        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start : batch_start + batch_size]
            try:
                response = self._openai_client.embeddings.create(
                    model=self.settings.azure_embedding_deployment,
                    input=batch,
                )
                for item in response.data:
                    embeddings.append(item.embedding)
            except Exception as exc:
                logger.error(
                    "Embedding batch %d-%d failed: %s",
                    batch_start,
                    batch_start + batch_size,
                    exc,
                )
                raise

        return embeddings

    def ingest_books(self, csv_path: str | Path) -> int:
        """Read *csv_path*, chunk each book, embed chunks, upload to search.

        Returns the total number of documents uploaded.
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        self._ensure_index_exists()

        df = pd.read_csv(csv_path)

        # Support both the original schema and the Google Books CSV schema
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

        # Use description as the text to chunk when no dedicated text column exists
        text_col = "text" if "text" in df.columns else "description"

        # Fill missing optional columns with sensible defaults
        for opt_col in ("thumbnail", "average_rating", "num_pages"):
            if opt_col not in df.columns:
                df[opt_col] = None

        total_uploaded = 0

        for _, row in df.iterrows():
            chunks = self.chunk_book_text(str(row[text_col]))
            if not chunks:
                logger.warning("No chunks for book '%s', skipping.", row["title"])
                continue

            embeddings = self.embed_chunks(chunks)

            # Safely coerce year; skip rows with unparseable year
            try:
                year = int(row["year"])
            except (ValueError, TypeError):
                logger.warning("Invalid year for '%s', skipping.", row["title"])
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
                    "thumbnail": str(row["thumbnail"]) if pd.notna(row.get("thumbnail")) else "",
                    "average_rating": float(row["average_rating"]) if pd.notna(row.get("average_rating")) else None,
                    "num_pages": int(row["num_pages"]) if pd.notna(row.get("num_pages")) else None,
                    "chunk_index": idx,
                    "chunk_text": chunk,
                    "content_vector": embedding,
                }
                documents.append(doc)

            try:
                results = self._search_client.upload_documents(documents=documents)
                succeeded = sum(1 for r in results if r.succeeded)
                total_uploaded += succeeded
                logger.info(
                    "Uploaded %d/%d chunks for '%s'.",
                    succeeded,
                    len(documents),
                    row["title"],
                )
            except Exception as exc:
                logger.error("Failed to upload chunks for '%s': %s", row["title"], exc)
                raise

        logger.info("Ingestion complete. Total documents uploaded: %d", total_uploaded)
        return total_uploaded

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_index_exists(self) -> None:
        """Create the Azure AI Search index if it does not already exist."""
        index_name = self.settings.azure_search_index

        existing = [idx.name for idx in self._index_client.list_index_names()]
        if index_name in existing:
            logger.info("Index '%s' already exists, skipping creation.", index_name)
            return

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="author", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="genre", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="year", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SimpleField(name="thumbnail", type=SearchFieldDataType.String),
            SimpleField(name="average_rating", type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SimpleField(name="num_pages", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
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
        logger.info("Created Azure AI Search index '%s'.", index_name)
