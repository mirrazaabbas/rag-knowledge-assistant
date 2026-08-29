"""Local retrieval layer for a RAG-style knowledge assistant.

Indexes .txt/.md files, ranks chunks with TF-IDF cosine similarity, and returns
source-grounded passages. Uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-Z0-9_'-]+")
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOCS = BASE_DIR / "sample_docs"


@dataclass(frozen=True)
class Chunk:
    source: str
    text: str
    tf: Counter[str]


def tokens(text: str) -> list[str]:
    """Normalize text into searchable terms."""
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 2]


def chunk_text(text: str, size: int = 120, overlap: int = 25) -> list[str]:
    """Split text into overlapping word chunks."""
    if size <= 0:
        raise ValueError("Chunk size must be greater than zero.")
    if overlap < 0 or overlap >= size:
        raise ValueError("Overlap must be >= 0 and smaller than chunk size.")

    words = text.split()
    if not words:
        return []
    step = size - overlap
    return [" ".join(words[i : i + size]) for i in range(0, len(words), step)]


def _document_paths(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        raise FileNotFoundError(f"Document folder does not exist: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Document path is not a folder: {folder}")
    return (
        path
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}
    )


def load_corpus(folder: Path) -> list[Chunk]:
    """Load supported documents and turn them into searchable chunks."""
    chunks: list[Chunk] = []
    for path in _document_paths(folder):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Document is not valid UTF-8: {path}") from exc
        for part in chunk_text(text):
            chunks.append(Chunk(str(path), part, Counter(tokens(part))))
    return chunks


def idf(chunks: list[Chunk]) -> dict[str, float]:
    """Calculate inverse document frequency for corpus terms."""
    if not chunks:
        return {}
    n = len(chunks)
    df = Counter(term for chunk in chunks for term in chunk.tf)
    return {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in df.items()}


def vector(tf: Counter[str], weights: dict[str, float]) -> dict[str, float]:
    total = sum(tf.values())
    if total <= 0:
        return {}
    return {
        term: (count / total) * weights[term]
        for term, count in tf.items()
        if term in weights
    }


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(value * b.get(term, 0.0) for term, value in a.items())
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def search(chunks: list[Chunk], query: str, k: int = 3) -> list[tuple[float, Chunk]]:
    """Return the top-k chunks ranked by cosine similarity."""
    if not chunks:
        return []
    if k <= 0:
        raise ValueError("top-k must be greater than zero.")
    query_terms = tokens(query)
    if not query_terms:
        raise ValueError("Query must contain at least one searchable word.")

    weights = idf(chunks)
    query_vector = vector(Counter(query_terms), weights)
    ranked = [
        (cosine(query_vector, vector(chunk.tf, weights)), chunk)
        for chunk in chunks
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[: min(k, len(ranked))]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search a local knowledge base with TF-IDF retrieval."
    )
    parser.add_argument("query", help="Question or search query")
    parser.add_argument(
        "--docs",
        type=Path,
        default=DEFAULT_DOCS,
        help=f"Folder containing .txt/.md files (default: {DEFAULT_DOCS})",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of passages to return")
    args = parser.parse_args()

    try:
        corpus = load_corpus(args.docs)
        if not corpus:
            raise ValueError(f"No .txt or .md documents found in: {args.docs}")
        results = search(corpus, args.query, args.top_k)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Indexed {len(corpus)} chunks from {args.docs}.\n")
    for rank, (score, chunk) in enumerate(results, 1):
        print(f"[{rank}] score={score:.3f} source={chunk.source}")
        print(chunk.text[:700], "\n")


if __name__ == "__main__":
    main()
