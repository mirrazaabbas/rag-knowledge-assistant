# Architecture — RAG Knowledge Assistant

## Credential-free baseline

```text
Local .md/.txt documents
        ↓
Document discovery
        ↓
Overlapping chunking
        ↓
Tokenization
        ↓
TF-IDF weighting
        ↓
Cosine-similarity ranking
        ↓
Top-k grounded passages + source paths
        ↓
FastAPI / CLI / browser UI
```

This path remains intentionally simple and reproducible. It does not require an API key or database.

## Semantic answer path

```text
Client / browser UI
        ↓
FastAPI
        ↓
Local document chunks
        ↓
OpenAI-compatible embeddings provider
        ↓
Dense similarity ranking
        ↓
Top-k grounded passages
        ↓
Prompt builder + untrusted-context boundary
        ↓
Chat model
        ↓
Cited answer
```

## Production vector-storage path

```text
Documents
   ↓
Chunking
   ↓
Embedding model
   ↓
PostgreSQL + pgvector
   ├─ persistent chunk metadata
   ├─ vector column
   └─ HNSW cosine index
   ↓
Nearest-neighbor retrieval
   ↓
Grounded answer pipeline
```

`storage.PgVectorStore` owns the database schema, upsert validation, and cosine vector search. `docker-compose.yml` provides a local PostgreSQL 16 + pgvector environment. The database path is optional so the transparent TF-IDF baseline stays easy to run.

## Runtime and observability

```text
Browser / API client
        ↓
FastAPI
   ├─ /health
   ├─ /readiness
   ├─ /search
   ├─ /semantic-search
   └─ /answer
        ↓
Optional OpenTelemetry instrumentation
        ↓
Console exporter locally / collector in a real deployment
```

Observability is disabled by default and enabled with `OTEL_ENABLED=true`. A production deployment should export traces to a real collector/backend rather than relying on the console exporter.

## Design goals

- Keep retrieval logic understandable end-to-end.
- Make every returned passage traceable to a source.
- Separate retrieval from generation so either layer can be evaluated independently.
- Preserve a credential-free baseline for CI and portfolio reproducibility.
- Make production capabilities optional instead of forcing cloud/database dependencies on local users.
- Fail clearly on missing documents, empty queries, invalid settings, and vector-dimension mismatches.

## Security considerations

Retrieved documents are data, not trusted instructions. Production deployments should isolate system instructions from retrieved content, validate uploads, restrict file types and sizes, avoid logging sensitive text, use secret management, enforce request/rate limits, and evaluate prompt-injection cases.

## Evaluation targets

- retrieval recall@k
- mean reciprocal rank (MRR)
- citation coverage and correctness
- groundedness
- answer relevance
- retrieval and end-to-end latency
- token / provider cost usage
- error and timeout rates

See `docs/BENCHMARKING.md` for the measurement plan. No benchmark numbers are claimed until they are actually measured.
