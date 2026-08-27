# Analyst bootstrap and interactive financial dashboard

- **ID:** SPEC-008
- **Status:** VERIFIED
- **Created:** 2026-08-27
- **Owner:** Product and engineering

## Problem

SPEC-007 introduced persistent RBAC but only bootstraps the administrator; teammates still need an administrator to create the first analyst manually. Financial results are presented mainly as tables and text, making relationships between capital structure, profitability, sales evolution, risk alerts and scenario cash flow harder to explore.

## Users and outcomes

- **Primary user:** authenticated financial analyst.
- **Secondary user:** administrator who may also use the analytical dashboard.
- **Desired outcome:** a ready-to-use least-privilege analyst account and interactive, deterministic visual explanations of the active analysis.
- **Success signal:** `analista/analista123` authenticates as `analyst`; the analyst cannot access administration; dashboard charts render only available owner-scoped analysis data and show useful empty states otherwise.

## Scope

### Included

- Idempotently bootstrap a configured analyst username/hash without overwriting an existing account.
- Verify both configured bootstrap hashes use bcrypt cost 12 or greater.
- Add a Dashboard tab for `analyst` and `admin` based on the active analysis already returned through owner-scoped APIs.
- Interactive charts for balance funding, sales comparison, grouped financial indicators, alert distribution and scenario cash flow when inputs exist.
- Explicit labels, units, tooltips, explanatory captions and partial-data empty states.

### Excluded

- Cross-user or portfolio dashboards, organization-wide aggregation and administrator access to analysts' documents.
- New financial formulas, predictive models, automated credit decisions or AI-generated chart values.
- Persistent dashboard preferences and external business intelligence services.

## Requirements

### Functional

- **FR-001:** Startup must idempotently bootstrap the configured analyst account with role `analyst`, active state and supplied bcrypt hash.
- **FR-002:** The dashboard must visualize the active analysis without modifying figures, indicators, alerts or projections.
- **FR-003:** When sufficient figures exist, the dashboard must provide interactive balance funding, sales comparison and operating-result charts.
- **FR-004:** When indicators or alerts exist, the dashboard must group them into understandable risk/liquidity/profitability views with tooltips and units.
- **FR-005:** When a scenario exists, the dashboard must show period cash flow and cumulative cash flow interactively.
- **FR-006:** Missing or partial inputs must produce specific empty states while still rendering independent available charts.

### Non-functional

- **NFR-001:** Visualization preparation must be deterministic and make no Gemini or network calls.
- **NFR-002:** The dashboard must remain usable on desktop and narrow viewports through Streamlit responsive containers.
- **NFR-003:** The migration must preserve existing users and must never reset their password, role or active state.
- **NFR-004:** Charts must not rely on color alone; titles, labels, values and tooltips must communicate meaning.

### Security and privacy

- **SEC-001:** The configured analyst hash must be validated as bcrypt cost 12+ and must match `analista123` in acceptance evidence without storing plaintext in application code.
- **SEC-002:** The analyst must retain 403 denial for settings and user administration.
- **SEC-003:** Dashboard data must come only from the authenticated user's active owner-scoped analysis and must not introduce cross-user queries.
- **SEC-004:** No password, hash, token, provider secret, PDF text or prompt content may be included in chart data or tooltips.

## Constraints and invariants

- Existing RBAC names remain `admin` and `analyst`.
- Altair is the chart engine already provided by Streamlit; it becomes an explicit dependency because application code imports it.
- Ratios retain their native semantic units: liquidity/coverage as multiples, ROA/ROE/margin/debt as percentages, capital amounts as currency-neutral values.
- Visuals are explanatory and include the existing human-review disclaimer.

## Risks and failure modes

- Misleading mixed scales: split percentage and multiple indicators into separate views and label units.
- Incomplete PDFs: render per-chart empty states rather than zero-filling missing financial values.
- Existing `analista` account differs from bootstrap config: `INSERT OR IGNORE` preserves it; operator must manage it explicitly.
- Sensitive cross-user aggregation: no new dashboard API or aggregate query is introduced.

## Open questions

None. The user supplied the account, password hash and requested analyst-only value; administrator retains access as the superset role.

## References

- `specs/007-security-rbac-sessions`
- `backend/agent/indicadores.py`
- `frontend/app.py`
