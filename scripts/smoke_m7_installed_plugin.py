"""M7 wheel-only smoke: actual separately packaged, deny-only plugin."""

import asyncio
import sys

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import ClaimedIdentity
from pyauthkit.domain.result import Authenticated, Rejected
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
    positive = tuple(
        c
        for c in candidates
        if c.distribution == "pyauthkit-m7-synthetic-plugin" and c.name == "positive-test-only"
    )
    if (
        len(selected) != 1
        or len(managed) != 1
        or len(positive) != 1
        or "m7_synthetic_plugin.factory" in sys.modules
    ):
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

    async def check_positive() -> None:
        approved = load_approved_authenticators(
            positive,
            grants=(
                PluginGrant(
                    distribution="pyauthkit-m7-synthetic-plugin",
                    version="0.0.1",
                    name="positive-test-only",
                    target="m7_synthetic_plugin.factory:create_positive_test_only",
                    method=EvidenceMethod.API_KEY,
                ),
            ),
        )
        allowed = compose_authentication_engine(
            snapshot,
            authenticators=approved,
            final_rule=lambda _subject, _entry: True,
        )
        blocked = compose_authentication_engine(
            snapshot,
            authenticators=approved,
            final_rule=lambda _subject, _entry: False,
        )
        synthetic = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, b"m7-synthetic-fixture"),
            CorrelationId("m7-positive-fixture"),
        )
        route = "api"
        ok = await allowed.engine.authenticate(
            synthetic, entry=allowed.catalog.resolve_for_host_route(route)
        )
        if not isinstance(ok, Authenticated):
            raise RuntimeError("qualified synthetic positive path was not allowed")
        refused = await blocked.engine.authenticate(
            synthetic, entry=blocked.catalog.resolve_for_host_route(route)
        )
        if not isinstance(refused, Rejected) or hasattr(refused, "principal"):
            raise RuntimeError("plugin bypassed the final policy gate")

        invalid = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, b"m7-wrong-fixture"),
            CorrelationId("m7-invalid-fixture"),
        )
        wrong = await allowed.engine.authenticate(
            invalid, entry=allowed.catalog.resolve_for_host_route(route)
        )
        if not isinstance(wrong, Rejected):
            raise RuntimeError("invalid synthetic proof was not rejected")
        foreign = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, b"m7-synthetic-fixture"),
            CorrelationId("m7-foreign-fixture"),
            claimed_identity=ClaimedIdentity(
                identifier_kind="fixture", identifier_value="synthetic",
                claimed_tenant="foreign-tenant",
            ),
        )
        denied = await allowed.engine.authenticate(
            foreign, entry=allowed.catalog.resolve_for_host_route(route)
        )
        if not isinstance(denied, Rejected):
            raise RuntimeError("client tenant hint overrode host trust context")

    asyncio.run(check_positive())
    print("M7 installed plugin: SYNTHETIC VERIFIED / POLICY DENY / INVALID REJECTED")
    print("M7 installed independent plugin smoke: DENIED AND MANAGED CLEANUP")


if __name__ == "__main__":
    main()
