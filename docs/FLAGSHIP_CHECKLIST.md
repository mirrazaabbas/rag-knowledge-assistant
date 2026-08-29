# Flagship Verification Status

The portfolio scope is complete. This file records what has actually been verified rather than listing optional product extensions as unfinished work.

## Verified

- [x] Local TF-IDF search passes
- [x] Full automated test suite passes
- [x] Ruff passes
- [x] Production dependencies install successfully
- [x] Production Docker image builds and passes health/readiness smoke tests
- [x] pgvector schema creation succeeds against PostgreSQL 16 in GitHub Actions
- [x] Vector upsert/search integration tests pass against real PostgreSQL/pgvector
- [x] `/semantic-search` routes through pgvector when `DATABASE_URL` is configured
- [x] Benchmark cases execute and raw results are saved as a workflow artifact
- [x] Measured Recall@3, MRR and retrieval latency are documented with accuracy boundaries
- [x] OpenTelemetry spans export over OTLP/HTTP to a real Jaeger service in CI
- [x] Deterministic prompt-injection boundary tests pass
- [x] Architecture diagram, deployment guide and recruiter demo walkthrough are present
- [x] Credential-free browser demo source is included under `live-demo/`

## Intentionally outside the completed portfolio scope

The following are optional deployment/product extensions, not outstanding requirements:

- A billable commercial embedding/chat-provider verification run
- A permanently hosted full FastAPI + PostgreSQL/pgvector service
- Durable managed tracing retention
- Public document/PDF upload and write endpoints
- Hybrid reranking beyond the current verified retrieval paths

Because the completed demo surface does not expose write/upload functionality, public-write authentication and rate limiting are not applicable to the current portfolio scope.

Only capabilities explicitly verified above should be presented as completed engineering evidence.
