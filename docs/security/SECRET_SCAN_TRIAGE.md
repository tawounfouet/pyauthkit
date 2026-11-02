# PyAuthKit M0 secret scan triage

- **Status:** APPROVED BY MAINTAINER (scoped exceptions only)
- **Review issue:** https://github.com/tawounfouet/pyauthkit/issues/59
- **Approval comment:** https://github.com/tawounfouet/pyauthkit/issues/59#issuecomment-6572710153
- **CI run on qualified main:** https://github.com/tawounfouet/pyauthkit/actions/runs/41414657347
- **Scope:** four `Secret Keyword` detections in design examples under `docs/specs`.

| Spec and line | Interpretation | Approved disposition |
|---|---|---|
| 07, line 1607 | Intentionally incorrect synthetic password in negative test | Scoped allowlist |
| 10, line 1154 | `PASSWORD` enum identifier | Scoped allowlist |
| 10, line 1155 | `API_KEY` enum identifier | Scoped allowlist |
| 28, line 423 | Anti-pattern presented explicitly as forbidden | Scoped allowlist |

The GitHub reviewer classified these as synthetic educational examples, **not
production credentials**. The exceptions are matched by exact path, line
number, detector type, and full-line SHA-256. Changes or additions to the
examples will fail the script, with no raw values printed in logs.

**Security limitations:** Manual review is not a credential history scan or
an external audit. Do not claim that no undiscovered secret exists. Follow the
private vulnerability reporting procedure in `SECURITY.md`.

## Evidence and qualification

- [x] Maintainer approved four exact exceptions in issue #59.
- [x] Issue #59 closed, with a permanent comment and scope.
- [x] Main branch detect-secrets check passed within the CI security job.
- [x] New/changed finding regression cases added in
      `tests/security/test_secret_scan_review.py`.
- [x] No blanket exclusion of `docs/specs` from secret scanning.

**Disposition:** closed for M0; future findings need a fresh, scoped review.
