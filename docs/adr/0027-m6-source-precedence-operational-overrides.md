# ADR-0027 - M6 source precedence is field-specific, not dictionary merge

Date: 2026-11-05
Status: PROPOSED / NOT APPROVED

## Problem

A second source can silently widen authentication trust by overriding a
profile issuer, algorithm, secret reference or tenant binding. An ordinary
dictionary merge can create a policy that no operator ever approved.

## Candidate decision

One complete authoritative M6 source defines all security-bearing properties.
A host-controlled `SourceLayerPolicy` specifies an exact, unique, ordered
chain of operational sources, checked separately against `SourcePolicy`.
Only `timeout_seconds` is eligible for override, in the validated M6 range.
Precedence is explicit low-to-high; no missing or unapproved layer is skipped.
Malformed or unknown fields fail closed. The immutable snapshot records its
base source and the ordered approved operational source provenance.

The v1/v2 schema and tenant/JWT trust blocks are not deep-merged. A future
atomic trust-profile replacement requires a separate ADR, change approval
and cross-field tests; no permissive compatibility fallback is inferred.

## Tradeoffs and tests

This adds a narrow operational convenience while refusing the broader
functionality of deployment-config overlays for JWT/tenant/plugin policies.
Testing covers ordering, source denial, missing layers, forbidden security
keys, invalid timeout and mutation after bootstrap. See
`tests/security/test_m6_source_precedence.py`.

No network/file/env retrieval is added. A host must independently establish
the authenticity of each `SourceProvenance`; this policy does not sign source
manifests or provide cluster-wide anti-rollback. GATE27-07 remains NO-GO.
