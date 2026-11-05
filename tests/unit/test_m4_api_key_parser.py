"""M4 PR-07B: structural/canonical parser checks, not AuthN outcomes."""

import base64
import copy
import pickle

import pytest
from hypothesis import given, settings, strategies as st

from pyauthkit.domain.api_key_format import (
    API_KEY_WIRE_BYTES,
    OpaqueApiKeyParser,
    ParsedOpaqueApiKey,
)


def encoded_key(
    selector: bytes = bytes(range(16)), secret: bytes = bytes(range(32))
) -> bytes:
    token = lambda part: base64.urlsafe_b64encode(part).rstrip(b"=")
    return b"ak1." + token(selector) + b"." + token(secret)


@pytest.mark.unit
def test_valid_opaque_key_has_exact_canonical_length() -> None:
    raw = encoded_key()
    assert len(raw) == API_KEY_WIRE_BYTES == 70
    result = OpaqueApiKeyParser.parse(raw)
    assert isinstance(result, ParsedOpaqueApiKey)
    assert result.key_id == "AAECAwQFBgcICQoLDA0ODw"
    assert result.secret_bytes == bytes(range(32))
    assert result.format_version == "ak1"


@pytest.mark.security
@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"ak1",
        b"ak0." + encoded_key()[4:],
        b"ak2." + encoded_key()[4:],
        encoded_key()[:-1],
        encoded_key() + b"a",
        encoded_key() + b"\n",
        encoded_key().replace(b".", b":", 1),
        encoded_key().replace(b".", b"..", 1),
        encoded_key().replace(b".", b"%2e", 1),
        encoded_key().replace(b"-", b"+", 1) + b" ",
        encoded_key()[:4] + b"A" * 22 + b"." + b"A" * 43,
        encoded_key()[:25] + b"x" + encoded_key()[26:],
        encoded_key()[:69] + b"9",
        encoded_key()[:26] + b"." + b"*" + encoded_key()[28:],
        b"\xc3\xa9" + encoded_key()[2:],
        b"ak1." + b"A" * 22 + b"." + b"A" * 43 + b"=",
        b"ak1." + b"A" * 22 + b"." + b"A" * 42,
    ],
)
def test_noncanonical_truncated_or_modified_input_is_rejected(raw: bytes) -> None:
    assert OpaqueApiKeyParser.parse(raw) is None


@pytest.mark.security
def test_parser_rejects_non_bytes_and_not_single_byte_secrets() -> None:
    assert OpaqueApiKeyParser.parse("not bytes") is None  # type: ignore[arg-type]
    assert OpaqueApiKeyParser.parse(bytearray(encoded_key())) is None  # type: ignore[arg-type]
    assert OpaqueApiKeyParser.parse(encoded_key(secret=b"x")) is None


@pytest.mark.security
def test_parser_rejects_noncanonical_unused_base64_bits() -> None:
    raw = encoded_key()
    # The last base64url char in 16-byte encoding has four unused low bits.
    assert raw[25:26] == b"w"
    assert OpaqueApiKeyParser.parse(raw[:25] + b"x" + raw[26:]) is None
    # The last base64url char in a 32-byte encoding has two unused low bits.
    assert raw[-1:] == b"8"
    assert OpaqueApiKeyParser.parse(raw[:-1] + b"9") is None


@pytest.mark.security
def test_parsed_bearer_does_not_serialize_or_leak_repr() -> None:
    key = OpaqueApiKeyParser.parse(encoded_key())
    assert key is not None
    assert key.key_id not in repr(key)
    assert "AAECAwQ" not in repr(key)
    assert "bytes" not in repr(key)
    with pytest.raises(AttributeError):
        key._secret = b"overwrite"  # type: ignore[misc]
    with pytest.raises(TypeError):
        copy.deepcopy(key)
    with pytest.raises(TypeError):
        pickle.dumps(key)


@pytest.mark.security
def test_direct_construction_still_checks_selector_and_secret() -> None:
    with pytest.raises(ValueError):
        ParsedOpaqueApiKey(key_id="bad", secret=bytes(range(32)))
    with pytest.raises(ValueError):
        ParsedOpaqueApiKey(key_id="AAECAwQFBgcICQoLDA0ODw", secret=b"short")


@pytest.mark.security
@settings(max_examples=80, deadline=None)
@given(st.binary(min_size=0, max_size=150))
def test_parser_never_returns_a_truncated_secret(raw: bytes) -> None:
    parsed = OpaqueApiKeyParser.parse(raw)
    if parsed is not None:
        assert len(raw) == API_KEY_WIRE_BYTES
        assert len(parsed.secret_bytes) == 32
