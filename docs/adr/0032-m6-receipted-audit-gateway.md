# ADR-0032 - Experimental M6 receipt-bearing audit gateway

Date: 2026-11-05
Status: PROPOSED / NOT APPROVED / NOT PRODUCTION QUALIFIED

## Context

M2 intentionally emits an optional audit event after computing AuthN and
swallows failures. ADR-0031 proved that persisting this event to a local
SQLite file is insufficient to enforce mandatory audit. We need a separate
application protocol for **commit-before-positive-response** without
silently changing legacy best-effort behavior.

## Candidate design

A host-generated 128-bit `AuditAttemptId` uniquely identifies one execution,
not a user, tenant or credential. A `AuditDecisionRecord` binds this ID to
the M2 outcome, method, correlation reference, approved scope/profile and, on
success only, the verified subject and principal type. The committer converts
these values into an HMAC-SHA256 decision tag, stores only the random attempt
ID, random receipt ID, key version, outcome, method, elapsed duration and
tag, and commits a SQLite transaction before returning a receipt.

The experimental `ReceiptedDecisionGateway` composes an ordinary M2
engine with **no best-effort sink**, computes a decision through the existing
policy gate, then waits for a trusted committer receipt. It returns
`Authenticated` only after validating the receipt's attempt ID and outcome.
If the store is unavailable, full, malformed or rejects the attempt, or if
a committer returns a wrong receipt, the gateway returns an AuthError and
never a positive result. A duplicate ID cannot reissue an old receipt.

The reference factory admits only the exact local SQLite committer; a
host-injected malicious committer must not be treated as accepted production
evidence. Test-only fake committers exercise the gateway's internal error and
delay behavior outside the approved factory.

## Crucial limitations

- This is NOT `AuditDeliveryPolicy(mode="required")`. The M6 config reader
  continues to reject that mode for all currently supported schemas.
- The gateway is opt-in and experimental. A host that exposes the underlying
  M2 engine directly can bypass it; Python process-private attributes are
  not a security sandbox. Non-bypassable framework integration is future work.
- The HMAC tag protects field minimization but does not attest an untrusted
  SQLite file. A privileged host attacker may rewrite or replace the file.
  The signing key belongs in a trusted external provider, not source code.
- Cancellation of `asyncio.to_thread` cannot terminate a running SQLite
  transaction. A write may commit after a caller has been cancelled, but
  no positive result is returned by the cancelled coroutine. A later retry
  with the same attempt ID must fail; no exactly-once transport guarantee.
- Host generation, verifier readiness, cluster routing, network partition,
  storage full, power outage, idempotency policy and independent review must
  be resolved before production required-audit semantics can be enabled.

## Next steps before GATE27-07

Define a deployment-enforced single required-audit entrypoint, integrate
the real M4/M5 specialized bootstraps without exposing an unguarded positive
path, validate durable store identity and generation fencing, test crash and
in-flight ambiguity with independent execution, decide retry behavior, and
obtain security reviewer sign-off.

Unit/integration candidate tests are in
`tests/integration/test_m6_receipted_audit_gateway.py`.
