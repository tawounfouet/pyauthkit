# M3 Password Resolver - Design Learning Card

**Status:** PROPOSED / NOT QUALIFIED. **WP:** WP27-019. **ADR:** 0010.

## Problem
A global `find_user(login)` may return a valid hash from the wrong tenant; a cryptographic match would then authenticate the wrong subject.

## Trust boundary and invariant
Caller-controlled `ClaimedIdentity` is only a lookup hint. The host-approved `TrustedScopeRef` must constrain the source-side query. Every returned record must also have a matching `scope_ref` and `subject_ref.scope_ref`.

## Design pressure and minimal solution
One narrow async `PasswordCredentialResolver` Protocol, immutable verifier projections, and typed lookup outcomes. Ports and Adapters apply because host stores vary; DDD does not require a new User aggregate.

## Negative evidence
Missing, ambiguous, cross-tenant, disabled and unavailable records cannot create `VerifiedOutcome`. M3 cryptographic integration and the final gate are required before any genuine authentication claim.

## Concepts practiced
DIP; Hexagonal Architecture; DDD read model versus Entity; immutability limitations in Python; test contract shared by adapters; information-flow redaction.

## Tradeoff
`is_current` on an in-memory snapshot is not an authoritative distributed revocation guarantee; production adapter tests must state consistency and freshness guarantees.
