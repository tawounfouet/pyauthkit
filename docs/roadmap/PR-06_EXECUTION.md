# PR-06 Execution - M3 Password Authentication

- Date: 2026-11-02
- Milestone: M3 (#4), WP27-019..022 / WP28-029..044
- Branch: `feat/m3-password-authentication-pr06`
- Pull request: [#75](https://github.com/tawounfouet/pyauthkit/pull/75), **DRAFT**
- Gate: [GATE27-04 #74](https://github.com/tawounfouet/pyauthkit/issues/74), **OPEN / NO GO**
- Entry M2 SHA: `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`

## Work completed in the candidate branch

| Slice | Contents | Evidence |
|---|---|---|
| PR-06A | Scoped record/resolver contracts, in-memory and callback adapters, contract tests, ADR-0010 | `e38ca483` |
| PR-06B | Argon2id-only PHC verifier, parameter bounds, worker capacity and optional `password` extra, ADR-0011/0012 | `a8cb29eb` |
| PR-06C | PasswordAuthenticator using M2 SPI, final gate, negative integration tests, audit and redaction | `625511ce` |
| Hardening | Ruff, mypy and synthetic-secret remediation | `39cb90bd`, `5fb1727f`, `ac35bb30` |
| Security | Mandatory host attempt guard, revocation/guard negative tests and ADR-0013 | `6b91b811`, `ada059c7` |

## Qualification notes

The intermediate candidate `ac35bb30d9bbb23990c2ec4434dd32c9110e9603`
reached **7/7 successful CI jobs** at [GitHub Actions run 41510028088](https://github.com/tawounfouet/pyauthkit/actions/runs/41510028088). This predates the mandatory attempt guard; **do not use the intermediate green check to qualify later code**.

The final PR requires a new green run on its CURRENT head, complete M3-T01..T40 evidence, ADR review and explicit GATE27-04 sign-off.

## Out of scope

No main merge, PyPI publication, production deployment, IAM authorization,
credential lifecycle mutations, MFA or session/token issuance. The in-memory
store and the dummy-hash technique do not establish distributed revocation,
online anti-enumeration timing guarantees or global rate limits.
