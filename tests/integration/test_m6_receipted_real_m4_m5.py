"""M6 receipt-gateway candidate with actual M4 HMAC and M5 RS256 verifiers.

All secrets and keys are ephemeral/synthetic. This is not a live AWS/KMS
test, durable distributed required audit or non-bypassable framework proof.
"""

import asyncio
import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from pyauthkit.adapters.audit_required_sqlite import (
    SqliteRequiredAuditCommitter,
    provision_sqlite_required_audit,
)
from pyauthkit.adapters.secrets_memory import SyntheticSecretResolver
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    load_approved_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.configuration.receipted_integrations import (
    compose_receipted_api_key_gateway,
    compose_receipted_jwt_gateway,
)
from pyauthkit.configuration.secrets import SecretAccessPolicy, SecretGrant
from pyauthkit.domain.api_key import (
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordStatus,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.ports.required_audit import AuditAttemptId

NOW = 1793880000
SCOPE = TrustedScopeRef("tenant-a:production")
ISSUER = "https://issuer.example.test"
AUDIENCE = "orders-api"
KEYSET = "signed-jwk-tenant-a"
REF = SecretRef("unit-vault", SCOPE.value, "hmac", "v1", "verify")
HMAC_KEY = bytes(range(32, 64))
SELECTOR = bytes(range(16))
API_SECRET = bytes(range(16, 48))
AUDIT_KEY = bytes(range(64, 96))


class FixedClock:
    def now(self) -> datetime:
        return datetime.fromtimestamp(NOW, UTC)


class Owner:
    def __init__(self, record: ApiKeyVerifierRecord) -> None:
        self.record = record

    async def resolve(self, *, scope_ref: TrustedScopeRef, key_id: str):
        if scope_ref != self.record.scope_ref or key_id != self.record.key_id:
            return ApiKeyMissing()
        return ApiKeyFound(self.record)

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        return record is self.record


class Guard:
    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        key_id: str | None,
    ) -> bool:
        return scope_ref == SCOPE and isinstance(correlation_id, CorrelationId)


def _b64(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def _api_wire(material: bytes = API_SECRET) -> bytes:
    return b"ak1." + _b64(SELECTOR) + b"." + _b64(material)


def _digest(secret: bytes) -> bytes:
    def frame(value: bytes) -> bytes:
        return len(value).to_bytes(4, "big") + value

    content = b"pyauthkit-api-key-v1\x00" + b"".join(
        frame(value)
        for value in (SCOPE.value.encode("ascii"), b"ak1", _b64(SELECTOR), API_SECRET)
    )
    return hmac.new(secret, content, hashlib.sha256).digest()


def _record() -> ApiKeyVerifierRecord:
    return ApiKeyVerifierRecord(
        scope_ref=SCOPE,
        subject_ref=ScopedSubjectRef("service-a", "issuer-a", SCOPE),
        principal_type=PrincipalType.SERVICE,
        key_id=_b64(SELECTOR).decode("ascii"),
        verifier_digest=_digest(HMAC_KEY),
        verifier_algorithm="hmac-sha256",
        protection_key_ref="hmac-v1",
        status=ApiKeyRecordStatus.ACTIVE,
        version=1,
        expires_at=ObservedAt(datetime(2027, 11, 5, tzinfo=UTC)),
    )


def _approved(raw: dict[str, object]):
    return load_approved_configuration(
        raw,
        policy=SourcePolicy(frozenset({("host", "mapping")})),
        provenance=SourceProvenance("host", "mapping", "rev-1"),
        generation=ConfigurationGeneration(1),
    )


def _api_snapshot():
    return _approved(
        {
            "schema_version": 1,
            "routes": [
                {
                    "route_id": "api",
                    "scope": SCOPE.value,
                    "profile_id": "api-auth",
                    "profile_version": "v1",
                    "allowed_methods": ["api_key"],
                }
            ],
            "timeout_seconds": 3.0,
            "audit_delivery": "best_effort",
            "secrets": [
                {
                    "provider": REF.provider,
                    "namespace": REF.namespace,
                    "key_id": REF.key_id,
                    "version": REF.version,
                    "purpose": REF.purpose,
                }
            ],
        }
    )


def _jwt_snapshot():
    return _approved(
        {
            "schema_version": 2,
            "routes": [
                {
                    "route_id": "jwt",
                    "scope": SCOPE.value,
                    "profile_id": "jwt-auth",
                    "profile_version": "v1",
                    "allowed_methods": ["jwt"],
                }
            ],
            "timeout_seconds": 3.0,
            "audit_delivery": "best_effort",
            "secrets": [],
            "jwt_profiles": [
                {
                    "scope": SCOPE.value,
                    "profile_id": "jwt-auth",
                    "profile_version": "v1",
                    "issuer": ISSUER,
                    "audience": AUDIENCE,
                    "expected_typ": "at+jwt",
                    "allowed_algorithms": ["RS256"],
                    "principal_type": "service",
                    "max_token_bytes": 8192,
                    "clock_skew_seconds": 0,
                    "max_age_seconds": None,
                    "key_source": {"kind": "static", "keyset_ref": KEYSET},
                }
            ],
        }
    )


@pytest.fixture(scope="module")
def signed_keys() -> tuple[rsa.RSAPrivateKey, str]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private.public_key().public_numbers()

    def encoded(value: int) -> str:
        content = value.to_bytes((value.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(content).rstrip(b"=").decode("ascii")

    jwk = json.dumps(
        {
            "kty": "RSA",
            "kid": "approved-key-a",
            "alg": "RS256",
            "use": "sig",
            "n": encoded(numbers.n),
            "e": encoded(numbers.e),
        }
    )
    return private, jwk


def _jwt_wire(private: rsa.RSAPrivateKey, *, audience: str = AUDIENCE) -> bytes:
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": audience,
            "sub": "workload-42",
            "iat": NOW - 10,
            "exp": NOW + 300,
        },
        private,
        algorithm="RS256",
        headers={"typ": "at+jwt", "kid": "approved-key-a"},
    ).encode("ascii")


def _store(tmp_path: Path, *, capacity: int = 100) -> SqliteRequiredAuditCommitter:
    path = tmp_path / "receipt.sqlite"
    provision_sqlite_required_audit(path)
    return SqliteRequiredAuditCommitter(
        path=path, signing_key=AUDIT_KEY, key_id="audit-key-v1", capacity=capacity
    )


def _attempt() -> AuditAttemptId:
    return AuditAttemptId(uuid4().hex)


class RevocableSecrets:
    def __init__(self) -> None:
        self.revoked = False

    async def resolve(self, *, ref: SecretRef, purpose: str) -> bytes:
        if self.revoked:
            raise RuntimeError("redacted provider outage")
        return HMAC_KEY


async def _api_gateway(committer: SqliteRequiredAuditCommitter, *, secrets=None, floor=1):
    return await compose_receipted_api_key_gateway(
        _api_snapshot(),
        bindings={(SCOPE, "hmac-v1"): REF},
        access_policy=SecretAccessPolicy(
            frozenset({SecretGrant("unit-vault", SCOPE.value, "verify")})
        ),
        secret_resolver=(
            secrets if secrets is not None else SyntheticSecretResolver({REF: HMAC_KEY})
        ),
        credential_resolver=Owner(_record()),
        attempt_guard=Guard(),
        committer=committer,
        final_rule=lambda _subject, _entry: True,
        clock=FixedClock(),
        minimum_generation=floor,
    )


def _jwt_gateway(committer, keys, *, floor=1):
    return compose_receipted_jwt_gateway(
        _jwt_snapshot(),
        approved_static_keysets={KEYSET: (keys,)},
        committer=committer,
        final_rule=lambda _subject, _entry: True,
        clock=FixedClock(),
        minimum_generation=floor,
    )


async def _check(gw, *, method: EvidenceMethod, raw: bytes, route: str, attempt_id=None):
    chosen = _attempt() if attempt_id is None else attempt_id
    result = await gw.authenticate(
        AuthenticationRequest(
            PresentedEvidence(method, raw), CorrelationId("private-trace-m6")
        ),
        entry=gw.catalog.resolve_for_host_route(route),
        attempt_id=chosen,
    )
    return chosen, result


def test_m6_receipted_real_m4_hmac_positive_and_rejected_always_committed(tmp_path: Path):
    committer = _store(tmp_path)

    async def scenario():
        gw = await _api_gateway(committer)
        attempt_ok, result = await _check(
            gw, method=EvidenceMethod.API_KEY, raw=_api_wire(), route="api"
        )
        assert isinstance(result, Authenticated)
        assert result.principal.subject.scope_ref == SCOPE
        assert committer.inspect_receipt(attempt_ok).result_status == "AUTHENTICATED"

        changed = bytearray(API_SECRET)
        changed[-1] ^= 1
        attempt_bad, denial = await _check(
            gw, method=EvidenceMethod.API_KEY, raw=_api_wire(bytes(changed)), route="api"
        )
        assert isinstance(denial, Rejected)
        assert committer.inspect_receipt(attempt_bad).result_status == "REJECTED"
        assert not hasattr(gw, "engine")
        assert "private-trace-m6" not in (tmp_path / "receipt.sqlite").read_bytes().decode(
            "latin1"
        )
        assert b"service-a" not in (tmp_path / "receipt.sqlite").read_bytes()

    asyncio.run(scenario())


def test_m6_receipted_real_m5_rs256_positive_and_wrong_audience_recorded(
    tmp_path: Path, signed_keys
):
    private, public = signed_keys
    committer = _store(tmp_path)
    gw = _jwt_gateway(committer, public)

    async def scenario():
        good_id, good = await _check(
            gw, method=EvidenceMethod.JWT, raw=_jwt_wire(private), route="jwt"
        )
        assert isinstance(good, Authenticated)
        assert good.principal.subject.subject_id == "workload-42"
        assert committer.inspect_receipt(good_id).result_status == "AUTHENTICATED"
        bad_id, bad = await _check(
            gw,
            method=EvidenceMethod.JWT,
            raw=_jwt_wire(private, audience="foreign-api"),
            route="jwt",
        )
        assert isinstance(bad, Rejected)
        assert committer.inspect_receipt(bad_id).result_status == "REJECTED"
        assert b"workload-42" not in (tmp_path / "receipt.sqlite").read_bytes()
        assert b"private-trace-m6" not in (tmp_path / "receipt.sqlite").read_bytes()

    asyncio.run(scenario())


def test_m6_receipted_real_m4_revoked_secret_is_error_and_audited(tmp_path: Path):
    committer = _store(tmp_path)
    secrets = RevocableSecrets()

    async def scenario():
        gw = await _api_gateway(committer, secrets=secrets)
        secrets.revoked = True
        attempt_id, result = await _check(
            gw, method=EvidenceMethod.API_KEY, raw=_api_wire(), route="api"
        )
        assert isinstance(result, AuthError)
        assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        assert committer.inspect_receipt(attempt_id).result_status == "ERROR"

    asyncio.run(scenario())


@pytest.mark.parametrize("which", ["m4", "m5"])
def test_m6_receipted_m4_m5_cannot_return_positive_when_store_missing(
    tmp_path: Path, signed_keys, which: str
):
    private, public = signed_keys
    committer = _store(tmp_path)

    async def scenario():
        gw = (
            await _api_gateway(committer)
            if which == "m4"
            else _jwt_gateway(committer, public)
        )
        (tmp_path / "receipt.sqlite").unlink()
        method = EvidenceMethod.API_KEY if which == "m4" else EvidenceMethod.JWT
        route = "api" if which == "m4" else "jwt"
        raw = _api_wire() if which == "m4" else _jwt_wire(private)
        attempt_id, result = await _check(gw, method=method, raw=raw, route=route)
        assert isinstance(result, AuthError)
        assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE

    # Missing storage is denied; the gateway cannot inspect any receipt.
    asyncio.run(scenario())


def test_m6_receipted_m4_m5_share_one_attempt_namespace(tmp_path: Path, signed_keys):
    private, public = signed_keys
    committer = _store(tmp_path)

    async def scenario():
        api = await _api_gateway(committer)
        jwt_gate = _jwt_gateway(committer, public)
        shared = _attempt()
        _, good = await _check(
            api,
            method=EvidenceMethod.API_KEY,
            raw=_api_wire(),
            route="api",
            attempt_id=shared,
        )
        _, denied = await _check(
            jwt_gate,
            method=EvidenceMethod.JWT,
            raw=_jwt_wire(private),
            route="jwt",
            attempt_id=shared,
        )
        assert isinstance(good, Authenticated)
        assert isinstance(denied, AuthError)
        assert denied.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        assert committer.inspect_receipt(shared).result_status == "AUTHENTICATED"

    asyncio.run(scenario())


@pytest.mark.parametrize("which", ["m4", "m5"])
def test_m6_receipted_m4_m5_stale_generation_rejected_before_use(
    tmp_path: Path, signed_keys, which: str
):
    _private, public = signed_keys
    committer = _store(tmp_path)

    async def scenario():
        if which == "m4":
            with pytest.raises(ConfigurationRejected, match="stale"):
                await _api_gateway(committer, floor=2)
        else:
            with pytest.raises(ConfigurationRejected, match="stale"):
                _jwt_gateway(committer, public, floor=2)

    asyncio.run(scenario())


@pytest.mark.parametrize("which", ["m4", "m5"])
def test_m6_receipted_m4_m5_reject_untrusted_receipt_provider(
    tmp_path: Path, signed_keys, which: str
):
    _private, public = signed_keys

    class Forged:
        async def commit(self, _record):
            raise AssertionError("unexpected external commit access")

    async def scenario():
        if which == "m4":
            with pytest.raises(ConfigurationRejected, match="unapproved auditable"):
                await _api_gateway(Forged())  # type: ignore[arg-type]
        else:
            with pytest.raises(ConfigurationRejected, match="unapproved auditable"):
                _jwt_gateway(Forged(), public)  # type: ignore[arg-type]

    asyncio.run(scenario())
