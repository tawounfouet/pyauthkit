# M4 PR-07C - Authenticator, temporal validity and revocation Learning Card

- Date: 2026-11-05
- Status: IMPLEMENTATION CANDIDATE; NOT SECURITY-QUALIFIED
- Work package: WP27-025; proposed tasks WP28-052..054
- Related: ADR-0018 (PROPOSED); ADR-0016 and ADR-0017 (PROPOSED)

## Problem first / trust boundaries

A signed or MAC-matched API-key proof is not equivalent to an AuthN grant.
A stale record, revoked credential or insufficient policy must never become
`Authenticated`. The client controls the bearer and possible claimed tenant;
the host controls scope, admission guard, source resolver, verification key,
clock and the final policy. No IAM permissions are decided here.

## Minimal design

- [GoF: Strategy] `ApiKeyAuthenticator` is admitted through existing M2
  `AuthenticatorRegistryBuilder`, without a custom engine or fallback.
- [ARCH: Ports & Adapters] Three narrow ports: source-scoped resolver,
  HMAC-only verifier and mandatory host-managed attempt guard.
- [SECURITY: Temporal Validity] An injected clock validates the UTC window
  before proof and again after the freshness check; the request timestamp is
  not trusted.
- [SECURITY: Revocation] `is_current(record)` must consult an authoritative,
  versioned source. A return value of `False` cannot become a positive
  verification.
- [SECURITY: Provenance] The internal M2 outcome factory binds the proof to
  one exact attempt, method, scope, trust-profile version and correlation.
- [SECURITY: Final Authority] `AuthenticationPolicyGate` alone converts a
  verified outcome into the final `Authenticated` result after a host allow.

## Risks, rejected alternatives, learning

No shadow `AuthenticationEngine`; no positive result directly from
`HmacApiKeyVerifier`; no globally resolved record, default key source or
permissive default guard. A one-time freshness recheck is a useful check but
does not prove instantaneous revocation across competing distributed writes.
An in-memory test demonstrates ordering, not real PostgreSQL isolation,
network timing or deployment rate-limit budgets.

## Required evidence

Ruff, strict mypy, Python 3.12-3.14 and platform wheel checks, negative tests
and security review for this exact SHA. Future PR-07D must qualify the real
credential owner, concurrency/race semantics, timing, observer and audit
evidence. GATE27-05 is not approved by the existence of this adapter.
