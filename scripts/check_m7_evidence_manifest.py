"""Validate the static structure of M7's candidate evidence manifest.

This check DOES NOT fetch GitHub evidence or qualify security. It catches
missing/duplicate oracle entries and accidental promotion of partial oracles.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "qualification" / "M7_ORACLE_EVIDENCE_MANIFEST.md"
GATE = ROOT / "docs" / "qualification" / "GATE27-08_M7_SDK_AND_PLUGIN_DECISION.md"
T30 = ROOT / "docs" / "qualification" / "M7_T30_INDEPENDENT_REVIEW_READINESS_2026-11-07.md"
PARTIAL = {"17", "19", "24", "25", "30"}
PATTERN = re.compile(
    r"^\| M7-T(?P<id>\d{2}) \|[^|\n]+\|[^|\n]+\| "
    r"(?P<state>TESTED \(CI\)|PARTIAL \(CI\)) \|$",
    re.MULTILINE,
)


def main() -> None:
    rows = PATTERN.findall(MANIFEST.read_text(encoding="utf-8"))
    found = {number: status for number, status in rows}
    expected = {f"{i:02}" for i in range(1, 31)}
    if len(rows) != 30 or set(found) != expected:
        raise SystemExit("M7 oracle manifest is missing, duplicated, or malformed")
    for number, status in found.items():
        wanted = "PARTIAL (CI)" if number in PARTIAL else "TESTED (CI)"
        if status != wanted:
            raise SystemExit("M7 oracle status changed without an approved gate review")
    gate = GATE.read_text(encoding="utf-8")
    audit = T30.read_text(encoding="utf-8")
    if "NO-GO SECURITY" not in gate or "NO-GO SECURITY" not in audit:
        raise SystemExit("M7 gate is missing the unresolved security decision")
    if "required_approving_review_count=0" not in audit:
        raise SystemExit("M7 governance gap must remain explicit until verified remediated")
    print("M7 T30 evidence structure: 30 oracles / 25 TESTED / 5 PARTIAL / NO-GO")


if __name__ == "__main__":
    main()
