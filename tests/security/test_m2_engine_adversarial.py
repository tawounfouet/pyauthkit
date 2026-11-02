"""M2-T01..24: adversarial oracles independent of the async engine implementation.

All positive verifications below are SYNTHETIC and TEST ONLY. They validate
host/engine/policy wiring, NOT any password, API key or JWT cryptography.
"""

import asyncio
from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import (
    AuthenticatorNotConfigured,
    AuthenticatorRegistryBuilder,
)
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import ErrorOutcome, RejectedOutcome, VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.ports.events import AuthenticationEvent


class FakeAuthenticator:
    """Only in tests/, deliberately never registered by production defaults."""

    method = EvidenceMethod.JWT

    def __init__(self, behavior: str = "verified") -> None:
        self.behavior = behavior
        self.calls = 0
        self.contexts: list[VerificationContext] = []

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> object:
        self.calls += 1
        self.contexts.append(context)
        if self.behavior == "rejected":
            return RejectedOutcome()
        if self.behavior == "error":
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if self.behavior == "exception":
            raise RuntimeError("sensitive_token_ABC123")
        if self.behavior == "timeout":
            await asyncio.sleep(0.1)
        if self.behavior == "malicious-result":
            return object.__new__(Authenticated)
        if self.behavior == "foreign-attempt":
            context = VerificationContext(
                context.scope_ref,
                context.profile_ref,
                context.method,
                context.correlation_id,
                object(),
            )
        if self.behavior == "foreign-profile":
            wrong_scope = TrustedScopeRef("another-tenant")
            context = VerificationContext(
                wrong_scope,
                TrustProfileRef("another-profile", "v4", wrong_scope),
                context.method,
                context.correlation_id,
                object(),
            )
        if self.behavior == "foreign-method":
            context = VerificationContext(
                context.scope_ref,
                context.profile_ref,
                EvidenceMethod.API_KEY,
                context.correlation_id,
                context.attempt_token,
            )
        return _issue_verified_outcome(
            context,
            subject=ScopedSubjectRef("synthetic-subject", "test-only", context.scope_ref),
            principal_type=PrincipalType.HUMAN,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


class SpyPolicy(AuthenticationPolicyGate):
    def __init__(self, catalog: HostTrustCatalog, *, allow: bool = False) -> None:
        super().__init__(catalog, final_rule=lambda _subject, _entry: allow)
        object.__setattr__(self, "final_calls", 0)

    def final_decision(
        self,
        request: AuthenticationRequest,
        *,
        entry: object,
        context: VerificationContext,
        outcome: VerifiedOutcome,
    ) -> Authenticated | Rejected | AuthError:
        object.__setattr__(self, "final_calls", self.final_calls + 1)
        return super().final_decision(
            request, entry=entry, context=context, outcome=outcome  # type: ignore[arg-type]
        )


class MemorySink:
    def __init__(self, *, fails: bool = False) -> None:
        self.fails = fails
        self.events: list[AuthenticationEvent] = []

    async def emit(self, event: AuthenticationEvent) -> None:
        self.events.append(event)
        if self.fails:
            raise RuntimeError("sensitive_token_ABC123")


def request(
    method: EvidenceMethod = EvidenceMethod.JWT,
    tenant: str | None = None,
) -> AuthenticationRequest:
    claim = ClaimedIdentity("username", "unverified-user", claimed_tenant=tenant) if tenant else None
    return AuthenticationRequest(
        PresentedEvidence(method, b"secret_check_do_not_log"),
        CorrelationId("attempt-m2"),
        claim,
    )


def harness(
    behavior: str = "verified",
    *,
    allow: bool = False,
    sink: MemorySink | None = None,
    timeout_seconds: float = 1.0,
) -> tuple[AuthenticationEngine, FakeAuthenticator, SpyPolicy, HostTrustCatalog]:
    scope = TrustedScopeRef("tenant-a")
    profile = TrustProfileRef("approved-profile", "v1", scope)
    catalog = HostTrustCatalog(
        [HostBinding("host-route-a", scope, profile, frozenset({EvidenceMethod.JWT}))]
    )
    verifier = FakeAuthenticator(behavior)
    builder = AuthenticatorRegistryBuilder()
    builder.register(verifier)
    registry = builder.freeze()
    gate = SpyPolicy(catalog, allow=allow)
    engine = AuthenticationEngine(
        policy=gate,
        registry=registry,
        timeout_seconds=timeout_seconds,
        event_sink=sink,
    )
    return engine, verifier, gate, catalog


def test_m2_t13_only_host_bound_fake_plus_final_allow_succeeds() -> None:
    engine, fake, gate, catalog = harness(allow=True)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, Authenticated)
    assert result.status == "AUTHENTICATED"
    assert fake.calls == 1
    assert gate.final_calls == 1
    assert result.principal.subject.scope_ref == TrustedScopeRef("tenant-a")
    assert "synthetic-subject" not in repr(result)


def test_m2_t12_positive_fake_with_final_denial_never_yields_principal() -> None:
    engine, fake, gate, catalog = harness(allow=False)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, Rejected)
    assert not hasattr(result, "principal")
    assert gate.final_calls == 1
    assert fake.calls == 1


@pytest.mark.parametrize("behavior", ["foreign-attempt", "foreign-profile", "foreign-method"])
def test_m2_t11_foreign_positive_outcomes_fail_before_final_gate(behavior: str) -> None:
    engine, fake, gate, catalog = harness(behavior, allow=True)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, AuthError)
    assert not hasattr(result, "principal")
    assert fake.calls == 1
    assert gate.final_calls == 0


def test_m2_t24_verifier_cannot_return_final_authenticated_itself() -> None:
    engine, _, gate, catalog = harness("malicious-result", allow=True)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, AuthError)
    assert gate.final_calls == 0


@pytest.mark.parametrize(
    ("behavior", "expected"),
    [
        ("rejected", Rejected),
        ("error", AuthError),
        ("exception", AuthError),
    ],
)
def test_m2_t09_t10_t14_negative_fault_paths(
    behavior: str, expected: type[Rejected] | type[AuthError]
) -> None:
    engine, fake, gate, catalog = harness(behavior, allow=True)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, expected)
    assert not hasattr(result, "principal")
    assert gate.final_calls == 0
    assert fake.calls == 1
    assert "sensitive_token" not in repr(result)


def test_m2_t05_disallowed_method_short_circuits_verification() -> None:
    engine, fake, gate, catalog = harness(allow=True)
    result = asyncio.run(
        engine.authenticate(
            request(method=EvidenceMethod.PASSWORD),
            entry=catalog.resolve_for_host_route("host-route-a"),
        )
    )
    assert isinstance(result, Rejected)
    assert fake.calls == 0
    assert gate.final_calls == 0


def test_m2_t02_t03_foreign_tenant_and_unknown_route() -> None:
    engine, fake, gate, catalog = harness(allow=True)
    result = asyncio.run(
        engine.authenticate(
            request(tenant="tenant-b"),
            entry=catalog.resolve_for_host_route("host-route-a"),
        )
    )
    assert isinstance(result, Rejected)
    assert fake.calls == gate.final_calls == 0
    with pytest.raises(Exception, match="unconfigured host route"):
        catalog.resolve_for_host_route("tenant-b")


def test_m2_t06_t07_t08_registry_freeze_and_no_fallback() -> None:
    fake = FakeAuthenticator()
    builder = AuthenticatorRegistryBuilder()
    builder.register(fake)
    with pytest.raises(ValueError, match="duplicate"):
        builder.register(FakeAuthenticator())
    registry = builder.freeze()
    with pytest.raises(RuntimeError, match="frozen"):
        builder.register(FakeAuthenticator())
    with pytest.raises(RuntimeError, match="frozen"):
        builder.freeze()
    with pytest.raises(AuthenticatorNotConfigured):
        registry.resolve(EvidenceMethod.PASSWORD)
    assert registry.resolve(EvidenceMethod.JWT) is fake


def test_m2_t15_timeout_cannot_late_authenticate() -> None:
    engine, fake, gate, catalog = harness("timeout", allow=True, timeout_seconds=0.001)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert not hasattr(result, "principal")
    assert gate.final_calls == 0
    assert fake.calls == 1


def test_m2_t16_cancellation_is_propagated_not_normalized_to_success() -> None:
    async def scenario() -> None:
        engine, fake, gate, catalog = harness("timeout", allow=True)
        task = asyncio.create_task(
            engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert fake.calls <= 1
        assert gate.final_calls == 0
    asyncio.run(scenario())


@pytest.mark.parametrize("fails", [False, True])
def test_m2_t18_t21_event_redaction_and_documented_best_effort(fails: bool) -> None:
    sink = MemorySink(fails=fails)
    engine, _, _, catalog = harness(allow=True, sink=sink)
    result = asyncio.run(
        engine.authenticate(request(), entry=catalog.resolve_for_host_route("host-route-a"))
    )
    assert isinstance(result, Authenticated)
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.result_status == "AUTHENTICATED"
    assert event.method is EvidenceMethod.JWT
    assert event.duration_ms >= 0
    assert "secret_check_do_not_log" not in repr(event)
    assert "synthetic-subject" not in repr(event)


@given(st.sampled_from(["tenant-a", "tenant-b", "tenant-c"]))
def test_m2_t02_property_claimed_tenant_cannot_change_host_profile(tenant: str) -> None:
    engine, fake, gate, catalog = harness(allow=False)
    result = asyncio.run(
        engine.authenticate(
            request(tenant=tenant), entry=catalog.resolve_for_host_route("host-route-a")
        )
    )
    assert isinstance(result, Rejected)
    if tenant != "tenant-a":
        assert fake.calls == 0
        assert gate.final_calls == 0


def test_m2_t11_constructor_guards_are_still_enforced() -> None:
    with pytest.raises(TypeError, match="approved authenticator"):
        VerifiedOutcome()
    with pytest.raises(TypeError, match="verified policy gate"):
        Authenticated()


def test_m2_t01_untrusted_request_payload_limits() -> None:
    with pytest.raises(ValueError, match="invalid evidence payload"):
        PresentedEvidence(EvidenceMethod.JWT, b"")
    with pytest.raises(ValueError, match="invalid evidence payload"):
        PresentedEvidence(EvidenceMethod.JWT, b"x" * 65537)
