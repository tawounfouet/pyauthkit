"""Execute the reviewed M7 capability guide directly against installed PyAuthKit."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "guides" / "m7-capability-contract.md"
MARKER = "M7 capability guide: EXPLICIT HOST ROLES / DENY ONLY"


def main() -> None:
    contents = GUIDE.read_text(encoding="utf-8")
    blocks = re.findall(r"^```python\n(.*?)^```$", contents, re.DOTALL | re.MULTILINE)
    if len(blocks) != 1:
        raise SystemExit("M7 capability guide must contain one executable block")
    try:
        result = subprocess.run(
            [sys.executable, "-c", blocks[0]],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise SystemExit("M7 capability guide execution failed") from None
    if MARKER not in result.stdout:
        raise SystemExit("M7 capability guide output mismatch")
    print(MARKER)


if __name__ == "__main__":
    main()
