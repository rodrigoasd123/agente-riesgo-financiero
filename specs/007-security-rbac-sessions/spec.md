# Security consolidation with RBAC and revocable sessions

- **ID:** SPEC-007
- **Status:** VERIFIED
- **Created:** 2026-08-27
- **Owner:** Product and engineering

## Problem

The application authenticates one in-memory administrator, but the declared role is neither placed in the JWT nor enforced by protected routes. A copied JWT remains usable after the frontend logs out, and users cannot be safely provisioned or disabled. This prevents controlled access by teammates and leaves configuration secrets available to every authenticated account once more users are introduced.

## Users and outcomes

- **Primary user:** administrator who provisions application users and manages provider configuration.
- **Secondary user:** financial analyst who analyzes documents, asks questions and exports or emails reports.
- **Desired outcome:** persistent least-privilege access with revocable sessions and owner-scoped financial data.
- **Success signal:** analysts cannot reach administrative settings or user management; logout and user deactivation immediately invalidate existing sessions; the existing administrator remains compatible.

## Scope

### Included

- Additive SQLite persistence for users and login sessions.
- Bootstrap the configured administrator idempotently from `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH`.
- Roles `admin` and `analyst`, stored server-side and included in signed access JWTs.
- Admin-only user listing, creation and activation/deactivation.
- Authenticated identity endpoint and server-side logout revocation.
- Admin-only provider configuration/status; business analysis/report routes for both supported roles.
- Streamlit identity display, logout call and admin-only configuration visibility.

### Excluded

- Password recovery, email invitations, MFA, SSO and OAuth login.
- Refresh tokens, concurrent-device management UI and password change/reset endpoints.
- Distributed rate limiting or shared session storage for multi-instance deployment.
- Per-user Gmail OAuth connections; the configured Gmail sender remains application-wide.

## Requirements

### Functional

- **FR-001:** A valid active user must receive an access JWT containing immutable session id, username and role claims.
- **FR-002:** An authenticated user must be able to read their own username and role and revoke their current session through logout.
- **FR-003:** An administrator must be able to list users and create an `admin` or `analyst` with a bcrypt-hashed password.
- **FR-004:** An administrator must be able to activate or deactivate a non-self user.
- **FR-005:** Existing `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` configuration must idempotently bootstrap an active administrator without overwriting later database state.

### Non-functional

- **NFR-001:** The database migration must be additive and preserve existing analyses and questions.
- **NFR-002:** Existing login response fields and Bearer authentication must remain compatible; added response fields must be optional to old clients.
- **NFR-003:** Authorization decisions must be derived from current server-side user/session state on every request.
- **NFR-004:** Authentication failures must not disclose whether a username exists and must not log passwords, hashes or tokens.

### Security and privacy

- **SEC-001:** Passwords must only be persisted as bcrypt hashes with work factor 12 or greater.
- **SEC-002:** Every protected request must reject missing, malformed, expired, revoked, inactive-user, unknown-session, role-mismatched or stale-role JWTs.
- **SEC-003:** Provider settings, Gmail authorization management and user administration must require the `admin` role.
- **SEC-004:** Analysis, chat, history, finance and report operations must require `admin` or `analyst` and retain owner-scoped database filtering.
- **SEC-005:** An administrator must not be able to deactivate their own currently authenticated account.
- **SEC-006:** Usernames must be normalized, bounded and unique; passwords created through the API must be at least 12 characters and never returned.

## Constraints and invariants

- SQLite remains the supported local persistence engine and migrations must be idempotent.
- JWT continues to use the configured fixed HS256 algorithm, issuer, audience and expiry.
- Role values are a closed server-side enum: `admin`, `analyst`.
- The current academic/local deployment remains the operating assumption; HTTPS and external secret management remain deployment requirements.

## Risks and failure modes

- Stolen token remains usable until expiry unless logout/deactivation occurs: sessions are checked on every request and logout revokes the current `jti`.
- Database copied from an older release has no users: startup creates tables and bootstraps the configured administrator transactionally.
- Role changed while a token exists: token role is compared to the current database role and stale tokens are rejected.
- Last administrator could become inaccessible: self-deactivation is prohibited; administrative changes remain auditable in database timestamps.
- Multi-process login throttling is not solved by this slice and remains a production deployment risk.

## Open questions

None. The user explicitly requested consolidation using the existing specification methodology; the smallest coherent boundary is persistent two-role RBAC plus revocable access sessions.

## References

- `specs/000-project-completion-security-gemini`
- `SECURITY.md`
- `backend/auth/*`
- `backend/db/database.py`
