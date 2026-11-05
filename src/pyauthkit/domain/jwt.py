"""M5 JWT trust-policy value objects and strictly bounded *untrusted* JWS parsing.

[DDD: Value Object] [SECURITY: Host Trust First / Algorithm Confusion]
Parsing provides NO authenticity. Only a pinned cryptographic adapter may turn
a signed token into verified claims; the M2 engine alone grants final AuthN.
"""

from __future__ import annotations

import base64
import binascii
import json
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from .identity import PrincipalType
from .scope import TrustedScopeRef
from .trust import TrustProfileRef

_BASE64URL = re.compile(rb"[A-Za-z0-9_-]+\Z")
_MAX_HEADER_BYTES = 2048
_MAX_CLAIMS_BYTES = 4096
_MAX_SIGNATURE_BYTES = 2048
_ALLOWED_HEADERS = frozenset({"alg", "kid", "typ"})


@dataclass(frozen=True, slots=True, repr=False)
class TrustedJwtVerificationProfile:
    """Immutable, bootstrap-approved policy. Never built from JWT claims/headers."""

    scope_ref: TrustedScopeRef
    profile_ref: TrustProfileRef
    issuer: str
    audience: str
    expected_typ: str = "at+jwt"
    allowed_algorithms: frozenset[str] = frozenset({"RS256"})
    principal_type: PrincipalType = PrincipalType.SERVICE
    max_token_bytes: int = 8192
    clock_skew_seconds: int = 0
    max_age_seconds: int | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.scope_ref, TrustedScopeRef)
            or not isinstance(self.profile_ref, TrustProfileRef)
            or self.profile_ref.scope_ref != self.scope_ref
        ):
            raise ValueError("JWT profile must bind one approved scope and profile")
        if (
            type(self.issuer) is not str
            or not 1 <= len(self.issuer) <= 128
            or not self.issuer.strip()
            or any(ord(char) < 33 or ord(char) == 127 for char in self.issuer)
        ):
            raise ValueError("invalid approved issuer")
        if (
            type(self.audience) is not str
            or not 1 <= len(self.audience) <= 256
            or not self.audience.strip()
            or any(ord(char) < 33 or ord(char) == 127 for char in self.audience)
        ):
            raise ValueError("invalid approved audience")
        if self.expected_typ not in ("at+jwt", "application/at+jwt"):
            raise ValueError("only explicit access JWT type is supported in M5")
        if type(self.allowed_algorithms) is not frozenset or self.allowed_algorithms != frozenset(
            {"RS256"}
        ):
            raise ValueError("M5 baseline admits RS256 only")
        if not isinstance(self.principal_type, PrincipalType):
            raise ValueError("invalid host-approved principal kind")
        if type(self.max_token_bytes) is not int or not 512 <= self.max_token_bytes <= 8192:
            raise ValueError("invalid token size limit")
        if type(self.clock_skew_seconds) is not int or not 0 <= self.clock_skew_seconds <= 120:
            raise ValueError("invalid clock leeway")
        if self.max_age_seconds is not None and (
            type(self.max_age_seconds) is not int or not 1 <= self.max_age_seconds <= 86400
        ):
            raise ValueError("invalid JWT maximum age")

    def __repr__(self) -> str:
        return "TrustedJwtVerificationProfile(<host-approved, redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class ParsedCompactJws:
    """Untrusted parsing result, deliberately not an authentication claim."""

    protected_header: MappingProxyType[str, object]
    unverified_claims: MappingProxyType[str, object]

    def __repr__(self) -> str:
        return "ParsedCompactJws(<unverified, redacted>)"


def _unique_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous JSON object")
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise ValueError("nonfinite JSON number")


def strict_json_object(data: bytes, *, maximum: int, depth: int = 8) -> dict[str, object]:
    """Parse a bounded JSON object without duplicate names or nonfinite numbers."""
    if type(data) is not bytes or len(data) > maximum or not data:
        raise ValueError("JSON boundary exceeded")
    try:
        decoded = cast(
            object,
            json.loads(
                data.decode("utf-8"),
                object_pairs_hook=_unique_members,
                parse_constant=_reject_constant,
            ),
        )
    except (UnicodeError, ValueError, TypeError, RecursionError) as error:
        raise ValueError("invalid JSON") from error
    visited = 0

    def walk(node: object, level: int) -> None:
        nonlocal visited
        visited += 1
        if level > depth or visited > 256:
            raise ValueError("JSON complexity exceeded")
        if isinstance(node, dict):
            for key, value in node.items():
                if not isinstance(key, str):
                    raise ValueError("invalid JSON key")
                walk(value, level + 1)
        elif isinstance(node, list):
            for value in node:
                walk(value, level + 1)
        elif isinstance(node, float) and not math.isfinite(node):
            raise ValueError("invalid JSON number")

    if not isinstance(decoded, dict):
        raise ValueError("expected JSON object")
    walk(decoded, 0)
    return cast(dict[str, object], decoded)


def _decode_segment(segment: bytes, *, maximum: int) -> bytes:
    if not segment or len(segment) > maximum * 2 or _BASE64URL.fullmatch(segment) is None:
        raise ValueError("noncanonical JWS segment")
    try:
        decoded = base64.urlsafe_b64decode(segment + b"=" * (-len(segment) % 4))
    except (ValueError, binascii.Error) as error:
        raise ValueError("invalid JWS encoding") from error
    if len(decoded) > maximum or base64.urlsafe_b64encode(decoded).rstrip(b"=") != segment:
        raise ValueError("noncanonical JWS encoding")
    return decoded


def parse_compact_jws(raw: bytes, *, max_token_bytes: int = 8192) -> ParsedCompactJws | None:
    """Return structural hints only; no crypto, network access or trust selection."""
    if type(raw) is not bytes or not 1 <= len(raw) <= max_token_bytes:
        return None
    segments = raw.split(b".")
    if len(segments) != 3:
        return None
    try:
        header = strict_json_object(
            _decode_segment(segments[0], maximum=_MAX_HEADER_BYTES),
            maximum=_MAX_HEADER_BYTES,
        )
        claims = strict_json_object(
            _decode_segment(segments[1], maximum=_MAX_CLAIMS_BYTES),
            maximum=_MAX_CLAIMS_BYTES,
        )
        _decode_segment(segments[2], maximum=_MAX_SIGNATURE_BYTES)
        if not header.keys() <= _ALLOWED_HEADERS:
            return None
        if (
            type(header.get("alg")) is not str
            or type(header.get("kid")) is not str
            or type(header.get("typ")) is not str
        ):
            return None
        kid = cast(str, header["kid"])
        if not 1 <= len(kid) <= 128 or not kid.isascii() or not kid.isprintable():
            return None
    except (ValueError, UnicodeError, KeyError, TypeError):
        return None
    return ParsedCompactJws(MappingProxyType(header), MappingProxyType(claims))
