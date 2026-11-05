"""Reference single-host SQLite generation-floor ledger, not a KMS/HSM.

Explicit provisioning, no implicit database creation on a normal read,
transactional compare-and-advance and FULL synchronous rollback journaling.

An attacker with write access to the ledger file, parent directory or host
can replace/restore the database. This adapter does NOT provide tamper-proof,
distributed or cryptographically authenticated anti-rollback. Secure storage
permissions, backups, deployment routing and filesystem guarantees belong to
the host. Do not use an untrusted filesystem such as an NFS share.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path

from pyauthkit.configuration.models import ConfigurationRejected

_SQLITE_MAX_INTEGER = 2**63 - 1
_DDL = """
CREATE TABLE generation_floor (
    record_id INTEGER PRIMARY KEY CHECK(record_id = 1),
    floor INTEGER NOT NULL CHECK(floor >= 1)
)
"""


class GenerationLedgerUnavailable(ConfigurationRejected):
    """A sanitized refusal: never infer a default generation on store failure."""


class GenerationLedgerConflict(ConfigurationRejected):
    """The candidate cannot be activated after another generation advanced."""


def _generation(value: int) -> None:
    if type(value) is not int or not 1 <= value <= _SQLITE_MAX_INTEGER:
        raise GenerationLedgerUnavailable("invalid generation ledger value")


def _path(value: Path) -> Path:
    if not isinstance(value, Path) or not value.is_absolute():
        raise GenerationLedgerUnavailable("ledger requires an absolute host-owned path")
    if value.is_symlink():
        raise GenerationLedgerUnavailable("symlink ledger path not approved")
    return value


def provision_sqlite_generation_ledger(path: Path, *, initial_floor: int) -> None:
    """Explicit one-time trusted host provisioning; never overwrites any file.

    Requires an existing, access-controlled parent directory. No automatic
    recovery is attempted. A newly created DB starts at the chosen floor,
    never at a guessed default.
    """
    path = _path(path)
    _generation(initial_floor)
    fd: int
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        raise GenerationLedgerUnavailable("ledger provisioning rejected") from None
    os.close(fd)
    try:
        # sqlite3.Connection.__exit__ commits but does NOT close the handle.
        # Explicit closing is essential on Windows: an open handle prevents
        # removal/replacement in fail-closed recovery and restart drills.
        with closing(sqlite3.connect(path, timeout=2.0)) as conn:
            with conn:
                conn.execute("PRAGMA journal_mode=DELETE")
                conn.execute("PRAGMA synchronous=EXTRA")
                conn.execute("PRAGMA trusted_schema=OFF")
                conn.execute(_DDL)
                conn.execute(
                    "INSERT INTO generation_floor (record_id, floor) VALUES (1, ?)",
                    (initial_floor,),
                )
    except sqlite3.Error:
        # A partly provisioned file is NOT a working floor; subsequent reads
        # must fail. Avoid silently deleting forensic evidence.
        raise GenerationLedgerUnavailable("ledger provisioning failed") from None


class SqliteGenerationFloorLedger:
    """Atomic process-to-process CAS on one trusted local SQLite database."""

    __slots__ = ("_location",)

    _location: Path

    def __init__(self, *, path: Path) -> None:
        path = _path(path)
        if not path.is_file():
            raise GenerationLedgerUnavailable("provisioned generation ledger missing")
        object.__setattr__(self, "_location", path)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("generation ledger location is immutable")

    def __repr__(self) -> str:
        return "SqliteGenerationFloorLedger(<host-owned, reference-only>)"

    def _open(self) -> sqlite3.Connection:
        if self._location.is_symlink() or not self._location.is_file():
            raise GenerationLedgerUnavailable("generation ledger unavailable")
        try:
            # mode=rw makes loss of the file fail closed instead of creating G1.
            connection = sqlite3.connect(
                self._location.as_uri() + "?mode=rw",
                uri=True,
                isolation_level=None,
                timeout=2.0,
            )
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("PRAGMA synchronous=EXTRA")
            journal = connection.execute("PRAGMA journal_mode").fetchone()
            if journal is None or journal[0] != "delete":
                connection.close()
                raise GenerationLedgerUnavailable("unapproved generation journal mode")
            return connection
        except sqlite3.Error:
            raise GenerationLedgerUnavailable("generation ledger unavailable") from None

    @staticmethod
    def _stored_floor(connection: sqlite3.Connection) -> int:
        rows = connection.execute("SELECT record_id, floor FROM generation_floor").fetchall()
        if (
            len(rows) != 1
            or type(rows[0][0]) is not int
            or rows[0][0] != 1
            or type(rows[0][1]) is not int
        ):
            raise GenerationLedgerUnavailable("invalid generation ledger state")
        floor = rows[0][1]
        _generation(floor)
        return floor

    def read_floor(self) -> int:
        connection = self._open()
        try:
            connection.execute("BEGIN")
            floor = self._stored_floor(connection)
            connection.commit()
            return floor
        except sqlite3.Error:
            raise GenerationLedgerUnavailable("generation ledger read failed") from None
        finally:
            connection.close()

    def compare_and_advance(self, *, expected_floor: int, generation: int) -> None:
        _generation(expected_floor)
        _generation(generation)
        if generation < expected_floor:
            raise GenerationLedgerConflict("stale configuration generation")
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            actual = self._stored_floor(connection)
            if actual != expected_floor:
                raise GenerationLedgerConflict("generation changed before activation")
            cursor = connection.execute(
                "UPDATE generation_floor SET floor = ? WHERE record_id = 1 AND floor = ?",
                (generation, expected_floor),
            )
            if cursor.rowcount != 1:
                raise GenerationLedgerConflict("generation update conflict")
            connection.commit()
        except (GenerationLedgerUnavailable, GenerationLedgerConflict):
            connection.rollback()
            raise
        except sqlite3.Error:
            connection.rollback()
            raise GenerationLedgerUnavailable("generation update failed") from None
        finally:
            connection.close()
