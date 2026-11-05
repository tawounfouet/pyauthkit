"""Real TLS handshake in a local JWKS host (synthetic IP routing).

A genuine asyncio TLS server is used with ephemeral test certificates. The
test substitutes only the network route and observed peer IP to exercise the
reference adapter without calling public services. It is NOT a substitute for
real deployment DNS, firewall, public CA or egress qualification.
"""

import asyncio
import ssl
from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from pyauthkit.adapters.jwks_https import PinnedHttpsJwksFetcher
from pyauthkit.domain.failure import DomainTechnicalError
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.trust import TrustProfileRef

NAME = "jwks.example.test"
PINNED_IP = "1.1.1.1"
SCOPE = TrustedScopeRef("tls-host-test")
REF = TrustProfileRef("tls-profile", "rev-1", SCOPE)
SOURCE = ApprovedJwksSource(REF, "approved", "https://jwks.example.test/keys")
BODY = b'{"keys":[]}'


def test_context(tmp_path, *, certificate_hostname: str = NAME):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, certificate_hostname)])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(minutes=5))
        .not_valid_after(datetime.now(UTC) + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(certificate_hostname)]),
            critical=False,
        )
        .sign(private, hashes.SHA256())
    )
    cert_path = tmp_path / "tls-test.crt"
    key_path = tmp_path / "tls-test.key"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(str(cert_path), str(key_path))
    client_ctx = ssl.create_default_context(cafile=str(cert_path))
    return server_ctx, client_ctx


class RoutedWriter:
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer

    def get_extra_info(self, field: str):
        if field == "peername":
            return (PINNED_IP, 443)
        return self.writer.get_extra_info(field)

    def write(self, data: bytes) -> None:
        self.writer.write(data)

    async def drain(self) -> None:
        await self.writer.drain()

    def close(self) -> None:
        self.writer.close()

    async def wait_closed(self) -> None:
        await self.writer.wait_closed()


async def exercise_tls(monkeypatch, server_ctx, client_ctx):
    requests: list[bytes] = []

    async def service(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=2.0)
            requests.append(request)
            writer.write(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/jwk-set+json\r\n"
                + f"Content-Length: {len(BODY)}\r\n\r\n".encode()
                + BODY
            )
            await writer.drain()
        except (TimeoutError, ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()

    server = await asyncio.start_server(service, "127.0.0.1", 0, ssl=server_ctx)
    port = server.sockets[0].getsockname()[1]
    original_connect = asyncio.open_connection

    async def test_route(*, host, port: int, ssl, server_hostname, **kwargs):
        assert host == PINNED_IP and port == 443 and server_hostname == NAME
        reader, writer = await original_connect(
            "127.0.0.1",
            port=server_port,
            ssl=ssl,
            server_hostname=server_hostname,
            **kwargs,
        )
        return reader, RoutedWriter(writer)

    server_port = port

    async def approved_dns(_self, _source, _hostname):
        return PINNED_IP

    monkeypatch.setattr(PinnedHttpsJwksFetcher, "_resolve", approved_dns)
    monkeypatch.setattr(asyncio, "open_connection", test_route)
    try:
        fetcher = PinnedHttpsJwksFetcher(
            sources={REF: SOURCE},
            allowed_ips={REF: (PINNED_IP,)},
            ssl_context=client_ctx,
        )
        return await fetcher.fetch(source=SOURCE), requests
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.integration
@pytest.mark.security
def test_real_tls_certificate_hostname_sni_and_body_are_verified(tmp_path, monkeypatch) -> None:
    server_ctx, client_ctx = test_context(tmp_path)
    result, requests = asyncio.run(exercise_tls(monkeypatch, server_ctx, client_ctx))
    assert result == BODY
    assert len(requests) == 1
    assert requests[0].startswith(b"GET /keys HTTP/1.1\r\nHost: jwks.example.test\r\n")
    assert b"Cookie:" not in requests[0] and b"Authorization:" not in requests[0]


@pytest.mark.security
def test_real_tls_wrong_certificate_hostname_fails_closed(tmp_path, monkeypatch) -> None:
    server_ctx, client_ctx = test_context(tmp_path, certificate_hostname="different.example.test")
    with pytest.raises(DomainTechnicalError):
        asyncio.run(exercise_tls(monkeypatch, server_ctx, client_ctx))


@pytest.mark.security
def test_real_tls_untrusted_ca_fails_closed(tmp_path, monkeypatch) -> None:
    server_ctx, _trusted_ctx = test_context(tmp_path)
    untrusted_ctx = ssl.create_default_context()
    with pytest.raises(DomainTechnicalError):
        asyncio.run(exercise_tls(monkeypatch, server_ctx, untrusted_ctx))
