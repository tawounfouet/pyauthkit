# M6 Design Learning Card - Host-bound HTTP receipt ingress

Date: 2026-11-06
Status: EXPERIMENTAL QUALIFICATION CANDIDATE

## Architectural question

How can an HTTP endpoint reuse a complete M2/M4/M5 authentication pipeline
but avoid returning success before an audit commit?

## Patterns and boundaries

- [Ports & Adapters] The HTTP layer is a host adapter, not a verifier or
  tenant resolver. Its sole authentication dependency is
  `ReceiptedDecisionGateway`.
- [DDD / Trust Boundary] Host route and evidence method are selected at
  bootstrap. HTTP headers and token claims are untrusted credential data.
  They cannot choose tenant, profile, keyset, or audit store.
- [Explicit Dependency] No arbitrary authenticators or M2 runtimes may be
  supplied to the HTTP adapter. It accepts only the exact candidate gateway.
- [Fail Closed] No receipt means no HTTP 200. Missing/full/locked ledger
  blocks or delays the response; wrong evidence gives a generic 401.
- [Separation of Concerns] The standalone qualification app does not
  become a security sandbox for the host process. TLS, reverse proxy
  route policy, distributed storage and full-attempt recording are external.

## Negative proof still needed

The early framing path rejects nonempty HTTP bodies before the gateway,
so not every network attempt produces a receipt. A production required
audit contract must define whether and when such pre-verification rejections
are durably recorded. Server disconnects and late SQLite worker commits
also need independently qualified recovery semantics.

## Tests

Loopback TCP/Uvicorn/HTTPX, actual signed RS256 JWT and scoped HMAC,
spoofed user header denial of authority selection, direct-route probes,
no plaintext response, SQLite missing/full store and a held write lock.

These tests demonstrate **one reference app surface**, not the absence of
all possible bypasses in a separate host. See ADR-0034.
