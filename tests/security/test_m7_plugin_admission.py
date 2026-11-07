"""M7 plugin discovery/admission negative security contract tests.

Synthetic distribution metadata is installed under tmp_path. Its plugin module
must not be imported until the host grant passes all metadata preflights.
"""

import asyncio
import sys
from dataclasses import replace
from importlib.metadata import distributions
from pathlib import Path

import pytest

from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.plugins import (
    PluginAdmissionRejected,
    PluginGrant,
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


def installed_plugin(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    spi_major: int = 1,
    mode: str = "deny",
) -> tuple[object, Path]:
    site = tmp_path / "m7-site"
    site.mkdir()
    marker = tmp_path / "plugin-imported.txt"
    # This code is test-only and intentionally has an observable import effect.
    plugin = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('imported')\n"
        "import asyncio\n"
        "from pyauthkit.domain.evidence import EvidenceMethod\n"
        "from pyauthkit.domain.outcome import RejectedOutcome\n"
        "class Verifier:\n"
        "    @property\n"
        "    def method(self): return EvidenceMethod.API_KEY\n"
        "    async def verify(self, request, context):\n"
        + (
            "        raise RuntimeError('private-canary-value')\n"
            if mode == "raise"
            else "        await asyncio.sleep(1)\n        return RejectedOutcome()\n"
            if mode == "timeout"
            else "        return object()\n"
            if mode == "invalid"
            else "        return RejectedOutcome()\n"
        )
        + "def create(): return Verifier()\n"
        + f"create.SPI_MAJOR = {spi_major}\n"
    )
    (site / "m7_fixture_plugin.py").write_text(plugin, encoding="utf-8")
    dist_info = site / "m7_approved_plugin-1.0.0.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: M7.Approved_Plugin\nVersion: 1.0.0\n", encoding="utf-8"
    )
    (dist_info / "entry_points.txt").write_text(
        "[pyauthkit.authenticators.v1]\nsynthetic = m7_fixture_plugin:create\n",
        encoding="utf-8",
    )
    package = next(iter(distributions(path=[str(site)])))
    points = tuple(package.entry_points)
    assert len(points) == 1
    monkeypatch.syspath_prepend(str(site))
    monkeypatch.setattr(discovery, "entry_points", lambda **_kwargs: points)
    sys.modules.pop("m7_fixture_plugin", None)
    return points[0], marker


def grant() -> PluginGrant:
    return PluginGrant(
        distribution="m7-approved-plugin",
        version="1.0.0",
        name="synthetic",
        target="m7_fixture_plugin:create",
        method=EvidenceMethod.API_KEY,
    )


def snapshot() -> ConfigurationSnapshot:
    scope = TrustedScopeRef("m7-tenant")
    profile = TrustProfileRef("m7-profile", "v1", scope)
    return ConfigurationSnapshot(
        schema_version=1,
        generation=ConfigurationGeneration(1),
        provenance=SourceProvenance("host", "test", "v1"),
        bindings=(HostBinding("api", scope, profile, frozenset({EvidenceMethod.API_KEY})),),
        timeout_seconds=0.02,
        audit_delivery=AuditDeliveryPolicy(),
    )


def authenticate(plugins: tuple[object, ...]) -> object:
    runtime = compose_authentication_engine(snapshot(), authenticators=plugins)
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"private-canary-value"),
        CorrelationId("m7-plugin"),
    )
    return asyncio.run(
        runtime.engine.authenticate(request, entry=runtime.catalog.resolve_for_host_route("api"))
    )


def test_discovery_disabled_makes_no_metadata_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(**_kwargs: object) -> None:
        raise AssertionError("discovery must be disabled by default")

    monkeypatch.setattr(discovery, "entry_points", forbidden)
    assert discover_authenticator_plugins() == ()


def test_discovery_only_inspects_metadata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    assert len(candidates) == 1
    assert candidates[0].distribution == "m7-approved-plugin"
    assert "m7_fixture_plugin" not in sys.modules
    assert not (tmp_path / "plugin-imported.txt").exists()
    assert "private" not in repr(candidates[0])


def test_unapproved_plugin_is_not_loaded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    assert load_approved_authenticators(candidates, grants=[]) == ()
    assert not marker.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("distribution", "attacker-package"),
        ("version", "2.0.0"),
        ("target", "other_module:entry"),
    ],
)
def test_metadata_mismatch_fails_before_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, field: str, value: str
) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    with pytest.raises(PluginAdmissionRejected):
        load_approved_authenticators(candidates, grants=[replace(grant(), **{field: value})])
    assert not marker.exists()


def test_missing_grant_does_not_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    with pytest.raises(PluginAdmissionRejected):
        load_approved_authenticators([], grants=[grant()])
    assert not marker.exists()


def test_duplicate_entry_points_refused_without_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    point, marker = installed_plugin(monkeypatch, tmp_path)
    monkeypatch.setattr(discovery, "entry_points", lambda **_kwargs: (point, point))
    with pytest.raises(PluginAdmissionRejected, match="ambiguous"):
        discover_authenticator_plugins(enabled=True)
    assert not marker.exists()


def test_approved_plugin_uses_existing_engine_and_returns_denial(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    loaded = load_approved_authenticators(candidates, grants=[grant()])
    assert marker.exists()
    assert len(loaded) == 1
    assert isinstance(authenticate(loaded), Rejected)


@pytest.mark.parametrize("mode", ["raise", "invalid", "timeout"])
def test_third_party_failure_cannot_authenticate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
) -> None:
    installed_plugin(monkeypatch, tmp_path, mode=mode)
    candidates = discover_authenticator_plugins(enabled=True)
    loaded = load_approved_authenticators(candidates, grants=[grant()])
    outcome = authenticate(loaded)
    assert isinstance(outcome, AuthError)
    assert not hasattr(outcome, "principal")
    assert "private-canary-value" not in repr(outcome)


def test_spi_mismatch_fails_without_registration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    installed_plugin(monkeypatch, tmp_path, spi_major=2)
    candidates = discover_authenticator_plugins(enabled=True)
    with pytest.raises(PluginAdmissionRejected, match="activation rejected"):
        load_approved_authenticators(candidates, grants=[grant()])


def test_duplicate_method_grants_prevent_any_load(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    with pytest.raises(PluginAdmissionRejected):
        load_approved_authenticators(candidates, grants=[grant(), grant()])
    assert not marker.exists()


def test_grant_validation_rejects_unknown_method() -> None:
    with pytest.raises(PluginAdmissionRejected):
        replace(grant(), method="unlisted-method")  # type: ignore[arg-type]


def test_reserved_builtin_method_rejects_v1_before_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    with pytest.raises(PluginAdmissionRejected, match="duplicate") as err:
        load_approved_authenticators(
            candidates, grants=[grant()], reserved_methods=(EvidenceMethod.API_KEY,)
        )
    assert "private-canary-value" not in str(err.value)
    assert "m7_fixture_plugin" not in sys.modules
    assert not marker.exists()


def test_unknown_reserved_method_is_sanitized_and_does_not_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    with pytest.raises(PluginAdmissionRejected, match="reserved") as err:
        load_approved_authenticators(
            candidates,
            grants=[grant()],
            reserved_methods=["private-canary-method"],  # type: ignore[list-item]
        )
    assert "private-canary-method" not in str(err.value)
    assert not marker.exists()


def test_different_reserved_method_does_not_block_v1_plugin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    loaded = load_approved_authenticators(
        candidates, grants=[grant()], reserved_methods=(EvidenceMethod.JWT,)
    )
    assert len(loaded) == 1
    assert marker.exists()


def test_entry_point_changed_after_batch_preflight_never_imports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from pyauthkit.plugins import admission

    point, marker = installed_plugin(monkeypatch, tmp_path)
    candidates = discover_authenticator_plugins(enabled=True)
    original_preflight = admission._preflight_candidates
    metadata = (
        tmp_path / "m7-site" / "m7_approved_plugin-1.0.0.dist-info" / "METADATA"
    )

    def modified_after_preflight(*args: object, **kwargs: object) -> object:
        selected = original_preflight(*args, **kwargs)  # type: ignore[arg-type]
        # EntryPoint.value is immutable. Mutate the underlying *distribution*
        # metadata instead, which importlib.metadata reads on each access.
        metadata.write_text(
            "Metadata-Version: 2.1\nName: M7.Approved_Plugin\nVersion: 2.0.0\n",
            encoding="utf-8",
        )
        return selected

    monkeypatch.setattr(admission, "_preflight_candidates", modified_after_preflight)
    with pytest.raises(PluginAdmissionRejected, match="activation rejected") as error:
        load_approved_authenticators(candidates, grants=(grant(),))
    assert point.dist.version == "2.0.0"
    assert error.value.__suppress_context__
    assert not marker.exists()
    assert "m7_fixture_plugin" not in sys.modules


def test_distribution_metadata_alone_does_not_attest_import_origin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Document the known import-origin gap in a bounded subprocess.

    The child resolves a shadow module via sys.path, even though the installed
    entry-point metadata matches an exact host grant. This is a threat
    reproducer, NOT evidence of a secured origin. Isolating the child prevents
    module-cache pollution and limits third-party import side effects.
    """
    import subprocess

    _, original_marker = installed_plugin(monkeypatch, tmp_path)
    site = tmp_path / "m7-site"
    shadow = tmp_path / "shadowing-site"
    shadow.mkdir()
    shadow_marker = tmp_path / "SHADOW_MODULE_EXECUTED"
    (shadow / "m7_fixture_plugin.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(shadow_marker)!r}).write_text('shadow loaded')\n"
        "from pyauthkit.domain.evidence import EvidenceMethod\n"
        "from pyauthkit.domain.outcome import RejectedOutcome\n"
        "class ShadowVerifier:\n"
        "    @property\n"
        "    def method(self): return EvidenceMethod.API_KEY\n"
        "    async def verify(self, request, context): return RejectedOutcome()\n"
        "def create(): return ShadowVerifier()\n"
        "create.SPI_MAJOR = 1\n",
        encoding="utf-8",
    )

    # Child Python has no stale sys.modules entry; only the host-controlled
    # ephemeral test paths determine the module loaded by EntryPoint.load().
    child = f"""
import sys
from importlib.metadata import distributions
sys.path.insert(0, {str(shadow)!r})
sys.path.insert(1, {str(site)!r})
from pyauthkit.plugins import PluginGrant, load_approved_authenticators
from pyauthkit.plugins.discovery import _candidate_for
from pyauthkit.domain.evidence import EvidenceMethod
points = tuple(next(iter(distributions(path=[{str(site)!r}]))).entry_points)
assert len(points) == 1
candidate = _candidate_for(points[0])
assert candidate.target == "m7_fixture_plugin:create"
grant = PluginGrant(
    distribution="m7-approved-plugin",
    version="1.0.0",
    name="synthetic",
    target="m7_fixture_plugin:create",
    method=EvidenceMethod.API_KEY,
)
loaded = load_approved_authenticators((candidate,), grants=(grant,))
assert len(loaded) == 1
assert type(loaded[0]).__name__ == "ShadowVerifier"
"""
    completed = subprocess.run(
        [sys.executable, "-c", child],
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-800:]
    assert shadow_marker.exists()
    assert not original_marker.exists()
