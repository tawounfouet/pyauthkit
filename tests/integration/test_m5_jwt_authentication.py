"""M5 RS256 security and M2 policy integration using synthetic RSA fixtures.

These are local unit/integration proofs, not qualification of network JWKS,
reverse proxies, stale-cache policy or independent cryptographic review.
"""

import asyncio
import base64
import json
from datetime import UTC, datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from pyauthkit.adapters.jwt_authenticator import JWTAuthenticator
from pyauthkit.adapters.jwt_crypto import PyJwtRs256Verifier
from pyauthkit.adapters.jwt_static import StaticJwksKeyResolver, StaticJwtProfileResolver
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import PrincipalType
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile, parse_compact_jws
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef

SCOPE = TrustedScopeRef("tenant-a:production")
REF = TrustProfileRef("jwt-api", "v1", SCOPE)
ISSUER = "https://issuer.example.test"
AUDIENCE = "orders-api"
NOW = 1793880000.0


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@pytest.fixture(scope="module")
def signing() -> tuple[rsa.RSAPrivateKey, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private_key.public_key().public_numbers()

    def integer(value: int) -> str:
        return b64(value.to_bytes((value.bit_length() + 7) // 8, "big"))

    public_jwk = json.dumps(
        {
            "kty": "RSA",
            "kid": "key-1",
            "use": "sig",
            "alg": "RS256",
            "n": integer(numbers.n),
            "e": integer(numbers.e),
        }
    )
    return private_key, public_jwk


class FixedClock:
    def __init__(self, epoch: float = NOW) -> None:
        self.epoch = epoch

    def now(self) -> datetime:
        return datetime.fromtimestamp(self.epoch, UTC)


class Host:
    def __init__(
        self,
        signing: tuple[rsa.RSAPrivateKey, str],
        *,
        allow: bool | None = True,
        ref: TrustProfileRef = REF,
        scope: TrustedScopeRef = SCOPE,
        issuer: str = ISSUER,
        jwk: str | None = None,
        max_age: int | None = None,
    ) -> None:
        self.private, public = signing
        self.clock = FixedClock()
        self.profile = TrustedJwtVerificationProfile(
            scope,
            ref,
            issuer,
            AUDIENCE,
            principal_type=PrincipalType.SERVICE,
            max_age_seconds=max_age,
        )
        self.catalog = HostTrustCatalog(
            [HostBinding("orders", scope, ref, frozenset({EvidenceMethod.JWT}))]
        )
        self.profile_resolver = StaticJwtProfileResolver({ref: self.profile})
        self.key_resolver = StaticJwksKeyResolver({ref: (jwk or public,)})
        self.authenticator = JWTAuthenticator(
            profile_resolver=self.profile_resolver,
            key_resolver=self.key_resolver,
            signature_verifier=PyJwtRs256Verifier(),
            clock=self.clock,
        )
        registry = AuthenticatorRegistryBuilder()
        registry.register(self.authenticator)
        self.engine = AuthenticationEngine(
            registry=registry.freeze(),
            policy=AuthenticationPolicyGate(
                self.catalog, final_rule=(None if allow is None else lambda _sub, _ctx: allow)
            ),
        )

    def issue(
        self,
        *,
        claims: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        payload = (
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": "service-42",
                "exp": int(NOW + 300),
                "iat": int(NOW - 30),
            }
            if claims is None
            else claims
        )
        jose = {"typ": "at+jwt", "kid": "key-1"}
        if headers is not None:
            jose.update(headers)
        return jwt.encode(payload, self.private, algorithm="RS256", headers=jose).encode()

    def auth(self, raw: bytes | None = None):
        request = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.JWT, self.issue() if raw is None else raw),
            CorrelationId("m5-test"),
        )
        return asyncio.run(
            self.engine.authenticate(request, entry=self.catalog.resolve_for_host_route("orders"))
        )


@pytest.mark.integration
def test_valid_signed_access_jwt_passes_final_m2_policy(signing) -> None:
    host = Host(signing)
    result = host.auth()
    assert isinstance(result, Authenticated)
    assert result.principal.subject.subject_id == "service-42"
    assert result.principal.subject.issuer_ref == ISSUER
    assert result.principal.subject.scope_ref == SCOPE
    assert result.principal.method is EvidenceMethod.JWT


@pytest.mark.security
@pytest.mark.parametrize("allow", [False, None])
def test_valid_signature_does_not_bypass_final_policy(signing, allow) -> None:
    assert isinstance(Host(signing, allow=allow).auth(), Rejected)


@pytest.mark.security
def test_mutated_signature_is_rejected(signing) -> None:
    host = Host(signing)
    parts = host.issue().split(b".")
    signature = bytearray(parts[2])
    signature[1] = 65 if signature[1] != 65 else 66
    assert isinstance(host.auth(b".".join((parts[0], parts[1], bytes(signature)))), Rejected)


@pytest.mark.security
def test_unknown_kid_is_not_resolved_by_claimed_issuer(signing) -> None:
    host = Host(signing)
    assert isinstance(host.auth(host.issue(headers={"kid": "not-approved"})), Rejected)


@pytest.mark.security
def test_wrong_typ_cannot_substitute_id_token(signing) -> None:
    host = Host(signing)
    assert isinstance(host.auth(host.issue(headers={"typ": "JWT"})), Rejected)


@pytest.mark.security
@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://evil.example.test"},
        {"aud": "orders-api-evil"},
        {"aud": ["other-api"]},
        {"aud": 123},
        {"sub": ""},
        {"sub": True},
        {"exp": True},
        {"exp": float("inf")},
        {"exp": int(NOW)},
        {"nbf": int(NOW + 1)},
        {"iat": int(NOW + 1)},
        {"cnf": {"jkt": "unverified-key-binding"}},
    ],
)
def test_signed_claims_invalidities_fail_closed(signing, overrides) -> None:
    host = Host(signing)
    payload = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "service-42",
        "iat": int(NOW - 30),
        "exp": int(NOW + 300),
    }
    payload.update(overrides)
    assert isinstance(host.auth(host.issue(claims=payload)), Rejected)


@pytest.mark.security
def test_signed_roles_do_not_override_m2_denial(signing) -> None:
    host = Host(signing, allow=False)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "service-42",
        "exp": int(NOW + 300),
        "roles": ["admin"],
        "scope": "write:*",
    }
    assert isinstance(host.auth(host.issue(claims=claims)), Rejected)


@pytest.mark.security
@pytest.mark.parametrize(
    "bad",
    [
        b"abc",
        b"a.b",
        b"a.b.c.d.e",
        b"a.b.c.d",
        b"a..c",
        (b64(b'{"alg":"none"}').encode() + b"." + b64(b"{}").encode() + b"."),
        b" " * 16,
        b"x" * 9000,
    ],
)
def test_non_compact_oversized_and_unsigned_rejected(signing, bad) -> None:
    host = Host(signing)
    assert parse_compact_jws(bad) is None
    assert isinstance(host.auth(bad), Rejected)


@pytest.mark.security
def test_duplicate_untrusted_jose_properties_rejected(signing) -> None:
    host = Host(signing)
    token = host.issue().split(b".")
    header = b'{"alg":"RS256","alg":"none","kid":"key-1","typ":"at+jwt"}'
    altered = b64(header).encode() + b"." + token[1] + b"." + token[2]
    assert parse_compact_jws(altered) is None
    assert isinstance(host.auth(altered), Rejected)


@pytest.mark.security
def test_duplicate_claims_are_rejected_before_signature_check(signing) -> None:
    host = Host(signing)
    token = host.issue().split(b".")
    payload = b'{"iss":"x","iss":"y","aud":"orders-api","sub":"s","exp":1800000000}'
    altered = token[0] + b"." + b64(payload).encode() + b"." + token[2]
    assert parse_compact_jws(altered) is None
    assert isinstance(host.auth(altered), Rejected)


@pytest.mark.security
@pytest.mark.parametrize(
    "injected",
    [
        {"jku": "http://169.254.169.254/latest/meta-data/"},
        {"x5u": "https://unapproved.example.test/key"},
        {"jwk": '{"evil":true}'},
        {"crit": "b64"},
    ],
)
def test_untrusted_key_discovery_headers_rejected(signing, injected) -> None:
    host = Host(signing)
    assert isinstance(host.auth(host.issue(headers=injected)), Rejected)


@pytest.mark.security
def test_rsa_hmac_algorithm_confusion_rejected(signing) -> None:
    host = Host(signing)
    token = host.issue().split(b".")
    header = b'{"alg":"HS256","kid":"key-1","typ":"at+jwt"}'
    altered = b64(header).encode() + b"." + token[1] + b"." + token[2]
    assert isinstance(host.auth(altered), Rejected)


@pytest.mark.security
def test_profile_scoping_prevents_key_reuse_from_another_tenant(signing) -> None:
    other = TrustedScopeRef("tenant-b:production")
    other_ref = TrustProfileRef("jwt-api", "v1", other)
    host = Host(signing, scope=other, ref=other_ref, issuer="https://another.example.test")
    assert isinstance(host.auth(host.issue()), Rejected)


@pytest.mark.security
def test_duplicate_kids_rejected_at_bootstrap(signing) -> None:
    _private, jwk = signing
    with pytest.raises(ValueError, match="ambiguous"):
        StaticJwksKeyResolver({REF: (jwk, jwk)})


@pytest.mark.security
def test_secret_private_jwk_fields_rejected_at_bootstrap(signing) -> None:
    _private, jwk = signing
    document = json.loads(jwk)
    document["d"] = "pretend-private-exponent"
    with pytest.raises(ValueError, match="private"):
        StaticJwksKeyResolver({REF: (json.dumps(document),)})


@pytest.mark.security
def test_clock_and_expiry_do_not_use_untrusted_request_time(signing) -> None:
    host = Host(signing)
    host.clock.epoch = NOW + 600
    assert isinstance(host.auth(), Rejected)


@pytest.mark.security
def test_age_bound_requires_iat(signing) -> None:
    host = Host(signing, max_age=60)
    stale = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "service-42",
        "exp": int(NOW + 300),
        "iat": int(NOW - 120),
    }
    assert isinstance(host.auth(host.issue(claims=stale)), Rejected)


@pytest.mark.security
def test_no_token_secrets_in_representation(signing) -> None:
    host = Host(signing)
    raw = host.issue()
    result = host.auth(raw)
    assert raw.decode() not in repr(result)
    assert raw.decode() not in repr(host.authenticator)
    assert raw.decode() not in repr(host.profile)


@pytest.mark.security
def test_explicit_unencoded_payload_header_rejected(signing) -> None:
    host = Host(signing)
    _header, payload, signature = host.issue().split(b".")
    malicious = b64(b'{"alg":"RS256","kid":"key-1","typ":"at+jwt","b64":false}').encode()
    raw = malicious + b"." + payload + b"." + signature
    assert parse_compact_jws(raw) is None
    assert isinstance(host.auth(raw), Rejected)



@pytest.mark.security
@pytest.mark.parametrize(
    "unapproved",
    [
        {"kty": "oct"},
        {"use": "enc"},
        {"key_ops": ["sign"]},
        {"alg": "HS256"},
    ],
)
def test_unapproved_jwk_algorithm_key_use_and_type_rejected_at_bootstrap(
    signing, unapproved
) -> None:
    _private, raw_jwk = signing
    document = json.loads(raw_jwk)
    document.update(unapproved)
    with pytest.raises(ValueError):
        StaticJwksKeyResolver({REF: (json.dumps(document),)})


@pytest.mark.security
def test_jws_excessive_json_depth_and_noncanonical_base64url_rejected() -> None:
    header = b64(b'{"alg":"RS256","kid":"key-1","typ":"at+jwt"}').encode()
    nested = b'{"claim":' + b"[" * 16 + b"1" + b"]" * 16 + b"}"
    raw = header + b"." + b64(nested).encode() + b".AAAA"
    assert parse_compact_jws(raw) is None
    noncanonical = header + b"." + b64(b"{}").encode() + b"=.AAAA"
    assert parse_compact_jws(noncanonical) is None


@pytest.mark.security
def test_client_supplied_tenant_is_not_a_trust_profile_selector(signing) -> None:
    host = Host(signing)
    from pyauthkit.domain.identity import ClaimedIdentity

    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, host.issue()),
        CorrelationId("jwt-tenant-spoofing"),
        claimed_identity=ClaimedIdentity(
            "service", "service-42", claimed_tenant="foreign:production"
        ),
    )
    result = asyncio.run(
        host.engine.authenticate(
            request, entry=host.catalog.resolve_for_host_route("orders")
        )
    )
    assert isinstance(result, Rejected)


@pytest.mark.security
def test_profile_revision_cannot_fallback_to_another_versions_keys(signing) -> None:
    _private, jwk = signing
    resolver = StaticJwksKeyResolver({REF: (jwk,)})
    other_ref = TrustProfileRef("jwt-api", "v2", SCOPE)
    foreign = TrustedJwtVerificationProfile(SCOPE, other_ref, ISSUER, AUDIENCE)
    assert (
        asyncio.run(
            resolver.resolve_key(
                profile=foreign, kid_hint="key-1", algorithm_hint="RS256"
            )
        )
        is None
    )


@pytest.mark.security
def test_jwt_registry_has_no_other_authenticator_fallback(signing) -> None:
    host = Host(signing)
    from pyauthkit.composition.registry import AuthenticatorNotConfigured

    registry = AuthenticatorRegistryBuilder()
    registry.register(host.authenticator)
    frozen = registry.freeze()
    with pytest.raises(AuthenticatorNotConfigured):
        frozen.resolve(EvidenceMethod.PASSWORD)
    with pytest.raises(AuthenticatorNotConfigured):
        frozen.resolve(EvidenceMethod.API_KEY)
    assert isinstance(host.auth(host.issue(headers={"kid": "unknown"})), Rejected)


@pytest.mark.security
def test_signed_missing_expiry_is_rejected(signing) -> None:
    host = Host(signing)
    payload = {"iss": ISSUER, "aud": AUDIENCE, "sub": "service-42"}
    assert isinstance(host.auth(host.issue(claims=payload)), Rejected)
