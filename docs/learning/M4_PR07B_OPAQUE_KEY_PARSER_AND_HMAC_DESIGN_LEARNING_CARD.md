# M4 PR-07B - Canonical API-key parsing and HMAC proof Design Learning Card

- Date: 2026-11-05
- Status: IMPLEMENTATION CANDIDATE / NOT SECURITY-QUALIFIED
- Work package: WP27-024; proposed tasks WP28-049..051
- Related ADR: ADR-0016 (PROPOSED), ADR-0017 (PROPOSED)

## Problem / trust boundary

An untrusted API key is a bearer secret. A public selector is a lookup hint,
not a proof. The trusted host resolves tenant scope and allowed HMAC key refs;
an adapter tests the **entire decoded secret**. The authenticator and M2 gate
alone may later elevate a positive cryptographic check into a final result.

## Design pressures and choices

- [VALIDATION] A parser must be strict about a 70-byte, single-version,
  canonical URL-safe encoding. Accepting padding/spare-bit aliases would let
  several spellings represent the same bearer and complicate audit/revocation.
- [DDD: Value Object] `ParsedOpaqueApiKey` is a redacted, immutable evidence
  container, **not** a credential entity or an authenticated subject.
- [ARCH: Ports & Adapters] `ApiKeyProtectionKeySource` makes secret storage
  replaceable without leaking KMS/SQL/cloud imports into the core.
- [SECURITY: Cryptographic Domain Separation] HMAC message encodes trusted
  scope, version, selector and full secret with length prefixes.
- [SECURITY: Fail-closed] Immutable scope-to-approved-key-ref policy prevents
  discovery or downgrades from record/client-controlled hints.
- [TEST] An independently computed OpenSSL vector checks the positive proof;
  byte mutations and tenant changes must fail.

## Alternatives rejected or deferred

No Argon2id for randomly generated 256-bit secrets (different threat model
than human passwords); no plaintext storage; no generic CredentialRepository;
no clever hand-written timing comparison; no automatic registration in M2;
no `AuthenticatedPrincipal`, session, token or IAM permission.

## Learning point

Syntax-valid evidence is not verified evidence. A correct HMAC match proves
**only** that the complete secret corresponds to the selected verifier under
the configured protection key. Credential state, revocation freshness, host
policies and AuthN finality are separate decisions and tests.

## Limitations and evidence

In-process Python offers no guaranteed zeroization or sandbox isolation.
`hmac.compare_digest` on fixed-length values is not a guarantee of uniform
HTTP timing or protection against enumeration. Real KMS/Vault authorization
and distributed cache freshness still require deployed-host qualification.
A green PR-07B CI is not M4 GO, ADR approval or production readiness.
