# ADR-0001: Licensing and security governance

- **Status:** PARTIALLY ACCEPTED - MIT licensing selected; security reporting remains OPEN
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

## Decision B: vulnerability disclosure - OPEN

The preferred channel is **GitHub Private Vulnerability Reporting**.

- Activation is performed by a repository administrator through GitHub
  settings or the explicit `gh api --method PUT` admin operation.
- The active state must be verified via the repository API.
- Only after verification should `SECURITY.md` state that the private
  reporting channel is enabled.
- Avoid publishing real secrets or vulnerability details in public Issues.
- Response-time SLA and supported-version policy remain undecided.

## GATE27-01 remaining evidence

- [x] Maintainer's MIT selection recorded in this ADR (requires PR merge
      for the decision file and LICENSE to reach main)
- [ ] MIT LICENSE, package metadata and README merged and verified on main
- [ ] Private vulnerability reporting enabled and verified
- [ ] Security policy updated to reflect verified channel state
- [ ] Main Ruleset targeting main with required CI checks read back
- [ ] WP27-001 and other M0 lots qualified against the exit criteria

**Note:** Security governance remains OPEN, even when the MIT decision
is accepted. This ADR is therefore not a blanket security sign-off.
