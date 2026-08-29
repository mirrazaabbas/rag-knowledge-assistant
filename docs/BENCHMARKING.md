# RAG Benchmark Plan

A strong portfolio claim should be backed by measured results, not estimates. This project therefore separates the benchmark *method* from benchmark *results*.

## Retrieval metrics

For a labeled question set, record:

- recall@k: whether a relevant chunk appears in the top-k results
- mean reciprocal rank (MRR): how highly the first relevant chunk is ranked
- citation coverage: whether answer claims have retrieved supporting passages
- groundedness: whether generated statements are supported by retrieved context

## Operational metrics

Record at least:

- end-to-end latency
- retrieval latency
- provider latency
- input/output token usage when available
- estimated provider cost when pricing is known
- error and timeout rates

## Comparison matrix

Compare the transparent TF-IDF baseline against the pgvector semantic path on the same labeled cases.

| Metric | TF-IDF baseline | pgvector semantic |
|---|---:|---:|
| Recall@3 | Not measured yet | Not measured yet |
| MRR | Not measured yet | Not measured yet |
| Median latency | Not measured yet | Not measured yet |
| Citation coverage | Not measured yet | Not measured yet |

Do not replace `Not measured yet` with numbers until the benchmark has actually been executed in a reproducible environment.

## Reproducibility rules

1. Pin the corpus and labeled question set.
2. Record model/provider names and embedding dimensions.
3. Run both retrieval paths against the same cases.
4. Save raw results before summarizing averages.
5. Report failures and timeouts rather than silently dropping them.
6. Keep credential-free CI tests separate from paid live-provider benchmarks.
