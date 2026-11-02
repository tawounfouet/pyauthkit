# ADR-0010: Scoped Password Resolver and Credential Ownership

- Date: 2026-11-02
- Status: PROPOSED (review required)
- Milestone: M3 / PR-06A / WP27-019
- Entry baseline: M2 `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`

## Problem and trust boundary

The username is untrusted. A host-approved `TrustedScopeRef` must be passed as an explicit parameter to an authoritative credential source. No global lookup followed by an application-level tenant check is acceptable.

## Decision candidate

Use a narrow asynchronous `PasswordCredentialResolver` port, returning explicit `Found | Missing | Ambiguous | Unavailable` results and a scoped `PasswordVerifierRecord` projection. The host or an external IAM owns its persistence. A post-KDF `is_current` callback is a freshness check whose guarantees must be qualified for each backend. The in-memory implementation is for tests only.

## Alternatives

A generic UserRepository forces unwanted IAM/store ownership. A global username lookup creates cross-tenant risk. A mutable dataclass makes accidental leakage through generic serialization easier. These alternatives are rejected for M3.

## Consequences and evidence

No ORM, table, session, password reset or rehash write is introduced. Sensitive hashes are deliberately redacted in repr and cannot be serialized by dataclasses.asdict. Scoped contract tests exercise an in-memory and a host-callback adapter. Distributed revocation/consistency still require backend qualification. Neither the existence of a type nor passing unit tests proves trust in arbitrary host code.

## Learning transfer

Problem First -> provenance of credential -> scope invariant -> narrow Protocol -> failing cross-tenant test -> implementation -> independent review.
