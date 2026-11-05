# ADR-0016 - M4 opaque API-key format, HMAC-SHA-256 and protection-key authority

- Status: **PROPOSED / NOT ACCEPTED** (owner + independent security review required)
- Date: 2026-11-05
- Milestone: M4 / PR-07B / WP27-024 / proposed tasks WP28-049..051
- Scope: candidate wire format, verifier, key reference. **No issuance API or final AuthN**
- References: M4 implementation plan v1.0 sections 9, 10, 18, 19 and 23; specifications 07, 10, 18, 19, 20, 21, 25

## Problem first

An untrusted API-key selector, readable prefix or HTTP tenant header does not
establish possession of a bearer secret. Reuse of a secret digest from another
tenant, permissive base64 decoding, implicit fallback to a retired key, naive
comparison or loading a key from a client-controlled reference can all turn a
wrong credential into a plausible proof.

## Candidate decision (implementation PR-07B)

1. A single initial protocol version `ak1`, with wire representation:
   `ak1.<22-char-unpadded-base64url-selector>.<43-char-unpadded-base64url-secret>`.
   This yields exactly 70 ASCII bytes, representing **16 selector bytes** and
   **32 random secret bytes**. Generation belongs to a known credential owner;
   no issuance API is included in this pull request.
2. Parser operates on `bytes`, uses an anchored ASCII allow-list and checks
   round-trip canonical encoding. Any padding, unknown version, truncated
   field, whitespace, Unicode, extra separator or noncanonical spare bits
   are rejected *before store lookup*. The parser is structural **only**.
3. `HmacApiKeyVerifier` implements a **cryptographic boolean only**.
   `ApiKeyAuthenticator` and public `Authenticated` are not shipped in PR-07B.
   Record status, UTC expiry, revocation `is_current` and final M2 policy
   remain obligations of PR-07C.
4. The server-key source is an async, host-injected port. Each attempt passes
   a **host-approved scope** and a record `protection_key_ref`. An immutable
   bootstrap mapping defines which key references are approved **per scope**.
   Unknown algorithm, unapproved reference, missing material or malformed
   source response yields **no success and no fallback**. Key-source outage
   must never silently accept another key.
5. Use exactly 32 bytes of key material for the HMAC protection key. The
   owner must generate it using a CSPRNG and store it in an approved secret
   manager, KMS-backed adapter or equivalently controlled host storage.
   Neither production secrets nor fallback keys are checked into the repo.
6. The HMAC-SHA-256 message is **byte-framed and domain-separated**:
   `b"pyauthkit-api-key-v1\\x00"` followed by four 4-byte big-endian
   length-prefixed values **in this order**: `trusted scope ASCII`,
   `format version ASCII ("ak1")`, `public selector ASCII`, and
   **complete decoded 32-byte bearer secret**. Compare exactly 32-byte
   digests using Python `hmac.compare_digest`, never a prefix, hex string,
   timing-blind string equality or hand-rolled comparison.

## Independent test vector

This vector is a **synthetic fixture** computed independently using OpenSSL's
`dgst -sha256 -mac HMAC` on the framed bytes, then cross-checked with Python.

- Scope: `tenant-a:production`
- Version: `ak1`
- Selector bytes: `bytes(range(16))`, encoded `AAECAwQFBgcICQoLDA0ODw`
- Secret bytes: `bytes(range(32))`
- Server key: `bytes(range(32, 64))` (32 bytes; **test-only**, not a production secret)
- Message bytes: **113**
- HMAC digest hex:
  `540574633838c98c95e6afd36e8712768ade3a211ebf7bed39f55caccad22184`

The vector deliberately contains no real key or user secret.

## Alternatives and counterexamples

- Password KDF (Argon2id): not the default for a high-entropy random bearer;
  adds DoS pressure without addressing this use case.
- SHA-256 digest alone: simple but moves all protection to entropy of the
  issuer's CSPRNG; evaluate only in a separate approved ADR.
- Store plaintext full key: rejected.
- Prefix/selector as proof, global lookup or fallback key: prohibited.
- Globally discovered KMS key from a record-ref alone: prohibited; the host
  must allow-list `scope -> key_refs`.
- A generic verification middleware or automatic token/session issuance:
  rejected (no proven need / wrong bounded context).

## Security boundaries, error semantics and limits

Malformed external evidence rejects before a storage request. Cryptographic
mismatch returns only `False`. An unknown configured algorithm or unapproved
key reference yields `INVALID_TRUST_CONFIGURATION`; absent approved key
material yields `DEPENDENCY_UNAVAILABLE`. Exceptions from a malfunctioning
key source must be sanitized by the M2 Engine when composed in PR-07C.
`asyncio.CancelledError` propagates. Neither a verifier bool nor an
`ApiKeyVerifierRecord` can grant an authenticated principal.

Host-provided key-source callbacks are privileged in-process Python code:
the interface does not prove that a KMS/secret-manager implements correct
tenant isolation, key rotation or availability. PR-07B also cannot claim
zeroization of Python `bytes`, constant-time end-to-end network timing,
post-revocation freshness, or production key-management readiness.

## Rotation

Support different approved protection-key references simultaneously for
a bounded host policy. An old verifier cannot be re-HMACed under a new key
without the original bearer secret. The credential owner must plan expiration,
reissue or explicit bearer presentation for migration. There is no
implicit fallback when a key reference disappears.

## Qualification evidence required

- Canonical parser/negative property tests; external HMAC vector.
- Full-secret mutations, selector mismatch, digest tamper, cross-tenant,
  key-ref denial, key-source outage, redacted object surfaces.
- Ruff, strict mypy, package build, wheel smoke and security scans on an exact
  commit SHA, CI links, formal owner decision and independent security review.
- **Status remains PROPOSED** even after successful tests; M4 GATE27-05
  requires PR-07C/07D, all 40 oracles and independent adjudication.
