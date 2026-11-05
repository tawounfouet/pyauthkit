# M4 PR-07A - Source-scoped API Key Record and Resolver Design Learning Card

- Date: 2026-11-05
- Status: DESIGN + IMPLEMENTATION CANDIDATE; NOT SECURITY-QUALIFIED
- Work package: WP27-023; proposed tasks WP28-045..048
- Related ADR: ADR-0017 (PROPOSED); M4 plan 2026-11-05

## Problem and trust boundary

A caller can present a key identifier and claim a tenant, but neither
is an authentication proof. The trusted host chooses the scope. The
credential owner supplies a scoped record for a future full-secret verifier.
The M2 policy gate remains the sole final authentication decision authority.

## Model and justification

- [DDD: Value Object] `ApiKeyCredentialRef` syntax-validates a lookup hint,
  without trusting it.
- [DDD: Read Model] `ApiKeyVerifierRecord` is an immutable record projection
  with bounded identity/crypto metadata, redacted repr and no lifecycle writes.
- [ARCH: Hexagonal / DIP / ISP] `ApiKeyCredentialResolver` is a small async
  port with source-scoped lookup and a separate authoritative freshness check.
- [ARCH: Adapter] `HostCallbackApiKeyResolver` accepts explicit host
  callbacks. It rejects foreign-scope and mismatched-selector records.
- [TEST: Contract] The test-only in-memory adapter proves namespace isolation
  for its own dictionary, NOT isolation of an actual SQL query.

## Alternatives and tradeoffs

Global lookup + Python filtering is not accepted because the wrong source
could already reveal metadata. A generic repository and a shared Password
credential abstraction are deferred until a second proven use case. The
absence of an API-key authenticator in PR-07A prevents fake verification from
being mistaken for authenticated identity.

## Security oracles and limitations

This PR establishes preparatory evidence for M4-T05, T06, T11, T12, T16,
T29, T37, not the complete oracles, nor an M4 gate approval. Unknown
algorithms remain unapproved: cryptographic verification belongs to PR-07B.
No protection against privileged malicious in-process Python is claimed.
Revocation consistency is an external system guarantee to qualify later.

## Transfer of learning

A value object can validate *syntax* without asserting trust; a read model can
expose record metadata without owning its lifecycle; a port can require
tenant-scoped inputs but cannot prove how a remote adapter implements SQL.
Tests must cover the boundary crossing, not merely a green class constructor.
