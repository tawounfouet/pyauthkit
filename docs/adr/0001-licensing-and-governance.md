# ADR-0001: Licensing and security governance

- **Status:** ACCEPTED for MIT licensing and Private Vulnerability Reporting activation; broader security qualification remains OPEN
- **Decision date:** 2026-11-02
- **Decision owner:** repository maintainer (@tawounfouet)
- **Related work:** WP27-001 (M0), GATE27-01
- **Source:** roadmap 27 §13, §70; bootstrap 28 ADR28-002

## Context

PyAuthKit is a public Python authentication library intended for reuse in
applications, including commercial applications. The project needs an explicit
license. Public GitHub visibility alone is not a grant of reuse rights.

Because this project concerns authentication, vulnerability disclosure and
security qualification must be independently governed; choosing a license
does not demonstrate any security property.

## Decision A: MIT licensing - ACCEPTED

The maintainer selected the **MIT License** on 2026-11-02.

- Full terms: repository root `LICENSE`
- Package metadata: `[project].license = "MIT"` in `pyproject.toml`
- Copyright notice: 2026 Thomas AWOUNFOUET
- Distribution model: permissive reuse, modification and commercial
  distribution, subject to preserving the copyright and license notices.

### Considered alternatives

1. MIT (selected): short permissive license and broad reuse.
2. Apache-2.0 (not selected): adds an explicit patent grant and additional
   notice-related provisions.
3. Other licenses (deferred): unnecessarily complicate the initial governance.

### Consequences

- Preserve MIT terms with copies/substantial portions of the Software.
- Review license compatibility of future dependencies and third-party code.
- This decision does not authorize publication of the unqualified auth engine.

## Decision B: private vulnerability disclosure - ACCEPTED

The maintainer ran `scripts/gh_configure_m0_governance.sh --apply` on
2026-11-02 and provided the CLI result
`Private vulnerability reporting enabled and verified.`

- Reporting channel: **GitHub Private Vulnerability Reporting**.
- `SECURITY.md` documents the private reporting workflow.
- No public disclosure of live secrets or exploit details is permitted.
- Response-time SLA, supported release versions and incident-runbook
  maturity are **not** approved by this decision.

## Decision C: default-branch Ruleset - VERIFIED

The Ruleset `PYAUTHKIT_PROTECT_MAIN` (ID `26350656`) is active and
targets `refs/heads/main`. A fresh GitHub repository read confirmed the
branch is protected, the bypass list is empty and seven named status
checks are required. The required review count is **0** for the current
solo-maintainer phase, which does not constitute independent review.

A successful ruleset readback proves configuration, not that a failing PR
has been experimentally blocked. That gate evidence remains outstanding.


## GATE27-01 remaining evidence

- [x] Maintainer's MIT selection recorded in this ADR (requires PR merge
      for the decision file and LICENSE to reach main)
- [ ] MIT LICENSE, package metadata and README merged and verified on main
- [x] Private vulnerability reporting enabled and verified by maintainer CLI
- [x] Security policy updated in PR #60 (pending merge to main)
- [x] Main Ruleset targeting main with seven required CI checks read back
- [ ] WP27-001 and other M0 lots qualified against the exit criteria

**Note:** These decisions do not close GATE27-01. Independent review (if required),
CI enforcement experiments, Issue #59 adjudication, PR merges and full M0
qualification remain open.
