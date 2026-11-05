"""M4 API-key lookup domain contracts (PR-07A), not an authenticator.

[DDD: Immutable Read Model] [SECURITY: Scope Binding / Redaction]
A selector, record or lookup result never proves possession of a bearer key.
No public success, cryptographic verification or credential lifecycle writes live here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Never

from .identity import PrincipalType, ScopedSubjectRef
from .scope import TrustedScopeRef
from .temporal import ObservedAt

_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _bounded_ref(value: str, *, name: str) -> str:
    if not isinstance(value, str) or not _REF_PATTERN.fullmatch(value):
        raise ValueError(f"invalid {name}")
    return value


@dataclass(frozen=True, slots=True, repr=False)
class ApiKeyCredentialRef:
    """Non-secret scoped lookup selector. It is NOT proof of possession."""

    value: str

    def __post_init__(self) -> None:
        _bounded_ref(self.value, name="API key selector")

    def __repr__(self) -> str:
        return "ApiKeyCredentialRef(<redacted, unverified>)"


class ApiKeyRecordStatus(StrEnum):
    """Credential-owner state projected into M4; transitions are not owned here."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ApiKeyVerifierRecord:
    """Immutable read projection from a credential owner, not a key or permission.

    This is intentionally not a dataclass: generic asdict/deepcopy/pickle should
    not accidentally extract or duplicate sensitive verifier material. Trusted
    adapters must still protect every field exposed explicitly to Python code.
    """

    __slots__ = (
        "scope_ref",
        "subject_ref",
        "principal_type",
        "key_id",
        "verifier_digest",
        "verifier_algorithm",
        "protection_key_ref",
        "status",
        "version",
        "not_before",
        "expires_at",
    )

    scope_ref: TrustedScopeRef
    subject_ref: ScopedSubjectRef
    principal_type: PrincipalType
    key_id: str
    verifier_digest: bytes
    verifier_algorithm: str
    protection_key_ref: str
    status: ApiKeyRecordStatus
    version: int
    not_before: ObservedAt | None
    expires_at: ObservedAt | None

    def __init__(
        self,
        *,
        scope_ref: TrustedScopeRef,
        subject_ref: ScopedSubjectRef,
        principal_type: PrincipalType,
        key_id: str,
        verifier_digest: bytes,
        verifier_algorithm: str,
        protection_key_ref: str,
        status: ApiKeyRecordStatus,
        version: int,
        not_before: ObservedAt | None = None,
        expires_at: ObservedAt | None = None,
    ) -> None:
        if not isinstance(scope_ref, TrustedScopeRef):
            raise ValueError("invalid credential scope")
        if not isinstance(subject_ref, ScopedSubjectRef) or subject_ref.scope_ref != scope_ref:
            raise ValueError("credential subject/scope mismatch")
        if not isinstance(principal_type, PrincipalType) or principal_type not in (
            PrincipalType.SERVICE,
            PrincipalType.APPLICATION,
            PrincipalType.WORKLOAD,
        ):
            raise ValueError("unsupported API key principal type")
        _bounded_ref(key_id, name="API key selector")
        _bounded_ref(verifier_algorithm, name="verifier algorithm")
        _bounded_ref(protection_key_ref, name="protection key reference")
        if type(verifier_digest) is not bytes or not 16 <= len(verifier_digest) <= 128:
            raise ValueError("invalid verifier digest")
        if verifier_algorithm == "hmac-sha256" and len(verifier_digest) != 32:
            raise ValueError("invalid HMAC-SHA-256 digest length")
        if not isinstance(status, ApiKeyRecordStatus):
            raise ValueError("invalid API key status")
        if type(version) is not int or not 0 <= version < 2**63:
            raise ValueError("invalid credential version")
        if not_before is not None and not isinstance(not_before, ObservedAt):
            raise ValueError("invalid not-before instant")
        if expires_at is not None and not isinstance(expires_at, ObservedAt):
            raise ValueError("invalid expiration instant")
        if not_before is not None and expires_at is not None:
            if not_before.value > expires_at.value:
                raise ValueError("invalid credential validity window")
        for name, value in (
            ("scope_ref", scope_ref),
            ("subject_ref", subject_ref),
            ("principal_type", principal_type),
            ("key_id", key_id),
            ("verifier_digest", verifier_digest),
            ("verifier_algorithm", verifier_algorithm),
            ("protection_key_ref", protection_key_ref),
            ("status", status),
            ("version", version),
            ("not_before", not_before),
            ("expires_at", expires_at),
        ):
            object.__setattr__(self, name, value)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("API key verifier record is immutable")

    def __repr__(self) -> str:
        return "ApiKeyVerifierRecord(<redacted, unverified>)"

    def __deepcopy__(self, _memo: dict[int, object]) -> Never:
        raise TypeError("sensitive verifier record cannot be deep-copied")

    def __reduce_ex__(self, _protocol: int) -> Never:
        raise TypeError("sensitive verifier record cannot be pickled")


@dataclass(frozen=True, slots=True, repr=False)
class ApiKeyFound:
    """A scoped lookup candidate, never a verified credential."""

    record: ApiKeyVerifierRecord

    def __post_init__(self) -> None:
        if not isinstance(self.record, ApiKeyVerifierRecord):
            raise ValueError("invalid verifier record")

    def __repr__(self) -> str:
        return "ApiKeyFound(<redacted, unverified>)"


@dataclass(frozen=True, slots=True)
class ApiKeyMissing:
    """No candidate found within the approved source scope."""


@dataclass(frozen=True, slots=True)
class ApiKeyAmbiguous:
    """Multiple matching candidates: never select one arbitrarily."""


@dataclass(frozen=True, slots=True)
class ApiKeyUnavailable:
    """Source unavailable, contract broken or inconsistent: never fallback."""


type ApiKeyRecordLookup = ApiKeyFound | ApiKeyMissing | ApiKeyAmbiguous | ApiKeyUnavailable
