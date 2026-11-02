"""Host-controlled preflight and mandatory final authentication decision.

A verifier returns an *internal* outcome. Neither preflight nor a verifier
may create a final principal without a coherent verified outcome and allow.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pyauthkit.domain._verified import VerifiedSubject
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.outcome import VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import VerificationContext

from ._verification import _issue_authenticated, _verified_matches_attempt
from .host_context import HostTrustCatalog, TrustedEntryContext


@dataclass(frozen=True, slots=True, repr=False)
class VerificationPermitted:
    """Preflight permits an attempt, NEVER a final authentication result."""

    correlation_id: CorrelationId
    profile_ref: TrustProfileRef

    def __repr__(self) -> str:
        return "VerificationPermitted(<not authenticated>)"


type PreflightOutcome = VerificationPermitted | Rejected | AuthError
type FinalRule = Callable[[VerifiedSubject, TrustedEntryContext], bool]


class AuthenticationPolicyGate:
    """Two decisions: admission before verification, explicit allow after it."""

    __slots__ = ("_catalog", "_final_rule")

    def __init__(
        self, catalog: HostTrustCatalog, *, final_rule: FinalRule | None = None
    ) -> None:
        if not isinstance(catalog, HostTrustCatalog):
            raise ValueError("invalid host trust catalog")
        if final_rule is not None and not callable(final_rule):
            raise ValueError("invalid final policy")
        self._catalog = catalog
        self._final_rule = final_rule

    def preflight(
        self, request: AuthenticationRequest, *, entry: TrustedEntryContext
    ) -> PreflightOutcome:
        """Reject unknown host bindings, foreign tenant hints and disabled methods."""
        if not isinstance(request, AuthenticationRequest):
            raise ValueError("invalid authentication request")
        if not self._catalog.owns(entry):
            return AuthError(request.correlation_id, TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if request.claimed_identity is not None:
            hint = request.claimed_identity.claimed_tenant
            if hint is not None and hint != entry.scope_ref.value:
                return Rejected(request.correlation_id)
        if request.evidence.method not in entry.allowed_methods:
            return Rejected(request.correlation_id)
        return VerificationPermitted(request.correlation_id, entry.profile_ref)

    def final_decision(
        self,
        request: AuthenticationRequest,
        *,
        entry: TrustedEntryContext,
        context: VerificationContext,
        outcome: VerifiedOutcome,
    ) -> Authenticated | Rejected | AuthError:
        """Internal transition. A positive adapter outcome alone is insufficient."""
        correlation_id = request.correlation_id
        if not self._catalog.owns(entry):
            return AuthError(correlation_id, TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if (
            context.correlation_id != correlation_id
            or context.profile_ref != entry.profile_ref
            or context.scope_ref != entry.scope_ref
            or context.method != request.evidence.method
            or context.method not in entry.allowed_methods
            or not isinstance(outcome, VerifiedOutcome)
            or not _verified_matches_attempt(outcome, context)
        ):
            return AuthError(correlation_id, TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if self._final_rule is None:
            return Rejected(correlation_id)
        try:
            approved = self._final_rule(outcome.subject, entry)
        except Exception:
            return AuthError(correlation_id, TechnicalErrorCode.INTERNAL_ERROR)
        if approved is not True:
            return Rejected(correlation_id)
        return _issue_authenticated(outcome.subject, correlation_id)
