"""M7 supply-chain qualification: pre-install digest check, not import attestation."""

import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.plugins import PluginAdmissionRejected, PluginGrant
from pyauthkit.plugins.artifacts import verify_preinstall_wheel_digest


def grant() -> PluginGrant:
    return PluginGrant(
        distribution="m7-wheel-fixture",
        version="1.0.0",
        group="pyauthkit.authenticators.v1",
        spi_major=1,
        name="synthetic",
        target="m7_wheel_fixture:create",
        method=EvidenceMethod.API_KEY,
    )


def wheel(
    tmp_path: Path,
    *,
    version: str = "1.0.0",
    target: str = "m7_wheel_fixture:create",
    raw: bool = False,
    duplicate: bool = False,
) -> tuple[Path, str]:
    archive_path = tmp_path / "m7_wheel_fixture-1.0.0-py3-none-any.whl"
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "m7_wheel_fixture-1.0.0.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: m7-wheel-fixture\nVersion: {version}\n",
        )
        archive.writestr(
            "m7_wheel_fixture-1.0.0.dist-info/entry_points.txt",
            f"[pyauthkit.authenticators.v1]\nsynthetic = {target}\n",
        )
        archive.writestr(
            "m7_wheel_fixture.py",
            "raise RuntimeError('plugin-should-never-import-during-wheel-check')\n",
        )
        if duplicate:
            archive.writestr("m7_wheel_fixture.py", "different bytes\n")
        if raw:
            archive.writestr("../outside", "unexpected\n")
    return archive_path, hashlib.sha256(archive_path.read_bytes()).hexdigest()


def test_preinstall_digest_and_metadata_without_plugin_import(tmp_path: Path) -> None:
    path, digest = wheel(tmp_path)
    verify_preinstall_wheel_digest(path, expected_sha256=digest, grant=grant())
    assert "m7_wheel_fixture" not in sys.modules


def test_wrong_host_digest_is_denied(tmp_path: Path) -> None:
    path, _ = wheel(tmp_path)
    with pytest.raises(PluginAdmissionRejected, match="digest not approved"):
        verify_preinstall_wheel_digest(path, expected_sha256="0" * 64, grant=grant())


@pytest.mark.parametrize(
    "mutation",
    ["version", "target", "duplicate", "traversal"],
)
def test_repacked_bytes_cannot_bypass_host_grant(tmp_path: Path, mutation: str) -> None:
    path, digest = wheel(
        tmp_path,
        version="9.0.0" if mutation == "version" else "1.0.0",
        target="unapproved_module:create" if mutation == "target" else "m7_wheel_fixture:create",
        duplicate=mutation == "duplicate",
        raw=mutation == "traversal",
    )
    # This recomputed test fixture digest is deliberately NOT a trusted
    # production reference; it isolates structural rejection logic.
    with pytest.raises(PluginAdmissionRejected):
        verify_preinstall_wheel_digest(path, expected_sha256=digest, grant=grant())


def test_invalid_hash_format_fails_closed(tmp_path: Path) -> None:
    path, _ = wheel(tmp_path)
    for supplied in ("", "bad", "A" * 64, "0" * 65):
        with pytest.raises(PluginAdmissionRejected):
            verify_preinstall_wheel_digest(path, expected_sha256=supplied, grant=grant())


def test_modified_wheel_fails_with_original_approved_digest(tmp_path: Path) -> None:
    path, approved = wheel(tmp_path)
    with path.open("ab") as target:
        target.write(b"post-approval-change")
    with pytest.raises(PluginAdmissionRejected, match="digest not approved"):
        verify_preinstall_wheel_digest(path, expected_sha256=approved, grant=grant())


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(PluginAdmissionRejected):
        verify_preinstall_wheel_digest(
            tmp_path / "missing.whl", expected_sha256="1" * 64, grant=grant()
        )
