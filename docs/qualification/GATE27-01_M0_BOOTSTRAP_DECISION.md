# GATE27-01 - M0 Bootstrap Qualification Decision

- **Decision date:** 2026-11-02
- **Decision owner:** @tawounfouet (PyAuthKit repository maintainer)
- **Prepared from:** owner instruction to finalize M0 ADR and governance
- **Decision:** **GO - M0 BOOTSTRAP ONLY**, effective after merge of the
  supporting ADRs and successful checks for the merged commit on `main`.
- **Related:** issue #62, WP27-001..006, ADR-0001..0005
- **Not a release approval:** no PyPI publication or authentication
  implementation is authorized by this decision.

## Exit gate basis

`docs/specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md` §13 defines GATE27-01
in terms of dependency-free imports, installable wheel, PR CI execution,
discoverable artifacts, no unreviewed secrets, and decisions on support
matrix, license, OS compatibility and release process. Qualification gates
Q28-01..08 are defined in bootstrap 28 §42.

## Qualified baseline prior to this decision PR

- `main` SHA: `df13c212865e8bd824ef36e1e0c369e56e63cb15`
- Merged run: https://github.com/tawounfouet/pyauthkit/actions/runs/41414657347
- Seven CI jobs: SUCCESS.
- Five wheel/sdist smoke environments: Ubuntu Py3.12/3.13/3.14, macOS
  Py3.12 and Windows Py3.12. Fourteen tests passed per combination.
- MIT LICENSE and SPDX `license = "MIT"`; private vulnerability reporting.
- Ruleset #26350656 protected `main` with seven mandatory status checks,
  no bypass and no force-push.
- Strictly scoped synthetic secret examples were reviewed by the maintainer
  in issue #59.
- Failed PR https://github.com/tawounfouet/pyauthkit/pull/61 demonstrated
  required check failures and blocked mergeability; it was closed unmerged.

## Work packages to close when the supporting decision is merged

| WP | Technical outcome | Decision / evidence |
|---|---|---|
| WP27-001 | MIT, Security Policy and Ruleset | ADR-0001 and ADR-0005 |
| WP27-002 | Wheel/sdist import in fresh venv | ADR-0003, main CI |
| WP27-003 | Explicit tested Python/OS combinations | ADR-0002 |
| WP27-004 | Ruff, mypy, pytest, architecture | ADR-0003 and ADR-0004 |
| WP27-005 | Read-only CI with protected main | ADR-0004, negative PR #61 |
| WP27-006 | Dependency, SAST, secret scanning | ADR-0004, approved #59 |

## Formal risk acceptance for limited M0

The owner accepts these risks **only for non-production bootstrap**:

1. **No independent PR reviewer currently enforced**. Required approval
   count is 0. Compensating checks and ruleset apply, but this is not
   equivalent to independent review. ADR-0005 and issue #64 require a
   reviewer before GATE27-09 and any production publication.
2. **Cross-OS artifact hash divergence and non-locked tools**. Tested wheels
   install and import successfully, but builds are not demonstrated to be
   bitwise reproducible. ADR-0003 and issue #63 require resolution before
   GATE27-09 and publication.
3. **M0 has no verified authentication mechanism**. Password, API Key, JWT,
   scope trust and policy outcomes remain subject to their own milestones
   and qualification gates. There is no permission to expose a success path
   as a production API.

## Authorized next milestone

After the supporting ADR PR merges and its main CI is successful, M0 may
be marked **GO/CLOSED** for the *Bootstrap* scope only, permitting
**M1 - Domain Kernel** under the same mandatory CI and branch rules.
Issue #62 records the final decision and merge SHA.

No acceptance of M0 waives M8 security qualification or M9 release approval.

**Signed as a project decision:** maintainer's explicit authorization to
finalize M0, recorded in the issue after successful main CI. This file
alone is not evidence that the merge has already occurred.
