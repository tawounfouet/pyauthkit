"""Review detect-secrets output with exact, documented demonstration-line exceptions.

Only findings with matching file, line, detector and SHA-256 of the full source
line are acknowledged. Changes or new findings continue to fail closed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# These examples are documented in docs/security/SECRET_SCAN_TRIAGE.md.
# A maintainer must review the scoped exceptions before merging PR-02.
REVIEWED_EXAMPLES = {
    (
        "docs/specs/07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md",
        1607,
        "Secret Keyword",
    ): "47f08a5ebb2ea8a4a704819e7fa506cade84456593cc26ce82691fa92a4c631d",
    (
        "docs/specs/10_PYAUTHKIT_AUTHENTICATOR_AND_CREDENTIAL_MODEL.md",
        1154,
        "Secret Keyword",
    ): "3d3d7056eead814a05d60f978d9929b02ae31876df3264da8a9ca3fb29920373",
    (
        "docs/specs/10_PYAUTHKIT_AUTHENTICATOR_AND_CREDENTIAL_MODEL.md",
        1155,
        "Secret Keyword",
    ): "f8de390d58af8b1a6ebe4c24a54e56c8bfb82aae9e694f776053d68aca254fb8",
    (
        "docs/specs/28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md",
        423,
        "Secret Keyword",
    ): "b2a2793bea726d2e5a203d7576e79c5df7105082d545b7be738d4230df7107a5"
}


def is_reviewed_example(path: str, finding: dict[str, object], root: Path = ROOT) -> bool:
    """Accept only exact unchanged synthetic examples under source control."""
    line_number = finding.get("line_number")
    detector = finding.get("type")
    if not isinstance(line_number, int) or not isinstance(detector, str):
        return False
    expected = REVIEWED_EXAMPLES.get((path, line_number, detector))
    if expected is None:
        return False
    file_path = root / path
    if not file_path.is_file():
        return False
    lines = file_path.read_text(encoding="utf-8").splitlines()
    if line_number < 1 or line_number > len(lines):
        return False
    digest = hashlib.sha256(lines[line_number - 1].encode("utf-8")).hexdigest()
    return digest == expected


def evaluate(report: dict[str, object], root: Path = ROOT) -> tuple[int, int]:
    """Return (accepted examples, unreviewed findings), without printing raw values."""
    accepted = 0
    unreviewed = 0
    results = report.get("results", {})
    if not isinstance(results, dict):
        raise ValueError("invalid detect-secrets report")
    for path, values in results.items():
        if not isinstance(path, str) or not isinstance(values, list):
            raise ValueError("invalid detect-secrets result entry")
        for finding in values:
            if not isinstance(finding, dict):
                raise ValueError("invalid detect-secrets finding")
            line = finding.get("line_number", "?")
            detector = finding.get("type", "unknown")
            if is_reviewed_example(path, finding, root):
                accepted += 1
                print(f"REVIEWED DEMO: {path}:{line} ({detector}; exact-line SHA matched)")
            else:
                unreviewed += 1
                print(f"UNREVIEWED: {path}:{line} ({detector})")
    return accepted, unreviewed


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/check_secret_scan.py PATH")
        return 2
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    try:
        accepted, unreviewed = evaluate(report)
    except (ValueError, OSError) as exc:
        print(f"Invalid scan or source: {exc}")
        return 2
    print(f"Secret scan result: {accepted} scoped synthetic examples, {unreviewed} unreviewed")
    if unreviewed:
        print("SECURITY NO-GO: a newly detected or changed secret candidate needs review.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
