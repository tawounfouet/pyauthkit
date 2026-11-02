"""M2 integration: concurrent tenants and immutable runtime composition."""

import asyncio
from datetime import UTC, datetime

import pytest

from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import VerificationContext


class ScopedVerifier:
    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.JWT

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> VerifiedOutcome:
        await asyncio.sleep(0)
        return _issue_verified_outcome(
            context,
            subject=ScopedSubjectRef("synthetic-only", "test-fixture", context.scope_ref),
            principal_type=PrincipalType.WORKLOAD,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


def test_m2_t17_concurrent_tenants_are_cryptographically_unclaimed_but_scope_isolated() -> None:
    scope_a = TrustedScopeRef("tenant-a")
    scope_b = TrustedScopeRef("tenant-b")
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "route-a",
                scope_a,
                TrustProfileRef("profile", "v1", scope_a),
                frozenset({EvidenceMethod.JWT}),
            ),
            HostBinding(
                "route-b",
                scope_b,
                TrustProfileRef("profile", "v1", scope_b),
                frozenset({EvidenceMethod.JWT}),
            ),
        ]
    )
    builder = AuthenticatorRegistryBuilder()
    builder.register(ScopedVerifier())
    registry = builder.freeze()
    gate = AuthenticationPolicyGate(catalog, final_rule=lambda _subject, _entry: True)
    engine = AuthenticationEngine(policy=gate, registry=registry)

    async def scenario() -> list[Authenticated]:
        async def authenticate_route(route: str, trace: str) -> Authenticated:
            req = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.JWT, b"test-only"),
                CorrelationId(trace),
            )
            result = await engine.authenticate(req, entry=catalog.resolve_for_host_route(route))
            assert isinstance(result, Authenticated)
            return result

        return list(
            await asyncio.gather(
                authenticate_route("route-a", "trace-a"),
                authenticate_route("route-b", "trace-b"),
            )
        )

    first, second = asyncio.run(scenario())
    assert first.principal.subject.scope_ref == scope_a
    assert second.principal.subject.scope_ref == scope_b
    assert first.correlation_id != second.correlation_id


def test_m2_t08_t23_host_catalog_registry_engine_and_policy_are_not_mutable() -> None:
    scope = TrustedScopeRef("tenant-a")
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "route-a",
                scope,
                TrustProfileRef("p", "v1", scope),
                frozenset({EvidenceMethod.JWT}),
            )
        ]
    )
    builder = AuthenticatorRegistryBuilder()
    builder.register(ScopedVerifier())
    registry = builder.freeze()
    gate = AuthenticationPolicyGate(catalog, final_rule=lambda _subject, _entry: True)
    engine = AuthenticationEngine(policy=gate, registry=registry)
    with pytest.raises(AttributeError, match="catalog cannot be mutated"):
        catalog._entries = {}  # type: ignore[assignment]
    with pytest.raises(AttributeError, match="registry cannot be mutated"):
        registry._entries = {}  # type: ignore[assignment]
    with pytest.raises(AttributeError, match="policy cannot be mutated"):
        gate._final_rule = lambda _subject, _entry: False  # type: ignore[assignment]
    with pytest.raises(AttributeError, match="composition cannot be mutated"):
        engine._registry = object()  # type: ignore[assignment]
