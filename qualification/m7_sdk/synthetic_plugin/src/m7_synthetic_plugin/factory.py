"""Test-only plugin: demonstrates SPI packaging without proving credentials."""

import hmac
from datetime import UTC, datetime

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.outcome import RejectedOutcome, VerifiedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.plugins.verification import issue_verified_outcome
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


class SyntheticPositiveProofAuthenticator:
    """TEST-ONLY proof fixture. Public fixed bytes are not credentials.

    Never use this class or fixture for production authentication. Its sole
    purpose is exercising the attempt-bound VerifiedOutcome SPI and the
    *independent* final host policy gate.
    """

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> RejectedOutcome | VerifiedOutcome:
        if (
            request.evidence.method is not EvidenceMethod.API_KEY
            or context.method is not EvidenceMethod.API_KEY
        ):
            return RejectedOutcome()
        # This intentionally public fixture is not a secret or production proof.
        if not hmac.compare_digest(request.evidence.opaque_payload, b"m7-synthetic-fixture"):
            return RejectedOutcome()
        return issue_verified_outcome(
            request=request,
            context=context,
            subject=ScopedSubjectRef(
                "fixture-subject", "synthetic-qualification-only", context.scope_ref
            ),
            principal_type=PrincipalType.SERVICE,
            verified_at=ObservedAt(datetime.now(UTC)),
        )


def create_positive_test_only() -> SyntheticPositiveProofAuthenticator:
    return SyntheticPositiveProofAuthenticator()


create_positive_test_only.SPI_MAJOR = 1  # type: ignore[attr-defined]
