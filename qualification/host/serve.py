"""Disposable M3 reference host process, started only by qualification tests.

This ASGI process intentionally cannot be used without an explicit test
database URL, Redis URL and 32-byte shared HMAC key in the environment.
It never seeds a table, creates accounts or issues sessions/tokens.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from redis.asyncio import Redis

from pyauthkit.password.capacity import KDFWorkerPool

from .app import compose_qualification_app


def create_app() -> FastAPI:
    """Factory for `uvicorn qualification.host.serve:create_app --factory`."""
    postgres_dsn = os.environ["M3_PG_DSN"]
    redis_url = os.environ["M3_REDIS_URL"]
    key = bytes.fromhex(os.environ["M3_HMAC_KEY_HEX"])
    if len(key) != 32:
        raise ValueError("separate ASGI process requires a 32-byte HMAC key")
    per_source = int(os.environ.get("M3_RATE_MAX_SOURCE", "2"))
    per_identity = int(os.environ.get("M3_RATE_MAX_IDENTITY", "20"))

    @asynccontextmanager
    async def lifespan(shell: FastAPI) -> AsyncIterator[None]:
        pool = await asyncpg.create_pool(dsn=postgres_dsn, min_size=1, max_size=4)
        if pool is None:
            raise RuntimeError("test PostgreSQL connection not available")
        redis = Redis.from_url(
            redis_url, decode_responses=False, socket_connect_timeout=2, socket_timeout=2
        )
        workers = KDFWorkerPool(
            max_workers=1,
            max_inflight=2,
            max_memory_cost_kib=65536,
            memory_budget_kib=65536,
        )
        try:
            await redis.ping()
            shell.state.inner = compose_qualification_app(
                postgres_pool=pool,
                redis=redis,
                hmac_key=key,
                route_scopes={"alpha": "tenant-alpha", "beta": "tenant-beta"},
                workers=workers,
                max_per_source=per_source,
                max_per_identity=per_identity,
            )
            yield
        finally:
            await asyncio.to_thread(workers.close)
            await redis.aclose()
            await pool.close()

    shell = FastAPI(
        title="M3 qualification process - NOT PRODUCTION",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    class HostBridge:
        async def __call__(self, scope: dict, receive: object, send: object) -> None:
            await shell.state.inner(scope, receive, send)

    shell.mount("/", HostBridge())
    return shell
