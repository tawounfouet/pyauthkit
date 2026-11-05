"""M6 local SQLite audit evidence, pseudonymization and failure boundaries.

This is an append-only-by-API reference under an explicitly trusted local
host file. It is not an external immutable audit ledger or a required audit
guarantee. All event identifiers and sensitive fixtures are synthetic.
"""

import asyncio
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from pyauthkit.adapters.audit_sqlite import (
    AuditPersistenceUnavailable,
    SqliteAuthenticationAuditSink,
    provision_sqlite_audit_store,
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
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.ports.events import AuthenticationEvent

HMAC_KEY = bytes(range(32))
OTHER_KEY = bytes(range(32, 64))
CANARY = "CONFIDENTIAL_BEARER_AND_SUBJECT_M6"
TRACE = CorrelationId("corr-m6-007")


def event(
    *,
    correlation: CorrelationId = TRACE,
    method: EvidenceMethod = EvidenceMethod.JWT,
    outcome: str = "AUTHENTICATED",
    duration_ms: float = 12.5,
) -> AuthenticationEvent:
    return AuthenticationEvent(
        correlation_id=correlation,
        method=method,
        result_status=outcome,  # type: ignore[arg-type]
        duration_ms=duration_ms,
    )


def provisioned(tmp_path: Path, *, capacity: int = 100) -> SqliteAuthenticationAuditSink:
    path = tmp_path / "m6-audit.sqlite"
    provision_sqlite_audit_store(path)
    return SqliteAuthenticationAuditSink(
        path=path,
        pseudonymization_key=HMAC_KEY,
        pseudonym_key_id="audit-key-v1",
        capacity=capacity,
    )


def test_m6_local_audit_persists_across_connections_without_raw_correlation(
    tmp_path: Path,
) -> None:
    first = provisioned(tmp_path)
    asyncio.run(first.emit(event()))
    assert len(first.inspect_recent()) == 1
    second = SqliteAuthenticationAuditSink(
        path=tmp_path / "m6-audit.sqlite",
        pseudonymization_key=HMAC_KEY,
        pseudonym_key_id="audit-key-v1",
    )
    record = second.inspect_recent()[0]
    assert record.sequence == 1
    assert record.method == "jwt"
    assert record.outcome == "AUTHENTICATED"
    assert record.duration_ms == 12.5
    assert len(record.correlation_tag) == 64
    assert TRACE.value not in record.correlation_tag
    assert TRACE.value not in repr(record)
    assert CANARY not in repr(first)
    assert CANARY not in repr(record)
    with sqlite3.connect(tmp_path / "m6-audit.sqlite") as db:
        schema = db.execute("SELECT correlation_tag FROM audit_events").fetchone()
        assert schema is not None
        assert schema[0] == record.correlation_tag
        assert TRACE.value not in str(db.execute("SELECT * FROM audit_events").fetchall())


def test_m6_audit_payload_canary_is_never_persisted_in_database_file(tmp_path: Path) -> None:
    sink = provisioned(tmp_path)
    asyncio.run(sink.emit(event(correlation=CorrelationId("trace-no-secret"))))
    raw_db = (tmp_path / "m6-audit.sqlite").read_bytes()
    assert CANARY.encode() not in raw_db
    assert b"trace-no-secret" not in raw_db
    assert b"audit-key-v1" in raw_db


def test_m6_audit_pseudonym_is_stable_within_a_key_version(tmp_path: Path) -> None:
    sink = provisioned(tmp_path)
    async def scenario() -> None:
        await sink.emit(event(outcome="REJECTED"))
        await sink.emit(event(outcome="ERROR"))

    asyncio.run(scenario())
    recent = sink.inspect_recent()
    assert len(recent) == 2
    assert recent[0].event_id != recent[1].event_id
    assert recent[0].correlation_tag == recent[1].correlation_tag
    assert recent[0].outcome == "ERROR"
    assert recent[1].outcome == "REJECTED"


def test_m6_audit_key_rotation_changes_correlation_tag_without_rewriting_history(
    tmp_path: Path,
) -> None:
    sink = provisioned(tmp_path)
    asyncio.run(sink.emit(event()))
    rotated = SqliteAuthenticationAuditSink(
        path=tmp_path / "m6-audit.sqlite",
        pseudonymization_key=OTHER_KEY,
        pseudonym_key_id="audit-key-v2",
    )
    asyncio.run(rotated.emit(event()))
    latest, older = rotated.inspect_recent()
    assert latest.pseudonym_key_id == "audit-key-v2"
    assert older.pseudonym_key_id == "audit-key-v1"
    assert latest.correlation_tag != older.correlation_tag
    assert latest.event_id != older.event_id


@pytest.mark.parametrize(
    ("method", "status"),
    [
        (EvidenceMethod.PASSWORD, "REJECTED"),
        (EvidenceMethod.API_KEY, "ERROR"),
        (EvidenceMethod.JWT, "AUTHENTICATED"),
    ],
)
def test_m6_audit_methods_and_outcomes_are_bounded(
    tmp_path: Path, method: EvidenceMethod, status: str
) -> None:
    sink = provisioned(tmp_path)
    asyncio.run(sink.emit(event(method=method, outcome=status)))
    assert sink.inspect_recent()[0].method == method.value
    assert sink.inspect_recent()[0].outcome == status


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf"), 3_600_001.0, True])
def test_m6_invalid_audit_duration_rejected_before_storage(tmp_path: Path, bad) -> None:
    sink = provisioned(tmp_path)
    with pytest.raises(AuditPersistenceUnavailable, match="invalid audit event"):
        asyncio.run(sink.emit(event(duration_ms=bad)))
    assert sink.inspect_recent() == ()


def test_m6_audit_store_capacity_refuses_new_record_without_deleting_old(
    tmp_path: Path,
) -> None:
    sink = provisioned(tmp_path, capacity=1)
    asyncio.run(sink.emit(event()))
    with pytest.raises(AuditPersistenceUnavailable, match="not confirmed"):
        asyncio.run(sink.emit(event()))
    assert len(sink.inspect_recent()) == 1


def test_m6_audit_store_missing_after_bootstrap_fails_without_recreation(
    tmp_path: Path,
) -> None:
    sink = provisioned(tmp_path)
    path = tmp_path / "m6-audit.sqlite"
    path.unlink()
    with pytest.raises(AuditPersistenceUnavailable, match="unavailable"):
        asyncio.run(sink.emit(event()))
    assert not path.exists()


def test_m6_audit_store_missing_never_provisions_implicitly(tmp_path: Path) -> None:
    path = tmp_path / "m6-audit.sqlite"
    with pytest.raises(AuditPersistenceUnavailable, match="missing"):
        SqliteAuthenticationAuditSink(
            path=path, pseudonymization_key=HMAC_KEY, pseudonym_key_id="v1"
        )
    assert not path.exists()


def test_m6_audit_store_refuses_provisioning_collision(tmp_path: Path) -> None:
    sink = provisioned(tmp_path)
    with pytest.raises(AuditPersistenceUnavailable, match="provisioning rejected"):
        provision_sqlite_audit_store(tmp_path / "m6-audit.sqlite")
    assert sink.inspect_recent() == ()


def test_m6_audit_store_corruption_is_not_repaired_or_truncated(tmp_path: Path) -> None:
    sink = provisioned(tmp_path)
    with sqlite3.connect(tmp_path / "m6-audit.sqlite") as connection:
        connection.execute("DROP TABLE audit_events")
    with pytest.raises(AuditPersistenceUnavailable):
        asyncio.run(sink.emit(event()))
    with pytest.raises(AuditPersistenceUnavailable):
        sink.inspect_recent()


def test_m6_audit_store_sqlite_symlink_is_rejected(tmp_path: Path) -> None:
    provisioned(tmp_path)
    alias = tmp_path / "alias.sqlite"
    try:
        alias.symlink_to(tmp_path / "m6-audit.sqlite")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(AuditPersistenceUnavailable, match="unapproved"):
        SqliteAuthenticationAuditSink(
            path=alias, pseudonymization_key=HMAC_KEY, pseudonym_key_id="v1"
        )


@pytest.mark.parametrize(
    "key,identifier,capacity",
    [
        (b"x", "v1", 10),
        (HMAC_KEY, "", 10),
        (HMAC_KEY, "v1", 0),
        (HMAC_KEY, "v1", 100_001),
    ],
)
def test_m6_audit_sink_rejects_invalid_host_key_and_capacity(
    tmp_path: Path, key: bytes, identifier: str, capacity: int
) -> None:
    provisioned(tmp_path)
    with pytest.raises(AuditPersistenceUnavailable):
        SqliteAuthenticationAuditSink(
            path=tmp_path / "m6-audit.sqlite",
            pseudonymization_key=key,
            pseudonym_key_id=identifier,
            capacity=capacity,
        )


def test_m6_audit_store_concurrent_appends_do_not_lose_records(tmp_path: Path) -> None:
    sink = provisioned(tmp_path)
    async def scenario() -> None:
        await asyncio.gather(
            *(sink.emit(event(correlation=CorrelationId(f"concurrent-{i}"))) for i in range(8))
        )

    asyncio.run(scenario())
    records = sink.inspect_recent()
    assert len(records) == 8
    assert len({record.event_id for record in records}) == 8
    assert len({record.correlation_tag for record in records}) == 8


class PositiveSyntheticVerifier:
    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.JWT

    async def verify(self, request: AuthenticationRequest, context: VerificationContext):
        return _issue_verified_outcome(
            context,
            subject=ScopedSubjectRef("synthetic-subject", "test-only", context.scope_ref),
            principal_type=PrincipalType.WORKLOAD,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


def _runtime(sink: SqliteAuthenticationAuditSink):
    snapshot = load_approved_configuration(
        {
            "schema_version": 1,
            "routes": [{
                "route_id": "audit-route",
                "scope": "tenant-a",
                "profile_id": "synthetic-jwt",
                "profile_version": "v1",
                "allowed_methods": ["jwt"],
            }],
            "timeout_seconds": 2.0,
            "audit_delivery": "best_effort",
            "secrets": [],
        },
        policy=SourcePolicy(frozenset({("test-host", "host")})),
        provenance=SourceProvenance("test-host", "host", "rev-1"),
        generation=ConfigurationGeneration(1),
    )
    return compose_authentication_engine(
        snapshot,
        authenticators=(PositiveSyntheticVerifier(),),
        final_rule=lambda _subject, _entry: True,
        event_sink=sink,
    )


def test_m6_local_audit_integrates_m2_without_changing_authn_decision(
    tmp_path: Path,
) -> None:
    sink = provisioned(tmp_path)
    runtime = _runtime(sink)
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
        CorrelationId("trace-identity-free"),
    )
    result = asyncio.run(
        runtime.engine.authenticate(
            request,
            entry=runtime.catalog.resolve_for_host_route("audit-route"),
        )
    )
    assert isinstance(result, Authenticated)
    records = sink.inspect_recent()
    assert len(records) == 1
    assert records[0].outcome == "AUTHENTICATED"
    assert records[0].method == "jwt"
    assert CANARY not in str(records)


def test_m6_best_effort_m2_still_authenticates_if_local_audit_is_unavailable(
    tmp_path: Path,
) -> None:
    sink = provisioned(tmp_path)
    runtime = _runtime(sink)
    (tmp_path / "m6-audit.sqlite").unlink()
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.JWT, CANARY.encode()),
        CorrelationId("trace-failure-no-durable-proof"),
    )
    result = asyncio.run(
        runtime.engine.authenticate(
            request,
            entry=runtime.catalog.resolve_for_host_route("audit-route"),
        )
    )
    # A positive result without a stored event proves that this sink DOES NOT
    # implement the separate required-audit contract.
    assert isinstance(result, Authenticated)


def test_m6_required_audit_is_still_rejected_even_with_sqlite_store(tmp_path: Path) -> None:
    provisioned(tmp_path)
    with pytest.raises(ConfigurationRejected):
        load_approved_configuration(
            {
                "schema_version": 1,
                "routes": [{
                    "route_id": "audit-route",
                    "scope": "tenant-a",
                    "profile_id": "j",
                    "profile_version": "v1",
                    "allowed_methods": ["jwt"],
                }],
                "timeout_seconds": 2.0,
                "audit_delivery": "required",
                "secrets": [],
            },
            policy=SourcePolicy(frozenset({("test-host", "host")})),
            provenance=SourceProvenance("test-host", "host", "rev-1"),
            generation=ConfigurationGeneration(1),
        )


def test_m6_audit_local_file_provisioned_with_private_permissions(tmp_path: Path) -> None:
    provisioned(tmp_path)
    if os.name == "posix":
        assert (tmp_path / "m6-audit.sqlite").stat().st_mode & 0o777 == 0o600
