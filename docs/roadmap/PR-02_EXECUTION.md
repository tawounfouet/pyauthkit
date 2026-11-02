# PR-02 execution and qualification record

- **State:** MERGED / TECHNICAL QUALIFICATION PASS FOR M0
- **Scope:** WP27-004, WP27-005, WP27-006; WP28-008..011
- **Milestone gate:** GATE27-01
- **Merge PR:** https://github.com/tawounfouet/pyauthkit/pull/58
- **Qualified main SHA:** `df13c212865e8bd824ef36e1e0c369e56e63cb15`
- **Evidence:** https://github.com/tawounfouet/pyauthkit/actions/runs/41414657347

## Executed checks (Q28-01..08)

| Gate | Observed result | Evidence / limitation |
|---|---|---|
| Q28-01 | PASS | Ruff lint/format under CI |
| Q28-02 | PASS | mypy strict scope, 3 source files |
| Q28-03 | PASS | 14 pytest tests on each matrix combination |
| Q28-04 | PASS | Wheel and sdist built; SHA-256 recorded in issue #62 |
| Q28-05 | PASS | Isolated wheel import on five matrix combinations |
| Q28-06 | PASS IN M0 SCOPE | pip-audit, Bandit and scoped secret scans; #59 approved |
| Q28-07 | PASS IN M0 SCOPE | Architecture and workflow permission guards |
| Q28-08 | EXCEPTION DOCUMENTED | Solo maintainer, no independent PR approval, ADR-0005 |

The baseline does **not** claim cross-platform bitwise reproducibility or
full OS/Python support. Reproducible release requirements: issue #63.
Independent security reviewer before release: issue #64.

## Ruleset enforcement evidence

Negative PR #61:
https://github.com/tawounfouet/pyauthkit/pull/61

An intentionally failing test caused required checks to fail. GitHub
returned `mergeable_state=blocked`. This PR was closed unmerged; protected
`main` was unchanged. See the linked negative CI evidence in issue #62.

## Limits

- Build and security checks prove bootstrap health, not cryptographic security.
- Runtime has no live Password, API Key or JWT verifier.
- No production release/publish operation is authorized by this qualification.

**PR-02 qualification:** accepted for M0 only, subject to the separate final
gate decision and future release security gates.
