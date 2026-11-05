"""M6-T06: explicit precedence without partial security-policy merges."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourceLayerPolicy,
    SourcePolicy,
    SourceProvenance,
    load_layered_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected

AUTHORITY = SourceProvenance("security-root", "host", "rev-a")
OPS_LOW = SourceProvenance("deployment", "host", "rev-b")
OPS_HIGH = SourceProvenance("operator", "host", "rev-c")
SOURCE_POLICY = SourcePolicy(
    frozenset({
        ("security-root", "host"),
        ("deployment", "host"),
        ("operator", "host"),
    })
)
PRECEDENCE = SourceLayerPolicy(
    authority=("security-root", "host"),
    operational_overrides=(("deployment", "host"), ("operator", "host")),
)


def authority_config() -> dict[str, object]:
    return {
        "schema_version": 1,
        "routes": [
            {
                "route_id": "protected",
                "scope": "tenant-a",
                "profile_id": "jwt-profile",
                "profile_version": "v3",
                "allowed_methods": ["jwt"],
            }
        ],
        "timeout_seconds": 2.0,
        "audit_delivery": "best_effort",
        "secrets": [],
    }


def load(overrides=None, *, policy=PRECEDENCE, provenance=AUTHORITY):
    if overrides is None:
        overrides = (
            (OPS_LOW, {"timeout_seconds": 3.0}),
            (OPS_HIGH, {"timeout_seconds": 1.5}),
        )
    return load_layered_configuration(
        authority_config(),
        authority_provenance=provenance,
        operational_layers=overrides,
        layering_policy=policy,
        source_policy=SOURCE_POLICY,
        generation=ConfigurationGeneration(3),
    )


def test_m6_t06_last_explicit_host_order_wins_only_for_timeout() -> None:
    snapshot = load()
    assert snapshot.timeout_seconds == 1.5
    assert snapshot.provenance is AUTHORITY
    assert snapshot.operational_sources == (OPS_LOW, OPS_HIGH)
    assert snapshot.bindings[0].scope_ref.value == "tenant-a"
    assert snapshot.bindings[0].profile_ref.version == "v3"
    assert snapshot.audit_delivery.mode == "best_effort"
    assert snapshot.generation.value == 3


def test_m6_t06_precedence_order_is_not_inferred_from_input_order() -> None:
    with pytest.raises(ConfigurationRejected, match="precedence mismatch"):
        load(((OPS_HIGH, {"timeout_seconds": 1.0}), (OPS_LOW, {"timeout_seconds": 2.0})))


@pytest.mark.parametrize(
    "forbidden",
    [
        {"route_id": "public"},
        {"routes": []},
        {"jwt_profiles": []},
        {"secrets": []},
        {"audit_delivery": "required"},
        {"schema_version": 2},
        {"issuer": "https://another.example.test"},
        {"timeout_seconds": 1.0, "routes": []},
    ],
)
def test_m6_t06_operational_layer_cannot_change_security_fields(forbidden) -> None:
    with pytest.raises(ConfigurationRejected, match="trust-bearing"):
        load(((OPS_LOW, forbidden), (OPS_HIGH, {"timeout_seconds": 1.5})))


def test_m6_t06_missing_layer_never_falls_back_to_root() -> None:
    with pytest.raises(ConfigurationRejected, match="incomplete"):
        load(((OPS_LOW, {"timeout_seconds": 1.0}),))


def test_m6_t06_unknown_source_denied_before_parsing_root() -> None:
    attacker = SourceProvenance("attacker", "host", "rev-unknown")
    with pytest.raises(ConfigurationRejected, match="unapproved authoritative"):
        load(provenance=attacker)


def test_m6_t06_unapproved_override_source_denied() -> None:
    spoofed = SourceProvenance("attacker", "host", "rev-c")
    with pytest.raises(ConfigurationRejected, match="precedence mismatch"):
        load(((OPS_LOW, {"timeout_seconds": 3.0}), (spoofed, {"timeout_seconds": 1.5})))


def test_m6_t06_explicit_policy_rejects_duplicate_or_unbounded_sources() -> None:
    with pytest.raises(ConfigurationRejected, match="duplicate"):
        SourceLayerPolicy(authority=("root", "host"), operational_overrides=(("root", "host"),))
    with pytest.raises(ConfigurationRejected):
        SourceLayerPolicy(
            authority=("root", "host"),
            operational_overrides=tuple((f"ops{i}", "host") for i in range(5)),
        )


@pytest.mark.parametrize("timeout", [-1, 0, 31, True, float("inf"), float("nan"), "2"])
def test_m6_t06_bad_operational_timeout_is_not_admitted(timeout) -> None:
    with pytest.raises(ConfigurationRejected, match="timeout"):
        load(((OPS_LOW, {"timeout_seconds": timeout}), (OPS_HIGH, {"timeout_seconds": 1.5})))


def test_m6_t06_raw_overlay_mutation_cannot_change_activated_snapshot() -> None:
    raw = {"timeout_seconds": 3.0}
    snapshot = load(((OPS_LOW, raw), (OPS_HIGH, {"timeout_seconds": 1.0})))
    raw["timeout_seconds"] = 29.0
    raw["routes"] = deepcopy(authority_config()["routes"])
    assert snapshot.timeout_seconds == 1.0
    with pytest.raises(FrozenInstanceError):
        snapshot.operational_sources = ()  # type: ignore[misc]


def test_m6_t06_authority_only_requires_explicit_empty_policy() -> None:
    policy = SourceLayerPolicy(("security-root", "host"))
    result = load((), policy=policy)
    assert result.timeout_seconds == 2.0
    assert result.operational_sources == ()
