"""M2 AuthenticationPolicyGate preflight: deny by default, no final success.

Security invariant: an authenticator is not allowed to make a final
authentication decision. PR-05 will separately implement the final
verification-to-result policy transition.
"""

from dataclasses import dataclass

from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef

from .host_context import HostTrustCatalog, TrustedEntryContext


@dataclass(frozen=True, slots=True, repr=False)
class VerificationPermitted:
    """Preflight permission to attempt verification, NOT authentication.

    No principal, verification evidence, or positive result status is issued.
    """

    correlation_id: CorrelationId
    profile_ref: TrustProfileRef

    def __repr__(self) -> str:
        return "VerificationPermitted(<not authenticated>)"


type PreflightOutcome = VerificationPermitted | Rejected | AuthError


class AuthenticationPolicyGate:
    """Pre-verification policy guard over host-owned active bindings.

    [SECURITY: Complete Mediation / Fail Closed] PR-04 deliberately does
    NOT include final positive AuthenticationResult construction.
    """

    __slots__ = ("_catalog",)

    def __init__(self, catalog: HostTrustCatalog) -> None:
        if not isinstance(catalog, HostTrustCatalog):
            raise ValueError("invalid host trust catalog")
        self._catalog = catalog

    def preflight(
        self, request: AuthenticationRequest, *, entry: TrustedEntryContext
    ) -> PreflightOutcome:
        """Permit an attempt only for the catalog's host-issued entry.

        A claimed tenant is an untrusted lookup hint: it can cause denial if
        inconsistent, but it may never select the scope/profile.
        """
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
