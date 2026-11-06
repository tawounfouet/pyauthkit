"""M7 positive plugin-proof SPI: declaration is not final authentication."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.plugins.verification import (
    PluginProofDeclarationRejected,
    issue_verified_outcome,
)
from pyauthkit.ports.authenticator import VerificationContext


def fixture_context() -> tuple[AuthenticationRequest, VerificationContext, ScopedSubjectRef]:
    scope = TrustedScopeRef("tenant-a")
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"m7-positive-canary"),
        CorrelationId("m7-positive"),
    )
    context = VerificationContext(
        scope,
        TrustProfileRef("profile", "v1", scope),
        EvidenceMethod.API_KEY,
        request.correlation_id,
        object(),
    )
    subject = ScopedSubjectRef("synthetic", "m7-test-only", scope)
    return request, context, subject


def issue(
    request: AuthenticationRequest,
    context: VerificationContext,
    subject: ScopedSubjectRef,
) -> VerifiedOutcome:
    return issue_verified_outcome(
        request=request,
        context=context,
        subject=subject,
        principal_type=PrincipalType.SERVICE,
        verified_at=ObservedAt(datetime.now(UTC)),
    )


def test_verified_declaration_is_internal_and_not_final_authn() -> None:
    request, context, subject = fixture_context()
    outcome = issue(request, context, subject)
    assert isinstance(outcome, VerifiedOutcome)
    assert outcome.correlation_id == request.correlation_id
    assert not isinstance(outcome, Authenticated)
    assert "m7-positive-canary" not in repr(outcome)


@pytest.mark.parametrize("mutation", ["foreign_scope", "foreign_method", "foreign_trace"])
def test_declared_proof_rejects_context_confusion(mutation: str) -> None:
    request, context, subject = fixture_context()
    if mutation == "foreign_scope":
        subject = ScopedSubjectRef("synthetic", "m7-test-only", TrustedScopeRef("tenant-b"))
    elif mutation == "foreign_method":
        request = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.JWT, b"m7-positive-canary"),
            request.correlation_id,
        )
    else:
        request = AuthenticationRequest(
            request.evidence,
            CorrelationId("attacker-changed-correlation"),
        )
    with pytest.raises(PluginProofDeclarationRejected) as error:
        issue(request, context, subject)
    assert "m7-positive-canary" not in repr(error.value)


def test_declared_proof_rejects_wrong_subject_type() -> None:
    request, context, _ = fixture_context()
    with pytest.raises(PluginProofDeclarationRejected):
        issue_verified_outcome(
            request=request,
            context=context,
            subject="attacker-controlled-subject",  # type: ignore[arg-type]
            principal_type=PrincipalType.SERVICE,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


class ProofFixturePlugin:
    """Synthetic already-verified result; NOT a credential verifier."""

    def __init__(self, *, stale_attempt: bool = False) -> None:
        self.stale_attempt = stale_attempt

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> VerifiedOutcome:
        approved = context
        if self.stale_attempt:
            approved = replace(context, attempt_token=object())
        return issue(
            request,
            approved,
            ScopedSubjectRef("fixture-subject", "m7-test-only", context.scope_ref),
        )


def run_engine(*, allow: bool, stale_attempt: bool = False) -> object:
    scope = TrustedScopeRef("tenant-a")
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "host-route",
                scope,
                TrustProfileRef("profile", "v1", scope),
                frozenset({EvidenceMethod.API_KEY}),
            )
        ]
    )
    builder = AuthenticatorRegistryBuilder()
    builder.register(ProofFixturePlugin(stale_attempt=stale_attempt))
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(
            catalog, final_rule=lambda _subject, _entry: allow
        ),
        registry=builder.freeze(),
    )
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"test-only-not-proof"),
        CorrelationId("m7-engine"),
    )
    return asyncio.run(
        engine.authenticate(request, entry=catalog.resolve_for_host_route("host-route"))
    )


def test_policy_denial_overrides_synthetic_plugin_verified_outcome() -> None:
    result = run_engine(allow=False)
    assert isinstance(result, Rejected)
    assert not hasattr(result, "principal")


def test_wrong_engine_attempt_token_never_authenticates() -> None:
    result = run_engine(allow=True, stale_attempt=True)
    assert isinstance(result, AuthError)
    assert not hasattr(result, "principal")


def test_engine_is_only_issuer_of_final_success_in_synthetic_test() -> None:
    result = run_engine(allow=True)
    assert isinstance(result, Authenticated)
    assert result.principal.subject.scope_ref.value == "tenant-a"
