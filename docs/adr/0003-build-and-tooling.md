# ADR-0003: Bootstrap build and test toolchain

- **Status:** PROPOSED / NOT QUALIFIED
- **Related work:** WP27-002, WP27-004; PR-01 and PR-02
- **Source:** bootstrap 28 ADR28-005, ADR28-006, ADR28-010

## Proposal

Use PEP 517 with Hatchling for building a minimal src-layout package.
Use venv/pip for the initial bootstrap. Use pytest in importlib mode.
Ruff and mypy are candidates; CI qualification is intentionally deferred
to PR-02.

No framework, data store, cryptographic verifier, or PyIAMKit dependency is
imported by this package at PR-01. No positive authentication demonstration is
shipped.

## Acceptance

Install wheel in fresh venv, import outside checkout, run tests, build wheel
and sdist; inspect package content and record tool versions and hashes.
