# Implementation plan — Security consolidation with RBAC and revocable sessions

## Approach

Replace the in-memory user dictionary with small SQLite repositories for users and sessions. Login authenticates against the active user row, creates one session row and signs a JWT whose `jti` references it. A single `CurrentUser` dependency validates cryptographic claims, current session state, current user state and role consistency. A role dependency wraps this identity for administrative routes. Existing business routes continue receiving only the trusted username to preserve owner filtering.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| `backend/db/database.py` | Add user/session schema and transaction-safe repository operations | Backend |
| `backend/auth/security.py` | Password verification, JWT issue/decode and authentication service | Backend |
| `backend/auth/dependencies.py` | Resolve current identity and enforce closed roles | Backend |
| `backend/auth/routes.py` | Login, identity, logout and admin user contracts | Backend |
| `backend/api/routes_settings.py` | Restrict application-wide secrets/configuration to administrators | Backend |
| `frontend/app.py` | Store/display identity, hide admin settings, revoke on logout | Frontend |
| Tests and docs | Prove acceptance criteria and explain residual limits | QA/security |

## Data and control flow

1. Startup runs the additive schema and bootstraps the configured administrator only when absent.
2. Login normalizes the username, verifies bcrypt against the database hash and requires `is_active=1`.
3. A random `jti` session is persisted with expiry before the access JWT is returned.
4. Protected requests validate JWT cryptography and required claims, then load the matching unrevoked session and active user.
5. The database username must equal `sub`, and database role must equal the signed `role`; otherwise authentication fails.
6. Role dependencies return 403 for an authenticated but unauthorized caller.
7. Logout marks the current `jti` revoked; deactivation revokes all sessions for the target user in the same transaction.

## Data model and API changes

- **Migrations:** additive `users` and `auth_sessions` tables plus indexes; no analysis table contraction.
- **Compatibility:** bootstrap retains the existing administrator credentials; login retains `access_token`, `token_type`, `expires_in_minutes` and adds `username`, `role`.
- **API contracts:** add `GET /auth/me`, `POST /auth/logout`, `GET/POST /auth/users`, and `PATCH /auth/users/{username}/active`.

## Security and privacy

- **Authentication and authorization:** closed JWT algorithm and claims plus current database session/user check; admin routes use explicit role dependency.
- **Tenant/data isolation:** business routes continue deriving owner from the authenticated subject, never from request payloads.
- **Sensitive-data handling:** API never returns password hashes, raw passwords, JWT signing key or provider secrets.

## Observability and failure handling

- Authentication errors use generic messages. No credential value is logged.
- Bootstrap and schema creation are idempotent. Duplicate username returns conflict.
- Session rows expire naturally and can be purged later; validation treats expired records as invalid immediately.

## Rollout and rollback

- **Deployment order:** deploy code, start once to run additive schema/bootstrap, then create analysts through the admin API/UI-compatible backend.
- **Migration sequence:** old JWTs intentionally become invalid because they lack the required `role` claim and persisted session.
- **Rollback behavior:** older code ignores additive tables and continues with configured admin; new user accounts are unavailable after rollback but data remains intact.

## Verification strategy

- **Unit:** bcrypt boundaries, required JWT role, altered/expired tokens.
- **Integration:** bootstrap, login/session persistence, admin/analyst authorization, duplicate user, self-deactivation, logout and deactivation revocation.
- **End-to-end:** existing admin analysis flow remains passing and analyst ownership remains isolated.
- **Manual evidence:** Streamlit login displays actual identity; analyst has no configuration tab; logout returns to login.
