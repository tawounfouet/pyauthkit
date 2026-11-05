"""M5 pinned HTTPS transport adversarial contract tests (no external traffic).

These tests prove DNS/address policy and HTTP failure semantics under controlled
fakes. They do NOT prove firewall enforcement or public-provider TLS operations.
"""

import asyncio
import json
import ssl
from collections.abc import Callable

import pytest

from pyauthkit.adapters.jwks_cache import CachedApprovedJwksKeyResolver
from pyauthkit.adapters.jwks_https import PinnedHttpsJwksFetcher
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.trust import TrustProfileRef

ALLOWED_IP = "1.1.1.1"
HOST = "jwks.example.test"
SCOPE = TrustedScopeRef("test:production")
PROFILE = TrustProfileRef("orders", "v1", SCOPE)
SOURCE = ApprovedJwksSource(PROFILE, "issuer-1", "https://jwks.example.test/keys")
PROFILE_CONFIG = TrustedJwtVerificationProfile(
    SCOPE, PROFILE, "https://issuer.example.test", "orders"
)
JWK = {
    "kty": "RSA",
    "kid": "r1",
    "use": "sig",
    "alg": "RS256",
    "n": "AQ" + "A" * 339,
    "e": "AQAB",
}
BODY = json.dumps({"keys": [JWK]}).encode()


class PeerTLS:
    def getpeercert(self) -> dict[str, str]:
        return {"subject": "verified-in-fixture"}


class FakeStreamWriter:
    def __init__(self, peer: str, *, verified: bool = True) -> None:
        self.peer = peer
        self.verified = verified
        self.sent = bytearray()
        self.closed = False

    def get_extra_info(self, key: str):
        if key == "peername":
            return (self.peer, 443)
        if key == "ssl_object":
            return PeerTLS() if self.verified else None
        return None

    def write(self, value: bytes) -> None:
        self.sent.extend(value)

    async def drain(self) -> None:
        await asyncio.sleep(0)

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        return None


def raw_response(
    body: bytes = BODY, *, status: int = 200, headers: bytes = b"", length: bool = True
) -> bytes:
    return (
        f"HTTP/1.1 {status} synthetic\r\n".encode()
        + b"Content-Type: application/jwk-set+json\r\n"
        + (f"Content-Length: {len(body)}\r\n".encode() if length else b"")
        + headers
        + b"\r\n"
        + body
    )


class SimulatedInternet:
    def __init__(self, response: bytes = raw_response()) -> None:
        self.dns = [ALLOWED_IP]
        self.response = response
        self.calls = 0
        self.dns_calls = 0
        self.peers: list[str] = []
        self.writers: list[FakeStreamWriter] = []
        self.certified = True
        self.outage = False
        self.delay = 0

    async def lookup(self, _loop, host: str, port: int, **kwargs):
        assert host == HOST and port == 443
        assert kwargs["type"] > 0
        self.dns_calls += 1
        return [(2, 1, 6, "", (ip, 443)) for ip in self.dns]

    async def connect(self, *, host: str, port: int, ssl, server_hostname: str, **kwargs):
        self.calls += 1
        self.peers.append(host)
        assert port == 443 and server_hostname == HOST
        assert ssl.check_hostname and ssl.verify_mode == ssl_module.CERT_REQUIRED
        if self.outage:
            raise OSError("SENSITIVE_NETWORK_ERROR")
        if self.delay:
            await asyncio.sleep(self.delay)
        reader = asyncio.StreamReader()
        reader.feed_data(self.response)
        reader.feed_eof()
        writer = FakeStreamWriter(host, verified=self.certified)
        self.writers.append(writer)
        return reader, writer


ssl_module = ssl


def exercise(
    monkeypatch, scenario: SimulatedInternet, *,
    source: ApprovedJwksSource = SOURCE, allowed: tuple[str, ...] = (ALLOWED_IP,),
):
    original = asyncio.BaseEventLoop.getaddrinfo

    async def dns(self, host, port, **kwargs):
        return await scenario.lookup(self, host, port, **kwargs)

    monkeypatch.setattr(asyncio.BaseEventLoop, "getaddrinfo", dns)
    monkeypatch.setattr(asyncio, "open_connection", scenario.connect)
    del original
    return PinnedHttpsJwksFetcher(
        sources={source.profile_ref: source},
        allowed_ips={source.profile_ref: allowed},
    )


@pytest.mark.security
def test_approved_ip_dns_tls_metadata_and_bounded_jwks(monkeypatch) -> None:
    internet = SimulatedInternet()
    fetcher = exercise(monkeypatch, internet)
    assert asyncio.run(fetcher.fetch(source=SOURCE)) == BODY
    assert internet.calls == internet.dns_calls == 1
    assert internet.peers == [ALLOWED_IP]
    assert internet.writers[0].closed
    wire = bytes(internet.writers[0].sent)
    assert wire.startswith(b"GET /keys HTTP/1.1\r\nHost: jwks.example.test\r\n")
    assert b"Cookie:" not in wire and b"Authorization:" not in wire
    assert b"Accept-Encoding: identity\r\n" in wire


@pytest.mark.security
@pytest.mark.parametrize(
    "invalid_dns",
    [
        ["127.0.0.1"],
        ["10.0.0.2"],
        ["169.254.169.254"],
        ["::1"],
        ["::ffff:127.0.0.1"],
        [ALLOWED_IP, "10.0.0.2"],
        [ALLOWED_IP, "9.9.9.9"],
        [],
        ["9.9.9.9"],
    ],
)
def test_ssrf_invalid_dns_and_mixed_records_never_connect(monkeypatch, invalid_dns) -> None:
    internet = SimulatedInternet()
    internet.dns = invalid_dns
    fetcher = exercise(monkeypatch, internet)
    with pytest.raises(DomainTechnicalError) as raised:
        asyncio.run(fetcher.fetch(source=SOURCE))
    assert raised.value.code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert internet.calls == 0


@pytest.mark.security
def test_rebinding_to_private_address_after_first_approved_fetch(monkeypatch) -> None:
    internet = SimulatedInternet()
    fetcher = exercise(monkeypatch, internet)
    assert asyncio.run(fetcher.fetch(source=SOURCE)) == BODY
    internet.dns = ["169.254.169.254"]
    with pytest.raises(DomainTechnicalError):
        asyncio.run(fetcher.fetch(source=SOURCE))
    assert internet.calls == 1


@pytest.mark.security
@pytest.mark.parametrize("response", [
    raw_response(status=301, headers=b"Location: http://127.0.0.1/\r\n"),
    raw_response(status=307, headers=b"Location: https://other.example.test/keys\r\n"),
    raw_response(status=500),
    raw_response(headers=b"Content-Encoding: gzip\r\n"),
    raw_response(headers=b"Content-Length: 4\r\n"),
    raw_response(headers=b"Transfer-Encoding: chunked\r\n"),
    raw_response(headers=b"Content-Type: text/plain\r\n"),
    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 99999999\r\n\r\nx",
    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{}",
    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 6\r\n\r\nxx",
])
def test_redirect_compression_header_smuggling_and_truncation_fail_closed(
    monkeypatch, response: bytes
) -> None:
    internet = SimulatedInternet(response)
    fetcher = exercise(monkeypatch, internet)
    with pytest.raises(DomainTechnicalError):
        asyncio.run(fetcher.fetch(source=SOURCE))
    assert internet.calls == 1
    assert internet.writers[0].closed


@pytest.mark.security
def test_valid_chunked_jwks_is_bounded(monkeypatch) -> None:
    internet = SimulatedInternet(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/jwk-set+json\r\n"
        b"Transfer-Encoding: chunked\r\n\r\n"
        + f"{len(BODY):x}\r\n".encode() + BODY + b"\r\n0\r\n\r\n"
    )
    fetcher = exercise(monkeypatch, internet)
    assert asyncio.run(fetcher.fetch(source=SOURCE)) == BODY


@pytest.mark.security
def test_missing_tls_peer_proof_blocks_result(monkeypatch) -> None:
    internet = SimulatedInternet()
    internet.certified = False
    fetcher = exercise(monkeypatch, internet)
    with pytest.raises(DomainTechnicalError):
        asyncio.run(fetcher.fetch(source=SOURCE))
    assert internet.writers[0].closed


@pytest.mark.security
def test_unapproved_catalog_clone_cannot_retarget_transport(monkeypatch) -> None:
    internet = SimulatedInternet()
    fetcher = exercise(monkeypatch, internet)
    duplicate = ApprovedJwksSource(PROFILE, "issuer-1", SOURCE.uri)
    with pytest.raises(DomainTechnicalError):
        asyncio.run(fetcher.fetch(source=duplicate))
    assert internet.dns_calls == 0


@pytest.mark.security
def test_unverified_tls_context_and_private_allowlist_refused_at_bootstrap() -> None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    with pytest.raises(ValueError, match="verified TLS"):
        PinnedHttpsJwksFetcher(
            sources={PROFILE: SOURCE}, allowed_ips={PROFILE: (ALLOWED_IP,)},
            ssl_context=ctx,
        )
    with pytest.raises(ValueError, match="non-public"):
        PinnedHttpsJwksFetcher(
            sources={PROFILE: SOURCE}, allowed_ips={PROFILE: ("127.0.0.1",)}
        )


@pytest.mark.security
def test_network_failure_and_timeout_redact_cause(monkeypatch) -> None:
    internet = SimulatedInternet()
    internet.outage = True
    fetcher = exercise(monkeypatch, internet)
    with pytest.raises(DomainTechnicalError) as raised:
        asyncio.run(fetcher.fetch(source=SOURCE))
    assert "SENSITIVE_NETWORK_ERROR" not in repr(raised.value)
    internet.outage = False
    internet.delay = 1
    short_source = ApprovedJwksSource(
        PROFILE, "issuer-1", SOURCE.uri, timeout_seconds=0.1
    )
    fetcher = exercise(monkeypatch, internet, source=short_source)
    with pytest.raises(DomainTechnicalError):
        asyncio.run(fetcher.fetch(source=short_source))


@pytest.mark.integration
def test_approved_transport_connects_to_scoped_cache_without_jwt_source_control(
    monkeypatch,
) -> None:
    internet = SimulatedInternet()
    fetcher = exercise(monkeypatch, internet)
    resolver = CachedApprovedJwksKeyResolver(
        sources={PROFILE: SOURCE}, fetcher=fetcher
    )

    async def lookups():
        return await asyncio.gather(
            resolver.resolve_key(
                profile=PROFILE_CONFIG, kid_hint="r1", algorithm_hint="RS256"
            ),
            resolver.resolve_key(
                profile=PROFILE_CONFIG, kid_hint="unknown", algorithm_hint="RS256"
            ),
        )

    found, missing = asyncio.run(lookups())
    assert found is not None and missing is None
    assert internet.calls == 1
