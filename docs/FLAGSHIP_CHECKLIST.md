# Flagship Verification Checklist

Use this checklist before making stronger portfolio claims.

- [ ] Local TF-IDF search passes
- [ ] Full automated test suite passes
- [ ] Ruff passes
- [ ] Production dependencies install successfully
- [ ] Docker Compose starts FastAPI + PostgreSQL/pgvector
- [ ] pgvector schema creation succeeds
- [ ] vector upsert/search integration test passes against PostgreSQL
- [ ] one real semantic provider call is verified
- [ ] benchmark cases are executed and raw results saved
- [ ] measured metrics replace `Not measured yet` in benchmark docs
- [ ] OpenTelemetry spans are exported to a real backend
- [ ] cloud deployment health/readiness checks pass
- [ ] public live-demo URL is verified
- [ ] rate limiting/authentication added before public write/upload features

The repository should only claim items that have actually been checked above.
