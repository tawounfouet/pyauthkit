"""M4 PR-07C negative SPI/cancellation tests for host-controlled dependencies."""

import asyncio
from datetime import UTC, datetime

import pytest

from pyauthkit.adapters.api_key_authenticator import ApiKeyAuthenticator
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.outcome import ErrorOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import VerificationContext


class EmptyResolver:
    async def resolve(self, *, scope_ref, key_id):
        raise AssertionError("resolver must not be reached")

    async def is_current(self, *, record):
        raise AssertionError("freshness must not be reached")


class EmptyProof:
    async def verify(self, *, scope_ref, presented, record):
        raise AssertionError("proof must not be reached")


class CancellableGuard:
    async def admit(self, *, scope_ref, correlation_id, key_id):
        raise asyncio.CancelledError


class FaultyClock:
    def now(self) -> datetime:
        return datetime(2026, 11, 5)


class AdmitGuard:
    async def admit(self, *, scope_ref, correlation_id, key_id) -> bool:
        return True


@pytest.mark.security
def test_guard_cancellation_is_propagated_not_translated_to_rejection() -> None:
    verifier = ApiKeyAuthenticator(
        resolver=EmptyResolver(), proof_verifier=EmptyProof(), attempt_guard=CancellableGuard()
    )
    scope = TrustedScopeRef("tenant-a")
    context = VerificationContext(
        scope_ref=scope,
        profile_ref=TrustProfileRef("p", "v1", scope),
        method=EvidenceMethod.API_KEY,
        correlation_id=CorrelationId("trace-1"),
        attempt_token=object(),
    )
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"not-a-valid-api-key"),
        CorrelationId("trace-1"),
    )
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(verifier.verify(request, context))


@pytest.mark.security
def test_verifier_rejects_method_mismatch_before_guard() -> None:
    verifier = ApiKeyAuthenticator(
        resolver=EmptyResolver(), proof_verifier=EmptyProof(), attempt_guard=AdmitGuard()
    )
    scope = TrustedScopeRef("tenant-a")
    context = VerificationContext(
        scope_ref=scope,
        profile_ref=TrustProfileRef("p", "v1", scope),
        method=EvidenceMethod.PASSWORD,
        correlation_id=CorrelationId("trace-1"),
        attempt_token=object(),
    )
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"not-a-valid-api-key"),
        CorrelationId("trace-1"),
    )
    result = asyncio.run(verifier.verify(request, context))
    assert isinstance(result, ErrorOutcome)
    assert result.error_code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
