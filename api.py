"""HTTP API for the RAG Knowledge Assistant retrieval layer."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
CORE_PATH = BASE_DIR / "app.py"
SPEC = importlib.util.spec_from_file_location("rag_core", CORE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load RAG retrieval core.")
rag_core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rag_core
SPEC.loader.exec_module(rag_core)

app = FastAPI(
    title="RAG Knowledge Assistant API",
    version="1.0.0",
    description="Source-grounded local document retrieval with transparent TF-IDF ranking.",
)


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    try:
        corpus = rag_core.load_corpus(rag_core.DEFAULT_DOCS)
        if not corpus:
            raise ValueError("No documents are available for retrieval.")
        results = rag_core.search(corpus, request.query, request.top_k)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    passages = [
        Passage(
            rank=rank,
            score=round(score, 6),
            source=str(Path(chunk.source).relative_to(BASE_DIR)),
            text=chunk.text,
        )
        for rank, (score, chunk) in enumerate(results, 1)
    ]
    return SearchResponse(
        query=request.query,
        indexed_chunks=len(corpus),
        passages=passages,
    )
