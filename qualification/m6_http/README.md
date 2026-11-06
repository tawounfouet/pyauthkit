# M6 Receipt-Gated HTTP Qualification (not production)

This isolated FastAPI reference host is **not packaged into PyAuthKit**.
It exists to test a narrow HTTP surface over loopback TCP with actual M4
HMAC and M5 JWT verification, and with a local SQLite receipt store.
The public `audit_delivery=required` configuration remains disabled.

## Explicit composition

The trusted host provisions `SqliteRequiredAuditCommitter`, builds one
`compose_receipted_api_key_gateway` or
`compose_receipted_jwt_gateway`, then passes it to
`compose_receipted_http_app(gateway=..., host_route_id=...,
method=EvidenceMethod.API_KEY)`. The route is registered only as
`POST /authenticate`; no dynamic tenant/profile argument is accepted.

Disable access logs, proxy trust and framework docs in this test setup.
Never use production API keys, JWT keys, audit-signing material or data.

## Local qualification

Use an isolated development environment:

```bash
python -m pip install ".[dev]" "fastapi>=0.110" "uvicorn>=0.30" "httpx>=0.27" "pytest-asyncio>=0.24"
python -m pytest -v qualification/m6_http/tests
```

The CI job exercises actual loopback TCP via Uvicorn and HTTPX, rather
than only calling a request-handler function. No external AWS credentials
or network calls are used. A positive result is a bare JSON status and no
cookie or grant of permissions.

## Important security limits

- The host still can invoke M2 directly outside this adapter.
- Only structurally admitted requests go through the receipt gateway.
  Requests with bodies or ambiguous HTTP framing are denied before audit
  and **do not** get a receipt. Full-attempt mandatory audit is not proved.
- There is no reverse proxy/TLS, WAF, production size/rate budget, peer
  attribution, managed audit ledger, durable authenticated receipt or
  multi-instance fencing proof.
- Caller disconnect and `asyncio.to_thread` cannot guarantee rollback
  of an in-flight SQLite commit. A committed attempt may have no delivered
  HTTP response; retries need a separately reviewed policy.
- Host HTTP access logs must never include Authorization or request bodies.
  Only the qualification server disables access logs automatically.

GATE27-07 remains NO-GO. ADR-0034 is PROPOSED.

## Iteration 13 - transport refusal and ambiguous cancellation

The application now records malformed framing **when the request reached
`POST /authenticate`** using the host-bound gateway's
`reject_untrusted_transport` method. A valid credential paired with a
request body or invalid framing yields a committed REJECTED event and HTTP
401, never HTTP 200. If the store cannot commit, the response is HTTP 503.

This is not comprehensive required audit: a reverse proxy, HTTP parser,
ASGI server, unknown path or unsupported method can refuse traffic before
the route is called and without a receipt.

`probe_restart.py` is used only by the test suite with a synthetic
environment marker. It proves local receipt visibility and duplicate-ID
rejection from another OS process after normal restart, not crash- or
tamper-resistant durability.

The cancellation scenario shows a SQLite worker can commit even after
the awaiting task has been cancelled. A caller must treat timeout and
disconnect as an **unknown commit outcome**, never claim an unambiguous
rollback or exactly-once delivery. Reusing an already consumed attempt ID
does not replay a positive authentication.
