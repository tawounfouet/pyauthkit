"""M7 SPI v2: host-owned port injection, scope guard and fail-closed admission."""

import asyncio
import hashlib
import hmac
import sys
from dataclasses import replace
from importlib.metadata import distributions
from pathlib import Path

import pytest

from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.plugins import (
    ENTRY_POINT_GROUP_V2,
    PluginAdmissionRejected,
    PluginGrant,
    PluginHostServices,
    activate_approved_authenticators,
    discover_authenticator_plugins,
    discovery,
    load_approved_authenticators,
)
from pyauthkit.sdk import (
    AuditDeliveryPolicy,
    AuthenticationRequest,
    ConfigurationGeneration,
    ConfigurationSnapshot,
    CorrelationId,
    HostBinding,
    SourceProvenance,
    TrustedScopeRef,
    TrustProfileRef,
    compose_authentication_engine,
)


class HostHmacVerifier:
    """Qualification-only MAC verifier, never a production key source."""

    def __init__(self, scope_ref: TrustedScopeRef) -> None:
        self.scope_ref = scope_ref
        self.key = b"synthetic-m7-test-key"
        self.revoked = False
        self.calls = 0

    def token(self) -> bytes:
        return hmac.new(self.key, self.scope_ref.value.encode(), hashlib.sha256).digest()

    def verify(self, evidence: bytes, *, scope_ref: TrustedScopeRef) -> bool:
        self.calls += 1
        if scope_ref != self.scope_ref or self.revoked:
            return False
        return hmac.compare_digest(evidence, self.token())

    def __repr__(self) -> str:
        return "HostHmacVerifier(<test-only>)"


def host_snapshot(scope_name: str = "tenant-a") -> ConfigurationSnapshot:
    scope = TrustedScopeRef(scope_name)
    profile = TrustProfileRef("m7-v2-profile", "v1", scope)
    return ConfigurationSnapshot(
        schema_version=1,
        generation=ConfigurationGeneration(1),
        provenance=SourceProvenance("approved-m7", "host", "v1"),
        bindings=(
            HostBinding("approved-route", scope, profile, frozenset({EvidenceMethod.API_KEY})),
        ),
        timeout_seconds=0.3,
        audit_delivery=AuditDeliveryPolicy(),
    )


def grant() -> PluginGrant:
    return PluginGrant(
        distribution="m7-spi2-fixture",
        version="1.0.0",
        group=ENTRY_POINT_GROUP_V2,
        spi_major=2,
        name="hmac-synthetic",
        target="m7_spi2_fixture:create",
        method=EvidenceMethod.API_KEY,
        port_roles=frozenset({"hash_verifier"}),
    )


def installed_v2(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    site = tmp_path / "v2-site"
    site.mkdir()
    marker = tmp_path / "plugin-was-imported.txt"
    source = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('imported')\n"
        "from datetime import UTC, datetime\n"
        "from pyauthkit.domain.evidence import EvidenceMethod\n"
        "from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef\n"
        "from pyauthkit.domain.outcome import RejectedOutcome\n"
        "from pyauthkit.domain.temporal import ObservedAt\n"
        "from pyauthkit.plugins.verification import issue_verified_outcome\n"
        "class Verifier:\n"
        "    def __init__(self, services):\n"
        "        self.services = services\n"
        "        self.closed = False\n"
        "    @property\n"
        "    def method(self): return EvidenceMethod.API_KEY\n"
        "    async def verify(self, request, context):\n"
        "        port = self.services.port('hash_verifier')\n"
        "        if not port.verify(request.evidence.opaque_payload, scope_ref=context.scope_ref):\n"
        "            return RejectedOutcome()\n"
        "        return issue_verified_outcome(\n"
        "            request=request, context=context,\n"
        "            subject=ScopedSubjectRef('fixture', 'm7-synthetic', context.scope_ref),\n"
        "            principal_type=PrincipalType.SERVICE,\n"
        "            verified_at=ObservedAt(datetime.now(UTC)),\n"
        "        )\n"
        "    async def aclose(self): self.closed = True\n"
        "def create(services): return Verifier(services)\n"
        "create.SPI_MAJOR = 2\n"
    )
    (site / "m7_spi2_fixture.py").write_text(source, encoding="utf-8")
    dist = site / "m7_spi2_fixture-1.0.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: m7-spi2-fixture\nVersion: 1.0.0\n",
        encoding="utf-8",
    )
    (dist / "entry_points.txt").write_text(
        f"[{ENTRY_POINT_GROUP_V2}]\nhmac-synthetic = m7_spi2_fixture:create\n",
        encoding="utf-8",
    )
    points = tuple(next(iter(distributions(path=[str(site)]))).entry_points)
    assert len(points) == 1
    monkeypatch.syspath_prepend(str(site))
    monkeypatch.setattr(discovery, "entry_points", lambda **kwargs: points)
    sys.modules.pop("m7_spi2_fixture", None)
    return marker


def services(snapshot: ConfigurationSnapshot, verifier: HostHmacVerifier) -> PluginHostServices:
    return PluginHostServices.from_snapshot(
        snapshot,
        route_id="approved-route",
        method=EvidenceMethod.API_KEY,
        ports={"hash_verifier": verifier},
    )


def candidates() -> tuple[object, ...]:
    return discover_authenticator_plugins(enabled=True, group=ENTRY_POINT_GROUP_V2)


def test_spi2_discovery_remains_inert_and_opt_in(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    marker = installed_v2(monkeypatch, tmp_path)
    assert discover_authenticator_plugins(group=ENTRY_POINT_GROUP_V2) == ()
    assert len(candidates()) == 1
    assert not marker.exists()
    assert "m7_spi2_fixture" not in sys.modules


def test_spi2_requires_exact_preapproved_services_before_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    marker = installed_v2(monkeypatch, tmp_path)
    approved = candidates()
    snapshot = host_snapshot()
    verifier = HostHmacVerifier(snapshot.bindings[0].scope_ref)
    bound = services(snapshot, verifier)
    binding = {grant(): bound}

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected):
            async with activate_approved_authenticators(approved, grants=(grant(),)):
                pytest.fail("unbound v2 factory must never activate")
        with pytest.raises(PluginAdmissionRejected):
            async with activate_approved_authenticators(
                approved, grants=(grant(),), service_bindings={}
            ):
                pytest.fail("missing v2 services must never activate")
        with pytest.raises(PluginAdmissionRejected):
            async with activate_approved_authenticators(
                approved,
                grants=(replace(grant(), version="2.0.0"),),
                service_bindings=binding,
            ):
                pytest.fail("wrong version must never activate")
        with pytest.raises(PluginAdmissionRejected):
            load_approved_authenticators(approved, grants=(grant(),))
        assert not marker.exists()

        async with activate_approved_authenticators(
            approved, grants=(grant(),), service_bindings=binding
        ) as plugins:
            assert marker.exists()
            assert len(plugins) == 1

    asyncio.run(scenario())


def test_spi2_host_port_snapshot_is_immutable_and_redacted() -> None:
    snapshot = host_snapshot()
    verifier = HostHmacVerifier(snapshot.bindings[0].scope_ref)
    ports = {"hash_verifier": verifier}
    bound = services(snapshot, verifier)
    ports.clear()
    assert bound.port("hash_verifier") is verifier
    with pytest.raises(TypeError):
        bound.ports["hash_verifier"] = object()  # type: ignore[index]
    assert "synthetic-m7-test-key" not in repr(bound)
    with pytest.raises(PluginAdmissionRejected):
        bound.port("raw_secret")
    with pytest.raises(PluginAdmissionRejected):
        PluginHostServices.from_snapshot(
            snapshot,
            route_id="wrong-route",
            method=EvidenceMethod.API_KEY,
            ports={"hash_verifier": verifier},
        )
    with pytest.raises(PluginAdmissionRejected):
        PluginHostServices.from_snapshot(
            snapshot,
            route_id="approved-route",
            method=EvidenceMethod.API_KEY,
            ports={"hash_verifier": b"raw-secret"},
        )


def test_legacy_grant_rejects_v2_identity() -> None:
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), spi_major=1)
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), group="pyauthkit.authenticators.v1")


def test_spi2_scoped_positive_revocation_and_cross_tenant(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    installed_v2(monkeypatch, tmp_path)
    approved = candidates()
    own = host_snapshot()
    verifier = HostHmacVerifier(own.bindings[0].scope_ref)

    async def scenario() -> None:
        async with activate_approved_authenticators(
            approved,
            grants=(grant(),),
            service_bindings={grant(): services(own, verifier)},
        ) as plugins:
            allow = compose_authentication_engine(
                own, authenticators=plugins, final_rule=lambda _subject, _entry: True
            )
            deny = compose_authentication_engine(
                own, authenticators=plugins, final_rule=lambda _subject, _entry: False
            )
            correct = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.API_KEY, verifier.token()),
                CorrelationId("v2-positive"),
            )
            actual = await allow.engine.authenticate(
                correct, entry=allow.catalog.resolve_for_host_route("approved-route")
            )
            assert isinstance(actual, Authenticated)
            veto = await deny.engine.authenticate(
                correct, entry=deny.catalog.resolve_for_host_route("approved-route")
            )
            assert isinstance(veto, Rejected)
            assert not hasattr(veto, "principal")

            verifier.revoked = True
            revoked = await allow.engine.authenticate(
                correct, entry=allow.catalog.resolve_for_host_route("approved-route")
            )
            assert isinstance(revoked, Rejected)
            verifier.revoked = False

            # Reusing the scoped verifier in a different host runtime must
            # refuse before invoking the host-owned verification port.
            foreign = host_snapshot("tenant-b")
            other = compose_authentication_engine(
                foreign, authenticators=plugins, final_rule=lambda _subject, _entry: True
            )
            prior_calls = verifier.calls
            wrong = await other.engine.authenticate(
                correct, entry=other.catalog.resolve_for_host_route("approved-route")
            )
            assert isinstance(wrong, AuthError)
            assert verifier.calls == prior_calls
            assert not hasattr(wrong, "principal")

    asyncio.run(scenario())


def test_spi2_mismatched_bundle_method_is_rejected_without_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    marker = installed_v2(monkeypatch, tmp_path)
    snapshot = host_snapshot()
    verifier = HostHmacVerifier(snapshot.bindings[0].scope_ref)
    bad_scope = host_snapshot("tenant-other")
    misplaced = services(bad_scope, verifier)

    # Binding scope does not itself grant access to an arbitrary host runtime.
    # It is scoped to the binding supplied in the bundle by the trusted host.
    assert misplaced.scope_ref != snapshot.bindings[0].scope_ref

    # Different *method* cannot match the exact approved method.
    # The constructor itself fails as API_KEY is the only enabled method.
    with pytest.raises(PluginAdmissionRejected):
        PluginHostServices(snapshot.bindings[0], EvidenceMethod.JWT, {"hash_verifier": verifier})

    assert not marker.exists()


def test_spi2_reserved_internal_method_rejected_before_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    marker = installed_v2(monkeypatch, tmp_path)
    approved = candidates()
    snapshot = host_snapshot()
    verifier = HostHmacVerifier(snapshot.bindings[0].scope_ref)

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="duplicate"):
            async with activate_approved_authenticators(
                approved,
                grants=(grant(),),
                service_bindings={grant(): services(snapshot, verifier)},
                reserved_methods=(EvidenceMethod.API_KEY,),
            ):
                pytest.fail("host-reserved method must never execute a plugin")

    asyncio.run(scenario())
    assert not marker.exists()
    assert "m7_spi2_fixture" not in sys.modules


def test_spi2_port_descriptor_errors_are_sanitized() -> None:
    class HostilePort:
        @property
        def verify(self) -> object:
            raise RuntimeError("private-port-secret-canary")

    snapshot = host_snapshot()
    with pytest.raises(PluginAdmissionRejected) as error:
        PluginHostServices.from_snapshot(
            snapshot,
            route_id="approved-route",
            method=EvidenceMethod.API_KEY,
            ports={"hash_verifier": HostilePort()},
        )
    assert "private-port-secret-canary" not in str(error.value)
    assert error.value.__suppress_context__


def test_spi2_hostile_ports_mapping_is_sanitized() -> None:
    from collections.abc import Iterator, Mapping

    class HostilePorts(Mapping[str, object]):
        def __iter__(self) -> Iterator[str]:
            return iter(("hash_verifier",))

        def __len__(self) -> int:
            return 1

        def __getitem__(self, key: str) -> object:
            raise RuntimeError("private-mapping-secret-canary")

        def items(self) -> object:
            raise RuntimeError("private-mapping-secret-canary")

    snapshot = host_snapshot()
    with pytest.raises(PluginAdmissionRejected) as error:
        PluginHostServices.from_snapshot(
            snapshot,
            route_id="approved-route",
            method=EvidenceMethod.API_KEY,
            ports=HostilePorts(),
        )
    assert "private-mapping-secret-canary" not in str(error.value)
    assert error.value.__suppress_context__


def test_spi2_malicious_service_binding_mapping_is_sanitized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from collections.abc import Iterator, Mapping

    marker = installed_v2(monkeypatch, tmp_path)
    approved = candidates()

    class HostileBindings(Mapping[PluginGrant, PluginHostServices]):
        def __iter__(self) -> Iterator[PluginGrant]:
            raise RuntimeError("private-binding-secret-canary")

        def __len__(self) -> int:
            return 1

        def __getitem__(self, key: PluginGrant) -> PluginHostServices:
            raise RuntimeError("private-binding-secret-canary")

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected) as error:
            async with activate_approved_authenticators(
                approved,
                grants=(grant(),),
                service_bindings=HostileBindings(),
            ):
                pytest.fail("hostile bindings cannot activate")
        assert "private-binding-secret-canary" not in str(error.value)
        assert error.value.__suppress_context__

    asyncio.run(scenario())
    assert not marker.exists()


def test_spi2_grant_rejects_missing_or_unapproved_roles() -> None:
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), port_roles=frozenset())
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), port_roles=frozenset({"unknown_role"}))
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), method=EvidenceMethod.JWT, port_roles=frozenset({"hash_verifier"}))
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), port_roles=("hash_verifier",))  # type: ignore[arg-type]


def test_legacy_grant_cannot_inject_v2_roles() -> None:
    from pyauthkit.plugins import ENTRY_POINT_GROUP

    with pytest.raises(PluginAdmissionRejected):
        PluginGrant(
            distribution="legacy-fixture",
            version="1.0.0",
            name="legacy",
            target="legacy.factory:create",
            method=EvidenceMethod.API_KEY,
            group=ENTRY_POINT_GROUP,
            spi_major=1,
            port_roles=frozenset({"hash_verifier"}),
        )


def test_spi2_rejects_port_role_incompatible_with_method() -> None:
    class Resolver:
        def resolve(self, value: object) -> object:
            return None

    with pytest.raises(PluginAdmissionRejected, match="unsupported plugin host port"):
        PluginHostServices.from_snapshot(
            host_snapshot(),
            route_id="approved-route",
            method=EvidenceMethod.API_KEY,
            ports={"key_resolver": Resolver()},
        )


def test_spi2_grant_and_host_ports_must_match_before_plugin_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    marker = installed_v2(monkeypatch, tmp_path)
    approved = candidates()
    snapshot = host_snapshot()
    verifier = HostHmacVerifier(snapshot.bindings[0].scope_ref)

    class Clock:
        def now(self) -> int:
            return 0

    ungranted = PluginHostServices.from_snapshot(
        snapshot,
        route_id="approved-route",
        method=EvidenceMethod.API_KEY,
        ports={"hash_verifier": verifier, "clock": Clock()},
    )
    overgranted = replace(grant(), port_roles=frozenset({"hash_verifier", "clock"}))

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="host services"):
            async with activate_approved_authenticators(
                approved, grants=(grant(),), service_bindings={grant(): ungranted}
            ):
                pytest.fail("extra port cannot reach plugin factory")
        assert not marker.exists()
        with pytest.raises(PluginAdmissionRejected, match="host services"):
            async with activate_approved_authenticators(
                approved,
                grants=(overgranted,),
                service_bindings={overgranted: services(snapshot, verifier)},
            ):
                pytest.fail("missing port cannot reach plugin factory")
        assert not marker.exists()

    asyncio.run(scenario())
    assert "m7_spi2_fixture" not in sys.modules
