"""Syntactic trust-profile references, not authority-bearing host context.

[DDD: Value Object] [SECURITY: Host-Authoritative Trust / No Fallback]
The trusted host resolver and active policy are deliberately deferred to M2.
"""

from dataclasses import dataclass

from .identity import _identifier
from .scope import TrustedScopeRef


@dataclass(frozen=True, slots=True, repr=False)
class TrustProfileRef:
    """Pinned profile reference, structurally bound to one scope.

    Neither constructing this reference nor selecting a version authorizes
    its use. A trusted host resolver must validate the binding later.
    """

    profile_id: str
    version: str
    scope_ref: TrustedScopeRef

    def __post_init__(self) -> None:
        _identifier(self.profile_id, maximum=128, field_name="profile reference")
        _identifier(self.version, maximum=64, field_name="profile version")
        if not isinstance(self.scope_ref, TrustedScopeRef):
            raise ValueError("invalid profile scope")

    def __repr__(self) -> str:
        return "TrustProfileRef(<unapproved reference>)"


@dataclass(frozen=True, slots=True, repr=False)
class ScopeProfileRef:
    """Consistency check for *references*, not host binding approval."""

    scope_ref: TrustedScopeRef
    profile_ref: TrustProfileRef

    def __post_init__(self) -> None:
        if (
            not isinstance(self.scope_ref, TrustedScopeRef)
            or not isinstance(self.profile_ref, TrustProfileRef)
            or self.scope_ref != self.profile_ref.scope_ref
        ):
            raise ValueError("scope/profile mismatch")

    def __repr__(self) -> str:
        return "ScopeProfileRef(<unapproved references>)"
