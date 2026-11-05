"""Disposable PostgreSQL + Redis services for M4 qualification only."""

import base64
import hashlib
import hmac
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import asyncpg
import pytest_asyncio
from fastapi import FastAPI
from redis.asyncio import Redis

from qualification.m4_host.app import compose_app
from qualification.m4_host.storage import prepare_fixture_schema, seed_fixture

REFERENCE_KEY = bytes(range(32, 64))
BUCKET_KEY = bytes(range(64, 96))
SELECTOR = bytes(range(16))
SECRET = bytes(range(32))
OTHER_SECRET = bytes(range(1, 33))


def encode(part: bytes) -> bytes:
    return base64.urlsafe_b64encode(part).rstrip(b"=")


def wire(*, selector: bytes = SELECTOR, secret: bytes = SECRET) -> str:
    return (b"ak1." + encode(selector) + b"." + encode(secret)).decode("ascii")


def test_digest(scope: str, *, selector: bytes = SELECTOR, secret: bytes = SECRET) -> bytes:
    """Independently frame a synthetic issuer fixture per ADR-0016."""
    parts = (
        scope.encode("ascii"),
        b"ak1",
        encode(selector),
        secret,
    )
    message = b"pyauthkit-api-key-v1\x00" + b"".join(
        len(piece).to_bytes(4, "big") + piece for piece in parts
    )
    return hmac.new(REFERENCE_KEY, message, hashlib.sha256).digest()


class Infrastructure:
    def __init__(self, pool: asyncpg.Pool, redis: Redis) -> None:
        self.pool = pool
        self.redis = redis

    async def seed(
        self,
        *,
        scope: str = "tenant-alpha",
        selector: bytes = SELECTOR,
        secret: bytes = SECRET,
        subject: str = "service-alpha",
        expiry_hours: float = 24,
    ) -> None:
        await seed_fixture(
            self.pool,
            scope=scope,
            selector=encode(selector).decode("ascii"),
            subject=subject,
            digest=test_digest(scope, selector=selector, secret=secret),
            expires_at=datetime.now(UTC) + timedelta(hours=expiry_hours),
        )

    def app(
        self,
        *,
        peer_limit: int = 100,
        scope_limit: int = 2000,
        selector_limit: int = 200,
        minimum_refusal_seconds: float = 0.04,
    ) -> FastAPI:
        return compose_app(
            pool=self.pool,
            redis=self.redis,
            verifier_key=REFERENCE_KEY,
            bucket_key=BUCKET_KEY,
            routes={"alpha": "tenant-alpha", "beta": "tenant-beta"},
            peer_limit=peer_limit,
            scope_limit=scope_limit,
            selector_limit=selector_limit,
            minimum_refusal_seconds=minimum_refusal_seconds,
        )


@pytest_asyncio.fixture
async def infra() -> AsyncIterator[Infrastructure]:
    dsn = os.environ["M4_PG_DSN"]
    redis_url = os.environ["M4_REDIS_URL"]
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=12)
    if pool is None:
        raise RuntimeError("test PostgreSQL is unavailable")
    redis: Redis = Redis.from_url(redis_url, decode_responses=False)
    await redis.ping()
    await prepare_fixture_schema(pool)
    await redis.flushdb()
    try:
        yield Infrastructure(pool, redis)
    finally:
        await redis.flushdb()
        await redis.aclose()
        await pool.close()
