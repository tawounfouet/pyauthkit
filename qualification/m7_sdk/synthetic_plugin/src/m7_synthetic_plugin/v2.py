"""Isolated SPI v2 integration fixture; intentionally NOT production authentication."""

from datetime import UTC, datetime

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import RejectedOutcome, VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.plugins.services import PluginHostServices
from pyauthkit.plugins.verification import issue_verified_outcome
from pyauthkit.ports.authenticator import VerificationContext


class HostScopedHmacFixture:
    def __init__(self, services: PluginHostServices) -> None:
        self.services = services
        self.closed = False

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> RejectedOutcome | VerifiedOutcome:
        # Host owns and scopes the MAC verifier, not the plugin itself.
        verifier = self.services.port("hash_verifier")
        if not verifier.verify(request.evidence.opaque_payload, scope_ref=context.scope_ref):
            return RejectedOutcome()
        return issue_verified_outcome(
            request=request,
            context=context,
            subject=ScopedSubjectRef("fixture", "m7-host-only", context.scope_ref),
            principal_type=PrincipalType.SERVICE,
            verified_at=ObservedAt(datetime.now(UTC)),
        )

    async def aclose(self) -> None:
        self.closed = True


def create_host_scoped(services: PluginHostServices) -> HostScopedHmacFixture:
    return HostScopedHmacFixture(services)


create_host_scoped.SPI_MAJOR = 2  # type: ignore[attr-defined]
