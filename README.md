# RAG Knowledge Assistant

[![CI](https://github.com/mirrazaabbas/rag-knowledge-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/mirrazaabbas/rag-knowledge-assistant/actions/workflows/ci.yml)

A source-grounded RAG portfolio project with a transparent local retrieval baseline, FastAPI, a built-in web interface, optional semantic answer generation, and production-oriented PostgreSQL/pgvector and observability building blocks.

## Application Preview

![RAG Knowledge Assistant web interface](docs/images/rag-knowledge-assistant.png)

The browser interface provides a polished entry point to local TF-IDF retrieval, semantic retrieval, cited answer generation, API documentation, and the interactive knowledge workbench.

## What it demonstrates

This project deliberately keeps two layers:

1. a credential-free TF-IDF baseline that is easy to understand, reproduce, test, and inspect;
2. an optional production-oriented path with semantic providers, PostgreSQL/pgvector persistence, HNSW vector indexing, Docker Compose, readiness reporting, and OpenTelemetry-compatible tracing.

That separation makes the retrieval logic explainable while showing how the same application can grow toward a deployable RAG architecture without inventing cloud or benchmark claims.

## Architecture

```text
                         ┌──────────────────────────────┐
Local documents ──→ chunks ──→ TF-IDF + cosine ──────→ /search
                         │
                         ├─→ embeddings provider ──────→ /semantic-search
                         │                │
                         │                └─→ grounded context ─→ chat model ─→ /answer
                         │
                         └─→ optional PostgreSQL + pgvector
                                  ├─ persistent chunks
                                  ├─ vector column
                                  └─ HNSW cosine index

Browser / API client ──→ FastAPI ──→ health + readiness + optional OpenTelemetry
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the detailed design.

## Implemented features

- Recursive `.md` / `.txt` document ingestion
- Overlapping chunk generation
- TF-IDF weighting implemented from scratch
- Cosine-similarity baseline retrieval
- Source attribution and top-k ranking
- FastAPI REST API with Pydantic validation
- `GET /health`
- `GET /readiness` — reports optional production configuration without exposing secrets
- `POST /search` — local TF-IDF retrieval, no API key required
- `POST /semantic-search` — OpenAI-compatible embedding retrieval
- `POST /answer` — semantic retrieval plus source-grounded cited answer generation
- Built-in browser UI served from `/`
- Provider-neutral AI helper layer plus OpenAI-compatible retrieval adapter
- PostgreSQL/pgvector storage module with validated vector dimensions
- HNSW cosine index schema for persistent vector retrieval
- Docker Compose stack for FastAPI + PostgreSQL/pgvector
- Optional OpenTelemetry FastAPI instrumentation
- Deployment and benchmark documentation
- Safe 503 behavior when semantic provider credentials are unavailable
- Automated compile, lint, coverage, API, provider, CLI, and storage validation checks
- CI across Python 3.10, 3.11, and 3.12

## Run the credential-free baseline

```bash
python -m pip install -r requirements.txt
uvicorn api:app --reload
```

Open:

- Web UI: `http://127.0.0.1:8000/`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Readiness: `http://127.0.0.1:8000/readiness`

The local retrieval endpoint works without an API key or database:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"How can AI agents reduce unsupported claims?","top_k":3}'
```

The CLI remains available:

```bash
python app.py "How can an AI assistant reduce hallucinations?" --docs sample_docs --top-k 3
```

## Enable semantic retrieval and cited answers

Copy the environment template and set credentials in your local environment. Never commit a real API key.

```bash
cp .env.example .env
```

Provider configuration includes `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `EMBEDDING_MODEL`, `CHAT_MODEL`, and `PROVIDER_TIMEOUT_SECONDS`.

## Run the production-oriented local stack

```bash
docker compose up --build
```

This starts FastAPI and PostgreSQL 16 with pgvector. The Compose database credentials are development-only. For production setup details, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Production dependencies are separated from the lightweight baseline:

```bash
python -m pip install -r requirements-production.txt
```

The pgvector storage adapter is implemented in `storage.py`. It validates embedding dimensions, creates a persistent chunk table, creates an HNSW cosine index, supports idempotent upserts, and performs nearest-neighbor retrieval.

## Observability

Set:

```bash
OTEL_ENABLED=true
OTEL_SERVICE_NAME=rag-knowledge-assistant
```

The application then instruments FastAPI with OpenTelemetry. The included implementation uses a console span exporter as a safe local default; a real deployment should route spans to a collector/observability backend.

## Evaluation and benchmarking

The project defines a reproducible measurement plan covering recall@k, MRR, citation coverage, groundedness, latency, token usage, cost, errors, and timeouts.

See [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

**No benchmark numbers are presented as measured results until the benchmark is actually run.**

## Quality checks

```bash
python -m pip install -r requirements-dev.txt
ruff check .
coverage run -m unittest discover -s tests -v
coverage report --fail-under=80
```

Tests use deterministic fake providers and mocked HTTP transport, so CI can verify core semantic/provider behavior without storing external secrets. Storage validation tests do not require a running database.

## Security model

Retrieved documents are untrusted data, not system instructions. Provider credentials and database credentials are read from environment variables. Production guidance explicitly calls for managed secrets, request/rate limits, upload validation, prompt-injection testing, and controlled observability retention. See [SECURITY.md](SECURITY.md).

## Next verified milestones

These are intentionally listed as future work until they are completed and measured:

- wire document ingestion directly into pgvector-backed retrieval endpoints
- add validated PDF/document upload
- implement hybrid sparse+dense retrieval and optional reranking
- execute and publish reproducible retrieval benchmark results
- add adversarial/prompt-injection evaluation cases
- connect OpenTelemetry to a real collector/backend
- add authentication and rate limiting for a public service
- deploy to a real cloud environment and publish a verified live-demo URL

## Skills demonstrated

Python · FastAPI · Pydantic · RAG · Information Retrieval · Embeddings · LLM Integration · PostgreSQL · pgvector · Vector Search · HNSW · REST APIs · Source Grounding · Docker · Docker Compose · OpenTelemetry · Testing · CI/CD

## Scope and accuracy

The repository contains a real local retrieval baseline, optional provider integration, a pgvector storage implementation, a production-oriented container stack, and observability scaffolding. It **does not** claim a public cloud deployment, live external-provider verification, or measured benchmark numbers until those are actually run and verified.
