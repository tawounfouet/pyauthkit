# PyAuthKit

A modular, framework-agnostic authentication engine for the Python ecosystem.

> **State:** PR-01 bootstrap only. No password, API key or JWT verification is implemented.
> Nothing in this repository is security-qualified or production-ready.

## Documentation

- [Specification index](docs/specs/README.md) - 29 numbered design documents (00-28) and the Software Design & Learning convention.
- [Implementation roadmap](docs/specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md) - milestones M0-M9, beginning with M0 and PR-01.
- [Bootstrap plan](docs/specs/28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md) - initial implementation and qualification plan.
- [Software Design & Learning convention](docs/specs/PYAUTHKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md) - documentation and design methodology.

Authentication and authorization remain separate responsibilities. Consult the specifications for the intended scope, open decisions and test expectations.

## Scope

The planned MVP verifies *presented evidence* only within a host-approved trusted
context. Authentication does **not** imply an IAM account, authorization,
session, token issuance, or delegated rights. PyIAMKit is a distinct concern.

## PR-01: minimal Python package

The first delivery is limited to wheel/sdist packaging, import/version checks,
a syntactic scope reference, security reporting guidance, and the governance
decisions still awaiting approval.

### Setup (candidate toolchain)

Requires Python >=3.12 (proposal pending ADR review).

```shell
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src/pyauthkit
python -m build
```

Use `.venv\\Scripts\\activate` on Windows. Run wheel installation and
import in a *fresh environment* before signing off the packaging gate.

## Planning and decision records

- GitHub Issues `WP27-001` through `WP27-053` track the MVP backlog.
- M0 through M9 and exit gates GATE27-01 through GATE27-10 are **proposed**.
- The repository's `.github/workflows/bootstrap-planning.yml` is an
  idempotent synchronization job for milestones and labels.
- `docs/adr/` records undecided choices, including licensing and Python support.
- Canonical design sources: `27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md` and
  `28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md` (design corpus; to be
  imported separately, with provenance).

## Security

See [SECURITY.md](SECURITY.md). Do not open public issues containing passwords,
API keys, tokens, private keys, or personal data.

**Not a login system yet.** No `authenticate()` success path is provided.

Do not use this repository for production authentication until the relevant
security qualification gates are complete.

## License

PyAuthKit is licensed under the [MIT License](LICENSE). See `LICENSE` for the complete terms and required copyright notice.
