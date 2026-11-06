"""M7 API snapshot and host-owned pure-Python quickstart behavior."""

import asyncio
import runpy
import sys
from pathlib import Path

import pytest

from pyauthkit.application.host_context import HostTrustCatalog
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.sdk import (
    AuditDeliveryPolicy,
    AuthenticationRequest,
    ConfigurationGeneration,
    ConfigurationRejected,
    ConfigurationSnapshot,
    CorrelationId,
    HostBinding,
    SourceProvenance,
    TrustedScopeRef,
    TrustProfileRef,
    compose_authentication_engine,
)


class DenialOnly:
    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(self, request: object, context: object) -> object:
        from pyauthkit.domain.outcome import RejectedOutcome

        return RejectedOutcome()


def runtime():
    scope = TrustedScopeRef("tenant-m7")
    profile = TrustProfileRef("profile-m7", "v1", scope)
    snapshot = ConfigurationSnapshot(
        schema_version=1,
        generation=ConfigurationGeneration(1),
        provenance=SourceProvenance("host", "test", "v1"),
        bindings=(HostBinding("route-m7", scope, profile, frozenset({EvidenceMethod.API_KEY})),),
        timeout_seconds=0.2,
        audit_delivery=AuditDeliveryPolicy(),
    )
    return compose_authentication_engine(snapshot, authenticators=[DenialOnly()])


def test_public_manifest_exports_only_selected_symbols() -> None:
    import pyauthkit.sdk as sdk

    assert "AuthenticationRequest" in sdk.__all__
    assert "compose_authentication_engine" in sdk.__all__
    assert not hasattr(sdk, "_compose_approved_runtime")
    assert not hasattr(sdk, "ReceiptedDecisionGateway")
    assert not hasattr(sdk, "VerifiedOutcome")


def test_importing_sdk_and_plugins_does_not_pull_optional_providers() -> None:
    import pyauthkit.plugins  # noqa: F401
    import pyauthkit.sdk  # noqa: F401

    assert not any(
        name in sys.modules
        for name in ("django", "fastapi", "boto3", "jwt", "argon2", "redis")
    )


def test_synthetic_quickstart_script_runs(capsys: pytest.CaptureFixture[str]) -> None:
    example = Path(__file__).resolve().parents[2] / "examples/m7_pure_python.py"
    runpy.run_path(str(example), run_name="__main__")
    assert "REJECTED" in capsys.readouterr().out


def test_host_controls_entry_and_foreign_catalog_fails_closed() -> None:
    approved = runtime()
    foreign = runtime()
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, b"untrusted"), CorrelationId("m7-host")
    )
    actual = asyncio.run(
        approved.engine.authenticate(
            request, entry=approved.catalog.resolve_for_host_route("route-m7")
        )
    )
    denied = asyncio.run(
        approved.engine.authenticate(
            request, entry=foreign.catalog.resolve_for_host_route("route-m7")
        )
    )
    assert isinstance(actual, Rejected)
    assert isinstance(denied, AuthError)
    assert not hasattr(denied, "principal")
    assert isinstance(approved.catalog, HostTrustCatalog)


def test_required_audit_remains_rejected_by_public_sdk() -> None:
    with pytest.raises(ConfigurationRejected):
        AuditDeliveryPolicy("required")
