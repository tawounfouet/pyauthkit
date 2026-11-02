"""M1 domain unit tests: invariants, discriminated outcomes, and trust refs."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from pyauthkit.domain._verified import VerifiedSubject
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import DomainTechnicalError, RejectionCode, TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import (
    DomainTransitionBlocked,
    ErrorOutcome,
    RejectedOutcome,
    VerifiedOutcome,
    normalize_non_success,
)
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, ChallengeRequired, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.serialization import public_request_summary, public_result_summary
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import ScopeProfileRef, TrustProfileRef


def test_untrusted_identity_has_no_verified_or_permission_field() -> None:
    claim = ClaimedIdentity("email", "testuser@example.test", claimed_tenant="tenant-a")
    assert not hasattr(claim, "verified")
    assert not hasattr(claim, "permissions")
    assert not hasattr(claim, "scope")
    assert claim.claimed_tenant == "tenant-a"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("identifier_kind", ""),
        ("identifier_kind", "k" * 33),
        ("identifier_value", " "),
        ("identifier_value", "x" * 257),
        ("identifier_value", "abc\nxyz"),
        ("claimed_issuer", "\x00"),
        ("claimed_tenant", "x" * 129),
    ],
)
def test_invalid_identity_fields_fail_closed(field: str, value: str) -> None:
    args = {"identifier_kind": "username", "identifier_value": "alice", field: value}
    with pytest.raises(ValueError, match="invalid"):
        ClaimedIdentity(**args)


def test_claim_is_frozen_and_never_equivalent_to_verified_subject() -> None:
    claim = ClaimedIdentity("username", "alice")
    with pytest.raises(FrozenInstanceError):
        claim.identifier_value = "bob"  # type: ignore[misc]
    with pytest.raises(TypeError, match="approved verifier"):
        VerifiedSubject(claim)
    assert PrincipalType.HUMAN != PrincipalType.AGENT


def test_scoped_subject_identifiers_cannot_collapse_across_tenants_or_issuers() -> None:
    subject_a = ScopedSubjectRef("42", "issuer-1", TrustedScopeRef("tenant-a"))
    subject_b = ScopedSubjectRef("42", "issuer-1", TrustedScopeRef("tenant-b"))
    subject_c = ScopedSubjectRef("42", "issuer-2", TrustedScopeRef("tenant-a"))
    assert len({subject_a, subject_b, subject_c}) == 3


def test_profile_ref_is_not_host_authority_and_mismatch_fails_closed() -> None:
    scope_a = TrustedScopeRef("tenant-a")
    scope_b = TrustedScopeRef("tenant-b")
    profile = TrustProfileRef("profile-a", "v1", scope_a)
    assert ScopeProfileRef(scope_a, profile).scope_ref == scope_a
    with pytest.raises(ValueError, match="scope/profile mismatch"):
        ScopeProfileRef(scope_b, profile)
    assert "unapproved" in repr(profile)


@pytest.mark.parametrize(
    ("version", "scope"),
    [
        ("", TrustedScopeRef("tenant-a")),
        ("v1\n", TrustedScopeRef("tenant-a")),
        ("v1", "tenant-a"),
    ],
)
def test_invalid_profile_references_fail_closed(version: str, scope: object) -> None:
    with pytest.raises(ValueError, match="invalid"):
        TrustProfileRef("profile-a", version, scope)  # type: ignore[arg-type]


def test_evidence_is_bounded_immutable_and_not_a_dataclass() -> None:
    evidence = PresentedEvidence(EvidenceMethod.JWT, b"header.payload.signature")
    assert evidence.opaque_payload == b"header.payload.signature"
    with pytest.raises(AttributeError):
        evidence.method = EvidenceMethod.API_KEY
    assert evidence != PresentedEvidence(EvidenceMethod.JWT, b"header.payload.signature")


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        ("unknown", b"payload"),
        (EvidenceMethod.JWT, b""),
        (EvidenceMethod.JWT, b"x" * 65537),
        (EvidenceMethod.JWT, "not-bytes"),
        (EvidenceMethod.JWT, bytearray(b"x")),
    ],
)
def test_invalid_evidence_rejected_without_fallback(method: object, payload: object) -> None:
    with pytest.raises(ValueError):
        PresentedEvidence(method, payload)  # type: ignore[arg-type]


def test_request_has_no_scope_policy_or_positive_authentication_fields() -> None:
    request = AuthenticationRequest(
        evidence=PresentedEvidence(EvidenceMethod.API_KEY, b"x" * 24),
        claimed_identity=ClaimedIdentity("client_id", "test-client", claimed_tenant="tenant-a"),
        correlation_id=CorrelationId("m1-req-1"),
    )
    assert not hasattr(request, "trusted_scope")
    assert not hasattr(request, "trust_profile")
    assert not hasattr(request, "principal")
    assert not hasattr(request, "authenticated")
    assert public_request_summary(request) == {
        "method": "api_key",
        "correlation_id": "m1-req-1",
        "verified": False,
    }


def test_request_rejects_invalid_types() -> None:
    evidence = PresentedEvidence(EvidenceMethod.JWT, b"x")
    with pytest.raises(ValueError, match="invalid evidence"):
        AuthenticationRequest("bad", CorrelationId("trace-1"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid correlation"):
        AuthenticationRequest(evidence, "trace")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid claimed"):
        AuthenticationRequest(evidence, CorrelationId("trace-2"), claimed_identity="alice")  # type: ignore[arg-type]


def test_public_non_success_variants_have_no_principal_and_are_falsey() -> None:
    corr = CorrelationId("trace-m1")
    cases = [
        Rejected(corr),
        AuthError(corr, TechnicalErrorCode.DEPENDENCY_UNAVAILABLE),
        ChallengeRequired(corr),
    ]
    assert [case.status for case in cases] == ["REJECTED", "ERROR", "CHALLENGE_REQUIRED"]
    for case in cases:
        assert not hasattr(case, "principal")
        assert not case
        assert "principal" not in repr(case)


def test_positive_variants_have_no_public_constructor_in_m1() -> None:
    with pytest.raises(TypeError, match="approved verifier"):
        VerifiedSubject("fake")
    with pytest.raises(TypeError, match="approved authenticator"):
        VerifiedOutcome("fake")
    with pytest.raises(TypeError, match="verified policy gate"):
        Authenticated("fake")


def test_rejected_and_error_are_distinct_without_secret_messages() -> None:
    corr = CorrelationId("trace")
    rejection = Rejected(corr)
    error = AuthError(corr, TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
    assert rejection.status == "REJECTED"
    assert error.status == "ERROR"
    assert rejection.reason_code is RejectionCode.AUTHENTICATION_REJECTED
    assert error.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


def test_non_success_normalization_never_bypasses_policy_gate() -> None:
    corr = CorrelationId("trace")
    rejected = normalize_non_success(RejectedOutcome(), correlation_id=corr)
    failure = normalize_non_success(
        ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION), correlation_id=corr
    )
    assert isinstance(rejected, Rejected)
    assert isinstance(failure, AuthError)
    assert failure.error_code == TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
    with pytest.raises(DomainTransitionBlocked, match="policy gate"):
        normalize_non_success("VERIFIED", correlation_id=corr)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    ["", "with space", "with\nnewline", "x" * 129, "bad/slash", "\x00"],
)
def test_correlation_ids_reject_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError, match="invalid correlation"):
        CorrelationId(value)


def test_injected_clock_and_timezone_normalization() -> None:
    class FakeClock:
        def now(self) -> datetime:
            return datetime(2026, 11, 2, 11, 0, tzinfo=timezone(timedelta(hours=1)))

    result = ObservedAt.from_clock(FakeClock())
    assert result.value == datetime(2026, 11, 2, 10, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="timezone-aware"):
        ObservedAt(datetime(2026, 11, 2))


def test_domain_technical_error_exposes_only_safe_code() -> None:
    error = DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
    assert str(error) == "dependency_unavailable"
    assert "DEPENDENCY_UNAVAILABLE" not in str(error)
    with pytest.raises(ValueError, match="invalid technical"):
        DomainTechnicalError("raw exception detail")  # type: ignore[arg-type]


def test_public_result_serialization_is_allowlisted() -> None:
    corr = CorrelationId("trace-1")
    assert public_result_summary(Rejected(corr)) == {
        "status": "REJECTED",
        "correlation_id": "trace-1",
        "code": "authentication_rejected",
    }
    assert public_result_summary(AuthError(corr, TechnicalErrorCode.INTERNAL_ERROR)) == {
        "status": "ERROR",
        "correlation_id": "trace-1",
        "code": "internal_error",
    }
    assert public_result_summary(ChallengeRequired(corr)) == {
        "status": "CHALLENGE_REQUIRED",
        "correlation_id": "trace-1",
        "code": "additional_verification_required",
    }


def test_unexpected_objects_cannot_be_serialized_as_success() -> None:
    with pytest.raises(ValueError, match="policy gate"):
        public_result_summary(object())  # type: ignore[arg-type]
