"""T25/T26 - Real localhost HTTP/1.1 transport with an actual Uvicorn server.

The timing sample is a CI smoke study, NOT a production claim of constant time
or non-enumerability behind arbitrary load balancers, CDNs or real networks.
"""

import asyncio
import json
import random
import socket
import statistics
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
import uvicorn
from fastapi import FastAPI

from .conftest import Infrastructure


@asynccontextmanager
async def live_host(app: FastAPI) -> AsyncIterator[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    sock.setblocking(False)
    port = sock.getsockname()[1]
    config = uvicorn.Config(
        app=app,
        log_level="critical",
        access_log=False,
        lifespan="off",
        server_header=False,
        date_header=False,
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(250):
            if server.started:
                break
            if task.done():
                await task
            await asyncio.sleep(0.01)
        assert server.started
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=8.0)
        sock.close()


def denial_signature(response: httpx.Response) -> tuple[object, ...]:
    return (
        response.status_code,
        response.content,
        response.headers.get("content-type"),
        response.headers.get("content-length"),
        response.headers.get("cache-control"),
        response.headers.get("www-authenticate"),
        response.headers.get("x-content-type-options"),
    )


@pytest.mark.asyncio
async def test_t25_real_network_denials_have_identical_status_body_headers(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"real-test-phrase", "alpha-id")
    app = infra.app(max_per_source=500, max_per_identity=500)
    async with live_host(app) as url, httpx.AsyncClient(base_url=url) as client:
        bad = await client.post(
            "/alpha/login", json={"username": "alice", "password": "invalid"}  # pragma: allowlist secret
        )
        missing = await client.post(
            "/alpha/login", json={"username": "unknown", "password": "invalid"}
        )
        await infra.pool.execute(
            "UPDATE m3q_credentials SET status='revoked', version=version+1 "
            "WHERE scope_id='tenant-alpha' AND identifier_value='alice'"
        )
        revoked = await client.post(
            "/alpha/login",
            json={"username": "alice", "password": "real-test-phrase"},  # pragma: allowlist secret
        )
        assert denial_signature(bad) == denial_signature(missing)
        assert denial_signature(bad) == denial_signature(revoked)
        assert bad.status_code == 401
        assert bad.json() == {"error": "invalid_credentials"}
        assert bad.headers.get("cache-control") == "no-store"
        # Unknown routes cannot mint an approved trust profile by body/header.
        unknown = await client.post(
            "/not-registered/login",
            json={"username": "alice", "password": "real-test-phrase"},
            headers={"X-Tenant": "tenant-alpha"},
        )
        assert unknown.status_code == 404

    await infra.redis.flushdb()
    # Fresh host + reduced limit, real socket again: throttled refusal is identical.
    limiter = infra.app(max_per_source=1, max_per_identity=20)
    async with live_host(limiter) as url, httpx.AsyncClient(base_url=url) as client:
        first = await client.post(
            "/alpha/login", json={"username": "unknown", "password": "invalid"}
        )
        throttled = await client.post(
            "/alpha/login", json={"username": "alice", "password": "real-test-phrase"}
        )
        assert denial_signature(first) == denial_signature(throttled)
        assert denial_signature(bad) == denial_signature(throttled)


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    offset = (len(ordered) - 1) * p / 100.0
    lower = int(offset)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (offset - lower)


def statistical_report(wrong: list[float], missing: list[float]) -> dict[str, object]:
    """Median comparison, paired-size permutation test and bootstrap CI.

    A non-significant p-value is NOT proof of equivalence or non-enumerability.
    """
    rng = random.Random(272604)
    observed = statistics.median(missing) - statistics.median(wrong)
    joined = wrong + missing
    n = len(wrong)
    repetitions = 500
    exceedances = 0
    for _ in range(repetitions):
        sample = joined[:]
        rng.shuffle(sample)
        diff = statistics.median(sample[n:]) - statistics.median(sample[:n])
        if abs(diff) >= abs(observed):
            exceedances += 1
    bootstrap_deltas: list[float] = []
    for _ in range(repetitions):
        a = [wrong[rng.randrange(n)] for _ in range(n)]
        b = [missing[rng.randrange(n)] for _ in range(n)]
        bootstrap_deltas.append(statistics.median(b) - statistics.median(a))
    return {
        "number_per_case": n,
        "wrong_p50_ms": round(statistics.median(wrong), 3),
        "missing_p50_ms": round(statistics.median(missing), 3),
        "wrong_p95_ms": round(percentile(wrong, 95), 3),
        "missing_p95_ms": round(percentile(missing, 95), 3),
        "difference_median_ms": round(observed, 3),
        "permutation_two_sided_p": round((exceedances + 1) / (repetitions + 1), 4),
        "bootstrap_95pct_delta_median_ms": [
            round(percentile(bootstrap_deltas, 2.5), 3),
            round(percentile(bootstrap_deltas, 97.5), 3),
        ],
        "limits": (
            "localhost HTTP/1.1; CI runner; synthetic secrets; no CDN/proxy; "
            "no claim of constant time or network-wide non-enumerability"
        ),
    }


@pytest.mark.asyncio
async def test_t26_real_http_randomized_timing_statistical_study(
    infra: Infrastructure,
) -> None:
    await infra.seed("tenant-alpha", "alice", b"real-test-phrase", "alpha-id")
    app = infra.app(max_per_source=500, max_per_identity=500)
    samples: dict[str, list[float]] = {"wrong": [], "missing": []}
    randomized = ["wrong", "missing"] * 60
    random.Random(20261103).shuffle(randomized)

    async with live_host(app) as url, httpx.AsyncClient(
        base_url=url, timeout=5.0
    ) as client:
        for case in randomized:
            payload = {
                "username": "alice" if case == "wrong" else "unknown",
                "password": "invalid",
            }
            before = time.perf_counter_ns()
            result = await client.post("/alpha/login", json=payload)
            elapsed_ms = (time.perf_counter_ns() - before) / 1_000_000
            assert result.status_code == 401
            assert result.json() == {"error": "invalid_credentials"}
            samples[case].append(elapsed_ms)

    report = statistical_report(samples["wrong"], samples["missing"])
    print("M3_T26_NETWORK_TIMING_JSON=" + json.dumps(report, sort_keys=True))
    # Wide smoke alarm only. No equivalence or security certification implied.
    difference = abs(float(report["difference_median_ms"]))
    median_wrong = float(report["wrong_p50_ms"])
    assert difference <= median_wrong * 0.35
