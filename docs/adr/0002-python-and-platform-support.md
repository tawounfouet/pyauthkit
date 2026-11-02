# ADR-0002: Python and OS compatibility targets

- **Status:** PROPOSED / NOT QUALIFIED
- **Related work:** WP27-003, M0; PR-01 and PR-02
- **Source:** roadmap 27 §13, §70; bootstrap 28 ADR28-003 and ADR28-004

## Problem and boundary

A `requires-python` field is a compatibility promise only when supported by
tests on relevant Python/OS combinations and all required dependencies.

## Candidate decision

- Minimum interpreter: Python 3.12 (candidate).
- Qualification matrix to evaluate: Python 3.12, 3.13, 3.14.
- Target platforms to evaluate: Linux, macOS and Windows.
- Python 3.15: explicitly out of the initial confirmed matrix.
- Initial runtime dependencies: none. Crypto dependencies are post-PR-01.

The matrix is a hypothesis, not proof of support. PR-02 must add appropriate
CI jobs, wheel smoke tests and evidence before advertising official support.

## Acceptance

- Toolchain compatibility and upstream crypto library support reviewed.
- CI matrix passed, with linked runs, environment/version and tested wheel.
- Exceptions/unsupported combinations documented.
