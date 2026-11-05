"""Disposable M4 qualification Uvicorn process, never a production server."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from redis.asyncio import Redis

from .app import compose_app


def create_app() -> FastAPI:
    dsn = os.environ["M4_PG_DSN"]
    redis_url = os.environ["M4_REDIS_URL"]
    verifier_key = bytes.fromhex(os.environ["M4_REFERENCE_KEY_HEX"])
    bucket_key = bytes.fromhex(os.environ["M4_BUCKET_KEY_HEX"])

    @asynccontextmanager
    async def lifespan(shell: FastAPI) -> AsyncIterator[None]:
        pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=4)
        if pool is None:
            raise RuntimeError("M4 reference database unavailable")
        redis = Redis.from_url(redis_url, decode_responses=False)
        try:
            await redis.ping()
            shell.state.inner = compose_app(
                pool=pool,
                redis=redis,
                verifier_key=verifier_key,
                bucket_key=bucket_key,
                routes={"alpha": "tenant-alpha", "beta": "tenant-beta"},
                peer_limit=int(os.environ.get("M4_PEER_LIMIT", "2")),
            )
            yield
        finally:
            await redis.aclose()
            await pool.close()

    shell = FastAPI(
        title="M4 reference process only",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    class Bridge:
        async def __call__(self, scope: dict, receive: object, send: object) -> None:
            await shell.state.inner(scope, receive, send)

    shell.mount("/", Bridge())
    return shell
