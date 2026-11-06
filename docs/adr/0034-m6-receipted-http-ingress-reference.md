# ADR-0034 - M6 HTTP-only reference ingress for receipted decisions

Date: 2026-11-06
Status: PROPOSED / EXPERIMENTAL / NOT INDEPENDENTLY APPROVED

## Context

ADR-0032 adds a receipt-bearing decision gateway and ADR-0033 connects it
to real M4 HMAC and M5 RS256 verification. That still leaves a major bypass
hazard: an application could invoke M2 directly or expose another route
that sends positive decisions without waiting for a durable audit receipt.

## Candidate design

Build a **qualification-only**, single-entrypoint FastAPI host. A trusted
host chooses exactly one gateway, one `HostTrustCatalog` entry and one
`EvidenceMethod` before serving requests. The HTTP route is fixed:
`POST /authenticate`. No direct M2 engine or alternate route is
registered. OpenAPI, Swagger and ReDoc are disabled.

The only accepted proof input is one bounded Authorization header, with
a fixed ApiKey or Bearer scheme. Invalid proof syntax becomes a rejected
candidate handled by the real gateway. The server generates fresh random
128-bit attempt IDs and correlation IDs; user headers for audit attempt,
tenant, profile, issuer, peer, proxy or trace do not select authority.

A positive response contains only `{"status":"authenticated"}` after the
gateway validates an attempt-bound local receipt. Rejections return a
constant 401 body; technical audit errors return constant 503. Set
no-store, no-cache, nosniff and no-referrer headers; never emit sessions,
subject IDs, SQL errors or credentials in HTTP bodies.

## Explicitly unsolved

- HTTP framing refusals such as bodies and ambiguous Content-Length are
  denied before the gateway. They lack a committed decision record.
  Therefore this reference **does not satisfy full-attempt required audit**.
- Python closure privacy and private fields cannot prevent a privileged
  application from creating or exposing a different M2 engine. Isolation
  of all framework routes, middleware, sidecar access and load balancer
  paths must be separately enforced and independently reviewed.
- Tests use plain localhost HTTP. TLS termination, reverse proxies,
  network peers, DoS budgets, request-size enforcement before parsing,
  external log redaction, event-loop/backpressure behavior and deployment
  routing are not qualified.
- Client disconnect does not guarantee cancellation of a running server
  task or an in-flight SQLite worker transaction. A late commit may exist
  without a delivered HTTP 200; no exactly-once claim follows.
- SQLite is not an independent tamper-resistant audit authority. There is
  no distributed lease, authenticated ledger or multi-replica fencing.
- Public configuration mode `audit_delivery=required` is still refused.

## Qualification and result

`qualification/m6_http/tests/test_receipted_http.py` exercises real TCP
loopback via Uvicorn/HTTPX with actual M4 HMAC and M5 RS256 verification,
server-bound route selection, bypass attempts, credential rejection,
storage outage, concurrency and held SQL write locks.

An additional CI job keeps FastAPI/Uvicorn/HTTPX out of the PyAuthKit
runtime dependency surface. This proposal is NOT a production HTTP SDK,
not a ratified mandatory-audit design and not evidence of GATE27-07 PASS.
