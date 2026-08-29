# Portfolio Completion Status

The RAG Knowledge Assistant has reached its intended portfolio scope.

## Verified in the repository

- Credential-free TF-IDF retrieval baseline
- FastAPI API and browser interface
- PostgreSQL 16 + pgvector persistence and cosine retrieval
- HNSW vector index
- Semantic retrieval routed through pgvector when `DATABASE_URL` is configured
- Cited answer generation through an OpenAI-compatible provider boundary
- Production Docker image build and health/readiness smoke test
- Python 3.10, 3.11 and 3.12 CI
- Real PostgreSQL/pgvector integration tests in GitHub Actions
- Reproducible retrieval benchmark with saved workflow artifact
- OpenTelemetry FastAPI instrumentation
- OTLP/HTTP export verified against a real Jaeger service in CI
- Deterministic prompt-injection boundary tests
- Architecture diagram, deployment guide, benchmark documentation and demo walkthrough
- Self-contained credential-free browser demo source under `live-demo/`

## Scope boundary

Commercial provider calls, a permanently hosted full FastAPI/pgvector backend, managed tracing retention, document uploads, and write-capable public endpoints are optional deployment/product extensions rather than unfinished portfolio requirements. The repository does not claim those capabilities unless they are actually configured and verified.

The public/demo retrieval surface has no write/upload functionality, so public-write authentication and rate limiting are not required for the completed portfolio scope.
