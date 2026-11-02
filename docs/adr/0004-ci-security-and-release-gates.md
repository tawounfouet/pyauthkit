# ADR-0004: CI, supply-chain and M0 exit policy

- **Status:** PROPOSED / subject to evidence and maintainer approval
- **Scope:** PR-02, WP27-004..006, GATE27-01 and Q28-01..08
- **Sources:** design documents 20, 26, 27 §54-56, 28 §35-44 and §76

## Threats and constraints

A PR may change source, tests or tools. CI must not grant release secrets,
OIDC token minting or write permissions for that code. Tests passing on an
editable install do not demonstrate what ships in a wheel. Build and security
scans also need their own evidence.

## Candidate controls

- GitHub workflow `pull_request` plus `push: main` and manual dispatch.
- Workflow `permissions: contents: read` with no release secrets or OIDC.
- `actions/checkout` v4.3.0 SHA
  `08eba0b27e820071cde6df949e0beb9ba4906955`, and
  `actions/setup-python` v6.0.0 SHA
  `e797f83bcb11b83ae66e0230d6156d7c80228e7c`, verified against GitHub
  tag refs on 2026-11-02. Review their updates before rotation.
- Ruff, mypy, pytest and architecture rule tests on Python 3.12.
- Candidate wheel matrix: Linux 3.12/3.13/3.14, macOS 3.12,
  Windows 3.12. This is **not** the full OS x Python cross product.
- Build both wheel and sdist and run an isolated wheel import with no extras.
- Run dependency audit of isolated dev+security tooling, Bandit on runtime
  source, and detect-secrets over checked-in files. Review false positives,
  never assume a scanner replaces protocol-specific negative test vectors.
- Scan scripts are structural tools only. Neither SAST nor AST checks establish
  absence of exploitable authentication vulnerabilities.
- `CODEOWNERS` requests maintainer ownership; enforcement requires branch
  protection or rulesets configured outside this PR.

## Explicit gaps

- Dependency version constraints remain ranges; lock/constraints policy
  `ADR28-007` remains OPEN. A passing CI run does not prove fully reproducible
  dependency resolution over time.
- Secret scanning is checked against the current repository snapshot only.
  Security reporting channel and SPDX license remain OPEN in ADR-0001.
- `main` required checks and code-owner approval need GitHub Ruleset
  configuration and read-back verification by an admin.
- A CI failure or inconclusive scan is NOT a valid security gate PASS.
- The intentionally failing PR and broken-domain-import test should be
  demonstrated on a disposable branch/PR before closing GATE27-01.

## Acceptance evidence

Each report must identify Git SHA, Python/OS, tool versions and CI URL. M0
can be closed only after the protected check policy, build artifacts,
cross-environment smoke, security scans and open risk/ADR review are recorded.
