"""PR-07A: model invariants, defensive redaction and immutable projection."""

import copy
import pickle
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest

from pyauthkit.domain.api_key import (
    ApiKeyCredentialRef,
    ApiKeyFound,
    ApiKeyRecordStatus,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt


def make_record(**overrides: object) -> ApiKeyVerifierRecord:
    scope = TrustedScopeRef("tenant-a:production")
    fields: dict[str, object] = {
        "scope_ref": scope,
        "subject_ref": ScopedSubjectRef(
            subject_id="service-a", issuer_ref="issuer-a", scope_ref=scope
        ),
        "principal_type": PrincipalType.SERVICE,
        "key_id": "key-identifier-1",
        "verifier_digest": b"CANARY_SENSITIVE_DIGEST_123456789",  # 32 bytes
        "verifier_algorithm": "hmac-sha256",
        "protection_key_ref": "hmac-v1",
        "status": ApiKeyRecordStatus.ACTIVE,
        "version": 1,
        "not_before": ObservedAt(datetime(2026, 1, 1, tzinfo=UTC)),
        "expires_at": ObservedAt(datetime(2027, 1, 1, tzinfo=UTC)),
    }
    fields.update(overrides)
    return ApiKeyVerifierRecord(**fields)


@pytest.mark.security
def test_no_sensitive_material_in_record_or_found_repr() -> None:
    item = make_record()
    for value in (repr(item), repr(ApiKeyFound(item)), repr(ApiKeyCredentialRef(item.key_id))):
        assert "CANARY" not in value
        assert item.key_id not in value
        assert "issuer-a" not in value


@pytest.mark.security
def test_record_cannot_be_mutated_or_generically_copied() -> None:
    item = make_record()
    with pytest.raises(AttributeError):
        item.version = 2
    with pytest.raises(TypeError):
        copy.deepcopy(item)
    with pytest.raises(TypeError):
        asdict(item)
    with pytest.raises(TypeError):
        pickle.dumps(item)


@pytest.mark.security
def test_cross_scope_subject_is_rejected_on_construction() -> None:
    foreign_scope = TrustedScopeRef("tenant-b:production")
    foreign = ScopedSubjectRef(
        subject_id="service-b", issuer_ref="issuer-b", scope_ref=foreign_scope
    )
    with pytest.raises(ValueError, match="scope mismatch"):
        make_record(subject_ref=foreign)


@pytest.mark.security
@pytest.mark.parametrize("kind", [PrincipalType.HUMAN, PrincipalType.AGENT, PrincipalType.DEVICE])
def test_human_agent_and_device_not_silently_admitted(kind: PrincipalType) -> None:
    with pytest.raises(ValueError, match="principal type"):
        make_record(principal_type=kind)


@pytest.mark.security
@pytest.mark.parametrize("version", [-1, True, 2**63])
def test_invalid_record_versions_fail_closed(version: object) -> None:
    with pytest.raises(ValueError, match="version"):
        make_record(version=version)


@pytest.mark.security
def test_invalid_digest_length_or_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="digest length"):
        make_record(verifier_digest=b"wrong")
    with pytest.raises(ValueError, match="status"):
        make_record(status="active")


@pytest.mark.security
def test_inverted_window_is_rejected() -> None:
    future = ObservedAt(datetime(2027, 1, 1, tzinfo=UTC))
    past = ObservedAt(datetime(2026, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="validity window"):
        make_record(not_before=future, expires_at=past)


@pytest.mark.security
def test_naive_timestamp_rejected_by_existing_observed_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ObservedAt(datetime(2026, 1, 1))


@pytest.mark.security
def test_key_selector_is_bounded_and_not_proof() -> None:
    for value in ("", " ", "x" * 129, "key\ninvalid", "\u00e9"):
        with pytest.raises(ValueError, match="selector"):
            ApiKeyCredentialRef(value)


@pytest.mark.security
def test_record_fields_remain_unverified_even_if_active() -> None:
    item = make_record(status=ApiKeyRecordStatus.ACTIVE)
    assert item.status is ApiKeyRecordStatus.ACTIVE
    assert not hasattr(item, "authenticated")
    assert not hasattr(item, "permissions")
