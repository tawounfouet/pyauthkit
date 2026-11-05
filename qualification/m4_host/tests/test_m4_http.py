"""M4 real loopback HTTP refusals and two separate OS processes.

No reverse proxy, TLS termination, SIEM, network-wide constant-time or
production latency guarantee is claimed by localhost Uvicorn checks.
"""

import asyncio
import json
import os
import random
import socket
import statistics
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
import uvicorn
from fastapi import FastAPI

from qualification.m4_host.storage import revoke_cas

from .conftest import (
    BUCKET_KEY,
    OTHER_SECRET,
    REFERENCE_KEY,
    SELECTOR,
    Infrastructure,
    encode,
    wire,
)


def unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@asynccontextmanager
async def live_host(app: FastAPI) -> AsyncIterator[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    sock.setblocking(False)
    port = int(sock.getsockname()[1])
    config = uvicorn.Config(
        app=app,
        log_level="critical",
        access_log=False,
        lifespan="off",
        proxy_headers=False,
        server_header=False,
        date_header=False,
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(120):
            if server.started:
                break
            if task.done():
                await task
            await asyncio.sleep(0.025)
        assert server.started, "qualification HTTP server not ready"
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=8)
        sock.close()


@asynccontextmanager
async def process_host(port: int) -> AsyncIterator[str]:
    env = os.environ.copy()
    env["M4_REFERENCE_KEY_HEX"] = REFERENCE_KEY.hex()
    env["M4_BUCKET_KEY_HEX"] = BUCKET_KEY.hex()
    env["M4_PEER_LIMIT"] = "2"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "uvicorn",
        "qualification.m4_host.serve:create_app",
        "--factory",
        "--no-proxy-headers",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-access-log",
        "--log-level",
        "error",
        cwd=os.getcwd(),
        env=env,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        async with httpx.AsyncClient(base_url=url, timeout=3) as client:
            for _ in range(120):
                if process.returncode is not None:
                    raise AssertionError("M4 Uvicorn subprocess exited during startup")
                try:
                    response = await client.get("/alpha/authenticate")
                    if response.status_code in (404, 405):
                        break
                except httpx.ConnectError:
                    pass
                await asyncio.sleep(0.05)
            else:
                raise AssertionError("M4 Uvicorn subprocess did not start")
        yield url
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


def auth_header(secret: bytes, selector: bytes = SELECTOR) -> dict[str, str]:
    return {"Authorization": "ApiKey " + wire(secret=secret, selector=selector)}


def refusal_signature(response: httpx.Response) -> tuple[object, ...]:
    return (
        response.status_code,
        response.content,
        response.headers.get("cache-control"),
        response.headers.get("content-type"),
        response.headers.get("content-length"),
        response.headers.get("x-content-type-options"),
        response.headers.get("www-authenticate"),
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m4_http_generic_denials_and_host_tenant_binding(
    infra: Infrastructure,
) -> None:
    await infra.seed()
    app = infra.app()
    async with live_host(app) as url, httpx.AsyncClient(base_url=url, timeout=4) as client:
        wrong = await client.post("/alpha/authenticate", headers=auth_header(OTHER_SECRET))
        unknown_selector = await client.post(
            "/alpha/authenticate", headers=auth_header(OTHER_SECRET, bytes(range(1, 17)))
        )
        missing = await client.post("/alpha/authenticate")
        assert wrong.status_code == unknown_selector.status_code == missing.status_code == 401
        assert refusal_signature(wrong) == refusal_signature(unknown_selector)
        assert refusal_signature(wrong) == refusal_signature(missing)
        spoofed = await client.post(
            "/beta/authenticate",
            headers={**auth_header(OTHER_SECRET), "X-Tenant": "tenant-alpha"},
        )
        assert spoofed.status_code == 401
        no_route = await client.post(
            "/gamma/authenticate",
            headers={**auth_header(OTHER_SECRET), "X-Tenant": "tenant-alpha"},
        )
        assert no_route.status_code == 404
        valid = await client.post("/alpha/authenticate", headers=auth_header(bytes(range(32))))
        assert valid.status_code == 200
        assert valid.json() == {"status": "authenticated"}

        await revoke_cas(
            infra.pool,
            scope="tenant-alpha",
            selector=encode(SELECTOR).decode("ascii"),
            expected_version=1,
        )
        revoked = await client.post("/alpha/authenticate", headers=auth_header(bytes(range(32))))
        assert refusal_signature(wrong) == refusal_signature(revoked)

    await infra.redis.flushdb()
    throttled_app = infra.app(peer_limit=1)
    async with (
        live_host(throttled_app) as url,
        httpx.AsyncClient(base_url=url, timeout=4) as client,
    ):
        first = await client.post("/alpha/authenticate", headers=auth_header(OTHER_SECRET))
        denied = await client.post("/alpha/authenticate", headers=auth_header(OTHER_SECRET))
        assert refusal_signature(first) == refusal_signature(denied)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m4_two_uvicorn_os_processes_share_redis_and_pg(infra: Infrastructure) -> None:
    await infra.seed()
    await infra.seed(scope="tenant-beta", secret=OTHER_SECRET, subject="service-beta")
    first_port = unused_port()
    second_port = unused_port()
    assert first_port != second_port
    async with (
        process_host(first_port) as first_url,
        process_host(second_port) as second_url,
        httpx.AsyncClient(base_url=first_url, timeout=4) as one,
        httpx.AsyncClient(base_url=second_url, timeout=4) as two,
    ):
        first = await one.post(
            "/alpha/authenticate",
            headers={**auth_header(OTHER_SECRET), "X-Forwarded-For": "203.0.113.1"},
        )
        second = await two.post(
            "/alpha/authenticate",
            headers={**auth_header(OTHER_SECRET), "X-Forwarded-For": "203.0.113.2"},
        )
        third = await one.post(
            "/alpha/authenticate",
            headers={**auth_header(bytes(range(32))), "X-Forwarded-For": "203.0.113.3"},
        )
        separate = await two.post("/beta/authenticate", headers=auth_header(OTHER_SECRET))
        assert first.status_code == second.status_code == third.status_code == 401
        assert refusal_signature(first) == refusal_signature(second)
        assert refusal_signature(first) == refusal_signature(third)
        assert separate.status_code == 200
    assert len(await infra.redis.keys("m4q:peer:*")) == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m4_loopback_timing_observation_no_equivalence_claim(
    infra: Infrastructure, capsys: pytest.CaptureFixture[str]
) -> None:
    await infra.seed()
    app = infra.app(peer_limit=200, selector_limit=200)
    order = ["wrong", "missing"] * 20
    random.Random(20261105).shuffle(order)
    times: dict[str, list[float]] = {"wrong": [], "missing": []}
    async with live_host(app) as url, httpx.AsyncClient(base_url=url, timeout=4) as client:
        for kind in order:
            headers = (
                auth_header(OTHER_SECRET)
                if kind == "wrong"
                else auth_header(OTHER_SECRET, bytes(range(1, 17)))
            )
            start = time.perf_counter_ns()
            outcome = await client.post("/alpha/authenticate", headers=headers)
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            assert outcome.status_code == 401
            times[kind].append(elapsed)
    report = {
        "sample_size_each": 20,
        "wrong_median_ms": round(statistics.median(times["wrong"]), 3),
        "missing_median_ms": round(statistics.median(times["missing"]), 3),
        "context": "loopback only; no proxy/CDN; no proven constant time",
    }
    print("M4_HTTP_TIMING_OBSERVATION=" + json.dumps(report, sort_keys=True))
    assert len(times["wrong"]) == len(times["missing"]) == 20


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_bearer_replay_is_an_explicit_non_goal_of_api_keys(
    infra: Infrastructure,
) -> None:
    await infra.seed()
    async with (
        live_host(infra.app()) as url,
        httpx.AsyncClient(base_url=url, timeout=4) as client,
    ):
        first = await client.post("/alpha/authenticate", headers=auth_header(bytes(range(32))))
        repeated = await client.post("/alpha/authenticate", headers=auth_header(bytes(range(32))))
    # Both successes expose the natural bearer replay property.
    # This is NOT replay prevention, session security or a production guarantee.
    assert first.status_code == repeated.status_code == 200


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_duplicate_authorization_headers_never_authenticate(
    infra: Infrastructure,
) -> None:
    await infra.seed()
    app = infra.app()
    valid = "ApiKey " + wire(secret=bytes(range(32)))
    duplicates = [
        [("Authorization", valid), ("Authorization", valid)],
        [("Authorization", valid), ("Authorization", "Bearer untrusted")],
        [("Authorization", "Bearer untrusted"), ("Authorization", valid)],
    ]
    async with (
        live_host(app) as url,
        httpx.AsyncClient(base_url=url, timeout=4) as client,
    ):
        denied = []
        for headers in duplicates:
            response = await client.post("/alpha/authenticate", headers=headers)
            assert response.status_code == 401
            denied.append(refusal_signature(response))
        assert len(set(denied)) == 1
        # Duplicates are still accounted for by the mandatory attempt guard.
        assert len(await infra.redis.keys("m4q:scope:*")) == 1
        unique = await client.post("/alpha/authenticate", headers={"Authorization": valid})
        assert unique.status_code == 200
