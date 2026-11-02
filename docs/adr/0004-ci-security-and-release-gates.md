# ADR-0004: CI, supply chain and security gate for M0

- **Status:** ACCEPTED FOR M0 BOOTSTRAP WITH EXPLICIT RESIDUAL RISKS
- **Decision date:** 2026-11-02
- **Decision authority:** PyAuthKit maintainer (@tawounfouet)
- **Scope:** PR #58, WP27-004..006, GATE27-01, Q28-01..08
- **Sources:** 20, 26, roadmap 27 §54-56, bootstrap 28 §35-44 and §76

## Security boundary

The repository is a **non-production authentication-library bootstrap**.
No Password verifier, API Key verifier, JWT validation, positive auth success
path, or release to an artifact registry is covered by this decision. A green
CI cannot replace cryptographic protocol qualification or a threat-model review.

## Accepted safeguards

1. `pull_request` and `push: main` GitHub Actions workflows with
   `permissions: contents: read` and no OIDC token minting/release secrets.
2. SHA-pinned `actions/checkout` and `actions/setup-python`, plus
   `persist-credentials: false`. Explicit workflow structural policy guard.
3. Ruff lint/format, strict mypy, pytest, and AST architecture fitness checks.
   Negative architecture regression tests check representative illegal imports.
4. Wheel/sdist metadata and clean-`venv` wheel import smoke in the five
   combinations defined in ADR-0002.
5. `pip-audit` for third-party dev/security packages, Bandit on runtime
   source, and `detect-secrets` over the tracked repository snapshot.
   Source examples are never blanket-excluded.
6. Four pedagogical or prohibited-pattern detector findings are specifically
   reviewed and fingerprint-bound (path, line, detector, SHA-256), not ignored
   wholesale. Maintainer approval and closure: issue #59.
7. `PYAUTHKIT_PROTECT_MAIN` GitHub Ruleset (#26350656), active for
   `refs/heads/main`, with seven named required checks, strict up-to-date,
   no force-push, no deletion, PR required, conversation resolution required,
   and no bypass actors.

## Evidence

**Positive evidence:**
- `main` SHA: `df13c212865e8bd824ef36e1e0c369e56e63cb15`
- https://github.com/tawounfouet/pyauthkit/actions/runs/41414657347
- **SUCCESS: 7/7 jobs**, including Python tests, build and security scans.

**Negative enforcement evidence:**
- PR #61: https://github.com/tawounfouet/pyauthkit/pull/61
- Run: https://github.com/tawounfouet/pyauthkit/actions/runs/41415139807
- Deliberately failing assertion caused a required quality check and all five
  required packaging checks to fail. GitHub reported
  `mergeable_state=blocked`. PR #61 was **closed without merging**.
- This demonstrates blocked mergeability in the GitHub UI/API, not a separate
  adversarial attempt to execute an actual forbidden merge.

## Governance and residual risk

- The repository is operated by a solo maintainer: required approvals remain
  **0**. GitHub CODEOWNERS does not establish independent review.
- This is a **temporary accepted M0 governance exception**, not a security
  sign-off. See ADR-0005 and issue #64. Independent review and
  nonzero required approvals must be established **before GATE27-09
  and production distribution**.
- Build tools are version-ranged, and bit-for-bit reproducibility across
  operating systems is not demonstrated. See ADR-0003 and issue #63.
- A zero-finding scanner run does not prove absence of security issues.
- Current checks do not qualify future authentication protocols or
  untrusted third-party plugins.

## M0 gate policy

For the M0 bootstrap, the owner may accept the defined governance exception
only after the seven CI jobs succeed, the four secret-scan examples are
formally reviewed, Ruleset enforcement has a negative proof, MIT licensing
and private reporting are in place, and the residual risks are assigned
to tracked issues. All these technical prerequisites have evidence in #62.

**Decision:** ACCEPTED with explicitly limited M0 scope. Release gates
remain independent and **NO published auth engine is authorized**.
