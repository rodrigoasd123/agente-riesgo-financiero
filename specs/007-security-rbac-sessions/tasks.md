# Tasks — Security consolidation with RBAC and revocable sessions

## Preparation

- [x] **T-001** Confirm scope, threat boundaries and compatibility; no blocking questions remain. `[FR-001..FR-005, SEC-001..SEC-006]`

## Implementation

- [x] **T-010** Add compatible user/session schema, repositories and administrator bootstrap. `[FR-005, NFR-001, SEC-001, SEC-006]`
- [x] **T-011** Add role-bearing JWTs, persistent sessions, identity resolution and revocation. `[FR-001, FR-002, NFR-003, SEC-002]`
- [x] **T-012** Add admin user-management contracts and role protection. `[FR-003, FR-004, SEC-003, SEC-005, SEC-006]`
- [x] **T-013** Preserve business access and owner isolation for both supported roles. `[SEC-004]`
- [x] **T-014** Adapt Streamlit identity, navigation and logout behavior. `[FR-002, SEC-003]`

## Verification

- [x] **T-020** Add unit and API integration coverage for all acceptance scenarios. `[AC-001..AC-008]`
- [x] **T-021** Run focused authentication tests and the complete regression suite. `[NFR-001..NFR-004, SEC-001..SEC-006]`
- [x] **T-022** Perform an evidence-based security review of the final diff. `[SEC-001..SEC-006]`

## Release

- [x] **T-030** Update README, SECURITY and environment/operator guidance.
- [x] **T-031** Record acceptance evidence and mark the specification accurately.
