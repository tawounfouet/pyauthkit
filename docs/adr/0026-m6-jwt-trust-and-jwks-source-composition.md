# ADR-0026 - M6 schema v2 JWT trust and pinned JWKS admission

Date: 2026-11-05
Status: PROPOSED / review required. Not a production security sign-off.

## Context

M5 verifies RS256 JWT bearer access tokens using a host-authorized
`TrustedJwtVerificationProfile`, `JWTAuthenticator`, and M2's final
`AuthenticationPolicyGate`. M6 configuration version 1 only binds routes and
methods; it cannot itself guarantee which issuer, audience, keysets or remote
JWKS endpoints a separately supplied authenticator will trust.

## Decision candidate

A schema v2 trust snapshot has explicit `jwt_profiles`; when a route enables
JWT, its exact `TrustProfileRef` must have one and only one v2 JWT trust
binding. The binding owns issuer, audience, type, RS256 allowlist, principal
type, expiry/clock limits and one key source. Unknown fields fail bootstrap.

- Static source: the snapshot contains only a keyset reference. Public JWK
  material is supplied separately by the host and vetted by the existing M5
  `StaticJwksKeyResolver`. A private RSA JWK is never approved for verifying.
- HTTPS source: the snapshot describes an immutable
  `ApprovedJwksSource` and public IP allowlist. The host must separately
  approve an exact source-id/URI/IP grant. The actual M5 transport checks DNS,
  peer IP, TLS and redirects at connection time. Neither configuration nor a
  successful unit test is proof of a production network firewall.
- Runtime composition uses M5's `JWTAuthenticator`,
  `StaticJwtProfileResolver`, one exact-profile key router,
  `PyJwtRs256Verifier`, and M2's mandatory final policy. Tokens cannot
  select a new issuer or arbitrary key URL, and no second AuthN success path
  is introduced.
- A legacy v1 config is never silently reinterpreted as v2. The generic
  v2 composer refuses an unconsumed JWT profile. Mixing M4 secret consumer
  and M5 JWT trust in one v2 engine is deferred until an explicit, separately
  tested multi-consumer composition exists.

## Alternatives rejected

Wildcard issuers, disabling signature checks, `none` or HS256 in the M5
baseline, JWT-driven JWKS discovery, arbitrary HTTP/localhost/private IP
key sources, implicit fallback to another tenant/profile, and an optional
`verify_signature=false` switch.

## Consequences

The snapshot remains deeply immutable, and public keys and network source
authorities must be supplied at bootstrap. Key rotation remains under host
generation/credential policy, with no claim of immediate cluster revocation.
The optional `pyauthkit[jwt]` extra is required to verify signatures in
real traffic; the core reader adds no new mandatory dependency.

## Candidate oracles

M6-T03/T09/T11/T12, and the existing M5 JWT/JOSE/JWKS and M2 final-policy
regressions. All are development evidence pending GATE27-07 independent review.
