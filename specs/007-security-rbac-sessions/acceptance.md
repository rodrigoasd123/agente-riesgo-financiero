# Acceptance — Security consolidation with RBAC and revocable sessions

## AC-001 — Compatible administrator bootstrap and login

**Covers:** FR-001, FR-005, NFR-001, NFR-002, SEC-001

```gherkin
Given an existing database without security tables and configured admin credentials
When the application starts and admin logs in
Then the security tables are added without losing analyses and a role-bearing, session-backed JWT is returned
```

**Evidence:** `test_bootstrap_login_y_jwt_con_rol_y_sesion`, `test_legacy_database_migrates_without_losing_analysis`.

## AC-002 — Administrator provisions an analyst

**Covers:** FR-003, SEC-001, SEC-006

```gherkin
Given an authenticated administrator
When they create a valid analyst
Then only a bcrypt hash is persisted and the response contains no password or hash
```

**Evidence:** `test_admin_crea_analista_sin_exponer_password_ni_hash`.

## AC-003 — Analyst least privilege

**Covers:** SEC-003, SEC-004

```gherkin
Given an authenticated analyst
When they access analysis routes and then administrative settings or user management
Then business access succeeds while administrative access returns 403
```

**Evidence:** `test_analista_accede_negocio_pero_no_administracion`.

## AC-004 — Logout revokes the current session

**Covers:** FR-002, SEC-002

```gherkin
Given a valid authenticated session
When the user logs out and reuses the same JWT
Then logout succeeds once and subsequent protected requests return 401
```

**Evidence:** `test_logout_revoca_token_actual` plus live API smoke (`/auth/me` returns 401 after logout).

## AC-005 — Deactivation revokes all target sessions

**Covers:** FR-004, SEC-002

```gherkin
Given an analyst with one or more valid sessions
When an administrator deactivates the analyst
Then all existing analyst tokens are rejected and new login is denied without account enumeration
```

**Evidence:** `test_desactivar_usuario_revoca_sesiones_y_bloquea_login`.

## AC-006 — Self-deactivation is prohibited

**Covers:** SEC-005

```gherkin
Given an authenticated administrator
When they attempt to deactivate their own account
Then the API returns 409 and the current session remains valid
```

**Evidence:** `test_admin_no_puede_desactivarse_a_si_mismo`.

## AC-007 — Invalid and stale tokens fail closed

**Covers:** NFR-003, SEC-002

```gherkin
Given a JWT with a missing/altered role, unknown/revoked jti, expired signature, inactive user or role differing from the database
When it reaches a protected endpoint
Then the API returns 401 without protected data
```

**Evidence:** `test_jwt_*`, `test_token_sin_sesion_y_rol_obsoleto_fallan_cerrados`, logout/deactivation tests.

## AC-008 — Owner isolation remains enforced

**Covers:** SEC-004

```gherkin
Given two active users with analyses owned separately
When one requests the other's analysis, export or chat
Then the resource is not exposed
```

**Evidence:** `test_analisis_permanece_aislado_entre_admin_y_analista`, existing `test_no_expone_analisis_de_otro_actor`.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | Bootstrap/JWT and legacy migration integration tests | PASS |
| AC-002 | Admin provisioning, bcrypt and non-disclosure integration test | PASS |
| AC-003 | Analyst business/admin boundary integration test | PASS |
| AC-004 | Logout revocation test and live API smoke | PASS |
| AC-005 | Deactivation revocation and generic login failure test | PASS |
| AC-006 | Self-deactivation conflict test | PASS |
| AC-007 | JWT unit matrix and persistent-session integration tests | PASS |
| AC-008 | Two-user owner isolation integration tests | PASS |

## Verification evidence

- Focused security/API suite: `36 passed` before the final isolation additions.
- Complete suite: `.\.venv\Scripts\python.exe -m pytest tests -q` → `89 passed, 1 dependency warning`.
- Compile: `.\.venv\Scripts\python.exe -m compileall -q backend frontend tests` → pass.
- Diff hygiene: `git diff --check` → pass; only Windows line-ending notices.
- Live API: administrator identity resolved; capabilities available; reused JWT returned `401` after logout.
- Streamlit: updated application loaded and rendered the login workflow at `http://localhost:8501/`.
- Security review: no confirmed authorization bypass; residual production risks remain documented in `SECURITY.md`.
