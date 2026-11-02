"""Scoped password verifier read model, deliberately not a User entity.

[DDD: read model] [SECURITY: no secret in repr, no implicit global lookup]
The hash is sensitive offline-attack material even though it is not plaintext.
"""

from enum import StrEnum
from typing import Never

from pyauthkit.domain.identity import ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt


class PasswordRecordStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PasswordVerifierRecord:
    """Immutable host-owned projection, not an authority to authenticate.

    Avoid dataclasses so generic asdict() cannot inadvertently export the hash.
    The caller must not expose encoded_hash in exceptions, metrics or logs.
    """

    __slots__ = ("scope_ref", "subject_ref", "encoded_hash", "status", "version", "expires_at")

    scope_ref: TrustedScopeRef
    subject_ref: ScopedSubjectRef
    encoded_hash: str
    status: PasswordRecordStatus
    version: int
    expires_at: ObservedAt | None

    def __init__(
        self,
        *,
        scope_ref: TrustedScopeRef,
        subject_ref: ScopedSubjectRef,
        encoded_hash: str,
        status: PasswordRecordStatus,
        version: int,
        expires_at: ObservedAt | None = None,
    ) -> None:
        if not isinstance(scope_ref, TrustedScopeRef):
            raise ValueError("invalid password record scope")
        if not isinstance(subject_ref, ScopedSubjectRef) or subject_ref.scope_ref != scope_ref:
            raise ValueError("password record subject scope mismatch")
        if not isinstance(encoded_hash, str) or not 1 <= len(encoded_hash) <= 512:
            raise ValueError("invalid password verifier material")
        if not encoded_hash.isascii() or any(ord(ch) <= 32 or ord(ch) == 127 for ch in encoded_hash):
            raise ValueError("invalid password verifier encoding")
        if not isinstance(status, PasswordRecordStatus):
            raise ValueError("invalid password record status")
        if type(version) is not int or version < 0:
            raise ValueError("invalid password record version")
        if expires_at is not None and not isinstance(expires_at, ObservedAt):
            raise ValueError("invalid password expiration")
        object.__setattr__(self, "scope_ref", scope_ref)
        object.__setattr__(self, "subject_ref", subject_ref)
        object.__setattr__(self, "encoded_hash", encoded_hash)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "expires_at", expires_at)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("password verifier record cannot be mutated")

    def __deepcopy__(self, _memo: dict[int, object]) -> Never:
        raise TypeError("sensitive credential projection cannot be copied generically")

    def __repr__(self) -> str:
        return "PasswordVerifierRecord(<redacted>)"


class PasswordRecordFound:
    """Resolver found one scoped record, not a verified credential."""

    __slots__ = ("record",)

    record: PasswordVerifierRecord

    def __init__(self, record: PasswordVerifierRecord) -> None:
        if not isinstance(record, PasswordVerifierRecord):
            raise ValueError("invalid password lookup record")
        object.__setattr__(self, "record", record)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("lookup result cannot be mutated")

    def __repr__(self) -> str:
        return "PasswordRecordFound(<redacted>)"


class PasswordRecordMissing:
    __slots__ = ()

    def __repr__(self) -> str:
        return "PasswordRecordMissing()"


class PasswordRecordAmbiguous:
    __slots__ = ()

    def __repr__(self) -> str:
        return "PasswordRecordAmbiguous()"


class PasswordRecordUnavailable:
    __slots__ = ()

    def __repr__(self) -> str:
        return "PasswordRecordUnavailable()"


type PasswordRecordLookup = (
    PasswordRecordFound | PasswordRecordMissing | PasswordRecordAmbiguous | PasswordRecordUnavailable
)


def record_is_admissible(record: PasswordVerifierRecord, *, at: ObservedAt) -> bool:
    """Status and expiry gate; no cryptographic proof is implied."""
    return (
        record.status is PasswordRecordStatus.ACTIVE
        and (record.expires_at is None or at.value < record.expires_at.value)
    )


def is_scoped_human_record(record: PasswordVerifierRecord, scope: TrustedScopeRef) -> bool:
    """Defense-in-depth check against a broken or cross-tenant adapter."""
    return (
        isinstance(record, PasswordVerifierRecord)
        and record.scope_ref == scope
        and record.subject_ref.scope_ref == scope
        and record.subject_ref.issuer_ref != ""
    )
