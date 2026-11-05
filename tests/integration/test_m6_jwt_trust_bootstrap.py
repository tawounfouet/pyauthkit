"""M6 v2 host-controlled M5 JWT authentication and JWKS egress boundaries.

Synthetic RSA fixture. No external network calls, no production deployment
claims. The exact M2 AuthN/Policy chain handles the signed token.
"""

import asyncio
import base64
import json
from copy import deepcopy
from datetime import UTC, datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    compose_authentication_engine,
    compose_trusted_jwt_runtime,
    load_approved_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.temporal import CorrelationId

NOW = 1793880000
SCOPE = "tenant-a:production"
ISSUER = "https://issuer.example.test"
AUDIENCE = "orders-api"
KEYSET = "public-jwks-tenant-a"


@pytest.fixture(scope="module")
def rsa_fixture() -> tuple[rsa.RSAPrivateKey, str]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private.public_key().public_numbers()

    def b64_integer(number: int) -> str:
        raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    return (
        private,
        json.dumps(
            {
                "kty": "RSA",
                "kid": "host-approved-kid",
                "alg": "RS256",
                "use": "sig",
                "n": b64_integer(numbers.n),
                "e": b64_integer(numbers.e),
            }
        ),
    )


class FixedClock:
    def now(self) -> datetime:
        return datetime.fromtimestamp(NOW, UTC)


def raw_config(*, source: dict[str, object] | None = None) -> dict[str, object]:
    selected = {"kind": "static", "keyset_ref": KEYSET} if source is None else source
    return {
        "schema_version": 2,
        "routes": [
            {
                "route_id": "orders",
                "scope": SCOPE,
                "profile_id": "jwt-orders",
                "profile_version": "v1",
                "allowed_methods": ["jwt"],
            }
        ],
        "timeout_seconds": 3.0,
        "audit_delivery": "best_effort",
        "secrets": [],
        "jwt_profiles": [
            {
                "scope": SCOPE,
                "profile_id": "jwt-orders",
                "profile_version": "v1",
                "issuer": ISSUER,
                "audience": AUDIENCE,
                "expected_typ": "at+jwt",
                "allowed_algorithms": ["RS256"],
                "principal_type": "service",
                "max_token_bytes": 8192,
                "clock_skew_seconds": 0,
                "max_age_seconds": None,
                "key_source": selected,
            }
        ],
    }


def approved(raw: dict[str, object] | None = None):
    return load_approved_configuration(
        raw_config() if raw is None else raw,
        provenance=SourceProvenance("host", "mapping", "revision-1"),
        policy=SourcePolicy(frozenset({("host", "mapping")})),
        generation=ConfigurationGeneration(1),
    )


def issue(private: rsa.RSAPrivateKey, *, overrides: dict[str, object] | None = None, headers=None):
    claims: dict[str, object] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "workload-42",
        "iat": NOW - 10,
        "exp": NOW + 300,
    }
    if overrides:
        claims.update(overrides)
    jose = {"typ": "at+jwt", "kid": "host-approved-kid"}
    if headers:
        jose.update(headers)
    return jwt.encode(claims, private, algorithm="RS256", headers=jose).encode()


def authenticate(runtime, raw: bytes, *, route: str = "orders"):
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, raw),
        CorrelationId("m6-jwt-bootstrap"),
    )
    return asyncio.run(
        runtime.engine.authenticate(request, entry=runtime.catalog.resolve_for_host_route(route))
    )


def test_m6_jwt_v2_signed_token_authenticates_through_M2(rsa_fixture) -> None:
    private, public = rsa_fixture
    runtime = compose_trusted_jwt_runtime(
        approved(),
        approved_static_keysets={KEYSET: (public,)},
        clock=FixedClock(),
        final_rule=lambda _subject, _entry: True,
    )
    result = authenticate(runtime, issue(private))
    assert isinstance(result, Authenticated)
    assert result.principal.subject.issuer_ref == ISSUER
    assert result.principal.subject.scope_ref.value == SCOPE
    assert result.principal.subject.subject_id == "workload-42"


def test_m6_jwt_t03_signed_issuer_and_audience_cannot_select_a_new_profile(rsa_fixture):
    private, public = rsa_fixture
    runtime = compose_trusted_jwt_runtime(
        approved(),
        approved_static_keysets={KEYSET: (public,)},
        clock=FixedClock(),
        final_rule=lambda _subject, _entry: True,
    )
    for changed in (
        {"iss": "https://attacker.example.test"},
        {"aud": "invoices-api"},
    ):
        assert isinstance(authenticate(runtime, issue(private, overrides=changed)), Rejected)
    for untrusted_headers in (
        {"jku": "https://attacker.example.test/jwks"},
        {"x5u": "https://attacker.example.test/cert"},
    ):
        assert isinstance(
            authenticate(runtime, issue(private, headers=untrusted_headers)), Rejected
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("issuer", ""),
        ("issuer", "https://*.example.test"),
        ("audience", ""),
        ("allowed_algorithms", ["none"]),
        ("allowed_algorithms", ["RS256", "none"]),
        ("allowed_algorithms", []),
        ("clock_skew_seconds", 999),
        ("max_token_bytes", 100000),
    ],
)
def test_m6_t11_unapproved_jwt_trust_values_fail_bootstrap(field, value):
    raw = raw_config()
    raw["jwt_profiles"][0][field] = value
    with pytest.raises(ConfigurationRejected):
        approved(raw)


def test_m6_t11_missing_jwt_profile_or_key_source_is_rejected():
    raw = raw_config()
    raw["jwt_profiles"] = []
    with pytest.raises(ConfigurationRejected):
        approved(raw)
    raw = raw_config()
    del raw["jwt_profiles"][0]["key_source"]
    with pytest.raises(ConfigurationRejected):
        approved(raw)


def test_m6_jwt_v2_requires_complete_profile_binding():
    raw = raw_config()
    raw["jwt_profiles"][0]["scope"] = "tenant-b:production"
    with pytest.raises(ConfigurationRejected):
        approved(raw)
    raw = raw_config()
    raw["jwt_profiles"].append(deepcopy(raw["jwt_profiles"][0]))
    with pytest.raises(ConfigurationRejected):
        approved(raw)


def test_m6_jwt_v1_legacy_config_is_not_silently_upgraded():
    raw = raw_config()
    raw["schema_version"] = 1
    with pytest.raises(ConfigurationRejected):
        approved(raw)
    raw.pop("jwt_profiles")
    snap = approved(raw)
    assert snap.schema_version == 1
    assert not snap.jwt_profiles


def test_m6_jwt_generic_composer_cannot_bypass_v2_policy():
    snap = approved()
    with pytest.raises(ConfigurationRejected, match="unapproved JWT"):
        compose_authentication_engine(snap, authenticators=[])


def test_m6_jwt_missing_or_unapproved_static_keyset_cannot_activate(rsa_fixture):
    _private, public = rsa_fixture
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        compose_trusted_jwt_runtime(approved(), approved_static_keysets={})
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        compose_trusted_jwt_runtime(
            approved(), approved_static_keysets={KEYSET: (public,), "extra": (public,)}
        )


def test_m6_jwt_private_key_is_never_an_approved_verification_jwk(rsa_fixture):
    _private, public = rsa_fixture
    unauthorized = json.loads(public)
    unauthorized["d"] = "do-not-allow-private-parameters"
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        compose_trusted_jwt_runtime(
            approved(),
            approved_static_keysets={KEYSET: (json.dumps(unauthorized),)},
        )


def test_m6_jwt_wrong_signature_and_unknown_kid_cannot_authenticate(rsa_fixture):
    private, public = rsa_fixture
    runtime = compose_trusted_jwt_runtime(
        approved(),
        approved_static_keysets={KEYSET: (public,)},
        clock=FixedClock(),
        final_rule=lambda _subject, _entry: True,
    )
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert isinstance(authenticate(runtime, issue(other)), Rejected)
    assert isinstance(authenticate(runtime, issue(private, headers={"kid": "unknown"})), Rejected)


def test_m6_jwt_denied_by_final_M2_policy_even_with_valid_signature(rsa_fixture):
    private, public = rsa_fixture
    runtime = compose_trusted_jwt_runtime(
        approved(),
        approved_static_keysets={KEYSET: (public,)},
        clock=FixedClock(),
        final_rule=lambda _subject, _entry: False,
    )
    assert isinstance(authenticate(runtime, issue(private)), Rejected)


def remote_source(*, address: str = "1.1.1.1", uri: str = "https://keys.example.com/jwks"):
    return {
        "kind": "jwks_https",
        "source_id": "keys-a",
        "uri": uri,
        "ttl_seconds": 60,
        "timeout_seconds": 1.0,
        "max_response_bytes": 16384,
        "max_keys": 8,
        "allowed_ips": [address],
    }


@pytest.mark.parametrize(
    ("address", "uri"),
    [
        ("127.0.0.1", "https://keys.example.com/jwks"),
        ("169.254.169.254", "https://keys.example.com/jwks"),
        ("10.10.1.2", "https://keys.example.com/jwks"),
        ("1.1.1.1", "http://keys.example.com/jwks"),
        ("1.1.1.1", "https://localhost/jwks"),
        ("1.1.1.1", "https://keys.example.com/jwks?x=1"),
        ("1.1.1.1", "https://user:pass@keys.example.com/jwks"),
    ],
)
def test_m6_t12_unapproved_jwks_url_or_ip_rejected_before_egress(address, uri):
    with pytest.raises(ConfigurationRejected):
        approved(raw_config(source=remote_source(address=address, uri=uri)))


def test_m6_t12_jwks_egress_requires_separate_exact_host_grant():
    snap = approved(raw_config(source=remote_source()))
    ref = snap.jwt_profiles[0].profile.profile_ref
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        compose_trusted_jwt_runtime(snap, approved_static_keysets={})
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        compose_trusted_jwt_runtime(
            snap,
            approved_static_keysets={},
            approved_jwks_egress={
                ref: ("keys-a", "https://attacker.example.com/jwks", ("1.1.1.1",))
            },
        )


def test_m6_valid_host_granted_jwks_does_not_fetch_on_bootstrap_or_bad_jwt():
    snap = approved(raw_config(source=remote_source()))
    ref = snap.jwt_profiles[0].profile.profile_ref
    runtime = compose_trusted_jwt_runtime(
        snap,
        approved_static_keysets={},
        approved_jwks_egress={ref: ("keys-a", "https://keys.example.com/jwks", ("1.1.1.1",))},
        clock=FixedClock(),
        final_rule=lambda _subject, _entry: True,
    )
    assert isinstance(authenticate(runtime, b"invalid.jwt.structure"), Rejected)
