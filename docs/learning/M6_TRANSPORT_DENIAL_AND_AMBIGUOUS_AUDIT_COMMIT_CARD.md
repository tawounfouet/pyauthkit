# M6 Design Learning Card - Audited transport denials and ambiguous commits

Date: 2026-11-06
Status: EXPERIMENTAL / REVIEW REQUIRED

## A precise boundary matters

An HTTP parser or reverse proxy can reject malformed traffic before Python
receives it. A FastAPI handler cannot audit requests it never sees. Within
the admitted handler, however, an unexpected body or framing error can
be handled as a domain-neutral **transport refusal** without attempting
to verify credentials.

## Candidate application contract

`ReceiptedDecisionGateway.reject_untrusted_transport` takes only an
application-created attempt ID, a host-issued entry context and sanitized
method metadata. It writes REJECTED into the same local CAS ledger, validates
the commit receipt, and returns `Rejected` or an `AuthError` when storage
fails. It never returns `Authenticated`.

Do not pass an otherwise valid Authorization header to a verifier when
HTTP framing is invalid; a signed token does not authorize malformed
transport. Do not read an untrusted body to select a scope or key.

## Failure model for cancellation

`asyncio.to_thread` schedules a synchronous SQLite transaction. Cancelling
the awaiter does not terminate the underlying worker. An audit may be
committed after the caller has disconnected. A unique attempt ID plus SQLite
constraint prevents duplicate commit if the same attempt is retried.
This does not create exactly-once HTTP delivery or prove host crash safety.

A separate OS-process test reopens the same local test database, verifies
a receipt committed by the HTTP host and refuses a second transaction for
the same ID. This establishes normal process-boundary persistence only.

## What remains unqualified?

- HTTP parser/ASGI/reverse proxy denials that never enter the handler.
- Durable cross-host ledger identity and tamper-evidence.
- Host-global exclusive access to the decision gateway.
- Cancellation/timeout semantics across an external client, load balancer,
  server crash and concurrent multi-node restart.
- Public `audit_delivery=required` configuration and GATE27-07 sign-off.

Use the narrow evidence in tests, not broad security assertions.
