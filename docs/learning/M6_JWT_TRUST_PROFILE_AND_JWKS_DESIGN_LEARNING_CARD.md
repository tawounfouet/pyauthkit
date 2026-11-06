# M6 Design Learning Card - JWT trust profile as configuration authority

Date: 2026-11-05
Status: IMPLEMENTED + UNDER CI REVIEW (not independently security-qualified).

## Problem

A JWT is a signed statement from *some* issuer, not permission to choose an
issuer or a signing key on demand. A policy engine with untrusted source
selection may accidentally authenticate the wrong tenant, even if signatures
verify correctly.

## Boundary and pattern

The host controls a versioned immutable JWT trust profile. A matching route
chooses it before parsing the JWT. The token provides a `kid` hint only within
the selected issuer and key source. This is [DDD: Value Object] for the
`JwtTrustBinding`, [DIP: exact resolver port] for keys, and [GoF: Strategy]
for the existing M5 `JWTAuthenticator`. M2 still grants final authentication.

## Alternatives and failure behavior

No issuer from claims, no header-selected `jku`/`x5u`, no fallback keysets,
no arbitrary HTTP source, no partial JWT trust profile. Invalid config means
refused activation, not anonymous authentication. A pinned network URI and
IP allowlist are necessary but not sufficient for production SSRF defense.

## Evidence

`tests/integration/test_m6_jwt_trust_bootstrap.py` exercises real synthetic
RS256 signatures, negative issuer/audience/kid/headers, missing profile fields,
private-key JWK refusal and network source admission without live egress.
M5's independent local TLS tests remain required and do not replace an
actual host network security review.
