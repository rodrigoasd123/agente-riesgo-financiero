# Implementation plan — Graduated RAG and embedding cache

## Approach

Keep one bounded LangGraph retrieval node, but make its deterministic internal stages explicit and observable. Split PDF chunks from structured fragments. Precompute PDF embeddings best-effort during analysis; validate and reuse them in semantic search; lazily persist a replacement cache for old or mismatched rows.

## Components and ownership

| Component | Change |
|---|---|
| `backend/agent/qa.py` | Graduated routing, confidence, cache validation and semantic similarity |
| `backend/agent/financial_context.py` | Indicator aliases and structured-only fragments |
| `backend/db/database.py` | Additive `embeddings_json` column and owner-scoped cache update |
| Analyze/chat routes | Create, load, and lazily persist cache; return retrieval metadata |
| LangGraph state/node | Carry separate sources, cache and retrieval result metadata |
| MLflow tracing | Log allowlisted route and numeric metadata only |
| Streamlit | Display route and confidence beneath each response |

## Data and control flow

```text
question -> explicit indicator match -> sufficient? -> answer
         -> PDF lexical match       -> sufficient? -> answer
         -> cached semantic search  -> sufficient? -> answer
         -> clarification
```

On analysis, PDF chunks are embedded best-effort. On chat, cached vectors are accepted only if their count matches the document chunks and all vectors are non-empty. A regenerated cache is persisted using `(analysis_id, owner)`.

## Data model and API changes

- Expand: `analyses.embeddings_json TEXT NOT NULL DEFAULT '[]'`.
- Existing rows remain readable and trigger lazy best-effort cache generation.
- Chat response adds `retrieval_route` and `retrieval_confidence`; existing fields are unchanged.
- Rollback code can ignore the additive column; no destructive contraction is required.

## Security and privacy

- All cache access follows the existing owner-filtered analysis lookup/update.
- Only allowlisted route names, counts, cache flag, and confidence are traced.
- Questions, chunks, embeddings and financial values are not sent to MLflow.

## Observability and failure handling

- MLflow: route, confidence, selected chunk count, cache hit.
- Gemini embedding failure returns no semantic evidence and proceeds to clarification.
- Cache persistence failure does not change the answer already produced.

## Verification strategy

- Unit: stage order, zero-call structured/lexical paths, cache reuse, fallback and no-result.
- Database integration: additive migration, old row readability, owner-scoped cache write.
- API integration: response metadata, citations, old-analysis lazy upgrade and isolation.
- Regression: complete suite.
