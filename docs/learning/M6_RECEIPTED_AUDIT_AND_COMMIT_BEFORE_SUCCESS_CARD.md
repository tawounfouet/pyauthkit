# M6 Design Learning - Commit before a positive authentication result

Date: 2026-11-05
Status: EXPERIMENTAL / NOT G7 QUALIFIED

## Problem

An audit writer can be durable yet untrustworthy as a required-audit path
when its caller ignores storage errors. The actual security property
concerns the *ordering of observable effects*:
verify -> persist decision -> validate receipt -> return positive.

## Model and patterns

- [DDD Value Object] `AuditAttemptId` is an opaque, host-generated
  128-bit random ID, not a JWT or a correlation alias. It must be unique
  per execution; duplicate IDs are technical failures, never replayed
  positive results.
- [DIP / Ports & Adapters] `RequiredAuditCommitter` expresses the necessary
  commit receipt; `SqliteRequiredAuditCommitter` is a bounded local adapter,
  not a security guarantee about managed storage.
- [Application Service] `ReceiptedDecisionGateway` delegates M2 verification
  and final policy, commits a signed minimization of the result, and
  releases a positive response only after receipt validation.
- [Fail closed] Commit exceptions and invalid receipts turn into a safe
  dependency error. Cancellation propagates without returning positive.

## What remains unsolved

The M6 public config still refuses `required`, and the gateway is an
experimental integration sketch only. The host could bypass the gateway,
the local database can be replaced by a privileged process, and a cancelled
thread may still write later. Exactly-once, independent durable evidence,
distributed fan-out, power-loss and credential-provider integration require
separate authorization and tests.

## Synthetic tests

The suite demonstrates positive-after-commit, error-before-positive on
file loss and full store, replay rejection across reopen, concurrent CAS
and fake delayed/forged receipt handling. The synthetic verifier is NOT
cryptographic proof of a valid password, JWT or API key.
