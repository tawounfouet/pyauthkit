"""Explicit, allowlisted public serializers with no credential payloads."""

from typing import TypedDict

from .request import AuthenticationRequest
from .result import AuthenticationResult, AuthError, ChallengeRequired, Rejected


class PublicAuthenticationSummary(TypedDict):
    status: str
    correlation_id: str
    code: str


class PublicRequestSummary(TypedDict):
    method: str
    correlation_id: str
    verified: bool


def public_request_summary(request: AuthenticationRequest) -> PublicRequestSummary:
    """Report only method and correlation; never evidence or identity hints."""
    if not isinstance(request, AuthenticationRequest):
        raise ValueError("invalid authentication request")
    return {
        "method": request.evidence.method.value,
        "correlation_id": request.correlation_id.value,
        "verified": False,
    }


def public_result_summary(result: AuthenticationResult) -> PublicAuthenticationSummary:
    """No raw exception, claim or evidence is serialized.

    The positive variant requires the future M2 policy-gate serializer and
    must never pass through an implicit or generic fallback.
    """
    if isinstance(result, Rejected):
        code = result.reason_code.value
    elif isinstance(result, AuthError):
        code = result.error_code.value
    elif isinstance(result, ChallengeRequired):
        code = "additional_verification_required"
    else:
        raise ValueError("positive result serialization requires policy gate")
    return {"status": result.status, "correlation_id": result.correlation_id.value, "code": code}
