"""Untrusted identity claims and scoped subject references.

[DDD: Value Object] [SECURITY: Explicit Trust / Fail Closed]
No claimed identifier is proof of possession, authorization or authentication.
"""

from dataclasses import dataclass
from enum import StrEnum

from .scope import TrustedScopeRef


class PrincipalType(StrEnum):
    """Actor kind; separate from the issuer and authentication mechanism."""

    HUMAN = "human"
    APPLICATION = "application"
    SERVICE = "service"
    WORKLOAD = "workload"
    DEVICE = "device"
    AGENT = "agent"


def _identifier(value: str, *, maximum: int, field_name: str) -> str:
    """Bound textual identifiers without trusting their contents."""

    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= maximum
        or not value.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError(f"invalid {field_name}")
    return value


@dataclass(frozen=True, slots=True, repr=False)
class ClaimedIdentity:
    """Untrusted lookup hint, never a verified subject.

    Trust boundary: all fields originate from a caller and confer no authority.
    Repr deliberately excludes potentially sensitive or personal identifiers.
    """

    identifier_kind: str
    identifier_value: str
    claimed_issuer: str | None = None
    claimed_tenant: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.identifier_kind, maximum=32, field_name="identifier kind")
        _identifier(self.identifier_value, maximum=256, field_name="identifier value")
        if self.claimed_issuer is not None:
            _identifier(self.claimed_issuer, maximum=128, field_name="claimed issuer")
        if self.claimed_tenant is not None:
            _identifier(self.claimed_tenant, maximum=128, field_name="claimed tenant")

    def __repr__(self) -> str:
        return "ClaimedIdentity(<redacted, untrusted>)"


@dataclass(frozen=True, slots=True, repr=False)
class ScopedSubjectRef:
    """Structural identity key; never a verified or authorized subject.

    Namespace includes issuer *and* scope, preventing cross-tenant collapse.
    """

    subject_id: str
    issuer_ref: str
    scope_ref: TrustedScopeRef

    def __post_init__(self) -> None:
        _identifier(self.subject_id, maximum=256, field_name="subject identifier")
        _identifier(self.issuer_ref, maximum=128, field_name="issuer reference")
        if not isinstance(self.scope_ref, TrustedScopeRef):
            raise ValueError("invalid scope reference")

    def __repr__(self) -> str:
        return "ScopedSubjectRef(<redacted, unverified>)"
