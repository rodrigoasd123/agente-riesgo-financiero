# Acceptance — MLflow observability completion

## AC-001 — Successful node metadata

**Covers:** FR-001, SEC-001

```gherkin
Given an active MLflow run and a node receiving private financial state
When the node succeeds
Then duration, status, and input/output field names and counts are logged
And no state value is logged
```

**Evidence:** `tests/test_tracing.py::test_traced_node_logs_safe_input_and_output_schema` and real local MLflow run `verificacion-local`; status `FINISHED`, safe input/output schemas present, sentinel absent.

## AC-002 — Failed node metadata

**Covers:** FR-002, NFR-002, SEC-001

```gherkin
Given an active MLflow run
When a node raises an exception
Then failed status and exception class are logged without raw values
And the original exception is propagated
```

**Evidence:** `tests/test_tracing.py::test_traced_node_logs_failure_and_propagates`.

## AC-003 — Tracker failure isolation

**Covers:** NFR-001, SEC-002

```gherkin
Given MLflow is disabled or its logger fails
When a traced node executes
Then the node result and application behavior are unchanged
```

**Evidence:** `tests/test_tracing.py::test_tracker_failure_does_not_change_node_result`; complete suite remains green.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | Focused test and real SQLite-backed MLflow run | PASS |
| AC-002 | Focused failure-path test | PASS |
| AC-003 | Tracker failure isolation and complete regression suite | PASS |

- Focused command: `.\.venv\Scripts\python.exe -m pytest tests\test_tracing.py -q` → `4 passed`.
- Regression command: `.\.venv\Scripts\python.exe -m pytest tests -q` → `68 passed, 1 dependency warning`.
- Manual integration: local `sqlite:///tmp/mlflow-verification.db` run finished and did not contain the sentinel private value.
