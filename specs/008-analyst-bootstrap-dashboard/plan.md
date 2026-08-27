# Implementation plan — Analyst bootstrap and interactive financial dashboard

## Approach

Extend the existing additive bootstrap with a second environment-configured account. Keep all financial authorization and calculations unchanged. Add a pure dashboard-data preparation module and an Altair presentation module consumed by a new Streamlit tab. It reads only `st.session_state.analysis` and the current projection already authorized by the backend.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| Configuration/database | Analyst bootstrap variables, validation and idempotent insert | Backend |
| `frontend/dashboard.py` | Pure data shaping and chart construction | Frontend |
| `frontend/app.py` | Dashboard tab, empty/loading states and role-visible navigation | Frontend |
| Tests | Hash/bootstrap, least privilege and deterministic chart-data coverage | QA/security |

## Data and control flow

1. Startup validates administrator and analyst bcrypt formats/costs, creates tables, then inserts each bootstrap account only if absent.
2. Login and RBAC continue through SPEC-007 without special cases.
3. After an owner-scoped analysis succeeds, Streamlit keeps its structured response in session state.
4. Dashboard data preparation selects allowlisted numeric fields and preserves missing values as missing.
5. Altair renders independent interactive charts and Streamlit shows explicit messages for unavailable sections.

## Data model and API changes

- **Migrations:** no new tables; additive second bootstrap insert.
- **Compatibility:** existing database users are not updated; existing admin and analyst API contracts remain unchanged.
- **API contracts:** none; dashboard consumes current owner-scoped responses.

## Security and privacy

- **Authentication and authorization:** analyst uses existing role-bearing revocable JWT and has no new administrative access.
- **Tenant/data isolation:** no cross-user queries; dashboard uses only the active analysis fetched under the current JWT.
- **Sensitive-data handling:** only allowlisted numeric financial outputs and alert code/severity enter chart datasets.

## Observability and failure handling

- Bootstrap is idempotent and preserves existing users. Chart preparation has no external calls or retries.
- Empty sections are user-visible rather than logged as errors.

## Rollout and rollback

- **Deployment order:** add environment defaults, restart backend once, then serve updated frontend.
- **Migration sequence:** startup inserts `analista` only when absent.
- **Rollback behavior:** the analyst row remains a valid SPEC-007 user; older frontends simply omit the dashboard tab.

## Verification strategy

- **Unit:** hash verification, bootstrap preservation and chart dataset transformations for complete/partial inputs.
- **Integration:** analyst login, role claim, business access and 403 administrative denial.
- **End-to-end:** full existing suite plus Streamlit dashboard smoke.
- **Manual evidence:** desktop and narrow viewport inspect interactive labels, empty state and console errors.
