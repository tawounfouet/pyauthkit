# ADR-0003: Bootstrap build and test toolchain

- **Status:** ACCEPTED FOR M0 BOOTSTRAP
- **Decision date:** 2026-11-02
- **Decision authority:** PyAuthKit maintainer (@tawounfouet)
- **Related:** WP27-002, WP27-004; GATE27-01; issue #62
- **Source:** bootstrap 28 ADR28-005/006/010; roadmap 27 §13

## Decision

Use the following initial packaging and validation tools:

| Concern | Accepted M0 approach | Boundary |
|---|---|---|
| Distribution | PEP 517 with Hatchling, `src/pyauthkit` layout | No release publishing |
| Build artifacts | wheel and sdist via `python -m build` | Not promised bit-for-bit reproducible |
| Environment | Python `venv`, `pip` | Developer bootstrap only |
| Tests | `pytest` with `--import-mode=importlib`, strict markers | Unit and basic architecture tests |
| Lint and format | Ruff checks from `pyproject.toml` | Design Markdown files not autoformatted |
| Type checking | strict mypy on `src/pyauthkit` | Limited current package surface |
| Artifact smoke | `scripts/smoke_wheel.py`, isolated environment | Tested exact five-entry matrix |
| Packaging metadata | `twine check dist/*` | Not a proof of secure publication |

## Evidence accepted

- All seven CI jobs PASS on the protected `main` SHA
  `df13c212865e8bd824ef36e1e0c369e56e63cb15`:
  https://github.com/tawounfouet/pyauthkit/actions/runs/41414657347
- Packaging jobs build a wheel and sdist, then install the wheel into an
  isolated fresh `venv` and import the installed package outside the checkout.
- Fourteen tests pass per evaluated environment. Domain and workflow
  architecture guards also pass.
- Runtime dependencies remain empty in M0; none of the cryptographic
  authenticators has been implemented or qualified.

## Reproducibility limitation and accepted risk

Hatchling and developer tool dependency specifications use version ranges,
not a fully frozen dependency graph. Windows artifact SHA-256 values differ
from those produced on the tested Ubuntu/macOS runners even though both
sets pass package installation smoke tests.

This is **not accepted for release-grade artifact provenance**. For M0
bootstrap only, the maintainer accepts the documented limitation: do not
publish artifacts or claim deterministic cross-platform builds.

**Release-blocking follow-up:** issue #63; define a reference builder, record
the build dependency graph, and investigate cross-platform archive differences
before GATE27-09 and any M9 publishing.

## Supersession

This ADR is accepted for M0 but must be revisited when crypto dependencies
or externally distributed stable SDKs are introduced.

**Decision:** ACCEPTED for the initial non-production toolchain.
