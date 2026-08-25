# Graduated RAG and embedding cache

- **ID:** SPEC-006
- **Status:** VERIFIED
- **Created:** 2026-08-25
- **Owner:** Product and engineering

## Problem

Every question currently embeds the query and every document chunk before generation. This consumes Gemini quota repeatedly and searches semantically even when deterministic indicators or literal PDF evidence already answer the question.

## Users and outcomes

- **Primary user:** authenticated financial analyst.
- **Desired outcome:** grounded answers with fewer provider calls and a visible explanation of how evidence was recovered.
- **Success signal:** structured and lexical questions use no embedding calls; semantic questions reuse cached document embeddings and expose route/confidence.

## Scope

### Included

- Graduated retrieval: calculated indicators, PDF keywords, cached semantic search, then clarification.
- Confidence and retrieval route in graph state, API response, UI, and privacy-safe MLflow metadata.
- Backward-compatible SQLite storage for document embeddings.
- Best-effort embedding creation on analysis and lazy cache creation for existing analyses.

### Excluded

- LLM query rewriting, multi-pass reflection, external/web retrieval, reranker models, and vector database services.
- Industry benchmarks or automatic financial recommendations.

## Requirements

### Functional

- **FR-001:** Explicit indicator or alert questions must search structured calculated fragments before PDF retrieval.
- **FR-002:** Other questions must search PDF keywords before semantic retrieval.
- **FR-003:** Semantic retrieval must reuse owner-scoped cached document embeddings when present and persist a lazily generated cache for older analyses.
- **FR-004:** Every chat response must expose the retrieval route and a bounded confidence score from 0 to 1.
- **FR-005:** Insufficient evidence must follow the existing LangGraph clarification branch without invoking answer generation.
- **FR-006:** MLflow must record route, confidence, result count, and cache usage without document or question content.

### Non-functional

- **NFR-001:** Structured and sufficient lexical retrieval must make zero embedding-provider calls.
- **NFR-002:** Cached semantic retrieval must make only the query embedding call, not re-embed stored chunks.
- **NFR-003:** Embedding or MLflow failure must preserve the deterministic fallback and API availability.
- **NFR-004:** Existing analyses and API clients must remain compatible.

### Security and privacy

- **SEC-001:** Embedding reads and writes must require the authenticated owner of the analysis.
- **SEC-002:** MLflow must not store questions, PDF content, calculated values, embeddings, answers, or secrets.

## Constraints and invariants

- Calculations remain deterministic and authoritative.
- Citations are always drawn from the selected evidence fragment.
- Cached embeddings correspond positionally to the stored PDF chunks.
- The migration is additive, idempotent, and defaults existing rows to an empty cache.

## Risks and failure modes

- Stale/mismatched cache: validate count and vector shape, then regenerate best-effort.
- False lexical match: require a bounded coverage threshold.
- Gemini quota unavailable: skip cache creation and retain structured/lexical/clarification behavior.
- Embeddings are derived document data: keep them in the same owner-scoped local database and deletion lifecycle as the analysis.

## Open questions

None.

## References

- `backend/agent/qa.py`
- `backend/workflow/graph.py`
- `backend/db/database.py`
