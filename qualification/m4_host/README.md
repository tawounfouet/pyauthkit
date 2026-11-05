# PyAuthKit M4 - PostgreSQL / Redis reference-host qualification

**Status: isolated CI fixture, NOT production**, and not part of the PyAuthKit
wheel. This suite qualifies specific integration boundaries, not generic
claims about all hosts.

## Technical test topology

```text
client (loopback TCP/HTTP, no proxy)
  -> host-approved /alpha or /beta route (never X-Tenant)
  -> FastAPI Authorization: ApiKey <opaque ak1...>
  -> M2 Engine + final policy
  -> Redis Lua atomic tenant/peer/key budgets (host socket peer)
  -> Postgres SELECT ... WHERE scope_id = $1 AND key_id = $2
  -> full secret HMAC + host-scoped key-reference allowlist
  -> Postgres post-HMAC version/status/read-back
  -> 200 success | uniform 401 rejection | 503 technical
```

Postgres owns the test credential table and version changes. No issuer,
sign-in session, IAM permission or token is produced. The synthetic
positive policy is **only for this isolated qualification host**.

## Evidence boundaries

- SQL is source-scoped; two tenants may share a selector. Test-only
  `revoke_cas` / `rotate_cas` use PostgreSQL atomic UPDATE with a
  version predicate. This does **not** make authentication linearizable
  after the final read or guarantee revocation across all application caches.
- Redis EVAL increments scope, peer and selector buckets atomically,
  including denied attempts. All replicas must share the protected
  bucket-key bytes. An unavailable Redis service produces a technical
  outcome rather than a permissive fallback.
- The socket peer is trusted only with Uvicorn `proxy_headers=False`.
  `Forwarded`, `X-Forwarded-For` and request tenant headers are ignored.
  Real reverse-proxy chains/TLS termination are **not qualified**.
- Generic negative outcomes intentionally share HTTP 401 body and selected
  headers. Technical unavailable produces 503; unknown routes produce 404.
  A bounded 40ms refusal floor is test-only and is not a uniform-timing
  or anti-enumeration guarantee.
- Live tests use two different Uvicorn OS processes, actual Postgres and
  Redis services. Tests also observe 20 randomized samples per wrong/missing
  case; the observation is **not** a pass/fail statistical equivalence proof.
  No CDN, service mesh, high load, durable audit, KMS or reverse proxy tested.

## CI and reproducing

Dedicated job `m4_host` provisions disposable PostgreSQL 17 and Redis 7.
Normal `python -m pytest` does not include this directory, so all gate
reviews must explicitly inspect the separate job.

Local run (requires an isolated test database with no real credentials):

```bash
python -m pip install ".[dev]" asyncpg redis fastapi uvicorn httpx pytest-asyncio
# Set M4_PG_DSN and M4_REDIS_URL to disposable services.
python -m pytest -v -s qualification/m4_host/tests
```

Never point `prepare_fixture_schema` at a production database: it truncates
`m4q_credentials`. Subprocess tests pass **synthetic test-only keys** via
environment. Do not copy fixture credentials or key distribution into a
real host.

## Remaining security gate

An independent reviewer must adjudicate all M4-T01..T40 against a canonical
oracle definition and all G5-01..G5-16 with exact SHA, environment,
evidence, risk disposition and approved ADR-0016..0018. Production
consistency, replay response, external identity-system integration,
reverse-proxy/TLS and operational alerting require separate qualification.
The formal M4 decision remains **NO-GO**.
