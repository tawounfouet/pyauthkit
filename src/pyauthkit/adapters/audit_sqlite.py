"""Optional local SQLite audit append-only-by-API reference for M6.

[ARCH: Ports & Adapters] [SECURITY: Minimized, pseudonymized events]
The host explicitly provisions a local protected database and provides a
32-byte HMAC key for correlation pseudonymization. Audit material is committed
before emit() returns; M2 still swallows sink failures in best-effort mode.

NOT a required-audit implementation, security boundary against local file
tampering, power-loss guarantee on arbitrary filesystems, or distributed log.
A coroutine cancelled during asyncio.to_thread cannot kill an in-flight
SQLite transaction. No automatic clearing, schema migration or rotation.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import math
import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Never
from uuid import uuid4

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.ports.events import AuthenticationEvent

_ALLOWED_STATUS = frozenset({"AUTHENTICATED", "REJECTED", "ERROR"})
_KEY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_MAX_DURATION_MS = 3_600_000.0
_MAX_RECORDS = 100_000

_DDL = """
CREATE TABLE audit_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE CHECK(length(event_id) = 32),
    created_at_utc TEXT NOT NULL,
    correlation_tag TEXT NOT NULL CHECK(length(correlation_tag) = 64),
    pseudonym_key_id TEXT NOT NULL,
    method TEXT NOT NULL CHECK(method IN ('password', 'api_key', 'jwt')),
    outcome TEXT NOT NULL CHECK(outcome IN ('AUTHENTICATED', 'REJECTED', 'ERROR')),
    duration_ms REAL NOT NULL CHECK(duration_ms >= 0 AND duration_ms <= 3600000)
)
"""


class AuditPersistenceUnavailable(RuntimeError):
    """Sanitized audit-store failure; not evidence of a committed receipt."""


def _store_path(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or path.is_symlink():
        raise AuditPersistenceUnavailable("unapproved audit store path")
    return path


def provision_sqlite_audit_store(path: Path) -> None:
    """One-time host provisioning, refuses any existing file or symlink."""
    path = _store_path(path)
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise AuditPersistenceUnavailable("unapproved audit store directory")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        raise AuditPersistenceUnavailable("audit store provisioning rejected") from None
    os.close(fd)
    try:
        # sqlite3's connection context manager commits but does not close.
        with closing(sqlite3.connect(path, timeout=2.0)) as conn:
            with conn:
                conn.execute("PRAGMA journal_mode=DELETE")
                conn.execute("PRAGMA synchronous=EXTRA")
                conn.execute("PRAGMA trusted_schema=OFF")
                conn.execute(_DDL)
    except sqlite3.Error:
        # Do not erase a partially provisioned file: operator recovery only.
        raise AuditPersistenceUnavailable("audit store provisioning failed") from None


@dataclass(frozen=True, slots=True, repr=False)
class StoredAuditSummary:
    """For privileged diagnostics only, with no original correlation value."""

    sequence: int
    event_id: str
    correlation_tag: str
    pseudonym_key_id: str
    method: str
    outcome: str
    duration_ms: float

    def __repr__(self) -> str:
        return "StoredAuditSummary(<pseudonymized, no credential>)"


class SqliteAuthenticationAuditSink:
    """Uncached SQLite event sink; the file must have been provisioned.

    The configured HMAC key is supplied from a trusted host secret source.
    Its lifecycle, rotation and exclusion from logs/core dumps are host duties.
    """

    __slots__ = ("_location", "_hmac_key", "_key_id", "_capacity")

    _location: Path
    _hmac_key: bytes
    _key_id: str
    _capacity: int

    def __init__(
        self,
        *,
        path: Path,
        pseudonymization_key: bytes,
        pseudonym_key_id: str,
        capacity: int = _MAX_RECORDS,
    ) -> None:
        path = _store_path(path)
        if not path.is_file():
            raise AuditPersistenceUnavailable("audit store missing")
        if type(pseudonymization_key) is not bytes or len(pseudonymization_key) != 32:
            raise AuditPersistenceUnavailable("invalid audit pseudonymization key")
        if type(pseudonym_key_id) is not str or _KEY_ID.fullmatch(pseudonym_key_id) is None:
            raise AuditPersistenceUnavailable("invalid audit pseudonymization key id")
        if type(capacity) is not int or not 1 <= capacity <= _MAX_RECORDS:
            raise AuditPersistenceUnavailable("invalid audit store capacity")
        object.__setattr__(self, "_location", path)
        object.__setattr__(self, "_hmac_key", pseudonymization_key)
        object.__setattr__(self, "_key_id", pseudonym_key_id)
        object.__setattr__(self, "_capacity", capacity)

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("audit sink composition is immutable")

    def __repr__(self) -> str:
        return "SqliteAuthenticationAuditSink(<bounded, best-effort, local>)"

    def _open(self) -> sqlite3.Connection:
        if self._location.is_symlink() or not self._location.is_file():
            raise AuditPersistenceUnavailable("audit store unavailable")
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                self._location.as_uri() + "?mode=rw",
                uri=True,
                isolation_level=None,
                timeout=2.0,
            )
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("PRAGMA synchronous=EXTRA")
            mode = connection.execute("PRAGMA journal_mode").fetchone()
            if mode is None or mode[0] != "delete":
                raise AuditPersistenceUnavailable("unapproved audit store journal mode")
            return connection
        except (sqlite3.Error, AuditPersistenceUnavailable):
            if connection is not None:
                connection.close()
            raise AuditPersistenceUnavailable("audit store unavailable") from None

    @staticmethod
    def _validate_event(event: AuthenticationEvent) -> None:
        if (
            not isinstance(event, AuthenticationEvent)
            or not isinstance(event.correlation_id, CorrelationId)
            or not isinstance(event.method, EvidenceMethod)
            or event.result_status not in _ALLOWED_STATUS
            or type(event.duration_ms) not in (int, float)
            or not math.isfinite(event.duration_ms)
            or not 0 <= event.duration_ms <= _MAX_DURATION_MS
        ):
            raise AuditPersistenceUnavailable("invalid audit event")

    def _append(self, event: AuthenticationEvent) -> None:
        """Single transaction; a full store is never silently truncated."""
        tag = hmac.new(
            self._hmac_key,
            b"pyauthkit-audit-correlation-v1\x00" + event.correlation_id.value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        event_id = uuid4().hex
        created_at = datetime.now(UTC).isoformat(timespec="microseconds")
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()
            if count is None or type(count[0]) is not int or count[0] >= self._capacity:
                raise AuditPersistenceUnavailable("audit store capacity exceeded")
            connection.execute(
                """
                INSERT INTO audit_events (
                    event_id, created_at_utc, correlation_tag, pseudonym_key_id,
                    method, outcome, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    created_at,
                    tag,
                    self._key_id,
                    event.method.value,
                    event.result_status,
                    event.duration_ms,
                ),
            )
            connection.commit()
        except (sqlite3.Error, AuditPersistenceUnavailable):
            connection.rollback()
            raise AuditPersistenceUnavailable("audit record not confirmed") from None
        finally:
            connection.close()

    async def emit(self, event: AuthenticationEvent) -> None:
        """Commit before normal return; caller owns best-effort vs required.

        In the existing M2 engine, failures are swallowed by design; this
        sink does NOT change the resulting authentication decision.
        """
        self._validate_event(event)
        await asyncio.to_thread(self._append, event)

    def inspect_recent(self, *, limit: int = 100) -> tuple[StoredAuditSummary, ...]:
        """Privileged, bounded metadata read for operator proof and tests."""
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise AuditPersistenceUnavailable("invalid audit inspection limit")
        connection = self._open()
        try:
            rows = connection.execute(
                """
                SELECT sequence, event_id, correlation_tag, pseudonym_key_id,
                    method, outcome, duration_ms
                FROM audit_events ORDER BY sequence DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        except sqlite3.Error:
            raise AuditPersistenceUnavailable("audit inspection unavailable") from None
        finally:
            connection.close()
        return tuple(StoredAuditSummary(*row) for row in rows)
