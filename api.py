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
    version="1.2.0",
    description=(
        "Source-grounded document retrieval with transparent TF-IDF ranking, optional "
        "semantic retrieval and cited answer generation, plus production-ready "
        "pgvector and observability building blocks."
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


def _passage(rank: int, score: float, chunk: object) -> Passage:
    return Passage(
        rank=rank,
        score=round(score, 6),
        source=str(Path(chunk.source).relative_to(BASE_DIR)),
        text=chunk.text,
    )


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
        ranked = providers.semantic_rank(
            [chunk.text for chunk in corpus], request.query, client, request.top_k
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    passages = [
        _passage(rank, score, corpus[index])
        for rank, (score, index) in enumerate(ranked, 1)
    ]
    return SearchResponse(query=request.query, indexed_chunks=len(corpus), passages=passages)


@app.post("/answer", response_model=AnswerResponse)
def answer_question(request: SearchRequest) -> AnswerResponse:
    try:
        corpus = _load_corpus()
        client = provider_client_factory()
        ranked = providers.semantic_rank(
            [chunk.text for chunk in corpus], request.query, client, request.top_k
        )
        passages = [
            _passage(rank, score, corpus[index])
            for rank, (score, index) in enumerate(ranked, 1)
        ]
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
