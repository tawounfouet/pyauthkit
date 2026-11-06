"""M6 loopback TCP qualification: route-only receipt gateway, never production."""

import asyncio
import sqlite3
from pathlib import Path

import httpx
import pytest

from pyauthkit.domain.evidence import EvidenceMethod
from qualification.m6_http.app import compose_receipted_http_app

from .conftest import (
    RAW_SECRET,
    api_gateway,
    api_wire,
    jwt_gateway,
    jwt_wire,
    store,
    stored_rows,
    tcp_host,
)


def signature(response: httpx.Response) -> tuple[object, ...]:
    return (
        response.status_code,
        response.json(),
        response.headers.get("cache-control"),
        response.headers.get("x-content-type-options"),
    )


def api_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": "ApiKey " + (api_wire() if token is None else token)}


def jwt_headers(token: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + token}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m6_http_m4_valid_and_bad_hmac_have_local_receipts(tmp_path: Path) -> None:
    committer = store(tmp_path)
    gateway = await api_gateway(committer)
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            yes = await client.post("/authenticate", headers=api_headers())
            assert yes.status_code == 200
            assert yes.json() == {"status": "authenticated"}
            assert yes.headers["cache-control"] == "no-store"
            assert yes.headers["x-content-type-options"] == "nosniff"
            assert "set-cookie" not in yes.headers

            invalid = bytearray(RAW_SECRET)
            invalid[0] ^= 1
            no = await client.post(
                "/authenticate", headers=api_headers(api_wire(bytes(invalid)))
            )
            assert signature(no) == (401, {"error": "invalid_credentials"}, "no-store", "nosniff")
            rows = stored_rows(tmp_path / "receipt.sqlite")
            assert [result for _, result in rows] == ["AUTHENTICATED", "REJECTED"]
            assert len({key for key, _ in rows}) == 2
            raw = (tmp_path / "receipt.sqlite").read_bytes()
            for marker in (b"service-a", b"tenant-a:production", b"issuer-a", RAW_SECRET):
                assert marker not in raw


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m6_http_m5_valid_rs256_and_wrong_audience_receipted(tmp_path: Path, rsa_keys) -> None:
    private, public = rsa_keys
    committer = store(tmp_path)
    gateway = jwt_gateway(committer, public)
    async with tcp_host(gateway, route="jwt", method=EvidenceMethod.JWT) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            yes = await client.post("/authenticate", headers=jwt_headers(jwt_wire(private)))
            assert yes.status_code == 200
            assert yes.json() == {"status": "authenticated"}
            no = await client.post(
                "/authenticate", headers=jwt_headers(jwt_wire(private, audience="foreign-api"))
            )
            assert signature(no) == (401, {"error": "invalid_credentials"}, "no-store", "nosniff")
            assert [outcome for _, outcome in stored_rows(tmp_path / "receipt.sqlite")] == [
                "AUTHENTICATED",
                "REJECTED",
            ]
            raw = (tmp_path / "receipt.sqlite").read_bytes()
            assert b"workload-42" not in raw
            assert b"issuer.example.test" not in raw


@pytest.mark.asyncio
@pytest.mark.security
async def test_m6_http_no_alternative_engine_or_documentation_routes(tmp_path: Path) -> None:
    gateway = await api_gateway(store(tmp_path))
    app = compose_receipted_http_app(
        gateway=gateway, host_route_id="api", method=EvidenceMethod.API_KEY
    )
    assert {route.path for route in app.routes} == {"/authenticate"}
    assert not hasattr(app.state, "engine")
    assert not hasattr(app.state, "gateway")

    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            for path in (
                "/m2/authenticate",
                "/engine/authenticate",
                "/api/authenticate",
                "/jwt/authenticate",
                "/openapi.json",
                "/docs",
                "/redoc",
                "/authenticate/",
            ):
                assert (await client.post(path, headers=api_headers())).status_code == 404
            assert (await client.get("/authenticate")).status_code == 405
            assert (await client.options("/authenticate")).status_code == 405


@pytest.mark.asyncio
@pytest.mark.security
async def test_m6_http_untrusted_header_cannot_choose_tenant_or_audit_attempt(
    tmp_path: Path,
) -> None:
    gateway = await api_gateway(store(tmp_path))
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            headers = {
                **api_headers(),
                "X-Tenant": "foreign-tenant",
                "X-Trust-Profile": "foreign-profile",
                "X-Audit-Attempt-ID": "caller-selected-attempt",
                "X-Correlation-ID": "caller-selected-trace",
                "X-Forwarded-Host": "attacker.example.test",
            }
            assert (await client.post("/authenticate", headers=headers)).status_code == 200
            assert (await client.post("/authenticate", headers=headers)).status_code == 200
            rows = stored_rows(tmp_path / "receipt.sqlite")
            assert len(rows) == 2
            assert rows[0][0] != rows[1][0]
            raw = (tmp_path / "receipt.sqlite").read_bytes()
            assert b"caller-selected-attempt" not in raw
            assert b"caller-selected-trace" not in raw
            assert b"foreign-tenant" not in raw


@pytest.mark.asyncio
@pytest.mark.security
async def test_m6_http_missing_wrong_and_duplicate_auth_header_are_denied(
    tmp_path: Path,
) -> None:
    gateway = await api_gateway(store(tmp_path))
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            missing = await client.post("/authenticate")
            wrong = await client.post(
                "/authenticate", headers={"Authorization": "Bearer fake"}
            )
            duplicate = await client.post(
                "/authenticate",
                headers=[
                    ("Authorization", "ApiKey " + api_wire()),
                    ("Authorization", "ApiKey " + api_wire()),
                ],
            )
            assert signature(missing) == signature(wrong) == signature(duplicate)
            assert signature(missing) == (
                401, {"error": "invalid_credentials"}, "no-store", "nosniff"
            )
            assert [status for _, status in stored_rows(tmp_path / "receipt.sqlite")] == [
                "REJECTED", "REJECTED", "REJECTED"
            ]


@pytest.mark.asyncio
@pytest.mark.security
@pytest.mark.parametrize("mechanism", ["m4", "m5"])
async def test_m6_http_no_auth_success_when_receipt_store_removed(
    tmp_path: Path, rsa_keys, mechanism: str
) -> None:
    private, public = rsa_keys
    committer = store(tmp_path)
    if mechanism == "m4":
        gateway = await api_gateway(committer)
        method, route, headers = EvidenceMethod.API_KEY, "api", api_headers()
    else:
        gateway = jwt_gateway(committer, public)
        method, route, headers = EvidenceMethod.JWT, "jwt", jwt_headers(jwt_wire(private))
    async with tcp_host(gateway, route=route, method=method) as url:
        (tmp_path / "receipt.sqlite").unlink()
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            result = await client.post("/authenticate", headers=headers)
            assert result.status_code == 503
            assert result.json() == {"error": "temporarily_unavailable"}
            assert not (tmp_path / "receipt.sqlite").exists()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m6_http_concurrent_valid_requests_have_distinct_commits(tmp_path: Path) -> None:
    gateway = await api_gateway(store(tmp_path))
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            responses = await asyncio.gather(
                *(client.post("/authenticate", headers=api_headers()) for _ in range(5))
            )
            assert all(result.status_code == 200 for result in responses)
            rows = stored_rows(tmp_path / "receipt.sqlite")
            assert len(rows) == 5
            assert len({identifier for identifier, _ in rows}) == 5


@pytest.mark.asyncio
@pytest.mark.security
async def test_m6_http_full_audit_store_blocks_second_valid_request(tmp_path: Path) -> None:
    gateway = await api_gateway(store(tmp_path, capacity=1))
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            yes = await client.post("/authenticate", headers=api_headers())
            no = await client.post("/authenticate", headers=api_headers())
            assert yes.status_code == 200
            assert no.status_code == 503
            assert len(stored_rows(tmp_path / "receipt.sqlite")) == 1


@pytest.mark.asyncio
@pytest.mark.security
async def test_m6_http_auth_body_is_not_alternative_trust_input(tmp_path: Path) -> None:
    gateway = await api_gateway(store(tmp_path))
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            response = await client.post(
                "/authenticate", headers=api_headers(), content=b"untrusted-content"
            )
            assert response.status_code == 401
            # Early HTTP framing refusal is outside the receipt gate.
            # This reference does NOT prove full-attempt audit coverage.
            assert stored_rows(tmp_path / "receipt.sqlite") == []


def test_m6_http_factory_fails_closed_on_direct_m2_and_wrong_route(tmp_path: Path) -> None:
    gateway = asyncio.run(api_gateway(store(tmp_path)))
    with pytest.raises(ValueError, match="not host-approved"):
        compose_receipted_http_app(
            gateway=gateway, host_route_id="api", method=EvidenceMethod.JWT
        )
    with pytest.raises(ValueError, match="host route"):
        compose_receipted_http_app(
            gateway=gateway, host_route_id="foreign", method=EvidenceMethod.API_KEY
        )
    with pytest.raises(ValueError, match="unapproved HTTP"):
        compose_receipted_http_app(
            gateway=gateway._base,  # type: ignore[arg-type]
            host_route_id="api",
            method=EvidenceMethod.API_KEY,
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m6_http_write_lock_prevents_premature_positive_response(
    tmp_path: Path,
) -> None:
    gateway = await api_gateway(store(tmp_path))
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=5) as client:
            with sqlite3.connect(tmp_path / "receipt.sqlite", isolation_level=None) as db:
                db.execute("BEGIN IMMEDIATE")
                pending = asyncio.create_task(
                    client.post("/authenticate", headers=api_headers())
                )
                await asyncio.sleep(0.15)
                assert not pending.done()
                db.execute("COMMIT")
                result = await pending
                assert result.status_code == 200
            assert len(stored_rows(tmp_path / "receipt.sqlite")) == 1
