"""Adversarial M2 PR-04 tests: no client-selected trust or positive result."""

import pytest

from pyauthkit.application.host_context import (
    HostBinding,
    HostTrustCatalog,
    TrustedEntryContext,
)
from pyauthkit.application.policy import AuthenticationPolicyGate, VerificationPermitted
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef


def test_untrusted_tenant_hint_never_mints_positive_result() -> None:
    scope = TrustedScopeRef("tenant-accepted")
    profile = TrustProfileRef("profile-one", "v1", scope)
    catalog = HostTrustCatalog(
        [HostBinding("app-route", scope, profile, frozenset({EvidenceMethod.JWT}))]
    )
    gate = AuthenticationPolicyGate(catalog)
    entry = catalog.resolve_for_host_route("app-route")
    for hint in ("tenant-accepted", "tenant-foreign"):
        result = gate.preflight(
            AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.JWT, b"x"),
                CorrelationId("trace-1"),
                ClaimedIdentity("username", "alice", claimed_tenant=hint),
            ),
            entry=entry,
        )
        assert isinstance(result, VerificationPermitted | Rejected)
        assert not isinstance(result, Authenticated)
        assert not hasattr(result, "principal")


def test_arbitrary_context_is_rejected_not_defaulted() -> None:
    scope = TrustedScopeRef("tenant-one")
    profile = TrustProfileRef("profile-one", "v1", scope)
    catalog = HostTrustCatalog(
        [HostBinding("http-a", scope, profile, frozenset({EvidenceMethod.JWT}))]
    )
    forged = object.__new__(TrustedEntryContext)
    result = AuthenticationPolicyGate(catalog).preflight(
        AuthenticationRequest(PresentedEvidence(EvidenceMethod.JWT, b"x"), CorrelationId("trace")),
        entry=forged,
    )
    assert isinstance(result, AuthError)
    assert not hasattr(result, "principal")


def test_preflight_cannot_create_final_authenticated() -> None:
    with pytest.raises(TypeError, match="verified policy gate"):
        Authenticated()
