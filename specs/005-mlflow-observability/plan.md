# Implementation plan — MLflow observability completion

## Approach

Extend the existing node decorator. Capture only the mapping returned by a node, derive a bounded list/count of its keys, and log that metadata in the current parent run. Do not add nested runs or change graph state.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| `backend/observability/tracing.py` | Safe metadata helpers and complete node metrics | Backend |
| `tests/test_tracing.py` | Success, privacy, failure, and disabled/failing tracker coverage | QA |
| `README.md` and deployment guide | Local MLflow startup and interpretation | Documentation |

## Data and control flow

The API opens an `agent_run`; LangGraph calls decorated nodes; the decorator measures time, executes the node, derives input/output key metadata, and writes it to the active run. The node result is returned unchanged. Any MLflow exception is ignored.

## Data model and API changes

- Migrations: none.
- Compatibility: existing `mlflow.db` remains usable.
- API contracts: unchanged.

## Security and privacy

- Authentication and authorization are unchanged.
- No user, tenant, document, question, or financial value is logged.
- Only schema keys, counts, timing, status, model name, and prompt version are retained.

## Observability and failure handling

- Node metrics: duration, input count, output count.
- Node parameters: bounded input/output key names, status, exception class on failure.
- MLflow import, initialization, and logging remain fail-open for application availability.

## Rollout and rollback

- Deployment order: code, tests, documentation.
- No migration or feature flag beyond the existing `MLFLOW_ENABLED` setting.
- Rollback: restore the previous decorator; the SQLite tracking database remains compatible.

## Verification strategy

- Unit: fake tracker verifies exact metadata and absence of raw values.
- Integration: complete test suite.
- Manual: start MLflow UI against `mlflow.db` and inspect a new analysis run.
