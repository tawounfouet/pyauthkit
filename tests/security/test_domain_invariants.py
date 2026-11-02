"""Security and property-based M1 tests for untrusted input boundaries."""

from dataclasses import asdict, is_dataclass

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pyauthkit.domain._verified import VerifiedSubject
from pyauthkit.domain.evidence import MAX_EVIDENCE_BYTES, EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.serialization import public_request_summary, public_result_summary
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import ScopeProfileRef, TrustProfileRef


@given(
    st.binary(min_size=1, max_size=1024),
    st.sampled_from(list(EvidenceMethod)),
)
@settings(max_examples=80, deadline=None)
def test_property_evidence_payload_never_in_repr(payload: bytes, method: EvidenceMethod) -> None:
    evidence = PresentedEvidence(method, payload)
    assert "<redacted>" in repr(evidence)
    assert repr(payload) not in repr(evidence)
    assert not is_dataclass(evidence)
    assert "opaque_payload" not in repr(evidence)


@given(st.text(min_size=1, max_size=256).filter(lambda s: s.strip() != "" and all(
    32 <= ord(char) < 127 for char in s
)))
@settings(max_examples=80)
def test_property_claims_never_turn_into_verified_subject(value: str) -> None:
    claim = ClaimedIdentity("username", value, claimed_tenant="tenant-a")
    assert claim.identifier_value == value
    assert not hasattr(claim, "verified")
    with pytest.raises(TypeError, match="approved verifier"):
        VerifiedSubject(claim)
    with pytest.raises(TypeError, match="verified policy gate"):
        Authenticated(claim)


@given(st.binary(min_size=1, max_size=1024))
@settings(max_examples=80)
def test_property_request_serialization_omits_evidence(payload: bytes) -> None:
    req = AuthenticationRequest(
        evidence=PresentedEvidence(EvidenceMethod.JWT, payload),
        correlation_id=CorrelationId("trace-test"),
        claimed_identity=ClaimedIdentity("username", "alice"),
    )
    summary = public_request_summary(req)
    assert summary == {"method": "jwt", "correlation_id": "trace-test", "verified": False}
    assert "opaque_payload" not in summary
    assert "claimed_identity" not in summary
    assert repr(payload) not in repr(req)
    assert not is_dataclass(req.evidence)
    # Generic dataclass traversal is deliberately disabled for sensitive bytes.
    with pytest.raises(TypeError, match="cannot be copied"):
        asdict(req)


@given(st.text(min_size=1, max_size=127, alphabet=st.characters(
    whitelist_categories=("Ll", "Lu", "Nd")
)))
@settings(max_examples=60)
def test_property_scopes_never_coalesce_unequal_tenants(raw: str) -> None:
    # Alphanumeric ASCII only, matching the existing TrustedScopeRef grammar.
    tenant = "tenant-a"
    scope = TrustedScopeRef(tenant)
    foreign = TrustedScopeRef("tenant-b")
    subject_id = raw.encode("ascii", "ignore").decode("ascii")
    if not subject_id:
        return
    own = ScopedSubjectRef(subject_id, "issuer-a", scope)
    other = ScopedSubjectRef(subject_id, "issuer-a", foreign)
    assert own != other
    with pytest.raises(ValueError, match="scope/profile mismatch"):
        ScopeProfileRef(foreign, TrustProfileRef("p1", "v1", scope))


@pytest.mark.parametrize("size", [0, MAX_EVIDENCE_BYTES + 1, MAX_EVIDENCE_BYTES + 1024])
def test_evidence_size_limits_are_finite(size: int) -> None:
    with pytest.raises(ValueError, match="invalid evidence"):
        PresentedEvidence(EvidenceMethod.JWT, b"x" * size)


def test_secret_marker_is_absent_from_repr_and_all_serializers() -> None:
    marker = "SYNTHETIC_PRIVATE_MARKER_NOT_A_REAL_SECRET"
    corr = CorrelationId("safe-id")
    req = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.PASSWORD, marker.encode()),
        corr,
        ClaimedIdentity("username", marker),
    )
    rendered = repr(req) + repr(req.evidence) + repr(req.claimed_identity)
    rendered += repr(Rejected(corr)) + repr(AuthError(corr, TechnicalErrorCode.INTERNAL_ERROR))
    rendered += str(public_request_summary(req)) + str(public_result_summary(Rejected(corr)))
    assert marker not in rendered
