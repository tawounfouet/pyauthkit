"""M6 integration: real M4 HMAC and M2 policy with M6 scoped secret source.

All material is synthetic. This does not qualify a production Vault/KMS or
establish revocation guarantees across distributed host processes.
"""

import asyncio
import base64
import hashlib
import hmac
from datetime import UTC, datetime

import pytest

from pyauthkit.adapters.secrets_memory import SyntheticSecretResolver
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    compose_secret_backed_api_key_runtime,
    load_approved_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.configuration.secrets import SecretAccessPolicy, SecretGrant
from pyauthkit.domain.api_key import (
    ApiKeyFound,
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

SCOPE = TrustedScopeRef("tenant-a:production")
OTHER_SCOPE = TrustedScopeRef("tenant-b:production")
KEY_V1 = bytes(range(32, 64))
KEY_V2 = bytes(range(64, 96))
SECRET = bytes(range(32))
SELECTOR = bytes(range(16))
DIGEST_V1 = bytes.fromhex("540574633838c98c95e6afd36e8712768ade3a211ebf7bed39f55caccad22184")
REF_V1 = SecretRef("unit-vault", SCOPE.value, "hmac", "v1", "verify")
REF_V2 = SecretRef("unit-vault", SCOPE.value, "hmac", "v2", "verify")
POLICY = SecretAccessPolicy(frozenset({SecretGrant("unit-vault", SCOPE.value, "verify")}))
INSTANT = datetime(2026, 11, 5, tzinfo=UTC)
EXPIRY = datetime(2027, 11, 5, tzinfo=UTC)


def _b64(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def _wire(secret: bytes = SECRET) -> bytes:
    return b"ak1." + _b64(SELECTOR) + b"." + _b64(secret)


def _digest(key: bytes) -> bytes:
    def frame(value: bytes) -> bytes:
        return len(value).to_bytes(4, "big") + value

    message = b"pyauthkit-api-key-v1\x00" + b"".join(
        frame(value)
        for value in (
            SCOPE.value.encode("ascii"),
            b"ak1",
            _b64(SELECTOR),
            SECRET,
        )
    )
    return hmac.new(key, message, hashlib.sha256).digest()


def _record(*, key_name: str = "hmac-v1", digest: bytes = DIGEST_V1) -> ApiKeyVerifierRecord:
    return ApiKeyVerifierRecord(
        scope_ref=SCOPE,
        subject_ref=ScopedSubjectRef("service-a", "issuer-a", SCOPE),
        principal_type=PrincipalType.SERVICE,
        key_id=_b64(SELECTOR).decode("ascii"),
        verifier_digest=digest,
        verifier_algorithm="hmac-sha256",
        protection_key_ref=key_name,
        status=ApiKeyRecordStatus.ACTIVE,
        version=1,
        expires_at=ObservedAt(EXPIRY),
    )


class Owner:
    def __init__(self, record: ApiKeyVerifierRecord) -> None:
        self.record = record

    async def resolve(self, *, scope_ref: TrustedScopeRef, key_id: str):
        if scope_ref != self.record.scope_ref or key_id != self.record.key_id:
            from pyauthkit.domain.api_key import ApiKeyMissing

            return ApiKeyMissing()
        return ApiKeyFound(self.record)

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        return self.record is record


class Guard:
    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        key_id: str | None,
    ) -> bool:
        return scope_ref == SCOPE and isinstance(correlation_id, CorrelationId)


class FixedClock:
    def now(self) -> datetime:
        return INSTANT


def _snapshot(ref: SecretRef, *, generation: int = 1):
    data: dict[str, object] = {
        "schema_version": 1,
        "routes": [
            {
                "route_id": "protected",
                "scope": SCOPE.value,
                "profile_id": "api-auth",
                "profile_version": f"v{generation}",
                "allowed_methods": ["api_key"],
            }
        ],
        "timeout_seconds": 3.0,
        "audit_delivery": "best_effort",
        "secrets": [
            {
                "provider": ref.provider,
                "namespace": ref.namespace,
                "key_id": ref.key_id,
                "version": ref.version,
                "purpose": ref.purpose,
            }
        ],
    }
    return load_approved_configuration(
        data,
        policy=SourcePolicy(frozenset({("host", "mapping")})),
        provenance=SourceProvenance("host", "mapping", f"r{generation}"),
        generation=ConfigurationGeneration(generation),
    )


async def _runtime(
    ref: SecretRef = REF_V1,
    *,
    key: bytes | None = KEY_V1,
    key_name: str = "hmac-v1",
    record: ApiKeyVerifierRecord | None = None,
    generation: int = 1,
    floor: int = 1,
):
    return await compose_secret_backed_api_key_runtime(
        _snapshot(ref, generation=generation),
        bindings={(SCOPE, key_name): ref},
        access_policy=POLICY,
        secret_resolver=SyntheticSecretResolver({ref: key} if key is not None else {}),
        credential_resolver=Owner(record if record is not None else _record()),
        attempt_guard=Guard(),
        clock=FixedClock(),
        final_rule=lambda _subject, _entry: True,
        minimum_generation=floor,
    )


async def _authenticate(runtime, *, secret: bytes = SECRET, trace: str = "m6-api-key"):
    req = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, _wire(secret)),
        CorrelationId(trace),
    )
    return await runtime.engine.authenticate(
        req, entry=runtime.catalog.resolve_for_host_route("protected")
    )


@pytest.mark.integration
def test_m6_real_m4_hmac_using_scoped_secret_ref_and_m2_policy() -> None:
    assert _digest(KEY_V1) == DIGEST_V1

    async def scenario() -> None:
        runtime = await _runtime()
        result = await _authenticate(runtime)
        assert isinstance(result, Authenticated)
        assert result.principal.subject.scope_ref == SCOPE

    asyncio.run(scenario())


@pytest.mark.security
def test_m6_invalid_presented_api_key_never_authenticates() -> None:
    async def scenario() -> None:
        runtime = await _runtime()
        changed = bytearray(SECRET)
        changed[-1] ^= 1
        result = await _authenticate(runtime, secret=bytes(changed))
        assert isinstance(result, Rejected)

    asyncio.run(scenario())


@pytest.mark.security
def test_m6_unavailable_secret_blocks_activation() -> None:
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        asyncio.run(_runtime(key=None))


@pytest.mark.security
def test_m6_wrong_length_material_blocks_activation() -> None:
    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        asyncio.run(_runtime(key=b"short"))


@pytest.mark.security
def test_m6_cross_scope_binding_cannot_activate() -> None:
    foreign = SecretRef("unit-vault", OTHER_SCOPE.value, "hmac", "v1", "verify")

    async def scenario() -> None:
        await compose_secret_backed_api_key_runtime(
            _snapshot(foreign),
            bindings={(SCOPE, "hmac-v1"): foreign},
            access_policy=SecretAccessPolicy(
                frozenset({SecretGrant("unit-vault", OTHER_SCOPE.value, "verify")})
            ),
            secret_resolver=SyntheticSecretResolver({foreign: KEY_V1}),
            credential_resolver=Owner(_record()),
            attempt_guard=Guard(),
        )

    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        asyncio.run(scenario())


@pytest.mark.security
def test_m6_unapproved_secret_capability_blocks_activation() -> None:
    async def scenario() -> None:
        await compose_secret_backed_api_key_runtime(
            _snapshot(REF_V1),
            bindings={(SCOPE, "hmac-v1"): REF_V1},
            access_policy=SecretAccessPolicy(frozenset()),
            secret_resolver=SyntheticSecretResolver({REF_V1: KEY_V1}),
            credential_resolver=Owner(_record()),
            attempt_guard=Guard(),
        )

    with pytest.raises(ConfigurationRejected, match="bootstrap rejected"):
        asyncio.run(scenario())


@pytest.mark.security
def test_m6_secret_revocation_after_bootstrap_fails_closed() -> None:
    class RevocableResolver:
        def __init__(self) -> None:
            self.revoked = False

        async def resolve(self, *, ref: SecretRef, purpose: str) -> bytes:
            if self.revoked:
                raise RuntimeError("PRIVATE_KEY_EXPOSED_IN_PROVIDER_FAILURE")
            return KEY_V1

    async def scenario() -> None:
        resolver = RevocableResolver()
        runtime = await compose_secret_backed_api_key_runtime(
            _snapshot(REF_V1),
            bindings={(SCOPE, "hmac-v1"): REF_V1},
            access_policy=POLICY,
            secret_resolver=resolver,
            credential_resolver=Owner(_record()),
            attempt_guard=Guard(),
            clock=FixedClock(),
            final_rule=lambda _subject, _entry: True,
        )
        resolver.revoked = True
        result = await _authenticate(runtime)
        assert isinstance(result, AuthError)
        assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        assert "PRIVATE_KEY_EXPOSED" not in repr(result)

    asyncio.run(scenario())


@pytest.mark.security
def test_m6_restart_to_new_key_does_not_mix_generations() -> None:
    async def scenario() -> None:
        old = await _runtime()
        new = await _runtime(
            REF_V2,
            key=KEY_V2,
            key_name="hmac-v2",
            record=_record(key_name="hmac-v2", digest=_digest(KEY_V2)),
            generation=2,
            floor=2,
        )
        first, second = await asyncio.gather(
            _authenticate(old, trace="m6-generation-1"),
            _authenticate(new, trace="m6-generation-2"),
        )
        assert isinstance(first, Authenticated)
        assert isinstance(second, Authenticated)
        assert old.snapshot.generation.value == 1
        assert new.snapshot.generation.value == 2
        assert old.catalog.resolve_for_host_route("protected").profile_ref.version == "v1"
        assert new.catalog.resolve_for_host_route("protected").profile_ref.version == "v2"

    asyncio.run(scenario())


@pytest.mark.security
def test_m6_stale_generation_cannot_restart_even_when_secret_exists() -> None:
    with pytest.raises(ConfigurationRejected, match="stale"):
        asyncio.run(_runtime(generation=1, floor=2))


@pytest.mark.security
def test_m6_revoked_key_cannot_be_reactivated_by_restart() -> None:
    async def scenario() -> None:
        runtime = await _runtime(
            REF_V2,
            key=KEY_V2,
            key_name="hmac-v2",
            record=_record(key_name="hmac-v2", digest=_digest(KEY_V2)),
            generation=2,
            floor=2,
        )
        assert isinstance(await _authenticate(runtime), Authenticated)
        with pytest.raises(ConfigurationRejected):
            await _runtime(key=None, generation=1, floor=2)

    asyncio.run(scenario())


@pytest.mark.security
def test_m6_secret_bootstrap_cancellation_is_not_misreported() -> None:
    class CancelledProvider:
        async def resolve(self, *, ref: SecretRef, purpose: str) -> bytes:
            raise asyncio.CancelledError

    async def scenario() -> None:
        await compose_secret_backed_api_key_runtime(
            _snapshot(REF_V1),
            bindings={(SCOPE, "hmac-v1"): REF_V1},
            access_policy=POLICY,
            secret_resolver=CancelledProvider(),
            credential_resolver=Owner(_record()),
            attempt_guard=Guard(),
        )

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(scenario())


@pytest.mark.security
def test_m6_secret_bindings_are_deeply_immutable() -> None:
    async def scenario() -> None:
        from pyauthkit.adapters.api_key_secret import ScopedApiKeySecretSource

        source = ScopedApiKeySecretSource(
            snapshot=_snapshot(REF_V1),
            access_policy=POLICY,
            resolver=SyntheticSecretResolver({REF_V1: KEY_V1}),
            bindings={(SCOPE, "hmac-v1"): REF_V1},
        )
        with pytest.raises(AttributeError):
            source._bindings = {}  # type: ignore[assignment]
        with pytest.raises(TypeError):
            source.approved_refs[SCOPE] = frozenset()  # type: ignore[index]
        assert "no secret cache" in repr(source)

    asyncio.run(scenario())
