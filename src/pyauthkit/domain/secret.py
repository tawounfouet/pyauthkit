"""Opaque references to sensitive material, NOT the material itself.

[DDD: Value Object] A SecretRef describes an approved logical identity.
Provider and namespace are identifiers, never arbitrary filesystem paths or
network URLs. Serialization of the underlying bytes is never permitted here.
"""

import re
from dataclasses import dataclass

_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_PURPOSES = frozenset({"verify", "sign", "pepper", "audit_pseudonymization"})


@dataclass(frozen=True, slots=True, repr=False)
class SecretRef:
    provider: str
    namespace: str
    key_id: str
    version: str
    purpose: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(v, str) or not _COMPONENT.fullmatch(v)
            for v in (self.provider, self.namespace, self.key_id, self.version)
        ):
            raise ValueError("invalid secret reference")
        if self.purpose not in _PURPOSES:
            raise ValueError("invalid secret purpose")

    def __repr__(self) -> str:
        return "SecretRef(<redacted logical reference>)"

    def __str__(self) -> str:
        return "SecretRef(<redacted logical reference>)"
