# Architecture — RAG Knowledge Assistant

## Current pipeline

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
FastAPI / CLI
```

## Design goals

- Keep retrieval logic understandable end-to-end.
- Make every returned passage traceable to a source.
- Separate retrieval from generation so either layer can be evaluated independently.
- Fail clearly on missing documents, empty queries, and invalid settings.

## Production target

```text
Client/UI
   ↓
FastAPI service
   ↓
Document ingestion ──→ metadata store
   ↓
Chunking
   ↓
Embedding model
   ↓
Vector database
   ↓
Retriever → optional reranker
   ↓
Prompt builder + untrusted-context boundary
   ↓
LLM
   ↓
Answer + citations + retrieval metadata
   ↓
Evaluation / tracing / cost metrics
```

## Security considerations

Retrieved documents are data, not trusted instructions. A production version should isolate system instructions from retrieved content, validate uploads, restrict file types and sizes, avoid logging sensitive text, and evaluate prompt-injection cases.

## Evaluation targets

- retrieval hit rate / recall@k
- citation correctness
- groundedness
- answer relevance
- latency
- token / cost usage
