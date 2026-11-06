"""M7 pure-Python quickstart using a SYNTHETIC DENIAL-ONLY authenticator.

This is not a password or JWT implementation and cannot authenticate anyone.
Host route and configuration are explicit; no client-derived trust is accepted.
"""

import asyncio

from pyauthkit.domain.outcome import RejectedOutcome
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.sdk import (
    AuditDeliveryPolicy,
    AuthenticationRequest,
    ConfigurationGeneration,
    ConfigurationSnapshot,
    CorrelationId,
    EvidenceMethod,
    HostBinding,
    PresentedEvidence,
    Rejected,
    SourceProvenance,
    TrustedScopeRef,
    TrustProfileRef,
    compose_authentication_engine,
)


class SyntheticDenialAuthenticator:
    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> RejectedOutcome:
        return RejectedOutcome()


async def main() -> None:
    # Only trusted host code may choose this binding, never a request header.
    scope = TrustedScopeRef("demo-tenant")
    profile = TrustProfileRef("demo-profile", "v1", scope)
    snapshot = ConfigurationSnapshot(
        schema_version=1,
        generation=ConfigurationGeneration(1),
        provenance=SourceProvenance("demo", "host", "v1"),
        bindings=(
            HostBinding("host-api-route", scope, profile, frozenset({EvidenceMethod.API_KEY})),
        ),
        timeout_seconds=2.0,
        audit_delivery=AuditDeliveryPolicy(),
    )
    runtime = compose_authentication_engine(
        snapshot, authenticators=[SyntheticDenialAuthenticator()]
    )
    entry = runtime.catalog.resolve_for_host_route("host-api-route")
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"synthetic-invalid-evidence"),
        CorrelationId("m7-quickstart"),
    )
    result = await runtime.engine.authenticate(request, entry=entry)
    assert isinstance(result, Rejected)
    assert not hasattr(result, "principal")
    print("M7 Python-only synthetic denial: REJECTED (no principal)")


if __name__ == "__main__":
    asyncio.run(main())
