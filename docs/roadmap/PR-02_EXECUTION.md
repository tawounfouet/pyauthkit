# PR-02 execution and qualification record

**State:** IMPLEMENTATION PROPOSED / CI evidence pending.
**Scope:** `WP27-004`, `WP27-005`, `WP27-006`; `WP28-008..011`.
**Target gate:** `GATE27-01`, with Q28-01..08.

## New checks

1. `ruff check .` and `ruff format --check .`.
2. `mypy src/pyauthkit` and `pytest -v`.
3. `scripts/check_architecture.py` plus negative regression tests.
4. `scripts/check_workflow_security.py` for SHA-pinned `uses` and
   nonprivileged PR execution.
5. Wheel/sdist build, artifact hashes, and clean `venv` import.
6. `pip-audit`, Bandit and `detect-secrets`.

## Evidence and remaining DoD

- [ ] Every CI job passes on PR commit.
- [ ] Negative regression tests show architectural rule failures.
- [ ] Deliberately failing disposable PR demonstrates required-check
      enforcement (not just workflow failure).
- [ ] Repository rules require PR, reviewed code owner, and CI checks.
- [ ] Wheel/sdist hashes and tested Python/OS versions recorded.
- [ ] Dependency lock and unsupported Python/OS variants recorded in ADR.
- [ ] License SPDX and private disclosure channel decisions closed.
- [ ] GATE27-01 reviewed and recorded as GO or NO-GO.

No publication is authorized by this PR. No authentication mechanism is
implemented or qualified.
