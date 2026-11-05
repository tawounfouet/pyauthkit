# ADR-0017 - M4 source-scoped API key record resolution and credential ownership

- Status: **PROPOSED / NOT ACCEPTED** (security and maintainer review required)
- Date: 2026-11-05
- Milestone: M4 / PR-07A / WP27-023 / proposed tasks WP28-045..048
- Related: ADR27-012, ADR27-013; specifications 07, 10, 18, 19, 20, 23, 25 and M4 plan version 1.0

## Problem first

An API-key selector or readable prefix is not a possession proof. A global
lookup can select a credential from another tenant; duplicate identifiers can
silently select the wrong subject; an adapter may return another scope, leak a
sensitive digest through generic serialization, or treat a store outage as
absence. Credential lifecycle and version authority can belong to a host/IAM
system rather than the PyAuthKit library.

## Decision candidate

1. Model `ApiKeyVerifierRecord` as a read-only, redacted projection, **not**
   an aggregate that issues, rotates or revokes credentials.
2. Use `TrustedScopeRef` and `ScopedSubjectRef` from M1/M2, with an exact
   match before any verification. Include issuer, non-human principal type,
   bounded selector, verifier digest, algorithm label, key reference,
   lifecycle state, UTC validity window and authoritative version.
3. Model a four-way lookup: `ApiKeyFound`, `ApiKeyMissing`,
   `ApiKeyAmbiguous`, `ApiKeyUnavailable`. Found is not verified;
   ambiguous/unavailable never become a substitute record.
4. Require `resolve(scope_ref=..., key_id=...)` and an explicit
   `is_current(record=...)` port. Host callbacks receive both scope and
   selector, and must restrict their query **at the authoritative source**.
   A returned foreign record is rejected again as defense-in-depth.
5. Put an in-memory fake in tests only, not the library wheel. Do not add
   any default credential store, crypto verifier, authenticator or automatic
   registry admission in PR-07A.
6. Keep the API key format, HMAC key source, digest algorithm acceptance,
   refresh and consistency policy **open** until ADR-0016/0018. The read
   model's structural validation is not approval of its verifier algorithm.

## Alternatives considered

- Global lookup with post-query Python filtering: rejected, violates
  source-scoped isolation and may leak cross-tenant metadata.
- Raise an exception for all missing credentials: rejected, loses a typed
  normal absence distinction and encourages accidental exception leakage.
- Generic CredentialRepository shared with Password: deferred (YAGNI).
- Dataclass for a sensitive record: rejected for generic asdict/deepcopy risk.
- Implement issuance and rotation in the authentication library: deferred,
  lifecycle owner must be identified before exposing mutations.

## Failure semantics and limits

A missing candidate is ordinary absence, an ambiguous result is an integrity
failure, and an unavailable result is a technical/source failure. PR-07A
cannot by itself map these to public M2 results: that belongs to PR-07C.
Callback exceptions deliberately propagate to the future Engine's safe error
mapping; they are not normalized into Authenticated or a permissive cache hit.
`is_current` is a contract hook, not proof of distributed revocation
immediacy. The test-only fake proves no PostgreSQL/Redis behavior.

The domain is Python-level immutable, not a sandbox against privileged code.
Direct property access still exposes sensitive verifier material to a trusted
verifier and adapter. No bearer secret is persisted or compared in PR-07A.

## Tests and evidence before claim

- Contract: same selector in two scopes, unknown, ambiguous, unavailable,
  callback mis-scope/mis-selector, invalid callback outcome and freshness.
- Model: type/size, UTC instants, immutable/read-only, redacted repr and
  prohibited generic copy/serialization, no human principal auto-mapping.
- Architecture: `domain` imports no `ports`, adapter is optional; core
  has no mandatory framework, database or cryptography dependency.
- Evidence required: exact commit SHA + CI jobs + independent security review.
  **Documented design is not a qualified authenticator or a GO for M4.**
