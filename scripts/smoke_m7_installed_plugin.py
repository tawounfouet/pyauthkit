"""M7 wheel-only smoke: actual separately packaged, deny-only plugin."""

import asyncio
import hashlib
import hmac
import sys

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import ClaimedIdentity
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.plugins import (
    ENTRY_POINT_GROUP_V2,
    PluginGrant,
    PluginHostServices,
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
                identifier_kind="fixture",
                identifier_value="synthetic",
                claimed_tenant="foreign-tenant",
            ),
        )
        denied = await allowed.engine.authenticate(
            foreign, entry=allowed.catalog.resolve_for_host_route(route)
        )
        if not isinstance(denied, Rejected):
            raise RuntimeError("client tenant hint overrode host trust context")

    asyncio.run(check_positive())

    # SPI v2: separately installed factory receives a host-selected port,
    # rather than reading keys or tenant routing from client claims.
    class HostHmacFixture:
        def __init__(self, scope_ref: TrustedScopeRef) -> None:
            self.key = b"m7-v2-public-fixture-key"
            self.scope_ref = scope_ref
            self.revoked = False
            self.calls = 0

        def token(self) -> bytes:
            return hmac.new(self.key, self.scope_ref.value.encode(), hashlib.sha256).digest()

        def verify(self, payload: bytes, *, scope_ref: TrustedScopeRef) -> bool:
            self.calls += 1
            return (
                scope_ref == self.scope_ref
                and not self.revoked
                and hmac.compare_digest(payload, self.token())
            )

    async def check_v2() -> None:
        candidates_v2 = discover_authenticator_plugins(enabled=True, group=ENTRY_POINT_GROUP_V2)
        selected_v2 = tuple(
            c
            for c in candidates_v2
            if c.distribution == "pyauthkit-m7-synthetic-plugin" and c.name == "host-scoped"
        )
        if len(selected_v2) != 1 or "m7_synthetic_plugin.v2" in sys.modules:
            raise RuntimeError("v2 discovery imported plugin code")
        verifier = HostHmacFixture(scope)
        host_services = PluginHostServices.from_snapshot(
            snapshot,
            route_id="api",
            method=EvidenceMethod.API_KEY,
            ports={"hash_verifier": verifier},
        )
        selected_grant = PluginGrant(
            distribution="pyauthkit-m7-synthetic-plugin",
            version="0.0.1",
            group=ENTRY_POINT_GROUP_V2,
            spi_major=2,
            name="host-scoped",
            target="m7_synthetic_plugin.v2:create_host_scoped",
            method=EvidenceMethod.API_KEY,
            port_roles=frozenset({"hash_verifier"}),
        )
        async with activate_approved_authenticators(
            selected_v2,
            grants=(selected_grant,),
            service_bindings={selected_grant: host_services},
        ) as loaded:
            if "m7_synthetic_plugin.v2" not in sys.modules:
                raise RuntimeError("host-admitted v2 factory did not load")
            allowed = compose_authentication_engine(
                snapshot,
                authenticators=loaded,
                final_rule=lambda _subject, _entry: True,
            )
            denied = compose_authentication_engine(
                snapshot,
                authenticators=loaded,
                final_rule=lambda _subject, _entry: False,
            )
            correct = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.API_KEY, verifier.token()),
                CorrelationId("m7-v2-positive"),
            )
            yes = await allowed.engine.authenticate(
                correct, entry=allowed.catalog.resolve_for_host_route("api")
            )
            no = await denied.engine.authenticate(
                correct, entry=denied.catalog.resolve_for_host_route("api")
            )
            if not isinstance(yes, Authenticated) or not isinstance(no, Rejected):
                raise RuntimeError("host policy and scoped proof disagreed")
            verifier.revoked = True
            revoked = await allowed.engine.authenticate(
                correct, entry=allowed.catalog.resolve_for_host_route("api")
            )
            if not isinstance(revoked, Rejected):
                raise RuntimeError("revoked test-only verifier accepted")
            verifier.revoked = False
            wrong = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.API_KEY, b"invalid-v2-mac"),
                CorrelationId("m7-v2-invalid"),
            )
            invalid = await allowed.engine.authenticate(
                wrong, entry=allowed.catalog.resolve_for_host_route("api")
            )
            if not isinstance(invalid, Rejected):
                raise RuntimeError("invalid v2 MAC accepted")
            foreign_scope = TrustedScopeRef("m7-other-tenant")
            foreign_snapshot = ConfigurationSnapshot(
                schema_version=1,
                generation=ConfigurationGeneration(1),
                provenance=SourceProvenance("m7-wheel", "host", "v1"),
                bindings=(
                    HostBinding(
                        "api",
                        foreign_scope,
                        TrustProfileRef("m7-wheel-profile", "v1", foreign_scope),
                        frozenset({EvidenceMethod.API_KEY}),
                    ),
                ),
                timeout_seconds=1.0,
                audit_delivery=AuditDeliveryPolicy(),
            )
            foreign = compose_authentication_engine(
                foreign_snapshot,
                authenticators=loaded,
                final_rule=lambda _subject, _entry: True,
            )
            prior_calls = verifier.calls
            cross = await foreign.engine.authenticate(
                correct, entry=foreign.catalog.resolve_for_host_route("api")
            )
            if isinstance(cross, Authenticated) or verifier.calls != prior_calls:
                raise RuntimeError("cross-tenant v2 plugin was called")
        print("M7 SPI v2 installed wheel: HOST MAC / REVOCATION / SCOPE CHECKS")

    asyncio.run(check_v2())
    print("M7 installed plugin: SYNTHETIC VERIFIED / POLICY DENY / INVALID REJECTED")
    print("M7 installed independent plugin smoke: DENIED AND MANAGED CLEANUP")


if __name__ == "__main__":
    main()
