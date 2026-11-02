"""Discriminated final authentication result, with no M1 success factory.

[DDD: Result Object] [SECURITY: Fail Closed]
AUTHENTICATED requires completed verification *and* the M2 policy gate.
"""

from dataclasses import dataclass, field
from typing import Literal, Never

from ._verified import VerifiedSubject
from .failure import RejectionCode, TechnicalErrorCode
from .temporal import CorrelationId


class Authenticated:
    """Reserved positive variant. Construction is disabled until M2.

    A Python class cannot provide a trust boundary against arbitrary Python
    object manipulation. Only trusted M2 verification+policy may enable a
    positive decision; no such production path exists in this PR.
    """

    __slots__ = ("status", "principal", "correlation_id")

    status: Literal["AUTHENTICATED"]
    principal: VerifiedSubject
    correlation_id: CorrelationId

    def __new__(cls, *_args: object, **_kwargs: object) -> Never:
        raise TypeError("authentication success requires a verified policy gate")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("authenticated result is immutable")

    def __repr__(self) -> str:
        return "Authenticated(<redacted, restricted>)"


@dataclass(frozen=True, slots=True)
class Rejected:
    """Final denial, structurally without a principal or secret."""

    correlation_id: CorrelationId
    reason_code: RejectionCode = RejectionCode.AUTHENTICATION_REJECTED
    status: Literal["REJECTED"] = field(default="REJECTED", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.correlation_id, CorrelationId):
            raise ValueError("invalid correlation identifier")
        if not isinstance(self.reason_code, RejectionCode):
            raise ValueError("invalid rejection code")

    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class AuthError:
    """Technical failure, distinct from rejection, without a principal."""

    correlation_id: CorrelationId
    error_code: TechnicalErrorCode
    status: Literal["ERROR"] = field(default="ERROR", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.correlation_id, CorrelationId):
            raise ValueError("invalid correlation identifier")
        if not isinstance(self.error_code, TechnicalErrorCode):
            raise ValueError("invalid technical error code")

    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ChallengeRequired:
    """Reserved non-success response; no continuation is issued in M1."""

    correlation_id: CorrelationId
    status: Literal["CHALLENGE_REQUIRED"] = field(default="CHALLENGE_REQUIRED", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.correlation_id, CorrelationId):
            raise ValueError("invalid correlation identifier")

    def __bool__(self) -> bool:
        return False


type AuthenticationResult = Authenticated | Rejected | AuthError | ChallengeRequired
