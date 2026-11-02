# GitHub work-package planning

Source of truth for proposed scope: PyAuthKit design document
`27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md`, §13-22 and §70.
The bootstrap scope is specified in document 28, §43 (PR-01).

- **M0-M9:** ten candidate milestones; GATE27-01 through GATE27-10.
- **WP27-001..WP27-053:** 53 MVP Issues, one per work package.
- **PR-01:** initial packaging, import, syntax-only scope reference,
  governance and Python-version decisions.
- **PR-02:** CI, formatting, mypy, scans, architecture fitness functions.
- **Status:** an issue/label/milestone is planning metadata, never code
  delivery, a passing test, or a security qualification.
- **Issue taxonomy:** `category:*`, `priority:P0`,
  `type:work-package`, `milestone:m*`.
- **Gates:** each milestone is closed only after evidence and review.
- **Governance:** GitHub Actions planning bootstrap creates or updates
  milestones/labels without closing work packages or merging PRs.

The Python 3.12+ minimum version remains a proposal pending ADR review.
The package contains no login, token issuing, secret checking or authorization.
