# PR-04 - M2 Host Trust Context and Policy Preflight

- **State:** IMPLEMENTING / PR under review
- **Scope:** WP27-017 and first half of WP27-016
- **Next PR:** PR-05 for WP27-013..015, WP27-018 and final policy transition
- **Exit gate:** GATE27-03 applies to full M2, not to PR-04 alone

## Implemented

- `HostBinding`: explicit approved route, scope, profile and method set
- `HostTrustCatalog`: immutable, no default route, duplicate/collision guard
- `TrustedEntryContext`: catalog-issued and checked by identity
- `AuthenticationPolicyGate.preflight`: denies non-catalog entries, foreign
  tenant claims and disabled methods; returns a verification-only admission
  without a principal, NEVER `AUTHENTICATED`.
- Adversarial and negative tests under `tests/security` and `tests/unit`.

## Required qualification

- [ ] Ruff, mypy strict, pytest and architecture fitness on all PR code
- [ ] All seven required GitHub checks, five packaging matrices, GitGuardian
- [ ] Provenance, trust hints and policy-bypass review
- [ ] Explicit PR-04 acceptance without GATE27-03 or automatic merge

## PR-05 must add

- Async engine with an explicit sequenced pipeline
- Authenticator SPI, immutable registry and test-only fake
- Genuine verifier outcome provenance and final policy transition
- Timeout/cancellation and dependency failure semantics
- Tests showing no authenticator can alone issue a final principal

**No production verifier or release is included in PR-04.**
