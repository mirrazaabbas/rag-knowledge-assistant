"""Public package surface for RAG Knowledge Assistant."""
from app import Chunk, chunk_text, cosine, idf, load_corpus, search, tokens, vector
from integration_contract import build_evaluation_record, validate_evaluation_record

__all__ = [
    "Chunk",
    "build_evaluation_record",
    "chunk_text",
    "cosine",
    "idf",
    "load_corpus",
    "search",
    "tokens",
    "validate_evaluation_record",
    "vector",
]
