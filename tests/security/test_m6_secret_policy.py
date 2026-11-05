"""M6 secret boundary and audit timeout/receipt tests."""

import asyncio

import pytest

from pyauthkit.adapters.audit_memory import InMemoryAuthenticationEventSink
from pyauthkit.adapters.secrets_memory import SyntheticSecretResolver
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    compose_authentication_engine,
    load_approved_configuration,
)
from pyauthkit.configuration.audit import BoundedBestEffortAuditSink
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.configuration.secrets import (
    SecretAccessPolicy,
    SecretGrant,
    SecretResolutionUnavailable,
    resolve_authorized_secret,
)
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.ports.events import AuthenticationEvent

CANARY = b"M6_SUPER_SECRET_CANARY_12938"
REF_A = SecretRef("test-vault", "tenant-a", "pepper", "v2", "pepper")
REF_B = SecretRef("test-vault", "tenant-b", "pepper", "v2", "pepper")
POLICY = SecretAccessPolicy(frozenset({SecretGrant("test-vault", "tenant-a", "pepper")}))


def snapshot(refs: tuple[SecretRef, ...] = (REF_A,)):
    mapping: dict[str, object] = {
        "schema_version": 1,
        "routes": [{
            "route_id": "api", "scope": "tenant-a",
            "profile_id": "p", "profile_version": "v2", "allowed_methods": ["jwt"],
        }],
        "timeout_seconds": 1.0,
        "audit_delivery": "best_effort",
        "secrets": [
            dict(provider=r.provider, namespace=r.namespace, key_id=r.key_id,
                 version=r.version, purpose=r.purpose) for r in refs
        ],
    }
    return load_approved_configuration(
        mapping,
        provenance=SourceProvenance("host", "mapping", "r2"),
        policy=SourcePolicy(frozenset({("host", "mapping")})),
        generation=ConfigurationGeneration(2),
    )


def test_m6_t16_cross_scope_secret_denied_without_provider_call() -> None:
    class UnexpectedProvider:
        async def resolve(self, **_kwargs: object) -> bytes:
            raise AssertionError("forbidden provider call")

    with pytest.raises(SecretResolutionUnavailable, match="denied"):
        asyncio.run(resolve_authorized_secret(
            snapshot=snapshot((REF_A, REF_B)), policy=POLICY,
            resolver=UnexpectedProvider(), ref=REF_B, purpose="pepper",
        ))


def test_m6_t17_malformed_reference_and_purpose_denied() -> None:
    with pytest.raises(ValueError):
        SecretRef("https://evil/", "tenant-a", "pepper", "v1", "pepper")
    with pytest.raises(ValueError):
        SecretRef("test-vault", "../tenant-b", "pepper", "v1", "pepper")
    with pytest.raises(ValueError):
        SecretRef("test-vault", "tenant-a", "pepper", "v1", "any-purpose")


def test_m6_t18_missing_provider_is_sanitized() -> None:
    store = SyntheticSecretResolver({})
    with pytest.raises(SecretResolutionUnavailable, match="secret unavailable"):
        asyncio.run(resolve_authorized_secret(
            snapshot=snapshot(), policy=POLICY,
            resolver=store, ref=REF_A, purpose="pepper",
        ))


def test_m6_t19_revoked_secret_has_no_fallback() -> None:
    store = SyntheticSecretResolver({REF_A: CANARY}, revoked=frozenset({REF_A}))
    with pytest.raises(SecretResolutionUnavailable):
        asyncio.run(resolve_authorized_secret(
            snapshot=snapshot(), policy=POLICY,
            resolver=store, ref=REF_A, purpose="pepper",
        ))


def test_m6_t20_approved_scoped_secret_is_exact_match() -> None:
    store = SyntheticSecretResolver({REF_A: CANARY, REF_B: b"other-tenant"})
    result = asyncio.run(resolve_authorized_secret(
        snapshot=snapshot((REF_A, REF_B)), policy=POLICY,
        resolver=store, ref=REF_A, purpose="pepper",
    ))
    assert result == CANARY
    with pytest.raises(SecretResolutionUnavailable):
        asyncio.run(resolve_authorized_secret(
            snapshot=snapshot((REF_A, REF_B)), policy=POLICY,
            resolver=store, ref=REF_B, purpose="pepper",
        ))


def test_m6_t21_references_and_snapshot_never_dump_material() -> None:
    snap = snapshot()
    store = SyntheticSecretResolver({REF_A: CANARY})
    for value in (REF_A, snap, store, POLICY):
        assert CANARY.decode() not in repr(value)
        assert CANARY.decode() not in str(value)


def test_m6_t22_provider_exception_cannot_leak_canary() -> None:
    class LeakyProvider:
        async def resolve(self, **_kwargs: object) -> bytes:
            raise RuntimeError(CANARY.decode())

    with pytest.raises(SecretResolutionUnavailable) as exc:
        asyncio.run(resolve_authorized_secret(
            snapshot=snapshot(), policy=POLICY,
            resolver=LeakyProvider(), ref=REF_A, purpose="pepper",
        ))
    assert CANARY.decode() not in str(exc.value)
    assert exc.value.__cause__ is None
    assert exc.value.__context__ is not None  # suppressed, not exposed to the caller


def test_m6_t28_audit_submission_timeout_is_not_success_receipt() -> None:
    class SlowSink:
        async def emit(self, _event: object) -> None:
            await asyncio.sleep(0.1)

    sink = BoundedBestEffortAuditSink(SlowSink(), timeout_seconds=0.001)
    event = AuthenticationEvent(CorrelationId("trace-m6"), EvidenceMethod.JWT, "ERROR", 0.5)
    with pytest.raises(TimeoutError):
        asyncio.run(sink.emit(event))


def test_m6_t32_in_memory_sink_is_explicitly_non_durable() -> None:
    sink = InMemoryAuthenticationEventSink(capacity=1)
    event = AuthenticationEvent(CorrelationId("trace-m6"), EvidenceMethod.JWT, "REJECTED", 1.0)
    asyncio.run(sink.emit(event))
    assert sink.events == (event,)
    assert "non-durable" in repr(sink)
    with pytest.raises(RuntimeError):
        asyncio.run(sink.emit(event))


def test_m6_secret_config_cannot_activate_without_consumer_wiring() -> None:
    with pytest.raises(ConfigurationRejected, match="consumer composition"):
        compose_authentication_engine(snapshot(), authenticators=[])
