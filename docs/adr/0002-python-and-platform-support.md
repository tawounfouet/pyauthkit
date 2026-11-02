# ADR-0002: Python and OS compatibility targets

- **Status:** ACCEPTED FOR M0 BOOTSTRAP (limited qualification)
- **Decision date:** 2026-11-02
- **Decision authority:** PyAuthKit maintainer (@tawounfouet)
- **Related:** WP27-003, GATE27-01, PR #58, issue #62
- **Source:** roadmap 27 §13, §70; bootstrap 28 ADR28-003/004

## Context

The bootstrap Python support boundary must be evidence-based. A wheel
installation smoke test is not verification of every Python, operating system,
processor architecture, or future cryptographic backend combination.

## Accepted decision

1. Maintain `requires-python = ">=3.12"` in `pyproject.toml`.
   This is the **minimum interpreter constraint**, not a guarantee that every
   future interpreter or OS is qualified.
2. **M0-tested combinations** are exactly:
   - Ubuntu GitHub-hosted runner, CPython 3.12
   - Ubuntu GitHub-hosted runner, CPython 3.13
   - Ubuntu GitHub-hosted runner, CPython 3.14
   - macOS GitHub-hosted runner, CPython 3.12
   - Windows GitHub-hosted runner, CPython 3.12
3. Python 3.15 and the remaining Linux/macOS/Windows x CPython cross-products
   are **not qualified** by M0. Other distributions, architectures, PyPy, and
   FIPS builds are also outside the verified matrix.
4. No mandatory runtime dependency is shipped in M0. Dependency
   compatibility for future password/JWT crypto libraries remains
   **undecided** and requires its own verification at later milestones.

## Observed evidence

- Tested main SHA: `df13c212865e8bd824ef36e1e0c369e56e63cb15`
- CI run: https://github.com/tawounfouet/pyauthkit/actions/runs/41414657347
- All five wheel/sdist builds, package metadata checks, 14 tests per entry
  and isolated wheel imports **PASSED**.
- `pyauthkit` imports without Web, IAM or framework-specific runtime packages.
- Exact binary reproducibility is not demonstrated: Windows artifact digests
  differ from Linux/macOS, tracked in issue #63.

## Consequences

The readme and release documentation must distinguish M0-tested combinations
from contractual platform support. For later auth mechanisms, extend the CI
matrix only after selecting and verifying their real dependencies. Do not
claim blanket support across untested combinations.

**Decision:** ACCEPTED for M0 limited bootstrap, not authentication release
qualification. Issue #63 blocks claiming release-grade reproducibility.
