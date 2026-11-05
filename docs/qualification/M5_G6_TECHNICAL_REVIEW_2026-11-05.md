# M5 G6 Technical Review - 2026-11-05

> Project: PyAuthKit, PR-08 / GitHub PR #80
> Document status: PRELIMINARY TECHNICAL REVIEW, NOT AN INDEPENDENT APPROVAL
> Reviewed scope: feature branch M5 code and candidate test specifications
> GATE27-06 verdict: NO-GO
> Reviewer: AI-assisted technical author; independent human reviewer NOT ASSIGNED
> Merge, PyPI publication and deployment: NOT AUTHORIZED

## 1. Review method and boundaries

This review separates specification, code, CI execution, operational proof and human approval. It is not a security certification. A test file is only *candidate evidence* until checked on the exact HEAD SHA, examined for the correctness of its assertions, run with suitable adversarial inputs, and adjudicated independently. The 40 IDs and 16 G6 conditions remain proposed qualification criteria.

## 2. Oracle-by-oracle grouped assessment

| Candidate oracle IDs | Required property | Available candidate tests | Review disposition |
| --- | --- | --- | --- |
| T01-T08 | JWS proof, signature negative paths, RSA algorithm confusion | JWT integration and OpenSSL CLI-generated JWS | Candidate links; independent crypto review pending |
| T09-T13 | Strict compact JWS parser, unsupported critical headers, jku | Parser, duplicate, b64=false and injection tests | Candidate links; fuzz and source review pending |
| T14-T24 | Issuer, audience, typ, time, scoped subject, tenant, IAM boundary | OpenSSL and M2 engine tests | Candidate links; reviewer must approve semantic oracles |
| T25-T27 | Unknown kid, cross-tenant key isolation, duplicate kid | Static keyset and cache tests | Candidate links; no distributed guarantee |
| T28-T29 | SSRF, redirects, DNS rebinding, TLS and actual egress | Mocked DNS/HTTP and local real TLS with simulated peer IP | PARTIAL; organization/public-network qualification missing |
| T30-T36 | JWKS size/timeout, rotation/cache, version, concurrency, JSON depth | JWKS cache, HTTP, parser and cancellation tests | Candidate links; DNS stress untested |
| T37-T40 | Secret redaction, no fallback, wheel and CI | M2/M5 and CI jobs | Pending final SHA and human adjudication |

Every ID M5-T01..T40 is individually listed with candidate evidence in the companion manifest. These groups summarize the evaluation; none is marked independently APPROVED. T29 remains partial despite a local TLS test because real egress was deliberately simulated.

## 3. G6 condition register

| ID | Review question | Evidence or observation | Decision |
| --- | --- | --- | --- |
| G6-01 | Baseline/dependency isolation | core independent, optional jwt; architecture checks | REVIEW REQUIRED |
| G6-02 | Host-selected trust profiles | M2 HostTrustCatalog, exact source/profile identity | REVIEW REQUIRED |
| G6-03 | Strict bounded JOSE parser | JWS length/JSON duplicate/depth test paths | REVIEW REQUIRED |
| G6-04 | Algorithms and key types | RS256 only, RSA 2048+, JWK metadata negative tests | REVIEW REQUIRED |
| G6-05 | Independent cryptographic vectors | OpenSSL CLI signer, PyJWT verifier | REVIEW REQUIRED; no outside auditor |
| G6-06 | Issuer/audience | OpenSSL negative issuer/audience tests | REVIEW REQUIRED |
| G6-07 | Token purpose | at+jwt typ and cnf validation | REVIEW REQUIRED |
| G6-08 | Clock/scope identity | observed UTC exp/nbf/iat and scoped subject | REVIEW REQUIRED |
| G6-09 | Real-host anti-SSRF | DNS fake, pinned IP, redirect refusal, local TLS server | BLOCKED: actual public DNS + egress infrastructure unqualified |
| G6-10 | JWKS/cache isolation | tenant/profile/version and in-flight invalidation tests | REVIEW REQUIRED; distributed consistency unqualified |
| G6-11 | Fail-closed outage | HTTP budgets and dependency errors | REVIEW REQUIRED; real DNS timeout failure unqualified |
| G6-12 | No leak / no IAM grants | redacted error and mandatory final M2 policy | REVIEW REQUIRED |
| G6-13 | Port substitution/concurrency | per-profile single-flight and async timeout | REVIEW REQUIRED; stress environment unqualified |
| G6-14 | Exact-SHA CI / build | GitHub quality, M5, package compatibility and scans | PENDING latest exact HEAD |
| G6-15 | Accepted ADR / risk signoff | ADR-0020 candidate only | BLOCKED: approval absent |
| G6-16 | Formal gate owner signoff | Human reviewer, risk register, SHA, post-merge verification | BLOCKED: signoff/merge not authorized |


## 4. Threat and implementation analysis

### 4.1 Trust selection

The untrusted bearer cannot choose its own verification keys. The M2 engine
selects an approved scope and versioned trust profile from the host catalog.
The JWT verifier looks up only the approved profile. Remote JWKS URL and exact
IP destinations are supplied at operator bootstrap, never derived from token
issuer, kid, jku or x5u. The fetcher checks the approved source object by
identity and rejects a substitute. Python object identity is not a sandbox.

### 4.2 DNS rebinding, SSRF and egress

The reference fetcher checks every DNS answer against globally routable IPs
and the operator's exact IP allowlist. A mixed answer is rejected. It connects
using the validated literal IP, preserving the approved hostname for TLS SNI,
certificate hostname verification and the HTTP Host header. It verifies the
connected peer and never follows a 3xx Location value. The HTTP code does not
automatically use proxy settings or send application credentials.

**Unresolved P0 risk:** The tests use fake DNS/peer for the public egress
route. The local TLS host uses a genuine TLS handshake but a substituted public
IP route. Actual enterprise DNS, firewalls, proxy rules and external provider
rotation have not been tested. The deploying host must enforce egress at the
network layer, approve issuer host/IP policy, and evaluate real DNS rebinding
and destination changes. No GO without that independent host qualification.

### 4.3 Availability and parsing limits

The client uses finite asynchronous connect and read timeout, HTTP header
and JSON payload size budgets, strict allowed media type, no compressed
payloads, no redirects, and no cookies. It rejects bad status, conflicting
content framing, duplicate headers and invalid chunk encoding. The JWKS
cache is per profile/version with TTL, single-flight and generation counters.

**Unresolved P1 risk:** asyncio DNS resolution can involve operating-system
workers that outlive a canceled coroutine. Cancellation protects the awaiting
JWT result but does not prove DNS worker termination. Host DNS resolver
time budgets, concurrency pressure and multi-process cache invalidation
require explicit tests and documentation. Cache expiration is not instant
JWT revocation.

### 4.4 Cryptographic independence

OpenSSL CLI constructs and signs synthetic JWS with ephemeral RSA keys.
PyAuthKit uses PyJWT to verify the result through its approved RS256 adapter,
and rejects mutated payload, header, signature and other-key signatures.
This is independent token construction, NOT a third-party crypto audit:
OpenSSL CLI and PyJWT may share underlying OpenSSL primitives. Additional
review of library versions, key strength and signed-claim semantics remains
required.

### 4.5 Authorization isolation

A verified token creates only an internal verifier outcome. The M2
AuthenticationPolicyGate still makes the final authentication decision.
JWT roles, permissions, claimed tenant or issuer hints do not establish
PyIAMKit authorization. Tests must ensure no false Authenticated output.

## 5. Independent review checklist and disposition

A qualified human reviewer must record: name and independence; exact HEAD
SHA; run IDs and conclusions; code/crypto source inspection; 40 individual
oracles with test vectors and failure traces; 16 G6 decisions; actual
deployment-like DNS/TLS/firewall/redirect/egress evidence; approved domain
and IP list; risk ownership; and dated approval/waiver references.

| Required approval | State |
| --- | --- |
| Independent security reviewer | NOT ASSIGNED |
| M5-T01..T40 individually approved | NO |
| G6-01..G6-16 accepted | NO |
| Real public-network egress test | NOT RUN |
| ADR-0020 formally accepted | NO |
| Signed risk decisions | NO |
| Exact-HEAD green CI | PENDING at initial review |
| GO for GATE27-06 | NO-GO |
| Merge/release authority | NOT GRANTED |

## 6. Evidence index and source references

- docs/qualification/M5_CANDIDATE_EVIDENCE_MANIFEST.md
- docs/roadmap/PR-08_EXECUTION.md
- docs/adr/0020-m5-jwt-jose-and-trust-profile.md
- src/pyauthkit/adapters/jwks_https.py
- src/pyauthkit/adapters/jwks_cache.py
- tests/security/test_m5_jwks_https.py
- tests/qualification/test_m5_jwks_tls_host.py
- tests/qualification/test_m5_openssl_vectors.py

RFC 8725 sections 3.1, 3.8-3.12 and OWASP SSRF Prevention guidance
were considered as design inputs, not a certification.
