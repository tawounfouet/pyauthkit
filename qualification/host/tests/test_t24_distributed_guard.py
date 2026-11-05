"""T24 - Real Redis quotas for scope/peer/account across host replicas."""

import asyncio

import httpx
import pytest

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from qualification.host.guard import HOST_SOURCE, RedisPasswordAttemptGuard

from .conftest import Infrastructure


@pytest.mark.asyncio
async def test_t24_two_fastapi_replicas_share_limits_but_isolate_tenants(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"alpha-phrase", "alpha-subject")
    await infra.seed("tenant-beta", "alice", b"beta-phrase", "beta-subject")
    app_a = infra.app(max_per_source=2, max_per_identity=20)
    app_b = infra.app(max_per_source=2, max_per_identity=20)

    transport_a = httpx.ASGITransport(
        app=app_a, client=("198.51.100.10", 50123), raise_app_exceptions=False
    )
    transport_b = httpx.ASGITransport(
        app=app_b, client=("198.51.100.10", 50124), raise_app_exceptions=False
    )
    transport_new_peer = httpx.ASGITransport(
        app=app_b, client=("198.51.100.11", 50125), raise_app_exceptions=False
    )
    async with (
        httpx.AsyncClient(transport=transport_a, base_url="http://qualifier") as a,
        httpx.AsyncClient(transport=transport_b, base_url="http://qualifier") as b,
        httpx.AsyncClient(
            transport=transport_new_peer, base_url="http://qualifier"
        ) as second_peer,
    ):
        login = {"username": "ghost", "password": "incorrect"}  # pragma: allowlist secret
        assert (await a.post("/alpha/login", json=login)).status_code == 401
        assert (await b.post("/alpha/login", json=login)).status_code == 401

        # A spoofed forwarded header does not alter the peer identity.
        blocked = await b.post(
            "/alpha/login",
            json={"username": "alice", "password": "alpha-phrase"},  # pragma: allowlist secret
            headers={"X-Forwarded-For": "203.0.113.55"},
        )
        assert blocked.status_code == 401
        assert blocked.json() == {"error": "invalid_credentials"}

        # Source buckets are tenant-scoped; another approved tenant remains viable.
        cross_tenant = await b.post(
            "/beta/login", json={"username": "alice", "password": "beta-phrase"}  # pragma: allowlist secret
        )
        assert cross_tenant.status_code == 200
        assert (await second_peer.post(
            "/alpha/login", json={"username": "alice", "password": "alpha-phrase"}
        )).status_code == 200
        # No body-controlled tenant swap.
        assert (await second_peer.post(
            "/alpha/login",
            json={"username": "alice", "password": "beta-phrase"},
        )).status_code == 401


@pytest.mark.asyncio
async def test_t24_atomic_cross_replica_account_limit_under_64_concurrent_calls(
    infra: Infrastructure,
) -> None:
    """The shared Lua command admits exactly the configured global account cap."""
    guards = [
        RedisPasswordAttemptGuard(
            redis=infra.redis,
            hmac_key=infra.secret_key,
            max_per_source=64,
            max_per_identity=4,
            window_seconds=60,
        )
        for _ in range(2)
    ]
    scope = TrustedScopeRef("tenant-alpha")

    async def attempt(index: int) -> bool:
        token = HOST_SOURCE.set(f"198.51.100.{(index % 200) + 1}")
        try:
            return await guards[index % 2].admit(
                scope_ref=scope,
                correlation_id=CorrelationId("parallel-qualification"),
                identifier_kind="username",
                identifier_value="alice",
            )
        finally:
            HOST_SOURCE.reset(token)

    results = await asyncio.gather(*(attempt(i) for i in range(64)))
    assert sum(results) == 4
    account_keys = await infra.redis.keys("m3q:acct:*")
    assert len(account_keys) == 1
    assert int(await infra.redis.get(account_keys[0])) == 64


@pytest.mark.asyncio
async def test_t24_global_account_limit_applies_across_different_peers(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"alpha-phrase", "alpha-subject")
    a = infra.app(max_per_source=20, max_per_identity=2)
    b = infra.app(max_per_source=20, max_per_identity=2)

    async def post(app, ip: str, password: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app, client=(ip, 60000))
        async with httpx.AsyncClient(transport=transport, base_url="http://host") as client:
            return await client.post(
                "/alpha/login", json={"username": "alice", "password": password}
            )

    assert (await post(a, "203.0.113.1", "incorrect")).status_code == 401
    assert (await post(b, "203.0.113.2", "incorrect")).status_code == 401
    # Matching password is still denied because the global account cap is exhausted.
    rejected = await post(a, "203.0.113.3", "alpha-phrase")
    assert rejected.status_code == 401
    assert rejected.json() == {"error": "invalid_credentials"}
