"""M2 PR-04 host-authoritative binding and preflight contract tests."""

from dataclasses import FrozenInstanceError

import pytest

from pyauthkit.application.host_context import (
    HostBinding,
    HostRouteNotConfigured,
    HostTrustCatalog,
    TrustedEntryContext,
)
from pyauthkit.application.policy import AuthenticationPolicyGate, VerificationPermitted
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef


def binding(
    route: str = "api-login",
    scope_name: str = "tenant-a",
    methods: frozenset[EvidenceMethod] = frozenset({EvidenceMethod.JWT}),
) -> HostBinding:
    scope = TrustedScopeRef(scope_name)
    return HostBinding(route, scope, TrustProfileRef("profile-a", "v1", scope), methods)


def request(
    method: EvidenceMethod = EvidenceMethod.JWT, claimed_tenant: str | None = None
) -> AuthenticationRequest:
    claim = (
        ClaimedIdentity("username", "alice", claimed_tenant=claimed_tenant)
        if claimed_tenant is not None
        else None
    )
    return AuthenticationRequest(
        PresentedEvidence(method, b"x" * 20), CorrelationId("trace-pr04"), claim
    )


def test_approved_catalog_allows_only_attempt_not_authentication() -> None:
    catalog = HostTrustCatalog([binding()])
    entry = catalog.resolve_for_host_route("api-login")
    verdict = AuthenticationPolicyGate(catalog).preflight(request(), entry=entry)
    assert isinstance(verdict, VerificationPermitted)
    assert verdict.profile_ref == entry.profile_ref
    assert not hasattr(verdict, "principal")
    assert not hasattr(verdict, "status")
    assert "not authenticated" in repr(verdict)


def test_unknown_route_fails_without_a_default_scope() -> None:
    catalog = HostTrustCatalog([binding()])
    with pytest.raises(HostRouteNotConfigured, match="unconfigured"):
        catalog.resolve_for_host_route("unknown-route")


def test_duplicate_route_rejected_at_bootstrap() -> None:
    with pytest.raises(ValueError, match="duplicate host route"):
        HostTrustCatalog([binding(), binding(scope_name="tenant-b")])


def test_empty_catalog_and_empty_method_set_rejected() -> None:
    with pytest.raises(ValueError, match="empty host trust catalog"):
        HostTrustCatalog([])
    with pytest.raises(ValueError, match="approved method"):
        binding(methods=frozenset())


def test_scope_profile_mismatch_rejected_at_bootstrap() -> None:
    scope = TrustedScopeRef("tenant-a")
    wrong = TrustProfileRef("p", "v1", TrustedScopeRef("tenant-b"))
    with pytest.raises(ValueError, match="scope/profile mismatch"):
        HostBinding("api-login", scope, wrong, frozenset({EvidenceMethod.JWT}))


def test_unknown_or_invalid_route_label_rejected() -> None:
    with pytest.raises(ValueError, match="host route"):
        binding("api/login")
    with pytest.raises(HostRouteNotConfigured):
        HostTrustCatalog([binding()]).resolve_for_host_route(3)  # type: ignore[arg-type]


def test_client_tenant_claim_cannot_select_another_profile() -> None:
    catalog = HostTrustCatalog([binding()])
    entry = catalog.resolve_for_host_route("api-login")
    verdict = AuthenticationPolicyGate(catalog).preflight(
        request(claimed_tenant="tenant-b"), entry=entry
    )
    assert isinstance(verdict, Rejected)
    assert not hasattr(verdict, "principal")
    assert entry.profile_ref.scope_ref == TrustedScopeRef("tenant-a")


def test_matching_claim_does_not_change_host_profile() -> None:
    catalog = HostTrustCatalog([binding()])
    entry = catalog.resolve_for_host_route("api-login")
    verdict = AuthenticationPolicyGate(catalog).preflight(
        request(claimed_tenant="tenant-a"), entry=entry
    )
    assert isinstance(verdict, VerificationPermitted)
    assert verdict.profile_ref is entry.profile_ref


def test_disabled_method_fails_closed_even_under_valid_host_context() -> None:
    catalog = HostTrustCatalog([binding()])
    entry = catalog.resolve_for_host_route("api-login")
    verdict = AuthenticationPolicyGate(catalog).preflight(
        request(method=EvidenceMethod.API_KEY), entry=entry
    )
    assert isinstance(verdict, Rejected)
    assert not hasattr(verdict, "principal")


def test_context_from_other_catalog_is_rejected_despite_equal_fields() -> None:
    catalog = HostTrustCatalog([binding()])
    other = HostTrustCatalog([binding()])
    foreign_entry = other.resolve_for_host_route("api-login")
    assert not catalog.owns(foreign_entry)
    verdict = AuthenticationPolicyGate(catalog).preflight(request(), entry=foreign_entry)
    assert isinstance(verdict, AuthError)
    assert verdict.error_code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION


def test_fabricated_context_rejected_even_if_attributes_are_copied() -> None:
    catalog = HostTrustCatalog([binding()])
    original = catalog.resolve_for_host_route("api-login")
    fake = object.__new__(TrustedEntryContext)
    object.__setattr__(fake, "_scope_ref", original.scope_ref)
    object.__setattr__(fake, "_profile_ref", original.profile_ref)
    object.__setattr__(fake, "_allowed_methods", original.allowed_methods)
    assert not catalog.owns(fake)
    result = AuthenticationPolicyGate(catalog).preflight(request(), entry=fake)
    assert isinstance(result, AuthError)


def test_context_public_creation_and_mutation_are_blocked() -> None:
    catalog = HostTrustCatalog([binding()])
    entry = catalog.resolve_for_host_route("api-login")
    with pytest.raises(TypeError, match="approved catalog"):
        TrustedEntryContext()
    with pytest.raises(AttributeError, match="cannot be mutated"):
        entry._scope_ref = TrustedScopeRef("tenant-b")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen = binding()
        frozen.route_id = "new-route"  # type: ignore[misc]


def test_preflight_rejects_invalid_request_and_catalog_type() -> None:
    catalog = HostTrustCatalog([binding()])
    gate = AuthenticationPolicyGate(catalog)
    entry = catalog.resolve_for_host_route("api-login")
    with pytest.raises(ValueError, match="invalid authentication request"):
        gate.preflight("injected", entry=entry)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid host trust catalog"):
        AuthenticationPolicyGate(object())  # type: ignore[arg-type]


def test_host_catalog_snapshot_is_not_client_mutable() -> None:
    catalog = HostTrustCatalog([binding()])
    with pytest.raises(AttributeError):
        catalog.resolve_for_host_route("api-login")._allowed_methods = frozenset()  # type: ignore[misc]
    with pytest.raises(HostRouteNotConfigured):
        catalog.resolve_for_host_route("tenant-b")
