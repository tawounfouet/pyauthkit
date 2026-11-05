# ADR-0021 - JWKS HTTPS egress, DNS pinning and response bounds

- Status: CANDIDATE / NOT ACCEPTED
- Milestone: M5 / PR-08C / GATE27-06
- Date: 2026-11-05
- Decision authority: maintainer and independent security reviewer, pending
- Companion ADR: 0020-m5-jwt-jose-and-trust-profile.md

## Problem

A JWT bearer may contain an issuer, kid or remote key URL, and a valid
domain name may resolve to private or unexpected addresses. Fetching a JWK
Set with a generic HTTP client risks SSRF, DNS rebinding, redirect-to-internal,
credential forwarding, key-source confusion and resource exhaustion.
The source must come from the host trust profile, not the presented token.

## Candidate security design

1. The operator declares one ApprovedJwksSource per immutable versioned
   TrustProfileRef and a nonempty exact public IP allowlist for that source,
   not a domain wildcard or overly broad CIDR.
2. PinnedHttpsJwksFetcher validates all DNS answers. If any answer is
   non-global, private, link-local, loopback, mapped or not in the exact
   allowlist, it rejects the entire result before connection.
3. The actual connection uses the validated literal address, not another
   hostname lookup. The original approved host is used for TLS SNI, certificate
   hostname verification and the HTTP Host request field.
4. Require a trusted CA chain, hostname validation, TLS 1.2+ and an observed
   peer IP matching the previously validated destination. No implicit HTTP
   proxy and no token-supplied URL/key material.
5. Send an anonymous GET with no cookies, bearer credentials, redirects or
   compression. Accept only HTTP 200 JSON JWKS and bounded HTTP 1.0/1.1
   framing. Reject all redirects including same-host 301/302/307/308.
6. Source timeout is finite; parsing limits total HTTP headers, per-line
   bytes, response bytes and chunk sizes. Invalid or inaccessible remote
   JWKS returns a technical non-success, never fallback authentication.
7. CachedApprovedJwksKeyResolver isolates snapshots by profile/version,
   TTL and generation. Cache validity does not prove current key ownership.
8. Local simulation tests cover DNS/redirect/body and an ephemeral real
   TLS server. They do NOT qualify public DNS, firewall or distributed
   incident response.

## Alternatives rejected or deferred

- Trusting iss, kid, jku or x5u as a key source: rejected.
- Resolving DNS once, then reconnecting by hostname: rejected due to TOCTOU.
- Automatically following HTTP redirects: rejected.
- Permitting all globally routable IPs without exact host allowlist: rejected.
- Open proxy, cookies and automatic source discovery: rejected.
- Broad CIDRs/CDN auto-update and certificate pinning: deferred pending review.
- Stale-on-error for unknown key source: rejected initially.

## Failure semantics and operational obligations

A cache miss requires DNS and HTTPS. If DNS resolves to multiple addresses,
all must be approved; an unapproved IPv6 answer denies the whole response.
Hosts with changing CDN addresses must deliberately revise bootstrap
configuration. This reference adapter prefers safe denial to a silent trust
expansion.

The deploying host must independently enforce egress at the network layer,
approve issuer hostname and public IPs, monitor rotation and test actual
DNS failure and public IP changes. Python name privacy, source object identity
and dependency injection cannot isolate malicious in-process code.

Python asyncio name resolution can involve OS workers that remain active after
the awaiting coroutine is cancelled. Cancellation prevents success but does
not prove those workers instantly terminate. Host DNS time limits,
connection quotas and production firewall verification remain obligations.

## Test evidence (candidate)

- tests/security/test_m5_jwks_https.py : fake DNS mixed records, redirects,
  malformed HTTP, body size, timeout and no-credentials tests.
- tests/qualification/test_m5_jwks_tls_host.py : actual local TLS CA/hostname
  verification; public egress route and peer-IP view are simulated.
- tests/security/test_m5_jwks_cache.py : TTL, isolation, rotation, concurrency,
  invalidation race and safe outage.
- tests/qualification/test_m5_openssl_vectors.py : OpenSSL-created JWS
  independent from PyJWT's signing API.

Real egress, DNS rebinding and firewall qualification are still mandatory for
M5-T29 / G6-09, and all G6 criteria require an independent reviewer.

## Design Learning Card

- Problem: Remote metadata fetch opens a new trust boundary.
- Invariant: Every destination and key set is authorized by the host.
- Pattern: Ports & Adapters, immutable source value, per-profile cache.
- Anti-pattern: Validate domain then connect via unvalidated hostname.
- Oracle: Mixed public/private DNS must cause no connection.
- Residual risk: Public network, CDN churn, malicious host process,
  compromised issuer and distributed revocation.
