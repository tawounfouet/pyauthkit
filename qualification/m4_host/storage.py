"""PostgreSQL API-key owner projection, isolated for M4 qualification.

SQL queries filter by host-supplied scope *at the source*. This fixture owns
test schema and CAS updates, not PyAuthKit's public credential lifecycle.
"""

import asyncpg

from pyauthkit.domain.api_key import (
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordLookup,
    ApiKeyRecordStatus,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt

SCHEMA = """
CREATE TABLE IF NOT EXISTS m4q_credentials (
    scope_id VARCHAR(128) NOT NULL,
    key_id VARCHAR(128) NOT NULL,
    subject_id VARCHAR(256) NOT NULL,
    issuer_id VARCHAR(128) NOT NULL,
    principal_type VARCHAR(24) NOT NULL,
    verifier_digest BYTEA NOT NULL CHECK (octet_length(verifier_digest) = 32),
    verifier_algorithm VARCHAR(32) NOT NULL,
    protection_key_ref VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL CHECK (
        status IN ('active','disabled','suspended','revoked','expired')
    ),
    version BIGINT NOT NULL CHECK (version >= 0),
    not_before TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (scope_id, key_id)
);
"""
LOOKUP = """
SELECT scope_id, key_id, subject_id, issuer_id, principal_type,
    verifier_digest, verifier_algorithm, protection_key_ref,
    status, version, not_before, expires_at
FROM m4q_credentials
WHERE scope_id = $1 AND key_id = $2
"""
CURRENT = """
SELECT EXISTS (
    SELECT 1 FROM m4q_credentials
    WHERE scope_id = $1 AND key_id = $2
      AND subject_id = $3 AND issuer_id = $4 AND principal_type = $5
      AND verifier_digest = $6 AND verifier_algorithm = $7
      AND protection_key_ref = $8 AND version = $9
      AND status = 'active'
      AND (not_before IS NULL OR not_before <= clock_timestamp())
      AND expires_at > clock_timestamp()
)
"""
CAS_REVOKE = """
UPDATE m4q_credentials
SET status = 'revoked', version = version + 1
WHERE scope_id = $1 AND key_id = $2 AND version = $3 AND status = 'active'
RETURNING version
"""
CAS_ROTATE = """
UPDATE m4q_credentials
SET verifier_digest = $4, protection_key_ref = $5, version = version + 1
WHERE scope_id = $1 AND key_id = $2 AND version = $3 AND status = 'active'
RETURNING version
"""


class PostgresApiKeyCredentialResolver:
    """Source-scoped authoritative reads, no local positive cache or fallback."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def resolve(self, *, scope_ref: TrustedScopeRef, key_id: str) -> ApiKeyRecordLookup:
        row = await self._pool.fetchrow(LOOKUP, scope_ref.value, key_id)
        if row is None:
            return ApiKeyMissing()
        if row["scope_id"] != scope_ref.value or row["key_id"] != key_id:
            raise RuntimeError("inconsistent scoped owner response")
        try:
            record = ApiKeyVerifierRecord(
                scope_ref=scope_ref,
                subject_ref=ScopedSubjectRef(row["subject_id"], row["issuer_id"], scope_ref),
                principal_type=PrincipalType(row["principal_type"]),
                key_id=row["key_id"],
                verifier_digest=bytes(row["verifier_digest"]),
                verifier_algorithm=row["verifier_algorithm"],
                protection_key_ref=row["protection_key_ref"],
                status=ApiKeyRecordStatus(row["status"]),
                version=row["version"],
                not_before=(
                    ObservedAt(row["not_before"]) if row["not_before"] is not None else None
                ),
                expires_at=ObservedAt(row["expires_at"]),
            )
        except (ValueError, TypeError) as exc:
            raise RuntimeError("invalid credential owner projection") from exc
        return ApiKeyFound(record)

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        """Fresh authoritative read after HMAC, but not a linearizable AuthN grant."""
        return bool(
            await self._pool.fetchval(
                CURRENT,
                record.scope_ref.value,
                record.key_id,
                record.subject_ref.subject_id,
                record.subject_ref.issuer_ref,
                record.principal_type.value,
                record.verifier_digest,
                record.verifier_algorithm,
                record.protection_key_ref,
                record.version,
            )
        )


async def prepare_fixture_schema(pool: asyncpg.Pool) -> None:
    """Only call against the isolated CI database."""
    await pool.execute(SCHEMA)
    await pool.execute("TRUNCATE TABLE m4q_credentials")


async def seed_fixture(
    pool: asyncpg.Pool,
    *,
    scope: str,
    selector: str,
    subject: str,
    digest: bytes,
    expires_at: object,
) -> None:
    """Synthetic records only, never a public creation endpoint."""
    await pool.execute(
        """
        INSERT INTO m4q_credentials
        (scope_id, key_id, subject_id, issuer_id, principal_type, verifier_digest,
         verifier_algorithm, protection_key_ref, status, version, expires_at)
        VALUES ($1, $2, $3, 'fixture-issuer', 'service', $4, 'hmac-sha256',
                'key-v1', 'active', 1, $5)
        """,
        scope,
        selector,
        subject,
        digest,
        expires_at,
    )


async def revoke_cas(
    pool: asyncpg.Pool, *, scope: str, selector: str, expected_version: int
) -> bool:
    """Atomic source-level version check; returns false on racing updates."""
    return (
        await pool.fetchval(CAS_REVOKE, scope, selector, expected_version)
    ) is not None


async def rotate_cas(
    pool: asyncpg.Pool,
    *,
    scope: str,
    selector: str,
    expected_version: int,
    digest: bytes,
    protection_ref: str,
) -> bool:
    """Test-only verifier rotation with version CAS, no bearer reissue API."""
    return (
        await pool.fetchval(
            CAS_ROTATE, scope, selector, expected_version, digest, protection_ref
        )
    ) is not None
