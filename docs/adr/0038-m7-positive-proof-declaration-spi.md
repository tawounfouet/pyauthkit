# ADR 0038 - M7 Positive Proof Declaration SPI for Admitted Plugins

> Status: PROPOSED / DESIGN & SECURITY REVIEW REQUIRED (issue #86)
> Date: 2026-11-07
> Scope: PR #84, M7 / GATE27-08; NOT A PRODUCTION SECURITY APPROVAL

## Problem and trust boundary

A verifier plugin may legitimately validate an approved credential, but the engine alone must issue a final `Authenticated` after preflight, attempt binding, and the host's final policy. M3/M4/M5 use a private helper `_issue_verified_outcome`; copying that private import into externally distributed plugins produces an unstable hidden SPI.

Trust zones: untrusted `AuthenticationRequest` and claims -> host-selected trusted `VerificationContext` -> already-admitted verifier's cryptographic check -> *internal* `VerifiedOutcome` -> engine per-attempt validation -> host `AuthenticationPolicyGate` -> final `AuthenticationResult`. PyIAMKit authorization is a separate, later decision.

## Proposed decision

1. Provide `pyauthkit.plugins.verification.issue_verified_outcome` as an explicit SPI-only helper. Keep `pyauthkit.sdk` and the package root free from a final-success constructor.
2. Require typed `request`, `context`, `ScopedSubjectRef`, `PrincipalType`, and `ObservedAt`; reject mismatched method, correlation, scope and profile before the private transition helper.
3. Reuse `_issue_verified_outcome` and `_verified_matches_attempt` rather than creating a new result variant, attempt marker, policy or bypass.
4. Never infer subject or trust profile from unverified claims. Only a plugin which has actually checked the method-specific proof, expiry/freshness and revocation may declare an outcome.
5. Errors expose only a fixed sanitized code/message. The engine remains fail-closed on exceptions, malformed outcomes, stale attempt token, wrong method or scope and final policy DENY.
6. Approved arbitrary Python plugin code runs with host privileges. This helper is **not** a proof verifier, cryptographic capability, signature, sandbox, or a guard against intentionally malicious admitted code.

## Alternatives considered

- **Expose `Authenticated` factory:** rejected because a plugin would bypass the mandatory final policy.
- **Export private `_issue_verified_outcome`:** rejected because private implementation changes would silently break external SPI consumers.
- **Embed an opaque 'proof certificate' token:** rejected as false assurance; a token minted by untrusted plugin code cannot prove a cryptographic check happened.
- **Add a second engine or mutable global registry:** rejected; creates parallel authority and broadens attack surface.
- **Keep all third-party plugins denial-only:** safer but makes M7 extension ecosystem unable to provide valid verification outcomes. The explicit SPI declaration is a limited candidate, gated by independent review.

## Testable invariants

- A declared proof is only an **internal outcome**; an authenticated final result requires policy allow.
- Wrong method, scope, trace or attempt token never results in final success.
- Unrecognized proof shape is a technical failure; invalid evidence is rejected.
- No re-binding of trust based on client-provided tenant hints.
- Code provenance and algorithm correctness remain independent host security obligations.

## Evidence and open decisions

Tests: `tests/security/test_m7_plugin_positive_proof.py` and the separately installed qualification plugin wheel, exercised by `scripts/smoke_m7_installed_plugin.py`. Positive fixture uses known public bytes and is intentionally non-production. CI evidence must be recorded by exact SHA and run.

**Open:** factory v1 uses zero arguments. A production third-party verifier needs host-authoritative dependency injection for resolvers, secrets, key sources and guards. That extension design, supply-chain authenticity, positive proof conformance and independent reviewer signature are still needed before GATE27-08 can become GO.
