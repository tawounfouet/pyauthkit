# PR-09 - M6 Configuration, Secrets and Minimal Audit

Status: IN PROGRESS / DEVELOPMENT BRANCH, not qualified.
Date: 2026-11-05.
Base commit: `edeef0288ed9560324bac6f065a4d06057d5faeb`.
Branch: `feat/m6-config-secrets-audit-pr09`.

## Scope delivered as development code

- WP27-033: explicit host mapping with host-owned provenance allowlist. No environment
  discovery, no merge of security-critical fields, unknown keys always rejected.
- WP27-034: typed, deeply immutable snapshot (tuple/frozenset constituents),
  generation and source admission; explicit composition with M2 catalog, M2 gate,
  M2 engine and frozen authenticator registry. Missing authenticator means no start.
- WP27-035: `SecretRef`, purpose-and-namespace-granted asynchronous resolver,
  sanitized failure, synthetic-only in-memory adapter. Material does not enter
  `ConfigurationSnapshot`. A configured reference **blocks engine composition**
  until an approved consumer integration is actually built and verified.
- WP27-036/037: preserve M2 `AuthenticationEvent` and `AuthenticationEventSink`,
  add bounded best-effort adapter and non-durable memory sink. `required` mode
  is **rejected**, not simulated. Cancellation propagates.
- WP27-038: explicit generation floor at bootstrap. A durable, authenticated
  external generation ledger is the responsibility of the host. Without it,
  crash-safe anti-rollback across restarts is NOT guaranteed.

## Security and API limits

This is an internal, provisional composition API. No stable public SDK exports,
no Vault/KMS adapter, no durable audit, no hot reload, no cryptographic
qualification, and no deployment approval are claimed. The synthetic verifier in
tests does **not** perform real JWT verification. The existing M5 verifiers remain
the responsibility of the M5 security gate.

## Verification checklist

- [ ] CI at exact PR head SHA
- [ ] Ruff
- [ ] mypy strict
- [ ] M6 source, snapshot, secret, audit and rotation negative tests
- [ ] M2/M4/M5 regression
- [ ] packaging smoke and architecture fitness
- [ ] GATE27-07 independent review
- [ ] M5 GATE27-06 remains NO-GO
- [ ] Release/publication remain unauthorized

## Design learning

Problem: external operational inputs can widen trust or leak secret material.
Trust boundary: the Python host asserts source and scope authority, NOT the
source file nor the caller's JWT/header. Pattern: simple typed values, a strict
reader and ports only where an actual adapter varies. Alternatives rejected:
automatic discovery, dict union for trust blocks, secret string interpolation,
undocumented durable-audit claim, and a mutable engine registry.
