# PR-03 - M1 Domain Kernel implementation and qualification

- **State:** MERGED / DOMAIN-ONLY QUALIFIED; GATE27-02 final decision in qualification document
- **Milestone:** M1 - Domain Kernel & Invariants
- **Work packages:** WP27-007..WP27-012
- **Design sources:** specs 04-09, 24, 26, roadmap 27 §14, bootstrap 28 §45
- **Teaching convention:** `docs/specs/PYAUTHKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md`
- **Feature branch:** `feat/m1-pr03-domain-kernel-invariants`
- **Gate:** GATE27-02 (no principal on non-success; no client-made success)

## Delivered model candidates

| WP | Code | Negative test oracle |
|---|---|---|
| 007 | `identity.py`, `evidence.py`, `request.py` | Claims/evidence untrusted and bounded, no implicit verified |
| 008 | `_verified.py` | No normal public constructor for VerifiedSubject |
| 009 | `result.py`, `outcome.py`, `serialization.py` | Non-success no principal; no outcome-to-success shortcut |
| 010 | `trust.py`, existing `scope.py` | No tenant/profile fallback or claim-based authority |
| 011 | `temporal.py` | Clock injected, invalid naive time refused |
| 012 | `failure.py`, `result.py` | Technical error distinct from rejection; safe diagnostics |

## Decisions and limitations

- Positive subject/outcome/result **reserved**. There is no successful
  verification flow, policy gate, or public `authenticate()` yet.
- `TrustedScopeRef` is a syntax-only name and is NOT an authority-bearing
  host binding. `TrustProfileRef` is likewise only a reference.
- `AuthenticatedPrincipal` separate type is deferred as spec 05 recommends.
- Python privacy, annotations and frozen dataclasses are not a sandbox;
  don't use them as the only trust controls.
- Hypothesis is an explicit dev-only dependency; no runtime dependency added.
- Byte content lives in Python memory and cannot be guaranteed zeroized.
- Actual host-binding and policy-gate enforcement are **future work**,
  not claims of this PR.

## Qualification plan

- [x] All required GitHub checks PASS on PR HEAD.
- [x] Ruff lint and format, strict mypy, pytest unit/security/property tests.
- [x] Architecture fitness: Domain has no Web, IAM or adapter dependency.
- [x] Wheel/sdist builds and isolated imports on 5 matrix combinations.
- [x] Secret scanning and dependency/SAST checks pass.
- [x] Domain-only trust boundary evaluated and limitations documented in GATE27-02 decision.
- [x] Map invariant tests and exact SHA/run to work-package issues.
- [x] Gate GATE27-02 signed by maintainer authorization, scoped to M1 domain modeling.
- [x] PR #66 merged normally by maintainer; no bypass observed.

**Release status:** no production authentication or PyPI distribution approved.


## Verified M1 execution (2026-11-02)

- PR #66: https://github.com/tawounfouet/pyauthkit/pull/66 (MERGED)
- PR tested SHA: `3c992d8e70f7861c2d69c2ffc3307f7499ecb649`
- PR CI: https://github.com/tawounfouet/pyauthkit/actions/runs/41425128544 (7/7 and GitGuardian PASS)
- Protected `main` SHA: `9823bef47137b7837717c4a754031d5ca39326d4`
- Post-merge CI: https://github.com/tawounfouet/pyauthkit/actions/runs/41434368832 (7/7 PASS)
- 58 unit/architecture/security/property tests PASS, Ruff, mypy strict, 5 isolated wheel smoke environments, pip-audit, Bandit, scoped detect-secrets PASS.
- Supplemental macOS Apple Silicon / Python 3.14.5 local PASS from maintainer (not a dedicated isolated qualification).
- Formal qualification: `docs/qualification/GATE27-02_M1_DOMAIN_KERNEL_DECISION.md`.

**Constraint:** no production authenticator, no valid positive final decision, no host trust resolver, no publication. Python constructor blocking is a design guard, not runtime authorization.
