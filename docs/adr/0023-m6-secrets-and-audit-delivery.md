# ADR-0023: M6 secret references and honest audit delivery

Status: PROPOSED (review required)
Date: 2026-11-05

## Problem
Configuration must refer to secrets without storing material. A successful
audit sink call is not proof of persistent storage, and a plain `required`
switch cannot change the existing M2 best-effort contract.

## Decision candidate
Use typed `SecretRef(provider, namespace, key_id, version, purpose)`.
Authorize each resolution against a host-owned grant and the active snapshot.
Reject missing/revoked/out-of-scope secrets with sanitized errors; do not
log provider exception details or fall back to environment variables.

Retain the M2 event projection and non-durable sink contract. Wrap submissions
in a finite timeout, preserve cancellation. Only `best_effort` is admitted.
Refuse `required` until a separately tested durable committer and post-commit
AuthN outcome semantics exist.

## Consequences
No false claim of durable audit and no implicit secret consumer. The initial
composition implementation rejects snapshots containing secret references
rather than activating an unwired consumer. In-process `bytes` cannot be
reliably zeroized by Python. Consumer wiring, host-backed ledgers, and outbox
are explicitly subsequent work.

## Test oracles
M6-T16/T17/T18/T19/T20/T21/T22/T23/T27/T28/T29/T30/T32.
