"""Explicit positive-proof declaration for a *trusted, admitted* plugin.

SECURITY: this helper does NOT verify an authenticator's cryptographic proof,
attest third-party code, or issue a final authentication decision. An approved
plugin must complete its own method-specific proof, revocation, and freshness
checks before calling it. Its assertion stays subject to the engine's
per-attempt checks and mandatory final host policy.
"""

from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.ports.authenticator import VerificationContext


class PluginProofDeclarationRejected(ValueError):
    """Sanitized refusal of a malformed plugin declaration, never a success."""


def issue_verified_outcome(
    *,
    request: AuthenticationRequest,
    context: VerificationContext,
    subject: ScopedSubjectRef,
    principal_type: PrincipalType,
    verified_at: ObservedAt,
) -> VerifiedOutcome:
    """Declare a verified internal outcome after a plugin has checked the proof.

    Trust model: the plugin is already approved by the host. A result produced
    here is NOT proof that the plugin checked evidence honestly. This helper
    limits accidental context confusion; the engine additionally validates
    the exact attempt token, scope, method, profile and final policy gate.

    Untrusted evidence or a claimed tenant MUST NOT select the trusted context.
    Exceptions are deliberately constant-string to avoid leaking credentials.
    """
    if (
        not isinstance(request, AuthenticationRequest)
        or not isinstance(context, VerificationContext)
        or not isinstance(subject, ScopedSubjectRef)
        or not isinstance(principal_type, PrincipalType)
        or not isinstance(verified_at, ObservedAt)
        or not isinstance(request.evidence.method, EvidenceMethod)
        or request.evidence.method is not context.method
        or request.correlation_id != context.correlation_id
        or subject.scope_ref != context.scope_ref
        or context.profile_ref.scope_ref != context.scope_ref
    ):
        raise PluginProofDeclarationRejected("invalid plugin proof declaration")

    try:
        return _issue_verified_outcome(
            context,
            subject=subject,
            principal_type=principal_type,
            verified_at=verified_at,
        )
    except Exception:
        raise PluginProofDeclarationRejected("invalid plugin proof declaration") from None
