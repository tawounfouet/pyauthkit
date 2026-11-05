"""Reference PostgreSQL credential projection, read-only at authentication.

The schema and seed helper are only for qualification. Production schema
ownership, migrations, identity lifecycle and transaction boundaries belong
to the credential owner, not to PyAuthKit.
"""

import asyncpg

from pyauthkit.domain.identity import ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.password.records import (
    PasswordRecordFound,
    PasswordRecordLookup,
    PasswordRecordMissing,
    PasswordRecordStatus,
    PasswordRecordUnavailable,
    PasswordVerifierRecord,
)

QUALIFICATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS m3q_credentials (
    scope_id VARCHAR(128) NOT NULL,
    identifier_kind VARCHAR(32) NOT NULL,
    identifier_value VARCHAR(256) NOT NULL,
    subject_id VARCHAR(256) NOT NULL,
    issuer_id VARCHAR(128) NOT NULL,
    encoded_phc VARCHAR(512) NOT NULL,
    status VARCHAR(16) NOT NULL CHECK (
        status IN ('active','disabled','suspended','revoked','expired')
    ),
    version BIGINT NOT NULL CHECK (version >= 0),
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (scope_id, identifier_kind, identifier_value),
    UNIQUE (scope_id, subject_id, issuer_id)
);
"""
_LOOKUP = """
SELECT scope_id, subject_id, issuer_id, encoded_phc, status, version, expires_at
FROM m3q_credentials
WHERE scope_id = $1 AND identifier_kind = $2 AND identifier_value = $3
"""
_CURRENT = """
SELECT EXISTS (
    SELECT 1 FROM m3q_credentials
    WHERE scope_id = $1 AND subject_id = $2 AND issuer_id = $3
      AND encoded_phc = $4 AND version = $5 AND status = 'active'
      AND (expires_at IS NULL OR expires_at > clock_timestamp())
)
"""


class PostgresPasswordCredentialResolver:
    """PostgreSQL-backed resolver with source-side scope binding."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def resolve(
        self,
        *,
        scope_ref: TrustedScopeRef,
        identifier_kind: str,
        identifier_value: str,
    ) -> PasswordRecordLookup:
        if not isinstance(scope_ref, TrustedScopeRef):
            return PasswordRecordUnavailable()
        # Source-side WHERE scope_id = $1 prevents global username lookup.
        row = await self._pool.fetchrow(
            _LOOKUP, scope_ref.value, identifier_kind, identifier_value
        )
        if row is None:
            return PasswordRecordMissing()
        if row["scope_id"] != scope_ref.value:
            return PasswordRecordUnavailable()
        try:
            return PasswordRecordFound(
                PasswordVerifierRecord(
                    scope_ref=scope_ref,
                    subject_ref=ScopedSubjectRef(
                        row["subject_id"], row["issuer_id"], scope_ref
                    ),
                    encoded_hash=row["encoded_phc"],
                    status=PasswordRecordStatus(row["status"]),
                    version=row["version"],
                    expires_at=(
                        ObservedAt(row["expires_at"])
                        if row["expires_at"] is not None
                        else None
                    ),
                )
            )
        except (ValueError, TypeError):
            return PasswordRecordUnavailable()

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        # Re-read authoritative store after the real KDF, no cached snapshot.
        # It does not eliminate the time-of-check/time-of-use window after SQL.
        return bool(
            await self._pool.fetchval(
                _CURRENT,
                record.scope_ref.value,
                record.subject_ref.subject_id,
                record.subject_ref.issuer_ref,
                record.encoded_hash,
                record.version,
            )
        )


async def prepare_qualification_schema(pool: asyncpg.Pool) -> None:
    """Run only inside an isolated qualification database."""
    await pool.execute(QUALIFICATION_SCHEMA)
    await pool.execute("TRUNCATE TABLE m3q_credentials")


async def insert_fixture_record(
    pool: asyncpg.Pool,
    *,
    scope_id: str,
    login: str,
    subject_id: str,
    encoded_phc: str,
) -> None:
    """Seed synthetic test data only, never exposed as a public API."""
    await pool.execute(
        """
        INSERT INTO m3q_credentials
            (scope_id, identifier_kind, identifier_value, subject_id,
             issuer_id, encoded_phc, status, version)
        VALUES ($1, 'username', $2, $3, 'fixture-issuer', $4, 'active', 1)
        """,
        scope_id,
        login,
        subject_id,
        encoded_phc,
    )
