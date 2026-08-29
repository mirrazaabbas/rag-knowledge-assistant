"""Reproducible credential-free retrieval benchmark for portfolio evidence."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import app
from storage import PgVectorStore, VectorRecord

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "benchmarks" / "docs"
CASES = ROOT / "benchmarks" / "eval_cases.json"


def deterministic_embedding(text: str) -> list[float]:
    """Two-dimensional deterministic vector used only to verify pgvector plumbing."""
    lowered = text.lower()
    groups = (
        ("retrieval", "ground", "hallucination", "source", "cite"),
        ("hnsw", "vector", "nearest", "cosine", "embedding"),
        ("health", "readiness", "monitor", "latency", "production api"),
        ("api key", "credential", "secret", "environment", "rotation"),
    )
    scores = [sum(term in lowered for term in group) for group in groups]
    index = max(range(len(scores)), key=scores.__getitem__) if any(scores) else 0
    return ([1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0])[index]


def evaluate_ranking(ranked_sources: list[str], relevant: str, k: int = 3) -> tuple[float, float]:
    names = [Path(source).name for source in ranked_sources]
    recall = 1.0 if relevant in names[:k] else 0.0
    try:
        rank = names.index(relevant) + 1
    except ValueError:
        return recall, 0.0
    return recall, 1.0 / rank


def run_tfidf(corpus: list[object], cases: list[dict[str, str]]) -> dict[str, float]:
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    for case in cases:
        start = time.perf_counter()
        results = app.search(corpus, case["query"], 3)
        latencies_ms.append((time.perf_counter() - start) * 1000)
        sources = [str(chunk.source) for _score, chunk in results]
        recall, rr = evaluate_ranking(sources, case["relevant_source"])
        recalls.append(recall)
        reciprocal_ranks.append(rr)
    return {
        "recall_at_3": sum(recalls) / len(recalls),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "median_latency_ms": statistics.median(latencies_ms),
    }


def run_pgvector(corpus: list[object], cases: list[dict[str, str]], dsn: str) -> dict[str, float]:
    store = PgVectorStore(dsn, dimensions=2)
    store.ensure_schema()
    store.upsert(
        VectorRecord(Path(chunk.source).name, index, chunk.text, deterministic_embedding(chunk.text))
        for index, chunk in enumerate(corpus)
    )
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    for case in cases:
        start = time.perf_counter()
        results = store.search(deterministic_embedding(case["query"]), top_k=3)
        latencies_ms.append((time.perf_counter() - start) * 1000)
        recall, rr = evaluate_ranking(
            [str(result["source"]) for result in results], case["relevant_source"]
        )
        recalls.append(recall)
        reciprocal_ranks.append(rr)
    return {
        "recall_at_3": sum(recalls) / len(recalls),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "median_latency_ms": statistics.median(latencies_ms),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default="")
    parser.add_argument("--output", default="benchmark-results.json")
    args = parser.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    corpus = app.load_corpus(DOCS)
    results: dict[str, object] = {
        "dataset": "benchmarks/eval_cases.json",
        "cases": len(cases),
        "notes": "pgvector uses deterministic local feature vectors to verify retrieval plumbing; it is not a live embedding-model quality benchmark.",
        "tfidf": run_tfidf(corpus, cases),
    }
    if args.database_url:
        results["pgvector_pipeline"] = run_pgvector(corpus, cases, args.database_url)

    Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
