# M6 Design Learning Card - Persisted event vs required security audit

Date: 2026-11-05
Status: DEVELOPMENT CANDIDATE / NOT INDEPENDENTLY QUALIFIED

## Problem

A security event can be stored in SQLite and still fail to meet a policy that
requires a durable record before a successful login. In M2, the audit sink
runs after the authentication decision and its failures are swallowed.

## Design boundary

The `AuthenticationEventSink` port is an optional notification path, not a
transactional audit commit interface. A `SqliteAuthenticationAuditSink`
adapter can provide local committed persistence but not change that fact.
`AuditDeliveryPolicy(required)` must continue to fail at configuration time.

## Concepts and patterns

- DDD / immutable Value Objects: a bounded sanitized
  `AuthenticationEvent` is separated from any presented credential.
- Ports & Adapters: the SQLite store is a replaceable sink, not part of
  the authentication domain or an authorization decision.
- Security by construction: explicit database provisioning, bounded capacity,
  separate HMAC correlation pseudonyms, key versioning, no raw identifiers.
- Failure semantics: `best_effort` may lose audit on failure. A
  commit-before-success boundary requires a new contract, not a renamed flag.

## Alternatives rejected

Raw correlation IDs, JWT claims or API keys in SQL rows; automatic file
recreation after corruption; deleting old security records when capacity is
full; treating SQLite's transaction as a distributed outbox; silently
changing M2 response semantics; and declaring an untested exactly-once or
immutable audit guarantee.

## Evidence

Local reopen, concurrent append, storage failure, full capacity and two
versions of a host-held HMAC key are covered by synthetic tests. A separate
M2 integration test deliberately confirms that `Authenticated` remains
possible when the best-effort SQLite store is unavailable, preventing any
incorrect claim that the adapter already enforces required audit.

Further work: define a receipt-bearing required-audit application boundary
and qualify it independently against failure injection, cancellation,
replay, host crash, and actual storage durability.
