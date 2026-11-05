"""Candidate M6 commit-before-positive audit, without enabling required mode.

Real SQLite transactions, synthetic M2 verified outcomes and deliberate
failures establish the narrow property: no Authenticated result escapes
through this gateway unless the exact attempt received a local commit receipt.
This is not G7 required-audit production qualification.
"""

import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from pyauthkit.adapters.audit_required_sqlite import (
    RequiredAuditAttemptConflict,
    RequiredAuditCommitUnavailable,
    SqliteRequiredAuditCommitter,
    provision_sqlite_required_audit,
)
from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    compose_authentication_engine,
    load_approved_configuration,
)
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.configuration.receipted_audit import (
    ReceiptedDecisionGateway,
    compose_receipted_audit_gateway,
)
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.ports.required_audit import (
    AuditAttemptId,
    AuditCommitReceipt,
    AuditDecisionRecord,
)

KEY = bytes(range(32))
CANARY = "SENSITIVE_SUBJECT_AND_CREDENTIAL_CANARY"


class PositiveSyntheticVerifier:
    """Only tests the audit boundary, not real JWT cryptographic verification."""

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.PASSWORD

    async def verify(self, request: AuthenticationRequest, context: VerificationContext):
        return _issue_verified_outcome(
            context,
            subject=ScopedSubjectRef(CANARY, "synthetic-issuer", context.scope_ref),
            principal_type=PrincipalType.HUMAN,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


def approved_snapshot():
    return load_approved_configuration(
        {
            "schema_version": 1,
            "routes": [
                {
                    "route_id": "required-audit-synthetic",
                    "scope": "tenant-a",
                    "profile_id": "password-synthetic",
                    "profile_version": "v1",
                    "allowed_methods": ["password"],
                }
            ],
            "timeout_seconds": 3.0,
            "audit_delivery": "best_effort",
            "secrets": [],
        },
        provenance=SourceProvenance("host", "mapping", "r1"),
        policy=SourcePolicy(frozenset({("host", "mapping")})),
        generation=ConfigurationGeneration(1),
    )


def attempt() -> AuditAttemptId:
    return AuditAttemptId(uuid4().hex)


def req(method: EvidenceMethod = EvidenceMethod.PASSWORD) -> AuthenticationRequest:
    return AuthenticationRequest(
        PresentedEvidence(method, CANARY.encode()),
        CorrelationId("audit-correlation-m6"),
    )


def store(tmp_path: Path, *, capacity: int = 10) -> SqliteRequiredAuditCommitter:
    path = tmp_path / "receipted-audit.sqlite"
    provision_sqlite_required_audit(path)
    return SqliteRequiredAuditCommitter(
        path=path, signing_key=KEY, key_id="test-signing-key-v1", capacity=capacity
    )


def gateway(committer):
    if type(committer) is SqliteRequiredAuditCommitter:
        return compose_receipted_audit_gateway(
            approved_snapshot(),
            authenticators=[PositiveSyntheticVerifier()],
            committer=committer,
            final_rule=lambda _subject, _entry: True,
        )
    # Deliberately bypass the approved *factory* in fault-injection-only tests
    # of the gateway's internal receipt validation. Never deploy this path.
    base = compose_authentication_engine(
        approved_snapshot(),
        authenticators=[PositiveSyntheticVerifier()],
        final_rule=lambda _subject, _entry: True,
        event_sink=None,
    )
    return ReceiptedDecisionGateway(base=base, committer=committer)


async def check(gw, attempt_id, *, method=EvidenceMethod.PASSWORD):
    return await gw.authenticate(
        req(method),
        entry=gw.catalog.resolve_for_host_route("required-audit-synthetic"),
        attempt_id=attempt_id,
    )


def test_m6_receipted_positive_requires_sqlite_commit_and_survives_reopen(
    tmp_path: Path,
) -> None:
    committer = store(tmp_path)
    gw = gateway(committer)
    key = attempt()
    assert isinstance(asyncio.run(check(gw, key)), Authenticated)
    original = committer.inspect_receipt(key)
    assert isinstance(original, AuditCommitReceipt)
    reopened = SqliteRequiredAuditCommitter(
        path=tmp_path / "receipted-audit.sqlite",
        signing_key=KEY,
        key_id="test-signing-key-v1",
    )
    persisted = reopened.inspect_receipt(key)
    assert persisted == original
    assert persisted.result_status == "AUTHENTICATED"
    raw = (tmp_path / "receipted-audit.sqlite").read_bytes()
    assert CANARY.encode() not in raw
    assert b"audit-correlation-m6" not in raw
    assert b"tenant-a" not in raw
    assert b"synthetic-issuer" not in raw


def test_m6_receipted_failure_to_commit_denies_positive(tmp_path: Path) -> None:
    committer = store(tmp_path)
    gw = gateway(committer)
    (tmp_path / "receipted-audit.sqlite").unlink()
    result = asyncio.run(check(gw, attempt()))
    assert isinstance(result, AuthError)
    assert result.error_code == TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


def test_m6_receipted_capacity_exhaustion_denies_second_positive(tmp_path: Path) -> None:
    committer = store(tmp_path, capacity=1)
    gw = gateway(committer)
    first, second = attempt(), attempt()
    assert isinstance(asyncio.run(check(gw, first)), Authenticated)
    denied = asyncio.run(check(gw, second))
    assert isinstance(denied, AuthError)
    assert denied.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert committer.inspect_receipt(first) is not None
    assert committer.inspect_receipt(second) is None


def test_m6_receipted_reuse_of_attempt_id_denied_after_restart(tmp_path: Path) -> None:
    committer = store(tmp_path)
    key = attempt()
    assert isinstance(asyncio.run(check(gateway(committer), key)), Authenticated)
    reopened = SqliteRequiredAuditCommitter(
        path=tmp_path / "receipted-audit.sqlite",
        signing_key=KEY,
        key_id="test-signing-key-v1",
    )
    assert isinstance(asyncio.run(check(gateway(reopened), key)), AuthError)
    assert committer.inspect_receipt(key) == reopened.inspect_receipt(key)


def test_m6_receipted_same_attempt_id_concurrent_race_has_one_winner(
    tmp_path: Path,
) -> None:
    committer = store(tmp_path)
    gw = gateway(committer)
    key = attempt()

    async def scenario():
        return await asyncio.gather(check(gw, key), check(gw, key))

    results = asyncio.run(scenario())
    assert len([r for r in results if isinstance(r, Authenticated)]) == 1
    assert len([r for r in results if isinstance(r, AuthError)]) == 1
    assert committer.inspect_receipt(key) is not None


def test_m6_receipted_distinct_attempt_ids_are_not_deduplicated(tmp_path: Path) -> None:
    committer = store(tmp_path)
    gw = gateway(committer)
    keys = [attempt() for _ in range(3)]

    async def scenario():
        return await asyncio.gather(*(check(gw, key) for key in keys))

    assert all(isinstance(r, Authenticated) for r in asyncio.run(scenario()))
    assert len({committer.inspect_receipt(key).record_id for key in keys}) == 3


def test_m6_receipted_rejection_is_recorded_before_return(tmp_path: Path) -> None:
    committer = store(tmp_path)
    gw = gateway(committer)
    key = attempt()
    result = asyncio.run(check(gw, key, method=EvidenceMethod.API_KEY))
    assert isinstance(result, Rejected)
    receipt = committer.inspect_receipt(key)
    assert receipt is not None
    assert receipt.result_status == "REJECTED"


def test_m6_receipted_corrupt_store_is_not_silently_repaired(tmp_path: Path) -> None:
    committer = store(tmp_path)
    with sqlite3.connect(tmp_path / "receipted-audit.sqlite") as connection:
        connection.execute("DROP TABLE required_audit_attempts")
    result = asyncio.run(check(gateway(committer), attempt()))
    assert isinstance(result, AuthError)


def test_m6_receipted_missing_store_never_auto_recreated(tmp_path: Path) -> None:
    path = tmp_path / "receipted-audit.sqlite"
    with pytest.raises(RequiredAuditCommitUnavailable, match="missing"):
        SqliteRequiredAuditCommitter(path=path, signing_key=KEY, key_id="v1")
    assert not path.exists()


def test_m6_receipted_reprovisioning_denied(tmp_path: Path) -> None:
    store(tmp_path)
    with pytest.raises(RequiredAuditCommitUnavailable, match="provisioning denied"):
        provision_sqlite_required_audit(tmp_path / "receipted-audit.sqlite")


def test_m6_receipted_explicit_commit_conflict_is_not_idempotent(tmp_path: Path) -> None:
    committer = store(tmp_path)
    gw = gateway(committer)
    key = attempt()
    assert isinstance(asyncio.run(check(gw, key)), Authenticated)
    with pytest.raises(RequiredAuditAttemptConflict):
        # A direct duplicate commit also must not return an old receipt.
        earlier = committer.inspect_receipt(key)
        assert earlier is not None
        from pyauthkit.domain.scope import TrustedScopeRef
        from pyauthkit.domain.trust import TrustProfileRef
        from pyauthkit.ports.events import AuthenticationEvent

        direct = AuditDecisionRecord(
            attempt_id=key,
            event=AuthenticationEvent(
                correlation_id=CorrelationId("audit-correlation-m6"),
                method=EvidenceMethod.PASSWORD,
                result_status="REJECTED",
                duration_ms=1.0,
            ),
            profile=TrustProfileRef("password-synthetic", "v1", TrustedScopeRef("tenant-a")),
        )
        asyncio.run(committer.commit(direct))


@pytest.mark.parametrize("invalid", ["", "x" * 32, "0" * 31, "A" * 32])
def test_m6_receipted_attempt_id_requires_lowercase_random_shape(invalid: str) -> None:
    with pytest.raises(ValueError):
        AuditAttemptId(invalid)


def test_m6_receipted_untrusted_entry_denied_before_positive(tmp_path: Path) -> None:
    gw = gateway(store(tmp_path))
    result = asyncio.run(
        gw.authenticate(
            req(), entry=object(), attempt_id=attempt()  # type: ignore[arg-type]
        )
    )
    assert isinstance(result, AuthError)


def test_m6_receipted_invalid_receipt_cannot_enable_positive() -> None:

    class FakeCommitter:
        async def commit(self, record: AuditDecisionRecord):
            return AuditCommitReceipt(
                attempt_id=AuditAttemptId("f" * 32),
                record_id=uuid4().hex,
                sequence=1,
                result_status=record.event.result_status,
                decision_tag="a" * 64,
            )

    result = asyncio.run(check(gateway(FakeCommitter()), attempt()))
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


def test_m6_receipted_slow_commit_never_releases_positive_early() -> None:
    entered = asyncio.Event()
    release = asyncio.Event()

    class DelayedCommitter:
        async def commit(self, record: AuditDecisionRecord):
            entered.set()
            await release.wait()
            return AuditCommitReceipt(
                attempt_id=record.attempt_id,
                record_id=uuid4().hex,
                sequence=1,
                result_status=record.event.result_status,
                decision_tag="b" * 64,
            )

    async def scenario() -> None:
        gw = gateway(DelayedCommitter())
        task = asyncio.create_task(check(gw, attempt()))
        await entered.wait()
        assert not task.done()
        release.set()
        assert isinstance(await task, Authenticated)

    asyncio.run(scenario())


def test_m6_receipted_cancel_during_commit_never_returns_authenticated() -> None:
    entered = asyncio.Event()

    class HangingCommitter:
        async def commit(self, record: AuditDecisionRecord):
            entered.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    async def scenario() -> None:
        task = asyncio.create_task(check(gateway(HangingCommitter()), attempt()))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_m6_receipted_forbidden_required_configuration_still_rejected() -> None:
    raw = {
        "schema_version": 1,
        "routes": [
            {
                "route_id": "required-audit-synthetic",
                "scope": "tenant-a",
                "profile_id": "password-synthetic",
                "profile_version": "v1",
                "allowed_methods": ["password"],
            }
        ],
        "timeout_seconds": 3.0,
        "audit_delivery": "required",
        "secrets": [],
    }
    with pytest.raises(ConfigurationRejected):
        load_approved_configuration(
            raw,
            provenance=SourceProvenance("host", "mapping", "r1"),
            policy=SourcePolicy(frozenset({("host", "mapping")})),
            generation=ConfigurationGeneration(1),
        )


def test_m6_receipted_fake_committer_exception_is_sanitized() -> None:
    class HostileCommitter:
        async def commit(self, _record: AuditDecisionRecord):
            raise RuntimeError(CANARY)

    result = asyncio.run(check(gateway(HostileCommitter()), attempt()))
    assert isinstance(result, AuthError)
    assert CANARY not in repr(result)

def test_m6_receipted_factory_refuses_untrusted_fake_committer() -> None:
    class ForgingCommitter:
        async def commit(self, record: AuditDecisionRecord):
            return AuditCommitReceipt(
                attempt_id=record.attempt_id,
                record_id=uuid4().hex,
                sequence=1,
                result_status=record.event.result_status,
                decision_tag="a" * 64,
            )

    with pytest.raises(ConfigurationRejected, match="unapproved auditable"):
        compose_receipted_audit_gateway(
            approved_snapshot(),
            authenticators=[PositiveSyntheticVerifier()],
            committer=ForgingCommitter(),
        )
