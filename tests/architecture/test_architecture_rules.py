"""Negative architecture tests prove the guard detects representative violations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
CHECK = PROJECT / "scripts/check_architecture.py"


def run_check(tmp_path: Path, module: str) -> subprocess.CompletedProcess[str]:
    source = tmp_path / "src/pyauthkit/domain"
    source.mkdir(parents=True)
    (source / "misuse.py").write_text(module, encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(CHECK),
            "--src",
            str(tmp_path / "src/pyauthkit"),
            "--project",
            str(PROJECT / "pyproject.toml"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_domain_django_import_is_rejected(tmp_path: Path) -> None:
    result = run_check(tmp_path, "import django\n")
    assert result.returncode == 1
    assert "forbidden external import django" in result.stdout


def test_domain_application_dependency_is_rejected(tmp_path: Path) -> None:
    result = run_check(tmp_path, "from pyauthkit.application import engine\n")
    assert result.returncode == 1
    assert "forbidden domain -> pyauthkit.application" in result.stdout


def test_pure_domain_module_passes(tmp_path: Path) -> None:
    result = run_check(tmp_path, "from dataclasses import dataclass\n")
    assert result.returncode == 0, result.stdout + result.stderr
