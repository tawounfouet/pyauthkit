"""Verifier outcomes are not final authentication decisions.

A positive result must be bound to the exact engine attempt and the final gate.
The constructor remains blocked from the normal public Python API.
"""

from dataclasses import dataclass, field
from typing import Literal, Never

from ._verified import VerifiedSubject
from .failure import RejectionCode, TechnicalErrorCode
from .result import AuthError, Rejected
from .temporal import CorrelationId


class VerifiedOutcome:
    """Internal proof result, never itself a final authentication grant."""

    __slots__ = ("status", "subject", "correlation_id", "_attempt_token")

    status: Literal["VERIFIED"]
    subject: VerifiedSubject
    correlation_id: CorrelationId
    _attempt_token: object

    def __new__(cls, *_args: object, **_kwargs: object) -> Never:
        raise TypeError("verified outcomes require an approved authenticator")

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("verified outcome is immutable")

    def __repr__(self) -> str:
        return "VerifiedOutcome(<redacted, internal>)"


@dataclass(frozen=True, slots=True)
class RejectedOutcome:
    """A verifier's refusal, not a final permission decision."""

    reason_code: RejectionCode = RejectionCode.AUTHENTICATION_REJECTED
    status: Literal["REJECTED"] = field(default="REJECTED", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.reason_code, RejectionCode):
            raise ValueError("invalid rejection code")


@dataclass(frozen=True, slots=True)
class ErrorOutcome:
    """A verifier's inability to evaluate evidence, never success."""

    error_code: TechnicalErrorCode
    status: Literal["ERROR"] = field(default="ERROR", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.error_code, TechnicalErrorCode):
            raise ValueError("invalid error code")


type AuthenticatorOutcome = VerifiedOutcome | RejectedOutcome | ErrorOutcome


def normalize_non_success(
    outcome: AuthenticatorOutcome, *, correlation_id: CorrelationId
) -> Rejected | AuthError:
    """Convert only negative outcomes; a positive must pass through final policy."""
    if isinstance(outcome, RejectedOutcome):
        return Rejected(correlation_id=correlation_id, reason_code=outcome.reason_code)
    if isinstance(outcome, ErrorOutcome):
        return AuthError(correlation_id=correlation_id, error_code=outcome.error_code)
    raise DomainTransitionBlocked("verified outcomes require the policy gate")


class DomainTransitionBlocked(Exception):
    """Safe refusal of a missing or unauthorized result transition."""
