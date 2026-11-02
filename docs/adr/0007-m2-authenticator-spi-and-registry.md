# ADR-0007 - Minimal async Authenticator SPI and frozen registry

- Status: ACCEPTED FOR M2 DESIGN (tests and code evidence separate)
- Date: 2026-11-02
- Related: ADR27-007, ADR27-008, ADR28-013, ADR28-015, ADR28-016

## Context
Different authenticators will eventually verify Password, API Key, and JWT, but the engine must not import provider, framework, database or cryptographic implementations. A verifier cannot decide the final authentication status.

## Decision
Define a small Python `Protocol`: an approved authenticator declares one `EvidenceMethod` and an asynchronous `verify(request, context)` returning a discriminated internal outcome. The engine is async-first; a synchronous facade, if needed, is a separate future decision. A frozen `AuthenticatorRegistry` contains exactly the explicitly admitted implementations at bootstrap. The registry builder rejects duplicates and incorrect method contracts, supports a one-way freeze, and never loads Python entry points or scans installed plugins. Resolution is exact by method with no fallback.

The selected authenticator is an explicitly trusted in-process adapter. The engine validates the return type, attempt linkage, method, scope and trust-profile version *before* the final gate. Authentication failures, verifier exceptions and unknown methods cannot become success.

## Alternatives
- An engine-level `if method == password` cascade would require core changes and couple cryptographic implementations.
- Abstract factory hierarchies are unwarranted while a `Protocol` and explicit wiring suffice.
- Dynamic discovery or `last-wins` plugin registration would silently alter trust.

## Proof obligations
M2-T06/T07/T08/T09/T10/T11/T17/T20/T22/T23 and shared contract tests. No fake authenticator may ship inside a production wheel or be registered by an implicit default. In-process approved adapters still require their own later cryptographic qualification in M3/M4/M5.
