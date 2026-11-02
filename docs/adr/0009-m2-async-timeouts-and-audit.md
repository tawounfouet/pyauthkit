# ADR-0009 - Async cancellation, monotone budget and audit delivery

- Status: ACCEPTED FOR M2 DESIGN; operating guarantees pending CI
- Date: 2026-11-02
- Related: ADR28-018, specification 21, specification 25

## Problem
A hung verifier, retry, cancellation or failing event sink can convert a blocked authentication into a latent success or expose credentials in logs.

## Decision
`AuthenticationEngine.authenticate` is async-first and awaits one selected verifier with an explicit finite monotonic time budget enforced using `asyncio.timeout`. A deadline is local to the attempt and must not use UTC business time to measure execution. `asyncio.CancelledError` propagates; never catch `BaseException` to mask cancellation. A timeout is returned as a technical failure without principal. No automatic retry or fallback verifier is allowed.

Audit events use a minimal redacted port and only known-safe enumerations, correlation and method identifiers. No payloads, unfiltered claims, subject IDs, exception reprs, JWTs or secret sources enter audit. For M2 the default audit sink is optional *best effort* with bounded synchronous projection of the final status; a failure does not change the authentication decision. A deployment requiring durable/mandatory audit is explicitly NOT QUALIFIED by this M2 port and MUST fail startup or supply a stronger audited composition contract before that requirement is claimed.

## Consequences
Failures of async verifier are mapped to stable `AuthError` codes; cancellation stays a caller concern. Audit delivery success is not assumed durable. A time source can be injected for deterministic event timestamp tests; budget enforcement remains monotonic.

## Tests
M2-T14/T15/T16/T18/T21, including a verifier that blocks, a verifier that raises, an event sink that raises, redaction tests, task-cancellation propagation and no success after timeout. No token/session issuance or retry engine in M2.
