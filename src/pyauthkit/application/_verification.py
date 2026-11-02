"""Restricted internal transitions for approved verifiers and engine policy.

SECURITY: private Python helpers are not cryptographic capabilities or a sandbox.
Only explicitly admitted authenticators may legitimately emit verified outcomes.
No production authenticator is provided in M2.
"""

from pyauthkit.domain._verified import VerifiedSubject
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import VerifiedOutcome
from pyauthkit.domain.result import Authenticated
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.ports.authenticator import VerificationContext


def _issue_verified_outcome(
    context: VerificationContext,
    *,
    subject: ScopedSubjectRef,
    principal_type: PrincipalType,
    verified_at: ObservedAt,
) -> VerifiedOutcome:
    """Create an internal verified result *after* adapter-specific proof checks.

    This operation does not validate credentials; M2 calls it from test fakes.
    Future approved M3+ verifiers must actually validate proofs first.
    """
    if (
        not isinstance(context, VerificationContext)
        or not isinstance(subject, ScopedSubjectRef)
        or not isinstance(principal_type, PrincipalType)
        or not isinstance(verified_at, ObservedAt)
        or subject.scope_ref != context.scope_ref
    ):
        raise ValueError("invalid verified outcome context")
    verified = object.__new__(VerifiedSubject)
    object.__setattr__(verified, "subject", subject)
    object.__setattr__(verified, "principal_type", principal_type)
    object.__setattr__(verified, "method", context.method)
    object.__setattr__(verified, "profile", context.profile_ref)
    object.__setattr__(verified, "verified_at", verified_at)
    outcome = object.__new__(VerifiedOutcome)
    object.__setattr__(outcome, "status", "VERIFIED")
    object.__setattr__(outcome, "subject", verified)
    object.__setattr__(outcome, "correlation_id", context.correlation_id)
    object.__setattr__(outcome, "_attempt_token", context.attempt_token)
    return outcome


def _issue_authenticated(subject: VerifiedSubject, correlation_id: CorrelationId) -> Authenticated:
    """Only final policy may call; not part of the public SDK."""
    authenticated = object.__new__(Authenticated)
    object.__setattr__(authenticated, "status", "AUTHENTICATED")
    object.__setattr__(authenticated, "principal", subject)
    object.__setattr__(authenticated, "correlation_id", correlation_id)
    return authenticated


def _verified_matches_attempt(
    outcome: VerifiedOutcome, context: VerificationContext
) -> bool:
    """Reject cross-attempt, cross-tenant, cross-method and malformed outcomes."""
    try:
        subject = outcome.subject
        return (
            outcome.status == "VERIFIED"
            and outcome._attempt_token is context.attempt_token
            and outcome.correlation_id == context.correlation_id
            and isinstance(subject, VerifiedSubject)
            and isinstance(subject.subject, ScopedSubjectRef)
            and subject.subject.scope_ref == context.scope_ref
            and subject.method is context.method
            and subject.profile == context.profile_ref
            and isinstance(subject.principal_type, PrincipalType)
            and isinstance(subject.verified_at, ObservedAt)
        )
    except (AttributeError, TypeError, ValueError):
        return False
