# ADR-0018 - M4 API-key state, freshness and M2 final policy

- Date: 2026-11-05
- Status: **PROPOSED / NOT ACCEPTED**
- Work package: WP27-025; candidate tasks WP28-052..054
- Dependency: PR-07A/B technical implementation, M2 policy and authenticator SPI
- Formal gate: GATE27-05 **NOT EVALUATED**, no merge or release approval

## Problem first

A correct API-key HMAC match may be stale, expired, revoked, outside its host
scope or insufficient under a higher-level authentication policy. A read-model
status is not proof of currentness; a client timestamp is untrusted; a
positive verifier boolean must never issue an AuthenticatedPrincipal directly.

## Candidate decision

1. Implement `ApiKeyAuthenticator` as an explicitly registered async
   `Authenticator`, **not** a second engine. It accepts the M2
   `AuthenticationRequest` and `VerificationContext`, never a client-selected
   effective scope or profile. It returns `AuthenticatorOutcome`, not final AuthN.
2. Require host-supplied `ApiKeyAttemptGuard` and `ApiKeyCredentialResolver`.
   The guard is called for **every** attempt, including malformed API keys,
   before store lookup. Only literal boolean `True` admits a request; a
   guard exception produces a technical outcome and no fallback.
3. Perform source-scoped lookup, reject missing, map ambiguous records to a
   safe integrity/configuration error and unavailable source to a technical
   error. A returned record's scope and selector are independently checked.
4. Admit only `ACTIVE` records satisfying `not_before <= now < expires_at`
   where an expiry is **required** for a positive M4 result. This is an
   explicitly conservative MVP policy requiring owner approval. UTC time is
   obtained from an injected `Clock`; `request.observed_at` is not trusted.
5. Evaluate the **complete** bearer-secret proof through the PR-07B HMAC
   adapter. On a positive, recheck `resolver.is_current(record=record)`
   against the authoritative credential owner, then recheck clock expiry.
   If not current, deny; if owner unavailable, report a technical failure.
6. Only after the positive proof and latest recheck call the M2 internal
   `_issue_verified_outcome` helper, which binds the verification to the
   attempt token, context, subject and profile. The M2
   `AuthenticationPolicyGate.final_decision` remains the *sole* authority
   producing `Authenticated`; a missing final rule denies.
7. Any host restrictions on IP, audience, API or workload are checked at
   the **trusted host / final policy boundary**. A client-supplied
   `X-Forwarded-For` or tenant hint must not become effective policy input.

## Explicit failure meanings

- Bad encoding, unknown selector, disabled/revoked/expired/not-yet-valid
  record, false proof, stale version, guard refusal: `RejectedOutcome`.
- Absent store or key-source material, exception in guard/resolver/freshness:
  `ErrorOutcome` with safe code; no principal.
- Ambiguous record, trust mismatch or approved configuration inconsistency:
  `ErrorOutcome(INVALID_TRUST_CONFIGURATION)`.
- `CancelledError` propagates to the caller, not a silent retry.
- A positive internal outcome is not an IAM permission, session or token.

## Security tradeoffs and limitations

- `is_current` is a **host contract**; a test fake or Python type annotation
  cannot prove distributed cache invalidation, linearizability, transaction
  boundaries or revocation immediately after the last check. Production
  readiness requires real-store CAS/version tests and a documented
  consistency/race guarantee on the exact deployed host.
- Missing selectors and incorrect secrets can take observably different
  execution paths. A mandatory guard is necessary but not sufficient against
  enumeration or timing analysis. Uniform HTTP refusals, rate-limit buckets,
  reverse proxy trust and practical timing study belong to PR-07D.
- Requiring expiration is a new conservative M4 rule (candidate ADR), not
  a retroactive claim that all existing design records must expire.
- Default UTC wall clock is not monotonic and is used for validity, not
  computing timeout. The M2 Engine owns the separate monotonic time budget.
- Python-level object privacy is not isolation of malicious trusted adapters.
  Verifier material may be accessed explicitly by an approved in-process
  module; no memory zeroization or secure enclave is claimed.

## Qualification needed before approval

Security tests for malformed/unknown/false-secret inputs, cancelled guard,
outage, disabled/revoked/future/expired, boundary expiry, positive HMAC with
final-deny, cross-tenant, post-HMAC version change, in-flight expiration,
redacted audit and concurrent requests. Real host rate limiting and
source-consistency plus an independent security review remain mandatory.
