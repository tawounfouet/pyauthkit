"""Host-approved JWKS source descriptor; NOT a client-supplied URL.

A source declaration is not an egress firewall. The operator-provided transport
must also pin DNS/address policy at connection time and reject redirects.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .trust import TrustProfileRef

_HOSTNAME = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\Z")
_FORBIDDEN_SUFFIXES = (".localhost", ".local", ".internal", ".invalid")


@dataclass(frozen=True, slots=True, repr=False)
class ApprovedJwksSource:
    """Immutable host bootstrap authority for one versioned trust profile."""

    profile_ref: TrustProfileRef
    source_id: str
    uri: str
    ttl_seconds: int = 120
    timeout_seconds: float = 2.0
    max_response_bytes: int = 16384
    max_keys: int = 32

    def __post_init__(self) -> None:
        if not isinstance(self.profile_ref, TrustProfileRef):
            raise ValueError("missing approved JWKS profile")
        if (
            type(self.source_id) is not str
            or not 1 <= len(self.source_id) <= 64
            or not re.fullmatch(r"[A-Za-z0-9_.:-]+", self.source_id)
        ):
            raise ValueError("invalid JWKS source id")
        if type(self.uri) is not str or len(self.uri) > 512:
            raise ValueError("invalid JWKS URL")
        try:
            parsed = urlsplit(self.uri)
            hostname = parsed.hostname
            port = parsed.port
        except ValueError as error:
            raise ValueError("invalid JWKS URL") from error
        if (
            parsed.scheme != "https"
            or hostname is None
            or port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or not parsed.path.startswith("/")
            or not hostname.isascii()
            or not _HOSTNAME.fullmatch(hostname)
            or "." not in hostname
            or hostname == "localhost"
            or hostname.endswith(_FORBIDDEN_SUFFIXES)
        ):
            raise ValueError("JWKS URL must be a pinned HTTPS public DNS origin")
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            pass
        else:
            raise ValueError("IP-literal JWKS endpoints are not approved")
        if type(self.ttl_seconds) is not int or not 1 <= self.ttl_seconds <= 300:
            raise ValueError("invalid JWKS cache TTL")
        if type(self.timeout_seconds) not in (int, float) or not (
            0.1 <= self.timeout_seconds <= 3.0
        ):
            raise ValueError("invalid JWKS timeout")
        if type(self.max_response_bytes) is not int or not 1024 <= self.max_response_bytes <= 65536:
            raise ValueError("invalid JWKS byte budget")
        if type(self.max_keys) is not int or not 1 <= self.max_keys <= 32:
            raise ValueError("invalid JWKS key budget")

    def __repr__(self) -> str:
        return "ApprovedJwksSource(<host-approved, redacted>)"
