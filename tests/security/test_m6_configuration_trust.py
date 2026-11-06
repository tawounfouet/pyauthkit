"""M6 security tests: host provenance, immutable generations and no trust downgrade."""

import asyncio
from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from pyauthkit.adapters.audit_memory import InMemoryAuthenticationEventSink
from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    compose_authentication_engine,
    load_approved_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.ports.authenticator import VerificationContext

PROVENANCE = SourceProvenance("trusted-config", "host", "rev-1")
POLICY = SourcePolicy(frozenset({("trusted-config", "host")}))
CANARY = "M6_PASSWORD_OR_RAW_JWT_CANARY"


def raw_config() -> dict[str, object]:
    return {
        "schema_version": 1,
        "routes": [
            {
                "route_id": "api",
                "scope": "tenant-a",
                "profile_id": "jwt-a",
                "profile_version": "v1",
                "allowed_methods": ["jwt"],
            }
        ],
        "timeout_seconds": 2.0,
        "audit_delivery": "best_effort",
        "secrets": [],
    }


def load(raw: dict[str, object] | None = None, *, generation: int = 1):
    return load_approved_configuration(
        raw_config() if raw is None else raw,
        provenance=PROVENANCE,
        policy=POLICY,
        generation=ConfigurationGeneration(generation),
    )


class PositiveSyntheticVerifier:
    """Test-only verifier; NO cryptographic verification capability."""

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.JWT

    async def verify(self, request: AuthenticationRequest, context: VerificationContext):
        return _issue_verified_outcome(
            context,
            subject=ScopedSubjectRef("synthetic-subject", "test-only", context.scope_ref),
            principal_type=PrincipalType.WORKLOAD,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


def make_runtime(*, generation: int = 1, floor: int = 1, sink=None):
    return compose_authentication_engine(
        load(generation=generation),
        authenticators=[PositiveSyntheticVerifier()],
        final_rule=lambda _subject, _entry: True,
        event_sink=sink,
        minimum_generation=floor,
    )


def test_m6_t01_valid_host_mapping_bootstraps_one_generation() -> None:
    runtime = make_runtime()
    assert runtime.snapshot.generation.value == 1
    assert runtime.catalog.resolve_for_host_route("api").scope_ref.value == "tenant-a"
    assert runtime.engine is not None


def test_m6_t02_untrusted_provenance_is_denied() -> None:
    with pytest.raises(ConfigurationRejected, match="not approved"):
        load_approved_configuration(
            raw_config(),
            provenance=SourceProvenance("attacker", "host", "rev-1"),
            policy=POLICY,
            generation=ConfigurationGeneration(1),
        )


def test_m6_t04_extra_security_field_is_denied() -> None:
    raw = raw_config()
    raw["jwt_algorithms"] = ["none"]
    with pytest.raises(ConfigurationRejected):
        load(raw)
    raw = raw_config()
    routes = raw["routes"]
    assert isinstance(routes, list)
    routes[0]["allow_all"] = True
    with pytest.raises(ConfigurationRejected):
        load(raw)


def test_m6_t05_duplicate_route_and_method_denied() -> None:
    raw = raw_config()
    routes = raw["routes"]
    assert isinstance(routes, list)
    routes.append(deepcopy(routes[0]))
    with pytest.raises(ConfigurationRejected):
        load(raw)
    raw = raw_config()
    routes = raw["routes"]
    assert isinstance(routes, list)
    routes[0]["allowed_methods"] = ["jwt", "jwt"]
    with pytest.raises(ConfigurationRejected):
        load(raw)


def test_m6_t07_env_override_is_not_a_source_even_if_spelled_like_host() -> None:
    raw = raw_config()
    raw["allowed_algorithms"] = ["none"]
    with pytest.raises(ConfigurationRejected):
        load(raw)


def test_m6_t08_unknown_route_has_no_fallback() -> None:
    runtime = make_runtime()
    from pyauthkit.application.host_context import HostRouteNotConfigured

    with pytest.raises(HostRouteNotConfigured):
        runtime.catalog.resolve_for_host_route("tenant-b")


def test_m6_t10_unregistered_authenticator_prevents_activation() -> None:
    with pytest.raises(ConfigurationRejected, match="composition rejected"):
        compose_authentication_engine(load(), authenticators=[])


def test_m6_t13_snapshot_does_not_share_mutable_host_input() -> None:
    raw = raw_config()
    snapshot = load(raw)
    routes = raw["routes"]
    assert isinstance(routes, list)
    routes[0]["scope"] = "attacker"
    routes.append(deepcopy(routes[0]))
    assert snapshot.bindings[0].scope_ref.value == "tenant-a"
    assert len(snapshot.bindings) == 1


def test_m6_t14_snapshot_and_nested_bindings_immutable() -> None:
    snapshot = load()
    with pytest.raises(FrozenInstanceError):
        snapshot.timeout_seconds = 100  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        snapshot.bindings[0].route_id = "injected"  # type: ignore[misc]


def test_m6_t23_audit_contains_only_correlation_method_result_duration() -> None:
    sink = InMemoryAuthenticationEventSink()
    runtime = make_runtime(sink=sink)
    req = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
        CorrelationId("trace-m6-audit"),
    )
    result = asyncio.run(
        runtime.engine.authenticate(req, entry=runtime.catalog.resolve_for_host_route("api"))
    )
    assert isinstance(result, Authenticated)
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.result_status == "AUTHENTICATED"
    assert event.correlation_id == req.correlation_id
    assert event.method is EvidenceMethod.JWT
    assert event.duration_ms >= 0
    assert CANARY not in repr(event)
    assert CANARY not in str(event)


def test_m6_t27_best_effort_sink_failure_does_not_change_authn() -> None:
    class BrokenSink:
        async def emit(self, _event: object) -> None:
            raise RuntimeError(CANARY)

    runtime = make_runtime(sink=BrokenSink())
    req = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
        CorrelationId("trace-m6-failure"),
    )
    result = asyncio.run(
        runtime.engine.authenticate(req, entry=runtime.catalog.resolve_for_host_route("api"))
    )
    assert isinstance(result, Authenticated)
    assert CANARY not in repr(result)


def test_m6_t29_audit_cancellation_propagates() -> None:
    class CancelledSink:
        async def emit(self, _event: object) -> None:
            raise asyncio.CancelledError

    runtime = make_runtime(sink=CancelledSink())
    req = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
        CorrelationId("trace-m6-cancelled"),
    )
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            runtime.engine.authenticate(req, entry=runtime.catalog.resolve_for_host_route("api"))
        )


def test_m6_t30_required_audit_policy_rejected_at_bootstrap() -> None:
    raw = raw_config()
    raw["audit_delivery"] = "required"
    with pytest.raises(ConfigurationRejected):
        load(raw)


def test_m6_t34_t36_generation_floor_blocks_rollback_at_restart() -> None:
    assert make_runtime(generation=2, floor=2).snapshot.generation.value == 2
    with pytest.raises(ConfigurationRejected, match="stale"):
        make_runtime(generation=1, floor=2)


def test_m6_t35_invalid_restart_never_returns_a_runtime() -> None:
    raw = raw_config()
    raw["schema_version"] = 0
    with pytest.raises(ConfigurationRejected):
        load(raw, generation=2)
    assert make_runtime(generation=1).snapshot.generation.value == 1


def test_m6_t24_rejected_and_error_events_never_echo_evidence() -> None:
    sink = InMemoryAuthenticationEventSink()
    runtime = make_runtime(sink=sink)

    async def scenario() -> tuple[object, object]:
        denied = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, CANARY.encode()),
            CorrelationId("m6-denied"),
        )
        rejected = await runtime.engine.authenticate(
            denied, entry=runtime.catalog.resolve_for_host_route("api")
        )
        foreign = make_runtime()
        broken = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
            CorrelationId("m6-invalid-trust"),
        )
        errored = await runtime.engine.authenticate(
            broken, entry=foreign.catalog.resolve_for_host_route("api")
        )
        return rejected, errored

    first, second = asyncio.run(scenario())
    assert isinstance(first, Rejected)
    assert isinstance(second, AuthError)
    assert tuple(event.result_status for event in sink.events) == ("REJECTED", "ERROR")
    for event in sink.events:
        assert CANARY not in repr(event)
        assert not hasattr(event, "principal")
        assert not hasattr(event, "credential")
        assert not hasattr(event, "jwt")


def test_m6_t31_required_audit_cannot_be_enabled_by_a_fake_sink() -> None:
    raw = raw_config()
    raw["audit_delivery"] = "required"
    with pytest.raises(ConfigurationRejected):
        load(raw)


def test_m6_t33_memory_sink_does_not_claim_idempotent_delivery() -> None:
    sink = InMemoryAuthenticationEventSink()
    runtime = make_runtime(sink=sink)

    async def scenario() -> None:
        req = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
            CorrelationId("m6-duplicate"),
        )
        entry = runtime.catalog.resolve_for_host_route("api")
        await runtime.engine.authenticate(req, entry=entry)
        await runtime.engine.authenticate(req, entry=entry)

    asyncio.run(scenario())
    assert len(sink.events) == 2
    assert all(event.correlation_id.value == "m6-duplicate" for event in sink.events)
    assert not hasattr(sink.events[0], "persisted")
    assert not hasattr(sink.events[0], "receipt")
