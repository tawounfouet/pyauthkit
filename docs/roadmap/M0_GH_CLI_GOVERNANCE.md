# M0 governance via GitHub CLI

- **Ruleset:** `PYAUTHKIT_PROTECT_MAIN`, ID `26350656`
- **Target:** `refs/heads/main`
- **Security reporting:** GitHub Private Vulnerability Reporting
- **Script:** `scripts/gh_configure_m0_governance.sh`
- **Initial required approvals:** 0 for the solo-maintainer phase.
  This does not satisfy an independent-review requirement.

## Prerequisites

Install and authenticate the GitHub CLI (`gh`) and `jq`. The
authenticated account or token needs repository Administration write
permission for the Ruleset and private reporting endpoints.

```sh
gh auth login
gh auth status
bash scripts/gh_configure_m0_governance.sh --plan
```

The planning mode is read-only. Inspect the printed target and seven CI
contexts before applying:

```sh
bash scripts/gh_configure_m0_governance.sh --apply
```

The apply mode updates the **existing** ruleset, re-reads it,
enables private vulnerability reporting, and verifies its status.
No token or credentials are written to the repository.

Optionally set `REQUIRED_APPROVALS=1` if an independent eligible reviewer
is available. GitHub will not count the PR author's own approval.

## Sequencing

The required CI workflow exists in PR #58, not on the default branch until
PR #58 is merged. Requiring its checks on unrelated PRs before that
workflow is available on `main` can block merging. Verify the checks
on PR #58, approve the exceptions in Issue #59, and then merge in order
after the security review and chosen governance checks.

Do not declare GATE27-01 passed until checks, licensing, security reporting,
branch protection and required review evidence are attached. The
script does **not** merge PRs, close Issues or approve a security gate.
