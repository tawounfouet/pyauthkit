# PR-08 - M5 JWT Bearer Verification - Execution ledger

> Date: 2026-11-05
> Status: IN PROGRESS / DEVELOPMENT DRAFT
> PR: https://github.com/tawounfouet/pyauthkit/pull/80
> Branch: feat/m5-jwt-bearer-verification-pr08
> Base: M4-integrated main c2800044292e8b53528dc4f3cac2664c064cd888
> Gate: GATE27-06 NO-GO until formal independent review
> Scope: incoming JWT verification only; no token issuance, IAM, OAuth server or production rollout

## Truth levels

- SPECIFIED: M5 plan and 40 candidate security oracles.
- IMPLEMENTED (draft branch): bounded compact JWS parser, host-bound JWT policy,
  static scoped JWK resolver, optional PyJWT RS256 adapter, M2 JWT authenticator.
- TESTED: depends on exact-HEAD CI and independent evidence, not on the existence
  of functions named test_*.
- SECURITY QUALIFIED: NOT YET; no G6-01..16 signoff.
- RELEASE: NOT AUTHORIZED; no PyPI, deployment, merge or release requested.

## PR-08A - Profile and parser (WP27-027, WP27-028)

- [x] Immutable, scope-bound host policy in domain/jwt.py.
- [x] Strict 3-part compact JWS structure and canonical base64url.
- [x] Bounded header/payload/signature, duplicate JSON key rejection.
- [x] Drop untrusted JOSE key references and unapproved headers.
- [x] Ports in ports/jwt.py, no framework coupling.
- [ ] Independent parser fuzz/property qualification and snapshot review.

## PR-08B - Cryptographic verifier (WP27-029, WP27-030)

- [x] Static JWK sets indexed by exact approved TrustProfileRef.
- [x] RSA public-only profile, kid ambiguity rejected.
- [x] PyJWT+cryptography optional pyauthkit[jwt] extra, RS256 only.
- [x] Signature must verify before signed claims matter.
- [ ] Independent OpenSSL-generated positive and negative vectors.
- [ ] Crypto dependency review and accepted ADR.

## PR-08C - Remote JWKS (WP27-029, WP27-031)

- [x] Immutable approved fixed HTTPS JWKS source descriptor, sourced only from host.
- [x] Explicit operator-owned transport port; no permissive fetcher in core.
- [x] Per-profile cache isolation, TTL, invalidation, rotation and single-flight.
- [x] Synthetic concurrency, cancellation, timeout and malformed JWKS tests.
- [x] Cache rejects stale snapshots and network outages in synthetic tests.
- [ ] Real HTTPS transport with DNS rebinding, redirects, egress allowlist, TLS enforcement.
- [ ] Host-level adversarial network and key-rotation qualification under GATE27-06.

**Safety choice:** No generic URL fetching or token-driven JWKS discovery was
introduced merely to tick this checkbox. A static trusted source is supported for development and offline verification;
remote sources require an operator-controlled fetch adapter with proven network
safety. The built-in cache does not prove transport egress security.

## PR-08D - End-to-end M2 integration and release evidence (WP27-030, 032)

- [x] Explicitly register JWTAuthenticator in M2 registry; no auto-discovery.
- [x] Bind verification to exact M2 scope/profile/attempt.
- [x] Signed claims: iss, aud, sub, exp/nbf/iat, optional max_age.
- [x] typ=at+jwt and no sender-constrained cnf claims without binding proof.
- [x] Emit only M2 internal VerifiedOutcome, pass through final policy gate.
- [x] Adversarial tests for wrong issuer/audience/type/key, bad signature,
  duplicate JSON, none/HS confusion, role-based bypass and clock boundaries.
- [ ] 40-oracle manifest with exact SHA/job/node identifiers.
- [ ] CI matrix including dedicated M5 qualification job and wheel smoke.
- [ ] Independent GATE27-06 security signoff.

## Inheritance and debt

M3 PR #75 remains separate; never silently absorb it. M4 PR #76 merged on
main for pre-alpha development but GATE27-05 independent qualification remains
NO-GO. Passing M5 tests will not change either condition.

## Software Design & Learning

- Problem: Unverified claims must not choose trust or assert identity.
- Pattern: Host-owned immutable TrustProfile, Strategy SPI, dependency inversion
  for crypto and key resolution.
- Invariant: issuer+aud+typ+signature+time+scoped subject+final M2 gate.
- Proof: adversarial tests and CI exact SHA; negative-path coverage required.
- Risk: no proof of remote JWKS safety, multi-process revocation, release safety
  or compliance with the entirety of RFC 9068.
