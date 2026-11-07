"""M7 plugin SPI must preserve host-approved tenant binding and cancellation."""

import asyncio

import pytest

from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity
from pyauthkit.domain.outcome import RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import VerificationContext


class ScopedDenialPlugin:
    def __init__(self) -> None:
        self.contexts: list[VerificationContext] = []

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> RejectedOutcome:
        self.contexts.append(context)
        return RejectedOutcome()


def make_engine(plugin: ScopedDenialPlugin) -> tuple[AuthenticationEngine, HostTrustCatalog]:
    bindings = []
    for name in ("tenant-a", "tenant-b"):
        scope = TrustedScopeRef(name)
        profile = TrustProfileRef("m7-plugin", "v1", scope)
        bindings.append(
            HostBinding(f"route-{name}", scope, profile, frozenset({EvidenceMethod.API_KEY}))
        )
    catalog = HostTrustCatalog(bindings)
    builder = AuthenticatorRegistryBuilder()
    builder.register(plugin)
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _subject, _entry: True),
        registry=builder.freeze(),
        timeout_seconds=3.0,
    )
    return engine, catalog


def test_plugin_receives_only_host_approved_scope_and_cannot_accept_foreign_hint() -> None:
    plugin = ScopedDenialPlugin()
    engine, catalog = make_engine(plugin)

    async def scenario() -> None:
        foreign = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, b"synthetic-invalid"),
            CorrelationId("m7-cross-hint"),
            claimed_identity=ClaimedIdentity(
                identifier_kind="account",
                identifier_value="synthetic",
                claimed_tenant="tenant-b",
            ),
        )
        denied = await engine.authenticate(
            foreign, entry=catalog.resolve_for_host_route("route-tenant-a")
        )
        assert isinstance(denied, Rejected)
        assert plugin.contexts == []

        for tenant in ("tenant-a", "tenant-b"):
            request = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.API_KEY, b"synthetic-invalid"),
                CorrelationId(f"m7-{tenant}"),
            )
            result = await engine.authenticate(
                request, entry=catalog.resolve_for_host_route(f"route-{tenant}")
            )
            assert isinstance(result, Rejected)
            assert not hasattr(result, "principal")

    asyncio.run(scenario())
    assert [context.scope_ref.value for context in plugin.contexts] == ["tenant-a", "tenant-b"]


def test_cancelled_plugin_verification_is_not_normalized_to_a_success() -> None:
    class CancellablePlugin:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.cancelled = False

        @property
        def method(self) -> EvidenceMethod:
            return EvidenceMethod.API_KEY

        async def verify(
            self, request: AuthenticationRequest, context: VerificationContext
        ) -> RejectedOutcome:
            self.started.set()
            try:
                await asyncio.sleep(30)
            finally:
                self.cancelled = True
            return RejectedOutcome()

    plugin = CancellablePlugin()
    scope = TrustedScopeRef("tenant-cancel")
    profile = TrustProfileRef("m7-plugin", "v1", scope)
    catalog = HostTrustCatalog(
        [HostBinding("host-route", scope, profile, frozenset({EvidenceMethod.API_KEY}))]
    )
    builder = AuthenticatorRegistryBuilder()
    builder.register(plugin)
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog), registry=builder.freeze()
    )

    async def scenario() -> None:
        request = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, b"synthetic-invalid"),
            CorrelationId("m7-cancel"),
        )
        task = asyncio.create_task(
            engine.authenticate(request, entry=catalog.resolve_for_host_route("host-route"))
        )
        await plugin.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert plugin.cancelled
