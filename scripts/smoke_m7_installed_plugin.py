"""M7 wheel-only smoke: actual separately packaged, deny-only plugin."""

import asyncio
import sys

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.result import Rejected
from pyauthkit.plugins import (
    PluginGrant,
    activate_approved_authenticators,
    discover_authenticator_plugins,
    load_approved_authenticators,
)
from pyauthkit.sdk import (
    AuditDeliveryPolicy,
    AuthenticationRequest,
    ConfigurationGeneration,
    ConfigurationSnapshot,
    CorrelationId,
    HostBinding,
    PresentedEvidence,
    SourceProvenance,
    TrustedScopeRef,
    TrustProfileRef,
    compose_authentication_engine,
)


def main() -> None:
    candidates = discover_authenticator_plugins(enabled=True)
    selected = tuple(
        c
        for c in candidates
        if c.distribution == "pyauthkit-m7-synthetic-plugin" and c.name == "synthetic"
    )
    managed = tuple(
        c
        for c in candidates
        if c.distribution == "pyauthkit-m7-synthetic-plugin" and c.name == "managed"
    )
    if len(selected) != 1 or len(managed) != 1 or "m7_synthetic_plugin.factory" in sys.modules:
        raise RuntimeError("plugin discovery executed code or missed installed distribution")
    if load_approved_authenticators(selected, grants=()):
        raise RuntimeError("plugin loaded without host admission")
    if "m7_synthetic_plugin.factory" in sys.modules:
        raise RuntimeError("plugin was imported before grant")
    plugins = load_approved_authenticators(
        selected,
        grants=[
            PluginGrant(
                distribution="pyauthkit-m7-synthetic-plugin",
                version="0.0.1",
                name="synthetic",
                target="m7_synthetic_plugin.factory:create",
                method=EvidenceMethod.API_KEY,
            )
        ],
    )
    if len(plugins) != 1 or "m7_synthetic_plugin.factory" not in sys.modules:
        raise RuntimeError("approved plugin was not loaded")

    scope = TrustedScopeRef("m7-wheel-tenant")
    profile = TrustProfileRef("m7-wheel-profile", "v1", scope)
    snapshot = ConfigurationSnapshot(
        schema_version=1,
        generation=ConfigurationGeneration(1),
        provenance=SourceProvenance("m7-wheel", "host", "v1"),
        bindings=(HostBinding("api", scope, profile, frozenset({EvidenceMethod.API_KEY})),),
        timeout_seconds=1.0,
        audit_delivery=AuditDeliveryPolicy(),
    )
    runtime = compose_authentication_engine(snapshot, authenticators=plugins)
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"untrusted-synthetic"),
        CorrelationId("m7-installed-wheel"),
    )
    result = asyncio.run(
        runtime.engine.authenticate(request, entry=runtime.catalog.resolve_for_host_route("api"))
    )
    if not isinstance(result, Rejected) or hasattr(result, "principal"):
        raise RuntimeError("unexpected plugin decision")
    async def check_managed() -> None:
        managed_grant = PluginGrant(
            distribution="pyauthkit-m7-synthetic-plugin",
            version="0.0.1",
            name="managed",
            target="m7_synthetic_plugin.factory:create_managed",
            method=EvidenceMethod.API_KEY,
        )
        async with activate_approved_authenticators(managed, grants=(managed_grant,)) as admitted:
            if len(admitted) != 1 or getattr(admitted[0], "closed", None) is not False:
                raise RuntimeError("managed wheel plugin did not activate")
            managed_runtime = compose_authentication_engine(snapshot, authenticators=admitted)
            managed_result = await managed_runtime.engine.authenticate(
                request, entry=managed_runtime.catalog.resolve_for_host_route("api")
            )
            if not isinstance(managed_result, Rejected):
                raise RuntimeError("managed plugin unexpectedly authenticated")
        if getattr(admitted[0], "closed", None) is not True:
            raise RuntimeError("managed wheel plugin was not closed")

    asyncio.run(check_managed())
    print("M7 installed independent plugin smoke: DENIED AND MANAGED CLEANUP")


if __name__ == "__main__":
    main()
