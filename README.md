# RAG Knowledge Assistant

[![CI](https://github.com/mirrazaabbas/rag-knowledge-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/mirrazaabbas/rag-knowledge-assistant/actions/workflows/ci.yml)

A source-grounded RAG portfolio project with a transparent local retrieval baseline, a FastAPI service, a built-in web interface, and optional OpenAI-compatible semantic retrieval and cited answer generation.

## Application Preview

![RAG Knowledge Assistant web interface](docs/images/rag-knowledge-assistant.png)

The browser interface provides a polished entry point to local TF-IDF retrieval, semantic retrieval, cited answer generation, API documentation, and the interactive knowledge workbench.

## What it demonstrates

The project keeps a fully local TF-IDF retrieval path for explainability while adding a provider boundary for embeddings and chat generation. This makes the baseline usable without credentials and lets semantic/LLM behavior be enabled without hard-coding secrets or coupling the application to one provider implementation.

## Current architecture

```text
Local documents
      ↓
Overlapping chunks
      ├──────────────→ TF-IDF + cosine → /search
      │
      └→ Embeddings provider → dense cosine → /semantic-search
                                      ↓
                              grounded passages
                                      ↓
                                  chat model
                                      ↓
                              cited answer → /answer
```

A lightweight browser UI at `/` can call all three modes. See [ARCHITECTURE.md](ARCHITECTURE.md) for design details and remaining production milestones.

## Implemented features

- Recursive `.md` / `.txt` document ingestion
- Overlapping chunk generation
- TF-IDF weighting implemented from scratch
- Cosine-similarity baseline retrieval
- Source attribution and top-k ranking
- FastAPI REST API with Pydantic validation
- `GET /health`
- `POST /search` — local TF-IDF retrieval, no API key required
- `POST /semantic-search` — OpenAI-compatible embedding retrieval
- `POST /answer` — semantic retrieval plus source-grounded cited answer generation
- Built-in browser UI served from `/`
- OpenAI-compatible provider adapter with configurable base URL/models/timeouts
- Safe 503 behavior when semantic provider credentials are unavailable
- Docker packaging
- Automated compile, lint, coverage, API, provider, and CLI checks
- CI across Python 3.10, 3.11, and 3.12

## Run locally

Install dependencies and start the API:

```bash
python -m pip install -r requirements.txt
uvicorn api:app --reload
```

Open:

- Web UI: `http://127.0.0.1:8000/`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

The local retrieval endpoint works immediately:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"How can AI agents reduce unsupported claims?","top_k":3}'
```

The original CLI also remains available:

```bash
python app.py "How can an AI assistant reduce hallucinations?" --docs sample_docs --top-k 3
```

## Enable semantic retrieval and cited answers

Copy the environment template and set credentials in your local environment. Never commit a real API key.

```bash
cp .env.example .env
```

Supported variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `EMBEDDING_MODEL`
- `CHAT_MODEL`
- `PROVIDER_TIMEOUT_SECONDS`

The provider is OpenAI-compatible, so a compatible endpoint can be selected through configuration rather than code changes.

## Docker

```bash
docker build -t rag-knowledge-assistant .
docker run --rm -p 8000:8000 rag-knowledge-assistant
```

Pass provider environment variables to the container only when using semantic or answer modes.

## Quality checks

```bash
python -m pip install -r requirements-dev.txt
ruff check .
coverage run -m unittest discover -s tests -v
coverage report --fail-under=80
```

Tests use deterministic fake providers and mocked HTTP transport, so CI verifies semantic ranking, answer orchestration, provider error handling, and API behavior without storing external secrets.

## Remaining production milestones

- Persistent vector storage such as pgvector or Qdrant
- Document/PDF upload with file-type and size validation
- Hybrid sparse+dense retrieval and reranking
- Retrieval benchmark metrics such as recall@k / MRR / nDCG
- Prompt-injection and adversarial-document evaluation
- Structured tracing, token/cost metrics, and request correlation IDs
- Authentication/rate limiting for a public service
- Cloud deployment and a public live-demo URL

## Security model

Retrieved documents are untrusted data, not system instructions. Provider credentials are read from environment variables, provider failures are converted to controlled service errors, and the repository contains no required secret for its local retrieval mode. See [SECURITY.md](SECURITY.md).

## Skills demonstrated

Python · FastAPI · Pydantic · RAG · Information Retrieval · Embeddings · LLM Integration · REST APIs · Source Grounding · Docker · Testing · CI/CD

## Scope and accuracy

The repository implements an **optional real provider integration path**, but it does not claim a hosted production deployment, persistent vector database, or measured real-provider benchmark until those are configured and evaluated. The credential-free TF-IDF mode remains the reproducible baseline.
