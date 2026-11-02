"""Reserved positive-proof type; deliberately not constructible in M1.

SECURITY: The eventual verifier and trusted policy gate must establish this
object under an approved host context (M2). Python name privacy and typing
are NOT security boundaries against privileged or malicious local code.
"""

from typing import Never

from .evidence import EvidenceMethod
from .identity import PrincipalType, ScopedSubjectRef
from .temporal import ObservedAt
from .trust import TrustProfileRef


class VerifiedSubject:
    """A subject with proof provenance, reserved until a verifier exists.

    There is no public conversion from ClaimedIdentity or ScopedSubjectRef.
    Constructor is disabled, and no positive-auth factory exists in PR-03.
    """

    __slots__ = ("subject", "principal_type", "method", "profile", "verified_at")

    subject: ScopedSubjectRef
    principal_type: PrincipalType
    method: EvidenceMethod
    profile: TrustProfileRef
    verified_at: ObservedAt

    def __new__(cls, *_args: object, **_kwargs: object) -> Never:
        raise TypeError("verified subjects require an approved verifier")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("verified subject is immutable")

    def __repr__(self) -> str:
        return "VerifiedSubject(<redacted, restricted>)"
