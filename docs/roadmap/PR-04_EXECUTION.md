# PR-04 - M2 Host Trust Context and Policy Preflight

- **State:** MERGED / REVIEWED / CI QUALIFIED FOR PR-04 ONLY
- **PR:** https://github.com/tawounfouet/pyauthkit/pull/69
- **Head qualified:** `1b87ee1596af21744928bb69123d9043fde0c5b7`
- **Squash merge on main:** `8b2f2df35aecfe8e85cf0300606a2ce482514c1f`
- **PR CI:** https://github.com/tawounfouet/pyauthkit/actions/runs/41440351266
- **Post-merge main CI:** https://github.com/tawounfouet/pyauthkit/actions/runs/41449081791
- **Scope:** WP27-017 and preflight portion of WP27-016
- **M2 gate:** https://github.com/tawounfouet/pyauthkit/issues/70 remains OPEN.

## Implemented and qualified in this limited slice

- [x] Explicit operator-approved HostBinding + HostTrustCatalog with immutable snapshot.
- [x] No unknown/default route, duplicate binding or scope/profile mismatch.
- [x] Catalog-issued TrustedEntryContext and foreign-context rejection.
- [x] AuthenticationPolicyGate.preflight only permits verification attempt.
- [x] No Authenticated principal or positive verifier exposed by PR-04.
- [x] Ruff, mypy strict, 75 pytest tests, architecture fitness checks on PR head.
- [x] Seven required GitHub Actions jobs and GitGuardian positive check on PR.
- [x] Post-merge CI on main: seven required jobs successful.
- [x] Security design review on PR #69: https://github.com/tawounfouet/pyauthkit/pull/69.
- [x] Squash-merged normally under active main ruleset; no bypass.

## Trust boundary and residual exposure

The host adapter is REQUIRED to establish route provenance from an approved
server-side mapping. Raw Host, Forwarded, X-Forwarded-Host, X-Tenant, JWT iss/kid,
query or claims are never sufficient authority. The PR-04 tests prove the
library-level catalog/preflight behavior, NOT a real HTTP proxy integration.

The catalog's Python object-identity model is a misuse guard, not sandboxing
against privileged arbitrary Python code. VerificationPermitted alone is not
a final decision; PR-05 must re-run the preflight inside the engine. The
positive policy gate and all real cryptographic authenticators remain outside
the PR-04 qualification scope.

**Result: GO PR-04 ONLY. No M2 GO, no release, no production authentication.**
