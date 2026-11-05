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
- **Code and CI SHA evidence: to be filled only after exact checks.**

## Still excluded, blocking formal gate

- Slice C: `ApiKeyAuthenticator` conforming to the M2 SPI; lifecycle, expiry
  and revocation freshness; final M2 policy result.
- Slice D: host with real store, distributed abuse guard, cross-tenant
  adversarial validation, 40 M4 oracles and G5-01..16.
- Independent ADR/security review, a formal GO, merge, main CI and release
  remain uncompleted.
