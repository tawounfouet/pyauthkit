"""T24 strong evidence: separate OS processes, real HTTP, one Redis counter."""

import asyncio
import os
import socket
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

from .conftest import Infrastructure, login_data


def unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@asynccontextmanager
async def process_host(
    port: int,
    *,
    hmac_key: bytes,
) -> AsyncIterator[str]:
    environment = os.environ.copy()
    environment["M3_HMAC_KEY_HEX"] = hmac_key.hex()
    environment["M3_RATE_MAX_SOURCE"] = "2"
    environment["M3_RATE_MAX_IDENTITY"] = "20"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "uvicorn",
        "qualification.host.serve:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-access-log",
        "--log-level",
        "error",
        cwd=os.getcwd(),
        env=environment,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    address = f"http://127.0.0.1:{port}"
    try:
        async with httpx.AsyncClient(base_url=address, timeout=2.0) as client:
            for _ in range(120):
                if process.returncode is not None:
                    raise AssertionError("qualification Uvicorn worker terminated on startup")
                try:
                    health = await client.get("/alpha/login")
                    if health.status_code in (404, 405):
                        break
                except httpx.ConnectError:
                    pass
                await asyncio.sleep(0.05)
            else:
                raise AssertionError("qualification Uvicorn worker was not ready")
        yield address
    finally:
        if process.returncode is None:
            process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except TimeoutError:
            process.kill()
            await process.wait()
        if process.stderr is not None:
            await process.stderr.read()


@pytest.mark.asyncio
async def test_t24_two_separate_uvicorn_processes_enforce_shared_redis_source_limit(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"alpha-phrase", "alpha-id")
    await infra.seed("tenant-beta", "alice", b"beta-phrase", "beta-id")
    port_a, port_b = unused_loopback_port(), unused_loopback_port()
    assert port_a != port_b
    async with (
        process_host(port_a, hmac_key=infra.secret_key) as address_a,
        process_host(port_b, hmac_key=infra.secret_key) as address_b,
    ):
        async with (
            httpx.AsyncClient(base_url=address_a, timeout=4) as a,
            httpx.AsyncClient(base_url=address_b, timeout=4) as b,
        ):
            first = await a.post("/alpha/login", json=login_data("unknown", "bad"))
            second = await b.post("/alpha/login", json=login_data("unknown", "bad"))
            third = await a.post("/alpha/login", json=login_data("alice", "alpha-phrase"))
            separate_tenant = await b.post("/beta/login", json=login_data("alice", "beta-phrase"))
            assert first.status_code == second.status_code == third.status_code == 401
            assert first.content == second.content == third.content
            assert separate_tenant.status_code == 200

    keys = await infra.redis.keys("m3q:src:*")
    # Both tenants have independent source counters despite two OS processes.
    assert len(keys) == 2
    values = sorted([int(await infra.redis.get(key)) for key in keys])
    assert values == [1, 3]
