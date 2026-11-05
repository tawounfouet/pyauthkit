"""Strict structural parsing of M4 opaque API-key evidence (PR-07B).

[DDD: Value Object] [SECURITY: Untrusted Evidence / Canonical Encoding]
Parsing proves neither possession nor credential status. Only the host-approved
verifier can evaluate the complete 32-byte secret against a scoped record.
"""

from __future__ import annotations

import base64
import binascii
import re
from typing import Never, SupportsIndex

# Candidate wire format: ak1.<base64url(16 selector bytes)>.<base64url(32 secret bytes)>
# The fixed length prevents padding, whitespace, double-decoding and ambiguity.
_API_KEY_PATTERN = re.compile(rb"ak1\.([A-Za-z0-9_-]{22})\.([A-Za-z0-9_-]{43})\Z")
API_KEY_WIRE_BYTES = 70
WIRE_FORMAT_VERSION = "ak1"


def _canonical_decode(encoded: bytes, *, expected_length: int) -> bytes | None:
    padding = b"=" * (-len(encoded) % 4)
    try:
        decoded = base64.b64decode(encoded + padding, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(decoded) != expected_length:
        return None
    if base64.urlsafe_b64encode(decoded).rstrip(b"=") != encoded:
        return None
    return decoded


class ParsedOpaqueApiKey:
    """Parsed untrusted bearer; no default repr, equality or serialization.

    Python byte storage does not provide guaranteed zeroization. This type is
    deliberately not an authentication result or a verified credential.
    """

    __slots__ = ("_key_id", "_secret")

    _key_id: str
    _secret: bytes

    def __init__(self, *, key_id: str, secret: bytes) -> None:
        # Structural validation also applies to direct construction.
        if not isinstance(key_id, str):
            raise ValueError("invalid opaque API key")
        try:
            selector = key_id.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("invalid opaque API key") from exc
        if len(selector) != 22 or _canonical_decode(selector, expected_length=16) is None:
            raise ValueError("invalid opaque API key")
        if type(secret) is not bytes or len(secret) != 32:
            raise ValueError("invalid opaque API key")
        object.__setattr__(self, "_key_id", key_id)
        object.__setattr__(self, "_secret", secret)

    @property
    def format_version(self) -> str:
        return WIRE_FORMAT_VERSION

    @property
    def key_id(self) -> str:
        """Public selector, still sensitive operational metadata, not a proof."""
        return self._key_id

    @property
    def secret_bytes(self) -> bytes:
        """Complete bearer secret for an *approved* verifier, never for logs."""
        return self._secret

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("parsed API key is immutable")

    def __repr__(self) -> str:
        return "ParsedOpaqueApiKey(<redacted, unverified>)"

    def __deepcopy__(self, _memo: dict[int, object]) -> Never:
        raise TypeError("sensitive API-key evidence cannot be deep-copied")

    def __reduce_ex__(self, _protocol: SupportsIndex) -> Never:
        raise TypeError("sensitive API-key evidence cannot be pickled")


class OpaqueApiKeyParser:
    """Pure bounded parser. Returns None for every malformed input."""

    __slots__ = ()

    @staticmethod
    def parse(presented: bytes) -> ParsedOpaqueApiKey | None:
        if type(presented) is not bytes or len(presented) != API_KEY_WIRE_BYTES:
            return None
        match = _API_KEY_PATTERN.fullmatch(presented)
        if match is None:
            return None
        selector, encoded_secret = match.groups()
        if _canonical_decode(selector, expected_length=16) is None:
            return None
        secret = _canonical_decode(encoded_secret, expected_length=32)
        if secret is None:
            return None
        return ParsedOpaqueApiKey(key_id=selector.decode("ascii"), secret=secret)
