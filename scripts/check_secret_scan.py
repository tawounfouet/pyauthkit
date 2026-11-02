"""Fail the gate if detect-secrets reports unchecked findings."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/check_secret_scan.py PATH")
        return 2
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    findings = report.get("results", {})
    count = sum(len(values) for values in findings.values())
    print(f"detect-secrets findings: {count} across {len(findings)} files")
    if count:
        for name, values in sorted(findings.items()):
            print(f"Potential secret in {name}: {len(values)} finding(s)")
            for finding in values:
                print(
                    f"  line={finding.get('line_number', '?')} detector={finding.get('type', 'unknown')}"
                )
        print("Review findings; do not bypass this gate without security approval.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
