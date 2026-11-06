# ADR-0029 - M6 optional local persistent generation ledger

Date: 2026-11-05
Status: PROPOSED / REVIEW REQUIRED

## Problem

The existing M6 bootstrap checks a host-supplied integer generation floor.
If the host loses this integer during restart, it might accept an older trust
profile and revive previously revoked HMAC keys or disallowed JWT issuers.
A plain in-memory value is not a recoverable monotonic authority.

## Candidate decision

Introduce a small `GenerationFloorLedger` port with strict read and atomic
compare-and-advance operations. Do not make it a hidden global dependency.
A reference SQLite adapter supports explicit administrator provisioning to a
file that must already be present for any normal read; it uses SQLite's
BEGIN IMMEDIATE, a one-row constrained generation table, a monotonic CAS,
rollback journaling and synchronous EXTRA setting.

Host-side `prepare_with_generation_ledger` composes a candidate against
the read floor, checks that the returned runtime is for the exact supplied
snapshot, then commits the new floor before returning the runtime. Failed
preflight or conflicting concurrent updates are fail-closed. An async
variant supports secret-backed M4 bootstrap. No engine is modified in place.

## Excluded security claims

SQLite is not a trusted or cryptographically authenticated ledger if an
attacker can modify or replace its file or directory. SQLite is not a
distributed consistency service and should not be put on NFS for this use.
This adapter does not provide arbitrary power-loss guarantees, guaranteed
fsync on every filesystem, rotation orchestration, leader election,
distributed host fencing, or proof that a deployment router has switched
traffic. The host must independently secure the database, config source,
process, storage and activation path. Cancellation after a synchronous
commit boundary cannot reverse the persisted CAS.

In a multi-node deployment the host must provide a genuine authoritative
remote CAS/consensus-backed ledger with appropriate fencing and independent
fault tests. The project must never infer a default generation when the
ledger is absent.

## Alternatives rejected

Implicit create-on-read with default floor 1, unguarded environment variable
floor, writing a non-transactional JSON counter, silent rollback after
partial activation and treating SQLite as consensus.

## Evidence and status

`tests/integration/test_m6_generation_sqlite.py` proves limited local
persistence, re-opened connections, stale-generation denial, race/conflict
handling, corruption failures and no-commit-on-preflight failure.

GATE27-07 remains NO-GO; the adapter is an optional reference and is
not yet accepted for production security.
