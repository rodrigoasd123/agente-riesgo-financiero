# Acceptance — Graduated RAG and embedding cache

## Scenarios

- **AC-001 — Structured first:** Given an explicit ROA/ROE question, when retrieval runs, then it selects structured evidence with no embedding call.
- **AC-002 — Lexical second:** Given a PDF fact with sufficient keyword coverage, when retrieval runs, then it selects PDF evidence with no embedding call and preserves the PDF citation.
- **AC-003 — Cached semantic:** Given no sufficient literal match and a valid cache, when retrieval runs, then only the query is embedded and semantic evidence is selected.
- **AC-004 — Safe fallback:** Given unavailable embeddings or insufficient similarity, when retrieval runs, then the graph returns clarification without fabricated evidence.
- **AC-005 — Compatible persistence:** Given an existing pre-migration analysis, when the database initializes and a semantic cache is produced, then the row remains readable and only its owner can persist the cache.
- **AC-006 — Observable and private:** Given any retrieval route, when the run is traced, then route/confidence/count/cache flag are recorded and no content or embedding value is logged.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | `test_structured_route_precedes_embeddings`; live ROA/ROE smoke | PASS |
| AC-002 | `test_literal_route_precedes_embeddings_and_preserves_pdf`; API E2E | PASS |
| AC-003 | Cache unit tests plus `test_chat_semantico_crea_y_reutiliza_cache` | PASS |
| AC-004 | Embedding failure and low-similarity tests; API missing-evidence E2E | PASS |
| AC-005 | Legacy migration, precompute persistence and owner-scoped update tests | PASS |
| AC-006 | Retrieval tracing allowlist tests and live MLflow run | PASS |

## Verification evidence

- Focused suite: `22 passed` before the final precompute integration case.
- Complete suite: `.\.venv\Scripts\python.exe -m pytest tests -q` → `80 passed, 1 dependency warning`.
- Compile check: `.\.venv\Scripts\python.exe -m compileall -q backend frontend tests` → pass.
- Live application: API `1.6.0`, migration column present, frontend/backend healthy.
- Live chat: route `estructurada`, confidence `1.0`, two grounded fragments.
- Live MLflow: finished run with route, confidence, result count and cache flag.
- Release: commit `0d38bd4` synchronized to private `origin/master`.
