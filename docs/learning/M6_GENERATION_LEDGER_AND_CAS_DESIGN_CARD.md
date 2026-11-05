# M6 Design Learning Card - Preparing a runtime before committing its generation

Date: 2026-11-05
Status: DEVELOPMENT CANDIDATE / NOT QUALIFIED

## Problem and trust boundary

A valid but old configuration can authenticate subjects that newer policy
revoked. Checking against an in-memory integer does not survive restarts.
The host must supply a trusted durable and monotonic generation authority,
then coordinate readiness, generation promotion and traffic activation.

## Pattern and sequencing

The `GenerationFloorLedger` port isolates storage (Dependency Inversion,
Ports & Adapters). A transactionally updated SQLite adapter is a reference
implementation of compare-and-swap (CAS), not an authentication server.
The `prepare_with_generation_ledger` orchestration uses **Prepare ->
Verify Candidate -> Compare-and-Advance -> Return**. No new engine
is handed to the host if readiness or CAS fails. The host must still
activate the returned generation, and drain old requests independently.

## Failure examples

- Old config G1 after G2 committed: reject at the initial floor check.
- Missing/corrupt ledger: reject; never invent G1.
- Two requests prepared at floor G1: one CAS succeeds, the other must fail.
- Candidate with an unapproved secret: fail before CAS, preserve floor.
- Crash after CAS but before routing switch: restart G2; G1 remains blocked.

## Critical learning boundary

A local database is durable across ordinary process restart but is NOT
tamper-proof and cannot implement a distributed leader lease or fencing.
A security claim should state what failure model was actually tested, not
what the word "durable" might suggest. See ADR-0029 and the test suite.
