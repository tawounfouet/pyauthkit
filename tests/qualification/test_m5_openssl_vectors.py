"""Independent OpenSSL-created RS256 JWS qualification vectors for M5.

Signing happens with the openssl CLI, *not* PyJWT or cryptography.sign().
Public modulus is read using cryptography for JWK serialization only. No
private key or authentication token is checked into the repository.
This establishes independent signing interoperability, not an external audit.
"""

import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from pyauthkit.adapters.jwt_authenticator import JWTAuthenticator
from pyauthkit.adapters.jwt_crypto import PyJwtRs256Verifier
from pyauthkit.adapters.jwt_static import StaticJwksKeyResolver, StaticJwtProfileResolver
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef

OPENSSL = shutil.which("openssl")
pytestmark = pytest.mark.skipif(OPENSSL is None, reason="OpenSSL CLI unavailable on host")
NOW = 1793880000
SCOPE = TrustedScopeRef("openssl-qualification")
REF = TrustProfileRef("openssl-jwt", "v1", SCOPE)
ISS = "https://openssl-issuer.example.test"
AUD = "openssl-resource-api"


def _urlsafe(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _openssl(*args: str) -> None:
    subprocess.run(["openssl", *args], check=True, capture_output=True, timeout=15)


@pytest.fixture(scope="module")
def openssl_material():
    with tempfile.TemporaryDirectory(prefix="m5-openssl-") as temporary:
        root = Path(temporary)
        private = root / "signer.pem"
        other_private = root / "other.pem"
        _openssl(
            "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private)
        )
        _openssl(
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(other_private),
        )
        public_key = serialization.load_pem_private_key(
            private.read_bytes(), password=None
        ).public_key()
        assert isinstance(public_key, rsa.RSAPublicKey)
        numbers = public_key.public_numbers()
        def number(value: int) -> str:
            return _urlsafe(value.to_bytes((value.bit_length() + 7) // 8, "big")).decode()
        jwk = json.dumps(
            {
                "kty": "RSA",
                "kid": "openssl-key",
                "use": "sig",
                "alg": "RS256",
                "n": number(numbers.n),
                "e": number(numbers.e),
            }
        )
        yield root, private, other_private, jwk


def _jws(
    root: Path,
    signer: Path,
    claims: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    protected: dict[str, str] = {"alg": "RS256", "kid": "openssl-key", "typ": "at+jwt"}
    if headers is not None:
        protected.update(headers)
    payload = (
        claims
        if claims is not None
        else {
            "iss": ISS,
            "sub": "openssl-subject",
            "aud": AUD,
            "exp": NOW + 300,
            "iat": NOW - 30,
        }
    )
    signing_input = b".".join(
        (
            _urlsafe(json.dumps(protected, separators=(",", ":")).encode()),
            _urlsafe(json.dumps(payload, separators=(",", ":")).encode()),
        )
    )
    source = root / "signing-input.bin"
    signature = root / "signature.bin"
    source.write_bytes(signing_input)
    _openssl("dgst", "-sha256", "-sign", str(signer), "-out", str(signature), str(source))
    return signing_input + b"." + _urlsafe(signature.read_bytes())


class Clock:
    def now(self) -> datetime:
        return datetime.fromtimestamp(NOW, UTC)


class OpenSslHarness:
    def __init__(self, jwk: str, *, allow: bool = True):
        self.catalog = HostTrustCatalog(
            [HostBinding("openssl-api", SCOPE, REF, frozenset({EvidenceMethod.JWT}))]
        )
        profile = TrustedJwtVerificationProfile(SCOPE, REF, ISS, AUD)
        verifier = JWTAuthenticator(
            profile_resolver=StaticJwtProfileResolver({REF: profile}),
            key_resolver=StaticJwksKeyResolver({REF: (jwk,)}),
            signature_verifier=PyJwtRs256Verifier(),
            clock=Clock(),
        )
        registry = AuthenticatorRegistryBuilder()
        registry.register(verifier)
        self.engine = AuthenticationEngine(
            policy=AuthenticationPolicyGate(self.catalog, final_rule=lambda _sub, _entry: allow),
            registry=registry.freeze(),
        )

    def authenticate(self, encoded: bytes):
        return asyncio.run(
            self.engine.authenticate(
                AuthenticationRequest(
                    PresentedEvidence(EvidenceMethod.JWT, encoded),
                    CorrelationId("openssl-vector"),
                ),
                entry=self.catalog.resolve_for_host_route("openssl-api"),
            )
        )


@pytest.mark.integration
@pytest.mark.security
def test_openssl_cli_signed_rs256_jws_interoperates_with_pyauthkit(openssl_material) -> None:
    root, private, _other, jwk = openssl_material
    jws = _jws(root, private)
    result = OpenSslHarness(jwk).authenticate(jws)
    assert isinstance(result, Authenticated)
    assert result.principal.subject.subject_id == "openssl-subject"
    assert result.principal.subject.issuer_ref == ISS


@pytest.mark.security
def test_openssl_valid_jws_cannot_bypass_m2_final_deny(openssl_material) -> None:
    root, private, _other, jwk = openssl_material
    assert isinstance(OpenSslHarness(jwk, allow=False).authenticate(_jws(root, private)), Rejected)


@pytest.mark.security
@pytest.mark.parametrize("which", ["header", "payload", "signature"])
def test_openssl_signed_token_tampering_rejected(openssl_material, which) -> None:
    root, private, _other, jwk = openssl_material
    parts = _jws(root, private).split(b".")
    index = {"header": 0, "payload": 1, "signature": 2}[which]
    part = bytearray(parts[index])
    part[0] = ord("A") if part[0] != ord("A") else ord("B")
    parts[index] = bytes(part)
    assert isinstance(OpenSslHarness(jwk).authenticate(b".".join(parts)), Rejected)


@pytest.mark.security
def test_openssl_signature_from_other_rsa_key_is_rejected(openssl_material) -> None:
    root, _private, other, jwk = openssl_material
    assert isinstance(OpenSslHarness(jwk).authenticate(_jws(root, other)), Rejected)


@pytest.mark.security
@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://foreign.example.test"},
        {"aud": "other-api"},
        {"exp": NOW},
        {"nbf": NOW + 60},
        {"sub": ""},
    ],
)
def test_openssl_valid_signature_wrong_claims_rejected(openssl_material, overrides) -> None:
    root, private, _other, jwk = openssl_material
    claims: dict[str, object] = {
        "iss": ISS,
        "sub": "openssl-subject",
        "aud": AUD,
        "exp": NOW + 300,
        "iat": NOW - 30,
    }
    claims.update(overrides)
    assert isinstance(OpenSslHarness(jwk).authenticate(_jws(root, private, claims)), Rejected)


@pytest.mark.security
@pytest.mark.parametrize("headers", [{"typ": "JWT"}, {"alg": "HS256"}, {"kid": "unknown"}])
def test_openssl_signed_wrong_purpose_algorithm_or_key_rejected(openssl_material, headers) -> None:
    root, private, _other, jwk = openssl_material
    assert isinstance(
        OpenSslHarness(jwk).authenticate(_jws(root, private, headers=headers)), Rejected
    )
