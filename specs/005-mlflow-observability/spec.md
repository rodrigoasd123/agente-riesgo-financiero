# MLflow observability completion

- **ID:** SPEC-005
- **Status:** VERIFIED
- **Created:** 2026-08-24
- **Owner:** Product and engineering

## Problem

The agent records execution duration and input field names, but the rubric also requires evidence of what each graph node receives and returns. Recording raw financial content would create an unnecessary privacy risk.

## Users and outcomes

- **Primary user:** project operator or evaluator.
- **Desired outcome:** inspect successful and failed graph executions in MLflow without exposing PDF text, questions, credentials, or extracted financial values.
- **Success signal:** every traced node records duration, status, and safe input/output schema metadata; MLflow can be opened locally with documented instructions.

## Scope

### Included

- Record input/output field names and counts for each graph node.
- Record node completion status and exception type.
- Keep tracing optional and tolerant of MLflow failures.
- Add automated privacy and failure-path coverage.
- Document how to open the local MLflow interface.

### Excluded

- Raw state values, PDF fragments, user questions, API keys, tokens, or financial figures.
- Remote MLflow hosting, authentication, alerting, and production retention policies.
- Changes to graph routing, financial calculations, or API responses.

## Requirements

### Functional

- **FR-001:** Each traced node must record duration, status, input field names/count, and output field names/count in its active MLflow run.
- **FR-002:** A failed node must record failed status and the exception class before propagating the original exception.
- **FR-003:** Operator documentation must explain how to start and inspect local MLflow.

### Non-functional

- **NFR-001:** Tracing failures must not change the graph result or availability.
- **NFR-002:** Existing graph and API behavior must remain compatible.

### Security and privacy

- **SEC-001:** Traces must never contain state values, raw PDF text, questions, credentials, tokens, extracted figures, summaries, or generated answers.
- **SEC-002:** Tracing must remain disableable through `MLFLOW_ENABLED=false`.

## Constraints and invariants

- MLflow uses the configured local tracking URI and experiment.
- Field names are metadata; values remain inside application memory and persistence.
- The decorator always returns or raises exactly as the wrapped node does.

## Risks and failure modes

- Excessive metadata length: field-name lists are bounded before logging.
- MLflow unavailable or locked: errors are swallowed and agent execution continues.
- Sensitive values accidentally logged: automated tests assert secrets and financial values are absent from every logged parameter.

## Open questions

None.

## References

- `backend/observability/tracing.py`
- `backend/workflow/graph.py`
