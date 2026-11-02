"""Contract suite for explicitly admitted async Authenticator implementations.

These tests validate the SPI wiring and failure semantics; no cryptographic
verification or production authenticator is implied.
"""

import asyncio

import pytest

from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.outcome import ErrorOutcome, RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import VerificationContext


class ControlledVerifier:
    """Test-only adapter that cannot manufacture a positive authentication."""

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.JWT

    def __init__(self, outcome: object) -> None:
        self.outcome = outcome
        self.calls: list[VerificationContext] = []

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> object:
        self.calls.append(context)
        return self.outcome


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (RejectedOutcome(), Rejected),
        (ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE), AuthError),
        (object(), AuthError),
    ],
)
def test_m2_t09_t10_t24_all_spi_outcomes_are_normalized(
    outcome: object, expected: type[Rejected] | type[AuthError]
) -> None:
    scope = TrustedScopeRef("tenant-contract")
    profile = TrustProfileRef("profile-contract", "v1", scope)
    catalog = HostTrustCatalog(
        [HostBinding("api-contract", scope, profile, frozenset({EvidenceMethod.JWT}))]
    )
    verifier = ControlledVerifier(outcome)
    builder = AuthenticatorRegistryBuilder()
    builder.register(verifier)
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog),
        registry=builder.freeze(),
    )
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, b"synthetic-untrusted-input"),
        CorrelationId("contract-run"),
    )
    result = asyncio.run(
        engine.authenticate(request, entry=catalog.resolve_for_host_route("api-contract"))
    )
    assert isinstance(result, expected)
    assert not hasattr(result, "principal")
    assert len(verifier.calls) == 1
    context = verifier.calls[0]
    assert context.method is EvidenceMethod.JWT
    assert context.scope_ref == scope
    assert context.profile_ref == profile
    assert context.correlation_id == request.correlation_id


def test_m2_t07_registry_collision_fails_at_admission() -> None:
    builder = AuthenticatorRegistryBuilder()
    builder.register(ControlledVerifier(RejectedOutcome()))
    with pytest.raises(ValueError, match="duplicate"):
        builder.register(ControlledVerifier(RejectedOutcome()))


def test_m2_t08_frozen_registry_keeps_exact_approved_implementation() -> None:
    builder = AuthenticatorRegistryBuilder()
    expected = ControlledVerifier(RejectedOutcome())
    builder.register(expected)
    registry = builder.freeze()
    assert registry.resolve(EvidenceMethod.JWT) is expected
    with pytest.raises(RuntimeError, match="frozen"):
        builder.register(ControlledVerifier(RejectedOutcome()))
