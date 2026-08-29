"""Cross-platform grounded answering using local retrieval plus a provider-neutral chat client."""
from __future__ import annotations

from pathlib import Path

import app
from ai_platform import AIClient


def answer_with_ai(
    query: str,
    client: AIClient,
    docs: Path = app.DEFAULT_DOCS,
    top_k: int = 3,
) -> dict[str, object]:
    corpus = app.load_corpus(docs)
    if not corpus:
        raise ValueError("No documents are available for retrieval.")
    ranked = app.search(corpus, query, top_k)
    passages = [chunk.text for _, chunk in ranked]
    sources = [str(Path(chunk.source).relative_to(docs.parent)) for _, chunk in ranked]
    context = "\n\n".join(
        f"[{index}] Source: {source}\n{text}"
        for index, (source, text) in enumerate(zip(sources, passages, strict=True), 1)
    )
    system = (
        "You are a source-grounded assistant. Answer only from the supplied passages, cite "
        "supporting passages using [1], [2], etc., and say when the sources are insufficient."
    )
    user = f"Question: {query}\n\nRetrieved passages:\n{context}"
    return {
        "query": query,
        "answer": client.generate(system, user),
        "sources": sources,
        "passages": passages,
    }
