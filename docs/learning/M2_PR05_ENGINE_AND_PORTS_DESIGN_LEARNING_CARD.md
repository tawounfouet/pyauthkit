# M2 PR-05 - Async Authentication Engine and Ports Design Learning Card

- Date: 2026-11-02
- Stage: IMPLEMENTED ON PR CANDIDATE; CI AND GATE QUALIFICATION PENDING
- Work Packages: WP27-013, WP27-014, WP27-015, WP27-016 (final gate), WP27-018
- Related: ADR-0006..0009; specs 07, 09, 10, 18, 20, 21, 24, 25, 26; PR #71

## Problem first

When a host-approved request passes verification, an authenticator could try to
return a final principal, reuse a positive outcome from another tenant or
attempt, or bypass the final policy. A concrete verifier could hang or raise
while a concurrent request changes a registry. None of these must grant AuthN.

## Trust boundary and ownership

Untrusted input: `AuthenticationRequest`, `PresentedEvidence`,
`ClaimedIdentity`. Trusted input: operator-approved route to
`TrustedEntryContext` (PR-04). The engine owns sequencing, not credential
cryptography. Explicitly admitted `Authenticator` owns specialized proof
verification. `AuthenticationPolicyGate` owns the final decision.
`Authenticated` can only emerge *after* that decision in the ordinary engine
path; it remains separate from PyIAMKit identity and authorization.

## Minimal design chosen

- `Authenticator` and `AuthenticatorLookup` are narrow Python `Protocol`
  ports (DIP / Interface Segregation).
- `AuthenticatorRegistryBuilder` registers known instances, rejects collisions,
  freezes once and exposes an immutable snapshot (Composition Root).
- The engine is an **Application Service**, sequential and async-first, without
  a generic workflow framework or per-framework branches (SoC/KISS).
- A unique per-attempt in-process object plus correlation, scope, method and
  profile version bind a synthetic positive verifier outcome to one execution.
- The final gate defaults to deny without an explicit operator policy.
- `asyncio.timeout` bounds verification; `CancelledError` propagates.
- Audit is a sanitized best-effort projection, not durable event sourcing.

## Rejected alternatives

1. Default or fallback verifier/tenant after an error: an implicit downgrade.
2. Return the authenticator's result directly: a final-policy bypass.
3. Global mutable registry or discovered Python entry points: ungoverned code.
4. A full GoF State or Chain of Responsibility runtime: complexity without
   demonstrated invariants.
5. Per-call `os.environ` reloading: inconsistent trust snapshots.
6. Assuming a private Python name prevents privileged local code from
   manufacturing a positive object: false security promise.

## Independent oracles

M2-T11, T12, T13 and T24 reject cross-attempt outcomes, prove final denial
overrides positive verification, allow a test-only controlled positive only
after final gate, and reject an authenticator returning `Authenticated`.
Additional adversarial tests cover cross-tenant, unknown method, registry
freeze, timeout, cancellation, exception redaction and audit failure.

## Limits and transfer

The test-only `FakeAuthenticator` is stored under tests/, not src/, and does
not verify any password, API key or JWT. No cryptographic security or AAL
assurance is claimed. A compromised admitted in-process Python adapter may
still bypass Python-level privacy. This boundary requires trustworthy code,
dependency provenance, code review and sandboxing if untrusted plugins are
introduced later. The same trust-first architecture transfers to PyIAMKit
and other Py*Kit systems, without confusing authentication and authorization.

## Evidence before claim

Source commits and GitHub Actions must be linked before changing the status
to TESTED or QUALIFIED. An accepted design ADR does not prove successful CI.
