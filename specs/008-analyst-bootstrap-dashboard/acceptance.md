# Acceptance — Analyst bootstrap and interactive financial dashboard

## AC-001 — Analyst bootstrap and authentication

**Covers:** FR-001, NFR-003, SEC-001

```gherkin
Given a database without `analista` and the configured bcrypt hash
When the application starts and `analista/analista123` logs in
Then an active `analyst` is created and a role-bearing session-backed JWT is returned
```

**Evidence:** `test_hash_y_bootstrap_analista_autentican_con_rol_limitado`; live API login returned role `analyst`.

## AC-002 — Existing account preservation and least privilege

**Covers:** NFR-003, SEC-002

```gherkin
Given an existing `analista` row and an authenticated analyst
When startup repeats and the analyst accesses business then administrative routes
Then the row is not overwritten, business succeeds and administration returns 403
```

**Evidence:** `test_bootstrap_no_sobrescribe_analista_existente`; live `/analyses` 200 and `/settings/status` 403.

## AC-003 — Complete analysis dashboard

**Covers:** FR-002, FR-003, FR-004, NFR-001, NFR-004

```gherkin
Given an owner-scoped active analysis with complete figures, indicators and alerts
When the user opens Dashboard
Then balance, sales, operating results, indicator and alert charts render with labels, units and tooltips using the original values
```

**Evidence:** dashboard dataset/chart unit tests and `test_analista_renderiza_dashboard_completo_sin_configuracion`.

## AC-004 — Scenario cash flow

**Covers:** FR-005

```gherkin
Given an active financial projection
When Dashboard renders
Then period and cumulative cash flow are shown without recalculation or fabricated periods
```

**Evidence:** `test_dashboard_alertas_allowlisted_y_flujo_sin_recalculo` and Streamlit dashboard smoke.

## AC-005 — Partial and empty data

**Covers:** FR-006

```gherkin
Given no active analysis or a document missing some figures
When Dashboard renders
Then it shows a specific empty state and renders independent available sections without zero-filling missing values
```

**Evidence:** `test_dashboard_datos_parciales_no_inventan_ceros`; empty state is present in Streamlit workflow.

## AC-006 — Isolation and responsive UI

**Covers:** NFR-002, SEC-003, SEC-004

```gherkin
Given an analyst on desktop or narrow viewport
When they use Dashboard
Then only their active analysis data is displayed, no protected content enters chart datasets and the layout remains usable
```

**Evidence:** owner-isolation regression tests; alert allowlist test; AppTest confirms analyst-only tabs and no Configuración; browser desktop/narrow smoke has no console errors.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | Bcrypt/bootstrap integration and live login | PASS |
| AC-002 | Preservation/RBAC tests and live 200/403 smoke | PASS |
| AC-003 | Data/chart tests and authenticated Streamlit smoke | PASS |
| AC-004 | Exact cash-flow transformation and layered chart test | PASS |
| AC-005 | Partial-data tests and explicit UI empty states | PASS |
| AC-006 | Isolation/allowlist tests plus desktop/narrow smoke | PASS |

## Verification evidence

- Focused SPEC-008 suite: `7 passed, 2 dependency warnings`.
- Complete suite: `.\.venv\Scripts\python.exe -m pytest tests -q` → `96 passed, 2 dependency warnings`.
- Compile: `.\.venv\Scripts\python.exe -m compileall -q backend frontend tests` → pass.
- Diff hygiene: `git diff --check` → pass; only Windows line-ending notices.
- Live API: `analista` resolved as `analyst`, business endpoint returned 200 and settings returned 403.
- Streamlit component smoke: dashboard heading, KPI metrics and exactly three analyst tabs rendered without exception.
- Browser smoke: login UI remained usable at default and 390×844 viewports; console error log was empty.
- Security review: chart datasets allowlist finite numbers and fixed alert codes; no provider call, cross-user query, secret, PDF text or alert message is introduced.
