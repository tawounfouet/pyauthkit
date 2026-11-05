"""Pinned HTTPS JWKS transport with DNS/IP and connection-time egress checks.

[ARCH: Ports & Adapters] [SECURITY: SSRF / DNS Rebinding / No Redirect]
The operator must approve an exact profile-source identity and *every* permitted
public destination IP. DNS is evaluated on each cache miss, ALL responses must
be approved, and TLS connects using the validated IP (never a hostname lookup).
SNI and hostname verification retain the approved hostname. No HTTP proxy,
redirect, cookie or untrusted JWT URL is used.

The host network firewall should independently enforce the same IP egress policy.
This transport does not implement certificate pinning or distributed key revocation.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import ssl
from collections.abc import Mapping
from types import MappingProxyType
from urllib.parse import urlsplit

from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.trust import TrustProfileRef

_MAX_HEADERS = 32
_MAX_HEADER_BYTES = 8192
_MAX_LINE_BYTES = 2048
_MAX_DNS_ANSWERS = 16
_IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


def _reject_transport() -> DomainTechnicalError:
    """Do not reflect DNS, URLs, tokens, IPs or TLS exception text."""
    return DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)


def _approved_ip(raw: str) -> _IPAddress:
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError:
        raise ValueError("invalid approved egress IP") from None
    if (
        not ip.is_global
        or ip.is_multicast
        or isinstance(ip, ipaddress.IPv6Address)
        and ip.ipv4_mapped is not None
    ):
        raise ValueError("non-public egress destination")
    return ip


async def _read_line(reader: asyncio.StreamReader, *, maximum: int) -> bytes:
    line = await reader.readuntil(b"\r\n")
    if len(line) > maximum or b"\r" in line[:-2] or b"\n" in line[:-2]:
        raise ValueError("invalid HTTP line")
    return line[:-2]


async def _read_response(reader: asyncio.StreamReader, limit: int) -> bytes:
    """Tightly bounded HTTP/1.1 JSON body, no redirects or compression."""
    status = await _read_line(reader, maximum=512)
    if re.fullmatch(rb"HTTP/1\.[01] 200(?: [\x20-\x7e]*)?", status) is None:
        # Includes every 3xx. There is deliberately no Location processing.
        raise ValueError("unexpected JWKS response status")
    headers: dict[str, str] = {}
    budget = len(status) + 2
    for _ in range(_MAX_HEADERS):
        line = await _read_line(reader, maximum=_MAX_LINE_BYTES)
        budget += len(line) + 2
        if budget > _MAX_HEADER_BYTES:
            raise ValueError("HTTP header budget exceeded")
        if not line:
            break
        if line[:1] in (b" ", b"\t") or b":" not in line:
            raise ValueError("invalid HTTP header")
        key, value = line.split(b":", 1)
        if re.fullmatch(rb"[A-Za-z0-9-]+", key) is None:
            raise ValueError("invalid HTTP header name")
        key_str = key.decode("ascii").lower()
        if key_str in headers:
            raise ValueError("duplicate HTTP header")
        if any(byte < 32 and byte != 9 or byte == 127 for byte in value):
            raise ValueError("invalid HTTP header value")
        headers[key_str] = value.decode("latin-1").strip().lower()
    else:
        raise ValueError("HTTP header count exceeded")
    if headers.get("content-type") not in (
        "application/json",
        "application/jwk-set+json",
        "application/json; charset=utf-8",
        "application/jwk-set+json; charset=utf-8",
    ):
        raise ValueError("unexpected JWKS media type")
    if headers.get("content-encoding", "identity") != "identity":
        raise ValueError("compressed JWKS not supported")
    transfer = headers.get("transfer-encoding")
    length_text = headers.get("content-length")
    if transfer is not None and (transfer != "chunked" or length_text is not None):
        raise ValueError("unexpected HTTP transfer encoding")
    if transfer == "chunked":
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk_line = await _read_line(reader, maximum=64)
            if re.fullmatch(rb"[0-9a-fA-F]{1,8}", chunk_line) is None:
                raise ValueError("invalid chunk header")
            size = int(chunk_line, 16)
            if size > limit - total:
                raise ValueError("JWKS response budget exceeded")
            if size == 0:
                if await _read_line(reader, maximum=64) != b"":
                    raise ValueError("HTTP trailers not allowed")
                break
            data = await reader.readexactly(size)
            if await reader.readexactly(2) != b"\r\n":
                raise ValueError("invalid chunk delimiter")
            chunks.append(data)
            total += len(data)
        if total == 0:
            raise ValueError("empty JWKS response")
        return b"".join(chunks)
    if (
        length_text is None
        or re.fullmatch(r"[0-9]{1,8}", length_text) is None
        or not 1 <= int(length_text) <= limit
    ):
        raise ValueError("missing or out-of-budget content length")
    return await reader.readexactly(int(length_text))


class PinnedHttpsJwksFetcher:
    """Explicit host trust + approved IPs + peer-IP validation + verified TLS."""

    __slots__ = ("_sources", "_allowed_ips", "_ssl")

    _sources: MappingProxyType[TrustProfileRef, ApprovedJwksSource]
    _allowed_ips: MappingProxyType[TrustProfileRef, frozenset[_IPAddress]]
    _ssl: ssl.SSLContext

    def __init__(
        self,
        *,
        sources: Mapping[TrustProfileRef, ApprovedJwksSource],
        allowed_ips: Mapping[TrustProfileRef, tuple[str, ...]],
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        if not sources or set(sources) != set(allowed_ips) or len(sources) > 128:
            raise ValueError("every approved JWKS source requires an exact IP allowlist")
        checked_sources: dict[TrustProfileRef, ApprovedJwksSource] = {}
        checked_ips: dict[TrustProfileRef, frozenset[_IPAddress]] = {}
        for ref, source in sources.items():
            if not isinstance(ref, TrustProfileRef) or (
                not isinstance(source, ApprovedJwksSource) or source.profile_ref != ref
            ):
                raise ValueError("invalid JWKS authority binding")
            raw_ips = allowed_ips[ref]
            if type(raw_ips) is not tuple or not 1 <= len(raw_ips) <= _MAX_DNS_ANSWERS:
                raise ValueError("invalid exact IP egress allowlist")
            checked_sources[ref] = source
            checked_ips[ref] = frozenset(_approved_ip(value) for value in raw_ips)
        ctx = ssl_context if ssl_context is not None else ssl.create_default_context()
        if (
            not isinstance(ctx, ssl.SSLContext)
            or ctx.verify_mode != ssl.CERT_REQUIRED
            or not ctx.check_hostname
            or ctx.minimum_version < ssl.TLSVersion.TLSv1_2
        ):
            raise ValueError("verified TLS 1.2+ and hostname validation required")
        object.__setattr__(self, "_sources", MappingProxyType(checked_sources))
        object.__setattr__(self, "_allowed_ips", MappingProxyType(checked_ips))
        object.__setattr__(self, "_ssl", ctx)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("JWKS transport composition cannot be mutated")

    def __repr__(self) -> str:
        return "PinnedHttpsJwksFetcher(<redacted, egress-approved>)"

    async def _resolve(self, source: ApprovedJwksSource, hostname: str) -> str:
        loop = asyncio.get_running_loop()
        records = await loop.getaddrinfo(
            hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        if not 1 <= len(records) <= _MAX_DNS_ANSWERS:
            raise ValueError("invalid DNS answer count")
        permitted = self._allowed_ips[source.profile_ref]
        addresses: list[_IPAddress] = []
        for _family, _type, _proto, _canonical, sockaddr in records:
            ip = _approved_ip(sockaddr[0])
            if ip not in permitted:
                # Reject the whole DNS response, never choose the one good address.
                raise ValueError("DNS destination outside egress allowlist")
            addresses.append(ip)
        if not addresses:
            raise ValueError("empty DNS response")
        # Connect to the literal approved IP; no second hostname lookup.
        return str(addresses[0])

    async def fetch(self, *, source: ApprovedJwksSource) -> bytes:
        if not isinstance(source, ApprovedJwksSource) or (
            self._sources.get(source.profile_ref) is not source
        ):
            raise _reject_transport()
        parsed = urlsplit(source.uri)
        hostname = parsed.hostname
        if hostname is None:
            raise _reject_transport()
        path = parsed.path
        if re.fullmatch(r"/[A-Za-z0-9._~!$&'()*+,;=:@/%-]*", path) is None:
            raise _reject_transport()
        writer: asyncio.StreamWriter | None = None
        try:
            async with asyncio.timeout(source.timeout_seconds):
                address = await self._resolve(source, hostname)
                reader, writer = await asyncio.open_connection(
                    host=address,
                    port=443,
                    ssl=self._ssl,
                    server_hostname=hostname,
                    ssl_handshake_timeout=source.timeout_seconds,
                    limit=_MAX_HEADER_BYTES,
                )
                peer = writer.get_extra_info("peername")
                ssl_object = writer.get_extra_info("ssl_object")
                if (
                    not isinstance(peer, tuple)
                    or not peer
                    or _approved_ip(peer[0]) != ipaddress.ip_address(address)
                    or ssl_object is None
                    or ssl_object.getpeercert() is None
                ):
                    raise ValueError("unverified JWKS transport peer")
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {hostname}\r\n"
                    "Accept: application/jwk-set+json, application/json\r\n"
                    "Accept-Encoding: identity\r\n"
                    "Connection: close\r\n\r\n"
                )
                writer.write(request.encode("ascii"))
                await writer.drain()
                return await _read_response(reader, source.max_response_bytes)
        except asyncio.CancelledError:
            raise
        except Exception:
            raise _reject_transport() from None
        finally:
            if writer is not None:
                writer.close()
                # TLS shutdown is non-authoritative; never wait indefinitely.
                try:
                    await asyncio.wait_for(writer.wait_closed(), timeout=0.2)
                except (TimeoutError, OSError, ssl.SSLError):
                    pass
