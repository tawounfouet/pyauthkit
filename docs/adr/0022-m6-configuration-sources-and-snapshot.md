# ADR-0022: M6 host-controlled configuration and immutable snapshot

Status: PROPOSED (review required)
Date: 2026-11-05

## Problem
A valid JSON-like dictionary is not a trusted policy. M6 must prevent
unapproved source precedence, mixed-scope bindings, and in-flight reconfiguration.

## Decision candidate
Accept exactly one explicitly passed host mapping under a separate, host-owned
`SourcePolicy` and `SourceProvenance`. Reject unknown keys and ambiguous
bindings. Convert the structure into a typed immutable snapshot. Create fresh
M2 policy/catalog/registry/engine instances for the approved generation.

No import of environment sources, no ad-hoc file loading or HTTP-derived
provenance, no in-process hot-reload. Keep the current AuthN/AuthZ boundary.

## Consequences
Simpler deterministic bootstrap and narrow API. No secret value in snapshot.
Additional sources and per-field precedence require separate ADR/tests. A
generation integer is only a policy identifier; anti-rollback across crashes
requires a trusted external source of truth.

## Test oracles
M6-T01/T02/T04/T05/T07/T08/T10/T13/T14/T34/T35/T36.
