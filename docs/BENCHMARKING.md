# RAG Benchmarking

This project separates measured evidence from unverified claims. Retrieval metrics are generated in GitHub Actions against a pinned four-question benchmark corpus.

## Latest verified CI sample

GitHub Actions run `#52` executed the benchmark against the real PostgreSQL/pgvector service used by CI.

| Metric | TF-IDF baseline | pgvector pipeline |
|---|---:|---:|
| Recall@3 | 1.00 | 1.00 |
| MRR | 0.875 | 1.00 |
| Median retrieval latency | 0.076 ms | 11.834 ms |

These latency values are a single GitHub-hosted CI sample and are environment-dependent. They should not be treated as production latency guarantees.

## What the pgvector benchmark proves

The pgvector path uses a real PostgreSQL 16 server with the `vector` extension, persistent vector rows, cosine-distance search, and the same `PgVectorStore` implementation used by the application.

The benchmark deliberately uses deterministic local two-dimensional feature vectors. This makes the database/retrieval pipeline reproducible without storing third-party API credentials in CI.

**Therefore the pgvector figures verify retrieval plumbing and ranking behavior, not the quality of a commercial embedding model.** A live-provider benchmark remains a separate future measurement.

## Retrieval metrics

- **Recall@3** — whether the labeled relevant document appears in the first three results.
- **MRR** — mean reciprocal rank of the first labeled relevant result.
- **Median retrieval latency** — median measured retrieval duration for the four benchmark cases in that CI run.

## Reproduce locally

Run the credential-free TF-IDF benchmark:

```bash
python benchmark.py --output benchmark-results.json
```

Run both paths against PostgreSQL/pgvector:

```bash
python benchmark.py \
  --database-url postgresql://rag:rag@localhost:5432/rag \
  --output benchmark-results.json
```

GitHub Actions also uploads `benchmark-results.json` as the `retrieval-benchmark-results` workflow artifact so the raw output is preserved alongside the CI run.

## Future live-provider metrics

When an external embedding/chat provider is deliberately tested, add a separate result set covering:

- provider/model names and embedding dimensions
- Recall@k and MRR on a larger labeled corpus
- citation coverage and groundedness
- end-to-end, retrieval, and provider latency
- token usage and estimated cost where available
- errors and timeouts

No live-provider numbers should be published until that run is actually performed and recorded.
