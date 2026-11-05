"""M3 host revocation, freshness and service failure tests.

This verifies an actual PostgreSQL version change BETWEEN Argon2id and
is_current(), not just an in-memory fixture flag.
"""

import asyncio
import os
from threading import Event

import asyncpg
import httpx
import pytest
from redis.asyncio import Redis

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.password.records import PasswordRecordFound
from qualification.host.storage import PostgresPasswordCredentialResolver

from .conftest import Infrastructure


class PostKDFBarrier:
    """Wraps real Argon2id, blocks native worker after the correct KDF result."""

    def __init__(self) -> None:
        self._delegate = Argon2idPasswordHashVerifier(Argon2idPolicy())
        self.entered = Event()
        self.release = Event()

    @property
    def max_memory_cost_kib(self) -> int:
        return self._delegate.max_memory_cost_kib

    def validate_hash(self, encoded_hash: str) -> None:
        self._delegate.validate_hash(encoded_hash)

    def verify(self, *, password: bytes, encoded_hash: str) -> bool:
        result = self._delegate.verify(password=password, encoded_hash=encoded_hash)
        if result:
            self.entered.set()
            if not self.release.wait(5):
                raise RuntimeError("qualification barrier was not released")
        return result

    def needs_rehash(self, *, encoded_hash: str) -> bool:
        return self._delegate.needs_rehash(encoded_hash=encoded_hash)


@pytest.mark.asyncio
async def test_t33_real_postgres_revocation_between_kdf_and_freshness_check(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"good-phrase", "alpha-id")
    barrier = PostKDFBarrier()
    app = infra.app(hash_verifier=barrier)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://host") as client:
            pending = asyncio.create_task(
                client.post(
                    "/alpha/login",
                    json={"username": "alice", "password": "good-phrase"},  # pragma: allowlist secret
                )
            )
            assert await asyncio.to_thread(barrier.entered.wait, 3)
            # The authoritative row changes while Argon2id's native worker waits.
            await infra.pool.execute(
                "UPDATE m3q_credentials SET status='revoked', version=version+1 "
                "WHERE scope_id='tenant-alpha' AND identifier_value='alice'"
            )
            barrier.release.set()
            result = await pending
            assert result.status_code == 401
            assert result.json() == {"error": "invalid_credentials"}
            async_post = PostgresPasswordCredentialResolver(infra.pool)
            current = await async_post.resolve(
                scope_ref=TrustedScopeRef("tenant-alpha"),
                identifier_kind="username",
                identifier_value="alice",
            )
            assert isinstance(current, PasswordRecordFound)
            assert current.record.version == 2
    finally:
        barrier.release.set()


@pytest.mark.asyncio
async def test_t09_closed_postgres_pool_returns_503_and_no_authentication(
    infra: Infrastructure,
) -> None:
    # Isolated second connection pool, safe to close without affecting fixtures.
    isolated = await asyncpg.create_pool(dsn=os.environ["M3_PG_DSN"], min_size=1, max_size=2)
    assert isolated is not None
    await isolated.close()
    app = infra.app(postgres_override=isolated)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://host") as client:
        result = await client.post(
            "/alpha/login",
            json={"username": "alice", "password": "good-phrase"},
        )
        assert result.status_code == 503
        assert result.json() == {"error": "temporarily_unavailable"}
        assert result.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_t23_redis_outage_returns_503_without_credential_lookup(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"good-phrase", "alpha-id")
    broken_redis = Redis.from_url(
        "redis://127.0.0.1:1/15",
        socket_connect_timeout=0.15,
        socket_timeout=0.15,
        retry_on_timeout=False,
    )
    app = infra.app(redis_override=broken_redis)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://host",
        ) as client:
            result = await client.post(
                "/alpha/login", json={"username": "alice", "password": "good-phrase"}
            )
            assert result.status_code == 503
            assert result.json() == {"error": "temporarily_unavailable"}
            assert result.headers.get("cache-control") == "no-store"
    finally:
        await broken_redis.aclose()
