"""Portable evaluation contract for cross-project portfolio integration.

The RAG service can export an answer and its retrieval evidence without requiring
the evaluation harness to import RAG implementation details. The contract is
plain JSON-compatible data and intentionally contains no credentials.
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "portfolio-evidence/v1"
PRODUCER = "rag-knowledge-assistant"


def _passage_value(passage: Any, name: str, default: Any = None) -> Any:
    if isinstance(passage, dict):
        return passage.get(name, default)
    return getattr(passage, name, default)


def build_evaluation_record(
    query: str,
    answer: str,
    passages: list[Any],
    *,
    latency_ms: float | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the stable JSON contract consumed by the evaluation harness."""
    if not query.strip():
        raise ValueError("query cannot be empty")
    if not isinstance(answer, str):
        raise TypeError("answer must be a string")
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("latency_ms cannot be negative")

    retrieval: list[dict[str, Any]] = []
    context: list[str] = []
    retrieved_ids: list[str] = []
    for fallback_rank, passage in enumerate(passages, start=1):
        source = str(_passage_value(passage, "source", "")).strip()
        text = str(_passage_value(passage, "text", "")).strip()
        if not source or not text:
            raise ValueError("each passage must contain non-empty source and text")
        rank = int(_passage_value(passage, "rank", fallback_rank))
        score = float(_passage_value(passage, "score", 0.0))
        retrieved_ids.append(source)
        context.append(text)
        retrieval.append({"id": source, "rank": rank, "score": score})

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "producer": PRODUCER,
        "query": query,
        "output": answer,
        "retrieved_ids": retrieved_ids,
        "citations": list(dict.fromkeys(retrieved_ids)),
        "context": context,
        "retrieval": retrieval,
        "tool_calls": list(tool_calls or []),
    }
    if latency_ms is not None:
        record["latency_ms"] = float(latency_ms)
    return record


def validate_evaluation_record(record: dict[str, Any]) -> list[str]:
    """Return validation errors rather than throwing for evaluator-friendly use."""
    errors: list[str] = []
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if record.get("producer") != PRODUCER:
        errors.append(f"producer must be {PRODUCER!r}")
    for field in ("query", "output"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ("retrieved_ids", "citations", "context", "retrieval", "tool_calls"):
        if not isinstance(record.get(field), list):
            errors.append(f"{field} must be a list")
    latency = record.get("latency_ms")
    if latency is not None and (not isinstance(latency, (int, float)) or latency < 0):
        errors.append("latency_ms must be a non-negative number when provided")
    return errors
