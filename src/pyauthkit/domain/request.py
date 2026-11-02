"""Request DTO preserves untrusted provenance, without host trust binding."""

from dataclasses import dataclass

from .evidence import PresentedEvidence
from .identity import ClaimedIdentity
from .temporal import CorrelationId, ObservedAt


@dataclass(frozen=True, slots=True, repr=False)
class AuthenticationRequest:
    """Untrusted evidence and optional identity claim, without policy data.

    [DDD: Value Object] [SECURITY: Trust Boundary]
    It does not carry effective tenant, scope, key source or trust profile.
    Host-approved binding and verifier execution belong to later milestones.
    """

    evidence: PresentedEvidence
    correlation_id: CorrelationId
    claimed_identity: ClaimedIdentity | None = None
    observed_at: ObservedAt | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, PresentedEvidence):
            raise ValueError("invalid evidence")
        if not isinstance(self.correlation_id, CorrelationId):
            raise ValueError("invalid correlation identifier")
        if self.claimed_identity is not None and not isinstance(
            self.claimed_identity, ClaimedIdentity
        ):
            raise ValueError("invalid claimed identity")
        if self.observed_at is not None and not isinstance(self.observed_at, ObservedAt):
            raise ValueError("invalid observation timestamp")

    def __repr__(self) -> str:
        return "AuthenticationRequest(<redacted, unverified>)"
