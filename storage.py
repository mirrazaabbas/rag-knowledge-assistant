"""PostgreSQL/pgvector storage for production-oriented RAG retrieval."""
from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class VectorRecord:
    """A persisted RAG chunk and its embedding."""

    source: str
    chunk_index: int
    text: str
    embedding: Sequence[float]


class PgVectorStore:
    """Small pgvector-backed store with explicit schema and cosine search."""

    def __init__(self, dsn: str | None = None, *, dimensions: int | None = None) -> None:
        if dimensions is None:
            raw_dimensions = os.getenv("VECTOR_DIMENSIONS", "1536").strip()
            try:
                dimensions = int(raw_dimensions)
            except ValueError as exc:
                raise ValueError("VECTOR_DIMENSIONS must be an integer") from exc
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")
        self.dsn = dsn or os.getenv("DATABASE_URL", "")
        if not self.dsn:
            raise ValueError("DATABASE_URL is required for pgvector storage")
        self.dimensions = dimensions

    def _connect(self):
        try:
            import psycopg
            from pgvector.psycopg import register_vector
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Production storage requires requirements-production.txt"
            ) from exc

        connection = psycopg.connect(self.dsn)
        register_vector(connection)
        return connection

    def ensure_schema(self) -> None:
        """Create pgvector extension, table, and HNSW cosine index if needed."""
        vector_type = f"vector({self.dimensions})"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                        id BIGSERIAL PRIMARY KEY,
                        source TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        embedding {vector_type} NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE(source, chunk_index)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS rag_chunks_embedding_hnsw
                    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
                    """
                )

    def upsert(self, records: Iterable[VectorRecord]) -> int:
        """Insert or update chunks. Returns the number of records processed."""
        rows = list(records)
        if not rows:
            return 0
        for row in rows:
            if len(row.embedding) != self.dimensions:
                raise ValueError(
                    f"embedding length {len(row.embedding)} does not match {self.dimensions}"
                )

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO rag_chunks (source, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source, chunk_index)
                    DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding
                    """,
                    [
                        (row.source, row.chunk_index, row.text, list(row.embedding))
                        for row in rows
                    ],
                )
        return len(rows)

    def search(self, query_embedding: Sequence[float], *, top_k: int = 5) -> list[dict]:
        """Return nearest chunks by cosine distance with a normalized similarity score."""
        if len(query_embedding) != self.dimensions:
            raise ValueError(
                f"query embedding length {len(query_embedding)} does not match {self.dimensions}"
            )
        if top_k < 1 or top_k > 50:
            raise ValueError("top_k must be between 1 and 50")

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT source, chunk_index, content,
                           1 - (embedding <=> %s) AS similarity
                    FROM rag_chunks
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (list(query_embedding), list(query_embedding), top_k),
                )
                return [
                    {
                        "source": source,
                        "chunk_index": chunk_index,
                        "text": content,
                        "score": float(similarity),
                    }
                    for source, chunk_index, content, similarity in cursor.fetchall()
                ]
