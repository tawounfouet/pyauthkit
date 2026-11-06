"""Test-only plugin: demonstrates SPI packaging without proving credentials."""

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.outcome import RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.ports.authenticator import VerificationContext


class SyntheticDenyAuthenticator:
    """Deliberately cannot produce an authenticated principal."""

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> RejectedOutcome:
        return RejectedOutcome()


def create() -> SyntheticDenyAuthenticator:
    return SyntheticDenyAuthenticator()


create.SPI_MAJOR = 1  # type: ignore[attr-defined]


class ManagedDenyAuthenticator(SyntheticDenyAuthenticator):
    """Test-only managed plugin for an installed-wheel lifecycle smoke."""

    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def create_managed() -> ManagedDenyAuthenticator:
    return ManagedDenyAuthenticator()


create_managed.SPI_MAJOR = 1  # type: ignore[attr-defined]
