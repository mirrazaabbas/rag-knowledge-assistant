# Deployment Guide

This project keeps a credential-free local TF-IDF baseline and includes verified PostgreSQL/pgvector retrieval plus an OpenTelemetry OTLP tracing path.

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
- PostgreSQL 16 + pgvector on port `5432`
- Jaeger on port `16686` for trace inspection
- Jaeger OTLP/HTTP ingestion on port `4318`

The app exports FastAPI spans to `http://jaeger:4318/v1/traces`. Jaeger's bundled all-in-one setup uses transient in-memory trace storage and is intended for development/demo verification rather than durable production retention.

## Render deployment blueprint

The repository includes `render.yaml`, which defines:

- a Docker-based FastAPI web service using `Dockerfile.production`
- a managed PostgreSQL 16 database
- private database connection injection through `DATABASE_URL`
- `/health` as the service health-check path
- `VECTOR_DIMENSIONS=1536` for the default embedding model
- an environment-managed provider secret for semantic retrieval and cited answers

The production Docker image binds to `0.0.0.0` and honors the platform-provided `PORT` environment variable, with local fallback to port `8000`.

To deploy from the Render dashboard, create a new Blueprint from this GitHub repository. Render reads `render.yaml`, creates the web service and database, and injects the database connection string. `OPENAI_API_KEY` is configured as a secret prompt and must never be committed to the repository.

The application runs `CREATE EXTENSION IF NOT EXISTS vector` during pgvector schema initialization, so the selected managed database must support the vector extension.

### Free-tier accuracy boundary

The Blueprint uses free service and database plans as a portfolio-demo starting point. Free infrastructure has tighter limits and should not be described as a production SLA. For a durable deployment, use an appropriate database plan and configure backups/retention for the use case.

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string for pgvector retrieval |
| `VECTOR_DIMENSIONS` | Expected embedding dimensions |
| `OPENAI_API_KEY` | OpenAI-compatible provider key for semantic retrieval / answers |
| `OPENAI_BASE_URL` | OpenAI-compatible API base URL |
| `EMBEDDING_MODEL` | Embedding model name |
| `CHAT_MODEL` | Chat model name |
| `PROVIDER_TIMEOUT_SECONDS` | Provider request timeout |
| `PORT` | HTTP port supplied by the deployment platform |
| `OTEL_ENABLED` | Enable OpenTelemetry FastAPI instrumentation |
| `OTEL_SERVICE_NAME` | Service name emitted in traces |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | OTLP/HTTP trace receiver such as `http://collector:4318/v1/traces` |

If `OTEL_ENABLED=true` and no OTLP traces endpoint is configured, the application falls back to the console span exporter.

## Verification after deployment

A deployment is not considered verified until all of these succeed:

```text
GET  /health      -> 200 {"status":"ok"}
GET  /readiness   -> 200 and vector_store="configured"
POST /search      -> 200 with grounded local passages
POST /semantic-search -> 200 when provider credentials are configured
POST /answer      -> 200 with cited answer when provider credentials are configured
```

When external tracing is enabled, also verify that the configured backend receives spans under the expected service name.

Also verify HTTPS, application logs, database connectivity, and a clean restart/redeploy.

## Production checklist

1. Use managed PostgreSQL with pgvector enabled.
2. Store credentials in the platform secret manager.
3. Run CI and the retrieval benchmark before release.
4. Configure HTTPS, request limits, timeouts, and logging retention.
5. Point `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` at a secured, durable collector/backend when production trace retention is required.
6. Use `/health` and `/readiness` for platform checks.
7. Add provider budget/rate-limit controls before high-volume public use.
8. Run prompt-injection tests before accepting arbitrary user-uploaded documents.
9. Use a durable database plan with backups before relying on stored data.

## Accuracy boundary

Infrastructure-as-code is committed, the production container is tested in CI, the pgvector path is verified in GitHub Actions, and the repository includes a real OTLP-to-Jaeger integration test. A public live-demo URL is only added to the README after the external cloud deployment itself has been created and checked.
