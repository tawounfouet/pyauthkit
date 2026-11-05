# PR-07 / M4 API Key Authentication - Execution log

- Date: 2026-11-05
- Canonical PR: https://github.com/tawounfouet/pyauthkit/pull/76
- Base M2 main: `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`
- Current milestone decision: **GATE27-05 NOT EVALUATED / NO GO**
- M3 dependency: PR #75 remains without formal GATE27-04 sign-off.
- This log records implementation slices, **not** validation by narrative.

## Slice A - Domain & Resolver (WP27-023, proposed WP28-045..048)

- Immutable scoped verifier read model, four-way lookup and async resolver port.
- Explicit host callback adapter; in-memory-only test double.
- ADR-0017 PROPOSED; resolver Design Learning Card.
- Technical checkpoint: SHA `30d0ffc1ec128e801e8034b3048c7280421ff181`
- CI: https://github.com/tawounfouet/pyauthkit/actions/runs/42047793783
  7/7 SUCCESS; quality job 128 PASS; no independent security sign-off.

## Slice B - Opaque Parser + HMAC Proof (WP27-024, proposed WP28-049..051)

- A single canonical `ak1` format: 16-byte selector and 32-byte bearer secret.
- Domain-separated, length-prefixed SHA-256 HMAC using a host-approved scoped
  `ApiKeyProtectionKeySource` with no silent fallback.
- 32-byte fixed digest comparison with `hmac.compare_digest`.
- Negative parser, fuzz/property, OpenSSL-vector, tamper, cross-scope and
  secret material redaction tests.
- ADR-0016 PROPOSED; parser/HMAC Design Learning Card.
- - Technical checkpoint: SHA `c75e33eec679a49d15d5c96b0e2d8424684cd6fe`
- CI: https://github.com/tawounfouet/pyauthkit/actions/runs/42051460826
  **7/7 SUCCESS**. Candidate HMAC proof, not final AuthN; no independent signoff.

## Slice C - Authenticator, lifecycle and final M2 policy (WP27-025, WP28-052..054)

- Added production `ApiKeyAuthenticator` conforming to existing M2 async SPI.
- Mandatory operator-supplied `ApiKeyAttemptGuard`; fail-closed on refused or
  unavailable admission.
- Active status, not-before/required expiry under injected UTC Clock,
  complete-secret proof and source-freshness read-back before VERIFIED.
- No authentication outcome bypasses M2 policy. Declined policy never grants
  AuthenticatedPrincipal. No session/token issuance or IAM permissions.
- Tests: positive with actual HMAC vector, final deny, lifecycle, malformed
  bearer, HMAC mutation, guard outage, cross-tenant and post-HMAC revocation.
- ADR-0018 PROPOSED and Design Learning Card.
- Technical checkpoint: SHA `d4a2346de60d7f9ca05409dac4b18a6a65eca5c4`.
- CI: https://github.com/tawounfouet/pyauthkit/actions/runs/42052986729
  **7/7 SUCCESS; 207 total pytest PASS** in quality job.
- Documentation-only changes after this checkpoint need their own HEAD CI.
- Formal status: **not security qualified**.

## Slice D - Qualification and operational host (WP27-026, WP28-055..060)

- Candidate 40-case index: `docs/qualification/M4_PR07_SECURITY_ORACLES.md`.
- Gate tracker: `docs/qualification/GATE27-05_M4_API_KEY_DECISION.md`.
- REQUIRED: source-scoped real PostgreSQL adapter, distributed Redis quota,
  2-host process tests, revocation/rotation CAS consistency, HTTP denial and
  timing qualification, audit/observability evidence, independent crypto/ADR
  signoff and G5-01..G5-16.
- Status: **NOT IMPLEMENTED / NOT RUN / NO-GO** for real-host qualification.

## Blocked final outcome

M3 PR #75 still lacks GATE27-04 signoff. PR-07 #76 remains a draft. No formal
M4 GO, release, merge into main or production authorization. Neither 207 green
tests nor this roadmap update can replace real-host and independent evidence.

## Slice D - reference-host qualification workstream (2026-11-05)

- A standalone fixture exists under `qualification/m4_host` with actual
  PostgreSQL scoped reads and authoritative state/version recheck,
  source-level CAS revocation and verifier rotation, Redis Lua atomic
  quotas for tenant, socket peer and key selector, plus an explicit FastAPI
  composition boundary and Uvicorn runner.
- A dedicated GitHub Actions job uses disposable PostgreSQL/Redis services
  and installs reference-host packages only in CI, not core PyAuthKit.
- Tests include same-selector tenant separation, concurrent CAS single
  winner, post-HMAC revocation race, 64 concurrent Redis admissions,
  uniform HTTP refusal surfaces, two distinct Uvicorn OS processes and
  randomized loopback timing observations.
- This is a **candidate test fixture** only. No test evidence is claimed
  until the exact-HEAD CI completes; real TLS/proxy, SIEM, deployment-scale
  overload and external timing equivalence are not covered.
- M4-T34..40 and G5-01..G5-16 remain formally **PENDING**; ADRs and
  independent review are not waived by reference-host success.
