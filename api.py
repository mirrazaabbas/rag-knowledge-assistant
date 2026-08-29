"""HTTP API for the RAG Knowledge Assistant retrieval layer."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import providers
from observability import configure_observability
from storage import PgVectorStore, VectorRecord

BASE_DIR = Path(__file__).resolve().parent
CORE_PATH = BASE_DIR / "app.py"
UI_PATH = BASE_DIR / "static" / "index.html"
SPEC = importlib.util.spec_from_file_location("rag_core", CORE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load RAG retrieval core.")
rag_core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rag_core
SPEC.loader.exec_module(rag_core)
provider_client_factory = providers.create_provider_client

app = FastAPI(
    title="RAG Knowledge Assistant API",
    version="1.3.0",
    description=(
        "Source-grounded document retrieval with transparent TF-IDF ranking, optional "
        "semantic retrieval and cited answer generation, plus PostgreSQL/pgvector-backed "
        "production retrieval and optional observability."
    ),
)
configure_observability(app)


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


class Passage(BaseModel):
    rank: int
    score: float
    source: str
    text: str


class SearchResponse(BaseModel):
    query: str
    indexed_chunks: int
    passages: list[Passage]


class AnswerResponse(SearchResponse):
    answer: str


def _load_corpus() -> list[object]:
    corpus = rag_core.load_corpus(rag_core.DEFAULT_DOCS)
    if not corpus:
        raise ValueError("No documents are available for retrieval.")
    return corpus


def _source_path(chunk: object) -> str:
    return str(Path(chunk.source).relative_to(BASE_DIR))


def _passage(rank: int, score: float, chunk: object) -> Passage:
    return Passage(
        rank=rank,
        score=round(score, 6),
        source=_source_path(chunk),
        text=chunk.text,
    )


def _semantic_passages(
    corpus: list[object], request: SearchRequest, client: providers.ProviderClient
) -> list[Passage]:
    """Use pgvector when configured, otherwise keep the credential-light in-memory path."""
    if not os.getenv("DATABASE_URL"):
        ranked = providers.semantic_rank(
            [chunk.text for chunk in corpus], request.query, client, request.top_k
        )
        return [
            _passage(rank, score, corpus[index])
            for rank, (score, index) in enumerate(ranked, 1)
        ]

    texts = [chunk.text for chunk in corpus]
    vectors = client.embed_texts([*texts, request.query])
    if len(vectors) != len(texts) + 1:
        raise RuntimeError("Embedding provider returned an unexpected vector count.")
    if not vectors or not vectors[0]:
        raise RuntimeError("Embedding provider returned an empty vector.")
    dimensions = len(vectors[0])
    if any(len(vector) != dimensions for vector in vectors):
        raise RuntimeError("Embedding provider returned inconsistent vector dimensions.")

    store = PgVectorStore()
    if store.dimensions != dimensions:
        raise RuntimeError(
            f"VECTOR_DIMENSIONS={store.dimensions} does not match provider dimensions {dimensions}."
        )
    store.ensure_schema()
    store.upsert(
        VectorRecord(_source_path(chunk), index, chunk.text, vectors[index])
        for index, chunk in enumerate(corpus)
    )
    results = store.search(vectors[-1], top_k=request.top_k)
    return [
        Passage(
            rank=rank,
            score=round(float(result["score"]), 6),
            source=str(result["source"]),
            text=str(result["text"]),
        )
        for rank, result in enumerate(results, 1)
    ]


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    if not UI_PATH.is_file():
        raise HTTPException(status_code=404, detail="Web interface is not available.")
    return FileResponse(UI_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readiness")
def readiness() -> dict[str, str]:
    """Report optional production dependency configuration without exposing secrets."""
    return {
        "status": "ready",
        "vector_store": "configured" if os.getenv("DATABASE_URL") else "local-baseline",
        "observability": "enabled"
        if os.getenv("OTEL_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        else "disabled",
    }


@app.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    try:
        corpus = _load_corpus()
        results = rag_core.search(corpus, request.query, request.top_k)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    passages = [_passage(rank, score, chunk) for rank, (score, chunk) in enumerate(results, 1)]
    return SearchResponse(query=request.query, indexed_chunks=len(corpus), passages=passages)


@app.post("/semantic-search", response_model=SearchResponse)
def semantic_search_documents(request: SearchRequest) -> SearchResponse:
    try:
        corpus = _load_corpus()
        client = provider_client_factory()
        passages = _semantic_passages(corpus, request, client)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SearchResponse(query=request.query, indexed_chunks=len(corpus), passages=passages)


@app.post("/answer", response_model=AnswerResponse)
def answer_question(request: SearchRequest) -> AnswerResponse:
    try:
        corpus = _load_corpus()
        client = provider_client_factory()
        passages = _semantic_passages(corpus, request, client)
        answer = providers.grounded_answer(
            request.query,
            [passage.text for passage in passages],
            client,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AnswerResponse(
        query=request.query,
        indexed_chunks=len(corpus),
        passages=passages,
        answer=answer,
    )
