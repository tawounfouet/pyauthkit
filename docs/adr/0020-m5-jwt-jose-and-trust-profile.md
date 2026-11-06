# ADR-0020 - M5 RS256-only JWT verification and host-authoritative trust (candidate)

- **Status:** CANDIDATE / IMPLEMENTATION UNDER REVIEW; not security-approved
- **Milestone:** M5, PR-08, WP27-027..032
- **Date:** 2026-11-05
- **Gate:** GATE27-06, currently NO-GO
- **Baseline:** M4-integrated main c2800044292e8b53528dc4f3cac2664c064cd888

## Problem first

Parsing a JWT does not prove that its issuer is trusted or that the token was
issued to this API. A header-provided algorithm, key source or issuer may not
establish the trust root. Even a valid signature can authenticate the wrong
audience, tenant or token purpose. JWT verification must produce an internal
proof, not a final authorization decision.

## Candidate decision

1. M5 accepts compact, signed, three-segment JWS with mandatory typ=at+jwt
   as the baseline. JWE, nested JWTs, unsigned and detached payloads are out.
2. Allow exactly **RS256** for the initial slice. Reject none, HS-to-RS
   confusion, other algorithms, private JWK material, unknown crit and
   token-supplied jku/x5u/jwk/x5c or b64=false.
3. Crypto implementation is delegated to maintained **PyJWT + cryptography**
   behind optional pyauthkit[jwt]; core import must remain dependency-free.
   Pin acceptable version ranges, scan dependencies and reassess periodically.
4. TrustedJwtVerificationProfile is immutable and resolved exclusively from
   the host-issued M2 TrustProfileRef. A key set is scoped to that exact ref;
   no cross-issuer/tenant fallback, no JWT-provided URL or profile selection.
5. Require issuer exact match, audience exact recipient match, subject, exp and
   purpose/type; validate numeric dates under injected UTC clock, finite leeway,
   no bool coercion and no client-provided time.
6. Reuse AuthenticatorRegistryBuilder, JWTAuthenticator async SPI,
   _issue_verified_outcome and AuthenticationPolicyGate.final_decision.
   Claims roles, scope and tenant never grant IAM permissions.
7. Static trusted JWK adapter is supported. A reference remote HTTPS JWKS
   adapter with exact public IP allowlists, DNS-to-IP pinning, verified TLS,
   bounded HTTP and profile-isolated cache has been implemented under
   **candidate ADR-0021**. Real-host egress qualification and reviewer approval
   are still required; this code is not production-authorized.

## Alternatives and tradeoffs

- HS256: rejected for remote JWKS and baseline to prevent algorithm confusion.
- General-purpose JWT auto-discovery: rejected; issuers and keys must be
  pre-approved by the application host.
- Handwritten RSA/JWS verification: rejected; external vetted library used.
- Full RFC 9068 compliance claim: deferred; current profile is deliberately
  narrow. OAuth/OIDC token issuance and ID-token validation are separate.
- Direct HTTP JWKS client without egress protection: rejected for this slice;
  host-level DNS rebinding/SSRF cannot be solved merely by URL validation.

## Evidence and limits

PR #80 contains code and synthetic tests, which only become TESTED after CI
at an exact SHA passes. The branch also carries OpenSSL CLI-produced independent JWS
construction vectors verified by PyJWT; these do not constitute a third-party
cryptographic audit. No independent reviewer has signed any M5 oracle or
G6 criterion. This ADR remains a proposal until explicitly accepted.

## Learning card

- [Problem] Untrusted evidence attempts to name its own trust root.
- [Invariant] Valid JWT signature plus approved issuer, audience and purpose
  plus mandatory M2 final policy before any final principal.
- [Pattern] Strategy at M2 authenticator registry; Ports & Adapters at JOSE and
  key-source integration; immutable VO for trusted profile.
- [Anti-pattern] Unverified JWT decode treated as authentication; untrusted
  issuer -> auto-discovered JWKS; first matching kid globally; JWT roles -> IAM.
- [Test] Signed JWT for wrong audience/issuer/type and final M2 deny must
  all remain non-authenticated.
- [Residual risk] Key compromise, host configuration quality, proxy header
  normalization, remote SSRF, stale keys, independent crypto review.
