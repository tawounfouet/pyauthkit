# ADR-0031 - M6 local SQLite audit: persistence is not required delivery

Date: 2026-11-05
Status: PROPOSED / NOT INDEPENDENTLY APPROVED

## Problem before architecture

M2 emits a minimized `AuthenticationEvent` after deriving an authentication
result. The engine catches and suppresses sink failures in best-effort mode.
Using a file-based sink can preserve events across normal restarts, but by
itself cannot guarantee that a successful authentication is accompanied by
durably committed evidence.

## Candidate decision

Introduce the optional `SqliteAuthenticationAuditSink` as a reference
`AuthenticationEventSink`, without changing the M2 API or M6 audit policy.

The host explicitly provisions an access-controlled local SQLite database
once, injects a 32-byte HMAC pseudonymization key and its version identifier,
and selects a bounded event capacity. Every event has only method, outcome,
duration, an independent event ID, UTC timestamp, pseudonymization key ID
and HMAC correlation tag. No raw bearer token, password, API key, subject,
scope, IP address, user-agent, URL or plaintext correlation identifier is
persisted. The HMAC key itself is not stored in SQLite.

A transaction commits before `emit` returns normally. The adapter fails
closed on missing/corrupt state, full capacity, invalid event dimensions,
wrong journal or provisioning collision, without deleting or replacing
historical rows. The backing file is not cryptographically authenticated and
the adapter makes no distributed or tamper-proof storage claim.

## Explicit prohibition on false audit guarantees

Do NOT enable `AuditDeliveryPolicy(mode="required")` based merely on this
adapter. M2's `_emit_event` deliberately swallows failures, so an
`Authenticated` result can be returned while no SQLite record was stored.
The integration suite includes that exact negative proof.

An eventual required-audit contract must define an authenticated durable
receipt, commit-before-positive-response ordering, denial/error on commit
failure, cancellation behavior, concurrency, replay/idempotency rules, and
how records bind to the exact result and request. Cross-system transaction
semantics must be reviewed, not assumed. SQLite-only local storage is
insufficient for distributed audit correctness.

## Tradeoffs and residual risks

- HMAC correlation pseudonyms are linkable while the same key is active.
  Key management, rotation, access rights and privacy retention are host duties.
- Async `to_thread` does not cancel an already executing SQLite transaction;
  if the caller times out after a write was scheduled, commit status can be
  ambiguous to that caller. No exactly-once or deduplication claim follows.
- SQLite file permissions cannot defend against a privileged local attacker
  or unsafe filesystem; post-crash/power-loss guarantees are host-dependent.
- Full storage rejects new events rather than auto-dropping old records,
  but under M2 best-effort this still does not prevent a positive AuthN
  result. Operators need independent monitoring and storage lifecycle.
- Opening an existing DB does not attest its creator or detect malicious
  privileged DB replacement; not intended for a multi-replica audit cluster.

## Evidence and status

`tests/integration/test_m6_audit_sqlite.py` covers local persistence,
pseudonymization, key versioning, capacity, concurrent inserts, corruption,
deletion, no auto-provision and the explicit M2 best-effort failure case.

No independent review, deployed KMS/HSM key handling, power-loss drill,
managed append-only backend or required audit sign-off is complete.
GATE27-07 remains NO-GO.
