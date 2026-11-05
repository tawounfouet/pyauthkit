"""Dedicated CI service fixtures, never used by the package's normal test suite."""

import asyncio
import os
from collections.abc import AsyncIterator

import asyncpg
import pytest_asyncio
from argon2 import PasswordHasher
from argon2.low_level import Type
from fastapi import FastAPI
from redis.asyncio import Redis

from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.ports.password_hashing import PasswordHashVerifier
from qualification.host.app import compose_qualification_app
from qualification.host.storage import insert_fixture_record, prepare_qualification_schema


class Infrastructure:
    def __init__(self, pool: asyncpg.Pool, redis: Redis) -> None:
        self.pool = pool
        self.redis = redis
        self.secret_key = os.urandom(32)
        self.workers: list[KDFWorkerPool] = []

    async def seed(self, scope: str, username: str, password: bytes, subject_id: str) -> None:
        encoded = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, type=Type.ID).hash(
            password
        )
        await insert_fixture_record(
            self.pool,
            scope_id=scope,
            login=username,
            subject_id=subject_id,
            encoded_phc=encoded,
        )

    def app(
        self,
        *,
        max_per_source: int = 200,
        max_per_identity: int = 200,
        routes: dict[str, str] | None = None,
        hash_verifier: PasswordHashVerifier | None = None,
        redis_override: Redis | None = None,
        postgres_override: asyncpg.Pool | None = None,
    ) -> FastAPI:
        worker_pool = KDFWorkerPool(
            max_workers=2,
            max_inflight=4,
            max_memory_cost_kib=65536,
            memory_budget_kib=131072,
        )
        self.workers.append(worker_pool)
        return compose_qualification_app(
            postgres_pool=self.pool if postgres_override is None else postgres_override,
            redis=self.redis if redis_override is None else redis_override,
            hmac_key=self.secret_key,
            route_scopes=routes
            if routes is not None
            else {"alpha": "tenant-alpha", "beta": "tenant-beta"},
            workers=worker_pool,
            max_per_source=max_per_source,
            max_per_identity=max_per_identity,
            hash_verifier=hash_verifier,
        )


@pytest_asyncio.fixture
async def infra() -> AsyncIterator[Infrastructure]:
    dsn = os.environ["M3_PG_DSN"]
    redis_url = os.environ["M3_REDIS_URL"]
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=8)
    if pool is None:
        raise RuntimeError("qualification database not available")
    redis: Redis = Redis.from_url(
        redis_url, decode_responses=False, socket_connect_timeout=2, socket_timeout=2
    )
    await redis.ping()
    await prepare_qualification_schema(pool)
    await redis.flushdb()
    instance = Infrastructure(pool, redis)
    try:
        yield instance
    finally:
        for workers in instance.workers:
            await asyncio.to_thread(workers.close)
        await redis.flushdb()
        await redis.aclose()
        await pool.close()
