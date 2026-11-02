"""Secret-scan review must not mask new or changed findings."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/check_secret_scan.py"
BASELINE = {
    "docs/specs/07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md": [
        {"line_number": 1607, "type": "Secret Keyword"}
    ],
    "docs/specs/10_PYAUTHKIT_AUTHENTICATOR_AND_CREDENTIAL_MODEL.md": [
        {"line_number": 1154, "type": "Secret Keyword"},
        {"line_number": 1155, "type": "Secret Keyword"},
    ],
    "docs/specs/28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md": [
        {"line_number": 423, "type": "Secret Keyword"}
    ],
}


def invoke(tmp_path: Path, results: dict[str, object]) -> subprocess.CompletedProcess[str]:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"results": results}), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(report)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_unchanged_reviewed_spec_examples_are_recognized(tmp_path: Path) -> None:
    response = invoke(tmp_path, BASELINE)
    assert response.returncode == 0, response.stdout + response.stderr
    assert "4 scoped synthetic examples" in response.stdout


def test_new_finding_is_blocked(tmp_path: Path) -> None:
    changed: dict[str, object] = {
        **BASELINE,
        "src/pyauthkit/domain/scope.py": [{"line_number": 1, "type": "Secret Keyword"}],
    }
    response = invoke(tmp_path, changed)
    assert response.returncode == 1
    assert "UNREVIEWED" in response.stdout


def test_wrong_detector_on_reviewed_line_is_blocked(tmp_path: Path) -> None:
    changed = {
        "docs/specs/07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md": [
            {"line_number": 1607, "type": "High Entropy String"}
        ]
    }
    response = invoke(tmp_path, changed)
    assert response.returncode == 1
