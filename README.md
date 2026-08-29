# RAG Knowledge Assistant

[![CI](https://github.com/mirrazaabbas/rag-knowledge-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/mirrazaabbas/rag-knowledge-assistant/actions/workflows/ci.yml)

A source-grounded Retrieval-Augmented Generation portfolio project with a transparent retrieval core and a production-style FastAPI interface. The project indexes local Markdown/text documents, creates overlapping chunks, calculates TF-IDF weights, ranks passages with cosine similarity, and exposes results with source attribution through both CLI and HTTP APIs.

## Why this project matters

Reliable AI assistants need a retrieval layer that can bring relevant evidence into model context while preserving traceability. This implementation keeps retrieval understandable from first principles and provides clean extension points for embeddings, vector databases, reranking, and LLM answer synthesis.

## Architecture

`Documents → Chunking → Tokenization → TF-IDF Index → Query Vector → Cosine Ranking → Grounded Passages → API`

See [ARCHITECTURE.md](ARCHITECTURE.md) for the current and production-target designs.

## Features

- Recursive `.md` / `.txt` document ingestion
- Overlapping chunk generation
- TF-IDF weighting implemented from scratch
- Cosine-similarity ranking
- Top-k source attribution
- Input validation and clear retrieval errors
- FastAPI `/health` and `/search` endpoints
- Pydantic request/response schemas
- Interactive OpenAPI documentation
- Dockerized API runtime
- Automated linting, tests, coverage gate, and API smoke tests
- Dependency-free retrieval core
- Environment template for future LLM/vector integrations

## Run the retrieval CLI

```bash
python app.py "How can an AI assistant reduce hallucinations?" --docs sample_docs --top-k 3
```

## Run the API

```bash
python -m pip install -r requirements.txt
uvicorn api:app --reload
```

Open the generated API docs at `http://127.0.0.1:8000/docs`.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"How can AI agents reduce unsupported claims?","top_k":3}'
```

## Run with Docker

```bash
docker build -t rag-knowledge-assistant .
docker run --rm -p 8000:8000 rag-knowledge-assistant
```

## API contract

### `GET /health`
Returns a simple service health response.

### `POST /search`
Accepts a query and `top_k`, retrieves the strongest matching passages, and returns rank, similarity score, source path, and source text.

## Quality checks

```bash
python -m pip install -r requirements-dev.txt
ruff check .
coverage run -m unittest discover -s tests -v
coverage report --fail-under=80
```

GitHub Actions runs these checks on Python 3.10, 3.11, and 3.12.

## Engineering roadmap

1. Add embedding-model adapters.
2. Add persistent vector storage.
3. Add reranking and retrieval evaluation.
4. Add LLM answer synthesis with inline citations.
5. Add prompt-injection and unsafe-document defenses.
6. Add PDF/document upload with size/type validation.
7. Add tracing, latency, token, and cost metrics.
8. Add a lightweight web UI and deploy a live demo.

## Security model

Retrieved documents must be treated as untrusted data, not as system instructions. A production deployment should validate uploads, isolate trusted prompts from retrieved text, limit document size/type, avoid logging sensitive content, and test prompt-injection scenarios.

## Skills demonstrated

Python · FastAPI · Pydantic · Information Retrieval · RAG · NLP · TF-IDF · Cosine Similarity · REST APIs · Docker · Testing · CI/CD · AI Architecture

## Current scope

The project currently performs retrieval and source attribution. It does **not** claim to provide a production LLM, embedding model, or vector database yet; those integrations are intentionally represented as the next engineering milestones rather than simulated functionality.
