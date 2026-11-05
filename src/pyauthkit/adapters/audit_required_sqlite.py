"""Experimental local SQLite commit-before-return audit reference.

Separate DB and commit API from best-effort audit_sqlite.py. The host owns
the key, file, permissions, resource limits, generation and deployment route.
A malicious local file writer can replace records; no durable distributed
receipt, exactly-once transport, power-loss guarantee or HSM attestation.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Never
from uuid import uuid4

from pyauthkit.ports.required_audit import (
    AuditAttemptId,
    AuditCommitReceipt,
    AuditDecisionRecord,
)

_SCHEMA = """
CREATE TABLE required_audit_attempts (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT NOT NULL UNIQUE CHECK(length(attempt_id) = 32),
    record_id TEXT NOT NULL UNIQUE CHECK(length(record_id) = 32),
    created_at_utc TEXT NOT NULL,
    key_id TEXT NOT NULL,
    method TEXT NOT NULL CHECK(method IN ('password', 'api_key', 'jwt')),
    outcome TEXT NOT NULL CHECK(outcome IN ('AUTHENTICATED', 'REJECTED', 'ERROR')),
    duration_ms REAL NOT NULL CHECK(duration_ms >= 0 AND duration_ms <= 3600000),
    decision_tag TEXT NOT NULL CHECK(length(decision_tag) = 64)
)
"""


class RequiredAuditCommitUnavailable(RuntimeError):
    """No validated local commit acknowledgment; may not return Authenticated."""


class RequiredAuditAttemptConflict(RequiredAuditCommitUnavailable):
    """An attempt ID is single-use, even after process restart."""


def _checked_path(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or path.is_symlink():
        raise RequiredAuditCommitUnavailable("unapproved required audit location")
    return path


def provision_sqlite_required_audit(path: Path) -> None:
    """Host-controlled, one-time setup; no implicit repair or create-on-read."""
    path = _checked_path(path)
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise RequiredAuditCommitUnavailable("unapproved required audit directory")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        raise RequiredAuditCommitUnavailable("required audit provisioning denied") from None
    os.close(fd)
    try:
        with closing(sqlite3.connect(path, timeout=2.0)) as connection:
            with connection:
                connection.execute("PRAGMA journal_mode=DELETE")
                connection.execute("PRAGMA synchronous=EXTRA")
                connection.execute("PRAGMA trusted_schema=OFF")
                connection.execute(_SCHEMA)
    except sqlite3.Error:
        # Preserve the damaged file for privileged investigation.
        raise RequiredAuditCommitUnavailable("required audit provisioning failed") from None


def _framed(values: tuple[str, ...]) -> bytes:
    parts: list[bytes] = []
    for value in values:
        raw = value.encode("utf-8")
        parts.append(len(raw).to_bytes(4, "big") + raw)
    return b"pyauthkit-required-audit-v1\x00" + b"".join(parts)


class SqliteRequiredAuditCommitter:
    """Single-host append-only-by-API CAS on a random attempt identifier."""

    __slots__ = ("_path", "_key", "_key_id", "_capacity")

    _path: Path
    _key: bytes
    _key_id: str
    _capacity: int

    def __init__(
        self, *, path: Path, signing_key: bytes, key_id: str, capacity: int = 100_000
    ) -> None:
        path = _checked_path(path)
        if not path.is_file():
            raise RequiredAuditCommitUnavailable("required audit store missing")
        if type(signing_key) is not bytes or len(signing_key) != 32:
            raise RequiredAuditCommitUnavailable("invalid required audit key")
        if (
            type(key_id) is not str
            or not 1 <= len(key_id) <= 64
            or any(not (c.isascii() and (c.isalnum() or c in "._:-")) for c in key_id)
            or type(capacity) is not int
            or not 1 <= capacity <= 100_000
        ):
            raise RequiredAuditCommitUnavailable("invalid required audit policy")
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_key", signing_key)
        object.__setattr__(self, "_key_id", key_id)
        object.__setattr__(self, "_capacity", capacity)

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("required audit committer is immutable")

    def __repr__(self) -> str:
        return "SqliteRequiredAuditCommitter(<experimental, local-only>)"

    def _open(self) -> sqlite3.Connection:
        if self._path.is_symlink() or not self._path.is_file():
            raise RequiredAuditCommitUnavailable("required audit store unavailable")
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                self._path.as_uri() + "?mode=rw",
                uri=True,
                isolation_level=None,
                timeout=2.0,
            )
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("PRAGMA synchronous=EXTRA")
            mode = connection.execute("PRAGMA journal_mode").fetchone()
            if mode is None or mode[0] != "delete":
                raise RequiredAuditCommitUnavailable("required audit journal unavailable")
            return connection
        except (sqlite3.Error, RequiredAuditCommitUnavailable):
            if connection is not None:
                connection.close()
            raise RequiredAuditCommitUnavailable("required audit store unavailable") from None

    def _tag(self, record: AuditDecisionRecord) -> str:
        e = record.event
        subject = record.subject
        return hmac.new(
            self._key,
            _framed(
                (
                    record.attempt_id.value,
                    e.correlation_id.value,
                    e.method.value,
                    e.result_status,
                    record.profile.scope_ref.value,
                    record.profile.profile_id,
                    record.profile.version,
                    "" if subject is None else subject.subject_id,
                    "" if subject is None else subject.issuer_ref,
                    "" if record.principal_type is None else record.principal_type.value,
                )
            ),
            hashlib.sha256,
        ).hexdigest()

    def _commit_sync(self, record: AuditDecisionRecord) -> AuditCommitReceipt:
        tag = self._tag(record)
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            exists = connection.execute(
                "SELECT 1 FROM required_audit_attempts WHERE attempt_id = ?",
                (record.attempt_id.value,),
            ).fetchone()
            if exists is not None:
                raise RequiredAuditAttemptConflict("audit attempt already consumed")
            count = connection.execute(
                "SELECT COUNT(*) FROM required_audit_attempts"
            ).fetchone()
            if count is None or type(count[0]) is not int or count[0] >= self._capacity:
                raise RequiredAuditCommitUnavailable("required audit store full")
            record_id = uuid4().hex
            created = datetime.now(UTC).isoformat(timespec="microseconds")
            cursor = connection.execute(
                """
                INSERT INTO required_audit_attempts (
                    attempt_id, record_id, created_at_utc, key_id,
                    method, outcome, duration_ms, decision_tag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.attempt_id.value,
                    record_id,
                    created,
                    self._key_id,
                    record.event.method.value,
                    record.event.result_status,
                    record.event.duration_ms,
                    tag,
                ),
            )
            if type(cursor.lastrowid) is not int or cursor.lastrowid < 1:
                raise RequiredAuditCommitUnavailable("missing audit commit sequence")
            receipt = AuditCommitReceipt(
                attempt_id=record.attempt_id,
                record_id=record_id,
                sequence=cursor.lastrowid,
                result_status=record.event.result_status,
                decision_tag=tag,
            )
            connection.commit()
            return receipt
        except RequiredAuditAttemptConflict:
            connection.rollback()
            raise
        except (sqlite3.Error, RequiredAuditCommitUnavailable):
            connection.rollback()
            raise RequiredAuditCommitUnavailable("required audit commit failed") from None
        finally:
            connection.close()

    async def commit(self, record: AuditDecisionRecord) -> AuditCommitReceipt:
        if not isinstance(record, AuditDecisionRecord):
            raise RequiredAuditCommitUnavailable("invalid audit decision")
        # A cancelled coroutine cannot stop a running worker. The caller
        # must not return a positive response after cancellation, and
        # retries with the same attempt ID are rejected if that write landed.
        return await asyncio.to_thread(self._commit_sync, record)

    def inspect_receipt(self, attempt_id: AuditAttemptId) -> AuditCommitReceipt | None:
        """Privileged test/operator read. No replay authorization from a receipt."""
        if not isinstance(attempt_id, AuditAttemptId):
            raise RequiredAuditCommitUnavailable("invalid audit inspection")
        connection = self._open()
        try:
            rows = connection.execute(
                """
                SELECT record_id, sequence, outcome, decision_tag
                FROM required_audit_attempts WHERE attempt_id = ?
                """,
                (attempt_id.value,),
            ).fetchall()
            if not rows:
                return None
            if len(rows) != 1:
                raise RequiredAuditCommitUnavailable("invalid audit record state")
            return AuditCommitReceipt(attempt_id, rows[0][0], rows[0][1], rows[0][2], rows[0][3])
        except (sqlite3.Error, ValueError):
            raise RequiredAuditCommitUnavailable("audit inspection unavailable") from None
        finally:
            connection.close()
