# M3 Password Authenticator - Design Learning Card

- Milestone: M3 / PR-06B+06C / WP27-020..022
- Status: IMPLEMENTATION CANDIDATE / NOT QUALIFIED
- ADR: 0011, 0012

## Problem first
M2 can produce a positive result using an in-test fake. A real password verification must show that submitted bytes match a *trusted, scoped and current* salted verifier, with no bypass of the M2 final policy.

## Invariant before API
`Authenticated => Argon2id verified AND record active/current/scoped AND approved profile AND final policy ALLOW`.

## Design pressure
- Memory-hard KDF should never block asyncio or allocate unbounded memory.
- Asynchronous cancellation must not free a resource slot while native work continues.
- Missing user must not reveal the account by a different public result.
- The host owns source-side scope and network rate limits.

## Simplest supported design
A narrow PasswordCredentialResolver port; a synchronous PasswordHashVerifier port; one bounded KDFWorkerPool; a PasswordAuthenticator implementing the existing M2 SPI. Reuse the existing final policy, registry, request and event semantics. Avoid user ORM, password-reset engine and an extra command bus.

## Concepts to practice
Strategy (existing SPI), Ports & Adapters (real substitutable providers), DIP (crypto and persistence from boundary), concurrency/cancellation semantics, fail-closed error mapping and test evidence before security claims.

## Residual risks
No constant-time network behavior guarantee; process-local concurrency only; host callback consistency and rate limiting to qualify; operational cost benchmarks; audit best-effort in M2; PR remains draft until GATE27-04.
