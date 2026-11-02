# PR-03 - M1 Domain Kernel implementation and qualification

- **State:** IMPLEMENTING / PR checks and GATE27-02 review required
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

- [ ] All required GitHub checks PASS on PR HEAD.
- [ ] Ruff lint and format, strict mypy, pytest unit/security/property tests.
- [ ] Architecture fitness: Domain has no Web, IAM or adapter dependency.
- [ ] Wheel/sdist builds and isolated imports on 5 matrix combinations.
- [ ] Secret scanning and dependency/SAST checks pass.
- [ ] Reviewer evaluates trust boundary and reserved-positive semantics.
- [ ] Map invariant tests and exact SHA/run to work-package issues.
- [ ] Gate GATE27-02 separately signed after review and merged-main CI.
- [ ] PR intentionally remains open and unmerged until approval.

**Release status:** no production authentication or PyPI distribution approved.
