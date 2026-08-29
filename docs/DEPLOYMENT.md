# Deployment Guide

This project keeps a credential-free local TF-IDF baseline and adds an optional production path for persistent vector retrieval and tracing.

## Local baseline

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8000
```

No API key or database is required for `POST /search`.

## Production-oriented local stack

```bash
docker compose up --build
```

This starts:

- FastAPI on port `8000`
- PostgreSQL 16 with the pgvector extension on port `5432`
- persistent database storage in the `rag_pgdata` Docker volume

The Compose credentials are intentionally development-only. Use managed secrets and a rotated database password in a real deployment.

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string for pgvector storage |
| `OPENAI_API_KEY` | OpenAI-compatible provider key for semantic retrieval / answer generation |
| `OPENAI_BASE_URL` | OpenAI-compatible API base URL |
| `EMBEDDING_MODEL` | Embedding model name |
| `CHAT_MODEL` | Chat model name |
| `PROVIDER_TIMEOUT_SECONDS` | Provider request timeout |
| `OTEL_ENABLED` | Enable OpenTelemetry FastAPI instrumentation |
| `OTEL_SERVICE_NAME` | Service name emitted in traces |

## Cloud deployment checklist

Before calling a deployment production-ready:

1. Use a managed PostgreSQL service with pgvector enabled.
2. Store credentials in the platform's secret manager; never commit `.env` files.
3. Run the automated test suite and retrieval benchmark.
4. Configure HTTPS, request limits, timeouts, and logging retention.
5. Export OpenTelemetry spans to a real collector/backend rather than the console exporter.
6. Set up health/readiness checks against `/health` and `/readiness`.
7. Add provider budget/rate-limit controls and alerting.
8. Run prompt-injection and untrusted-document tests before accepting arbitrary uploads.

## Current status

The repository contains deployment-ready building blocks, but no public cloud URL is claimed here until a real deployment is created and verified.
