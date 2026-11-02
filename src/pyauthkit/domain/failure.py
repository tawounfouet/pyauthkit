"""Safe rejection and operational-failure vocabulary.

[SECURITY: Redaction] Public results expose stable codes, never raw causes.
"""

from enum import StrEnum


class RejectionCode(StrEnum):
    """Uniform public denial, intentionally avoiding account enumeration."""

    AUTHENTICATION_REJECTED = "authentication_rejected"


class TechnicalErrorCode(StrEnum):
    """Stable operational failures, distinct from incorrect credentials."""

    INTERNAL_ERROR = "internal_error"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    INVALID_TRUST_CONFIGURATION = "invalid_trust_configuration"


class DomainTechnicalError(Exception):
    """A failure with a safe fixed code, without raw exception messages.

    Failure semantics: a technical failure is not a rejected credential and
    may never be transformed to an authenticated result.
    """

    def __init__(self, code: TechnicalErrorCode) -> None:
        if not isinstance(code, TechnicalErrorCode):
            raise ValueError("invalid technical error code")
        self.code = code
        super().__init__(code.value)
