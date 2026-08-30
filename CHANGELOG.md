# Changelog

All notable changes to this project are documented here. Tagged releases follow semantic versioning.

## 1.0.0 - 2026-08-30

### Added
- Installable `rag-knowledge-assistant` package metadata and `rag-search` / `rag-benchmark` CLI entry points.
- FastAPI retrieval API, transparent TF-IDF baseline and PostgreSQL/pgvector semantic retrieval path.
- Source-grounded cited answer generation and prompt-injection boundaries.
- OpenTelemetry/OTLP tracing verified against Jaeger in CI.
- Production Docker build and runtime smoke tests.
- Reproducible retrieval benchmark artifacts.
- Versioned `portfolio-evidence/v1` integration contract and machine-readable JSON Schema.
- Cross-project compatibility with Agent Workflow Engine and AI Evaluation Harness.
- CodeQL, dependency auditing, CycloneDX SBOM generation and container scanning.
- Tagged release workflow with build provenance attestation.

### Scope
Commercial provider calls and a permanently hosted backend remain opt-in operational extensions. The repository does not claim those external services are continuously available without a configured deployment and credentials.
