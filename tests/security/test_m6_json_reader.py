"""M6 canonical JSON ingestion: duplicates, huge values and NaN fail closed."""

import json

import pytest

from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    load_approved_json_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected

PROVENANCE = SourceProvenance("operator", "json", "revision-1")
POLICY = SourcePolicy(frozenset({("operator", "json")}))


def v1() -> dict[str, object]:
    return {
        "schema_version": 1,
        "routes": [
            {
                "route_id": "api",
                "scope": "tenant-a",
                "profile_id": "p",
                "profile_version": "v1",
                "allowed_methods": ["jwt"],
            }
        ],
        "timeout_seconds": 1.0,
        "audit_delivery": "best_effort",
        "secrets": [],
    }


def decode(data: bytes):
    return load_approved_json_configuration(
        data,
        provenance=PROVENANCE,
        policy=POLICY,
        generation=ConfigurationGeneration(1),
    )


def test_v1_json_round_trip_keeps_single_approved_route() -> None:
    snapshot = decode(json.dumps(v1()).encode())
    assert snapshot.bindings[0].route_id == "api"
    assert snapshot.schema_version == 1


def test_m6_t05_duplicate_top_level_security_member_rejected() -> None:
    raw = json.dumps(v1()).replace(
        '"schema_version": 1', '"schema_version": 1, "schema_version": 2'
    )
    with pytest.raises(ConfigurationRejected, match="duplicate configuration member"):
        decode(raw.encode())


def test_m6_t05_duplicate_nested_route_member_rejected() -> None:
    raw = json.dumps(v1()).replace(
        '"scope": "tenant-a"', '"scope": "tenant-a", "scope": "tenant-b"'
    )
    with pytest.raises(ConfigurationRejected, match="duplicate configuration member"):
        decode(raw.encode())


def test_m6_t05_duplicate_v2_issuer_member_cannot_swap_authority() -> None:
    raw = v1()
    raw["schema_version"] = 2
    raw["jwt_profiles"] = [
        {
            "scope": "tenant-a",
            "profile_id": "p",
            "profile_version": "v1",
            "issuer": "https://approved.example.test",
            "audience": "orders-api",
            "expected_typ": "at+jwt",
            "allowed_algorithms": ["RS256"],
            "principal_type": "service",
            "max_token_bytes": 8192,
            "clock_skew_seconds": 0,
            "max_age_seconds": None,
            "key_source": {"kind": "static", "keyset_ref": "approved-public-jwk"},
        }
    ]
    good = decode(json.dumps(raw).encode())
    assert good.schema_version == 2
    injected = json.dumps(raw).replace(
        '"issuer": "https://approved.example.test"',
        '"issuer": "https://approved.example.test", "issuer": "https://other.example.test"',
    )
    with pytest.raises(ConfigurationRejected, match="duplicate configuration member"):
        decode(injected.encode())


def test_m6_json_reader_rejects_oversized_and_invalid_utf8() -> None:
    with pytest.raises(ConfigurationRejected, match="byte budget"):
        decode(b"{" + b"x" * 262144)
    with pytest.raises(ConfigurationRejected):
        decode(b"\xff\xfe")


@pytest.mark.parametrize("raw", [b"[]", b"null", b"NaN", b'{"x": NaN}', b'{"x": 1e999}'])
def test_m6_json_reader_rejects_nonobject_and_nonfinite(raw: bytes) -> None:
    with pytest.raises(ConfigurationRejected):
        decode(raw)


def test_m6_json_reader_rejects_deep_untrusted_nested_data() -> None:
    raw = b'{"deep":' + b"[" * 20 + b"0" + b"]" * 20 + b"}"
    with pytest.raises(ConfigurationRejected, match="complexity"):
        decode(raw)


def test_m6_json_reader_rejects_untrusted_source_before_parsing() -> None:
    with pytest.raises(ConfigurationRejected, match="not approved"):
        load_approved_json_configuration(
            b"not-json",
            provenance=SourceProvenance("attacker", "json", "revision-1"),
            policy=POLICY,
            generation=ConfigurationGeneration(1),
        )
