"""Approved verifier SPI. No authenticator may issue a final AuthN result."""

from dataclasses import dataclass, field
from typing import Protocol

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.outcome import AuthenticatorOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef


@dataclass(frozen=True, slots=True, repr=False)
class VerificationContext:
    """Host-approved attempt context; marker is internal, not cryptographic."""

    scope_ref: TrustedScopeRef
    profile_ref: TrustProfileRef
    method: EvidenceMethod
    correlation_id: CorrelationId
    attempt_token: object = field(repr=False)

    def __post_init__(self) -> None:
        if self.profile_ref.scope_ref != self.scope_ref:
            raise ValueError("verification scope/profile mismatch")
        if not isinstance(self.method, EvidenceMethod):
            raise ValueError("invalid verification method")
        if not isinstance(self.correlation_id, CorrelationId):
            raise ValueError("invalid correlation identifier")

    def __repr__(self) -> str:
        return "VerificationContext(<host-approved, redacted>)"


class Authenticator(Protocol):
    """Minimal async, explicitly registered verification strategy."""

    @property
    def method(self) -> EvidenceMethod: ...

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> AuthenticatorOutcome: ...


class AuthenticatorLookup(Protocol):
    """Narrow lookup dependency used by the application layer."""

    def resolve(self, method: EvidenceMethod) -> Authenticator: ...
