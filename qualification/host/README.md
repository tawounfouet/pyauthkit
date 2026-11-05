# M3 Password Authentication - Reference Host Qualification

**State:** a synthetic, isolated, *non-production* test fixture for GATE27-04.
It demonstrates adapter integration without changing the core PyAuthKit API.

## Architecture

```text
    HTTP client  ->  FastAPI approved route  -> TrustedEntryContext
                     peer from socket only        |
                                                   v
         Redis AttemptGuard (2 atomic quotas) -> M2 AuthenticationEngine
                                                   |
                           PostgresPasswordCredentialResolver (scope-filtered)
                                                   |
                       Argon2idPasswordHashVerifier + bounded KDF pool
                                                   |
                       Postgres current-version/status recheck
                                                   |
                            M2 final AuthenticationPolicyGate
                                                   |
                 HTTP 200 | generic 401 | generic 503 + no-store
```

### Security boundaries

1. **Host-approved routes**: `/alpha/login` and `/beta/login` are created
   at bootstrap from the operator's mapping. An HTTP `X-Tenant` or JSON
   `tenant` field cannot authorize a scope. Unconfigured route returns 404.
2. **Source identity**: uses the ASGI socket peer reported by the server.
   **All X-Forwarded-For / Forwarded input is ignored**. This sample MUST NOT
   be copied unchanged behind an unqualified reverse proxy. Real deployments
   must design a trusted-proxy chain and source extraction policy.
3. **Credential ownership**: PostgreSQL is the host's authoritative store.
   The resolver lookup requires `scope_id=$1` at the SQL source. Unique
   constraints prevent collisions in the reference schema. The `is_current`
   read after KDF catches intervening revocation/version updates, **but cannot
   eliminate revocations between its last read and publication of the result**.
   A real host must set and verify a consistency contract.
4. **Rate limits**: two Redis keys using **HMAC of scoped peer and scoped
   identifier**. A single atomic Lua operation increments and expires both
   counters, so separate app replicas using the **same HMAC key** share quotas.
   Keys contain no plaintext login or peer. Redis outage is fail-closed (503).
   Counts use a fixed window from first attempt. This is *not* a universal
   credential stuffing, DDoS, bot management or cross-region defense.
5. **Password verification**: genuine `argon2-cffi` Argon2id PHC, no
   normalization of UTF-8 input bytes, a finite native worker pool and M2's
   mandatory final policy. The synthetic positive final rule is allowed only
   inside this qualification fixture.
6. **HTTP responses**: a uniform generic 401 body and selected headers for
   bad, absent, revoked and throttled credentials. A technical backend error
   maps to 503; malformed envelopes to 400, oversized bodies to 413. The API
   does not issue sessions, tokens, IAM rights or user directory lookups.
7. **Audit**: M2's event sink is best-effort. This example does not claim a
   durable/security-grade audit trail, verified monitoring or incident response.

## Reproducing locally

Requires Docker Compose, Python >=3.12, and a disposable test environment.
No real passwords, identities or credential material should be used.

```bash
docker compose -f qualification/host/compose.yaml up -d --wait
python -m pip install -e '.[dev,password,qualification]'
export M3_PG_DSN='postgresql://m3qual:m3qual_ci_synthetic_only@127.0.0.1:54329/m3qual' # pragma: allowlist secret
export M3_REDIS_URL='redis://127.0.0.1:63799/15'
python -m pytest -v -s qualification/host/tests
docker compose -f qualification/host/compose.yaml down -v
```

The credential table is created/truncated *only by the fixture* against the
test database. No migrations or writes are injected into the PyAuthKit core.
Do not point these tests at an existing application database.

## CI evidence

The protected `Lint, types, unit and architecture` job provisions dedicated
PostgreSQL and Redis service containers and runs these tests, including
an actual localhost Uvicorn HTTP/1.1 listener. Five cross-platform package
jobs continue to exercise the optional `[password]` wheel. Security scans
remain a separate required job. CI evidence must be linked to the **exact
PR head**, with the complete log and reviewer.

### Oracle traceability

- **T24**: independent FastAPI application objects sharing Redis, two
  approved tenants, source anti-spoofing tests, 64 concurrent atomic account
  attempts and cross-peer global account cap. Network peer variation is
  simulated with ASGITransport, not multiple physical network interfaces.
- **T25**: real TCP/HTTP/1.1 Uvicorn test comparing status, content,
  content type/length and security headers across wrong/missing/revoked
  credentials and throttled attempts.
- **T26**: randomized real TCP/HTTP/1.1 timings, 60 measurements per
  wrong/missing case, 500 permutations and 500 bootstrap replications.
  Report p50/p95 and 95% bootstrap interval, with an explicitly loose
  CI-only timing alarm. **A large p-value is not evidence of equivalence.**
- **T33**: SQL revocation/version update during real native Argon2id work
  before `is_current`, causing a generic denial.
- **Chaos**: Redis outage and a closed PostgreSQL pool produce technical
  errors with no authenticated principal, no secret in the public body.
- **M1/M2 regression**: separate default test suite, not replaced by the
  host test suite.

## Explicit limits and remaining operator decisions

This runner's loopback study cannot validate CDN, proxy, L7 rate limiter,
TLS, external latency, real IP metadata or a geographically distributed
production deployment. Multi-node replicas in this harness share one CI
Redis service but execute within one test Python interpreter. The HMAC key
is ephemeral and shared only inside each fixture; an operator must manage
its distribution/rotation securely for real deployment.

A **GATE27-04 formal GO** still requires owner-approved ADR-0010..0015,
risk decisions, an eligible independent security reviewer, exhaustive
oracle evidence and explicit deployment restrictions. This fixture supplies
technical evidence, not that person's approval. Do not merge or publish
solely because these tests pass.
