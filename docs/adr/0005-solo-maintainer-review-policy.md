# ADR-0005: Solo-maintainer review exception for M0-M7

- **Status:** ACCEPTED AS A TEMPORARY RISK EXCEPTION (non-production only)
- **Decision date:** 2026-11-02
- **Decision owner:** @tawounfouet
- **Related:** WP27-001/005, GATE27-01, ADR-0004, issue #64
- **Expiry:** Before GATE27-09 (M8) and any release/publishing operation

## Context

PyAuthKit currently has one maintainer/owner. `CODEOWNERS` names that
owner, who cannot independently approve their own Pull Requests.
Requiring one approving review without another eligible reviewer could
make progression impossible. Disabling all checks would be unsafe.

## Accepted temporary decision

Maintain `required_approving_review_count = 0` on the main Ruleset for
pre-release bootstrap development, but keep:

- PR-required flow, protected `main` and no bypass actors.
- Seven mandatory checks and strict branch freshness before merges.
- Source/CI security scanners, negative tests and traceable gate decisions.
- Manual documented security review for sensitive exceptions.
- Separate milestone-specific threat-model and test-oracle requirements.

**This is not an independent approval policy.** The maintainer can merge
their own compliant PRs. The absence of an external reviewer is an explicit
residual risk, with @tawounfouet as risk owner.

## Compensating measures

- Prevent direct modification of protected `main` and required-check bypass.
- Preserve CI evidence for each merged PR and each gate.
- Document meaningful architecture/security decisions as accepted ADRs.
- Require an explicit issue/decision record whenever a security exception
  is needed (e.g. #59), without making automated green checks equal sign-off.

## Expiry and remediation

Before GATE27-09 or any production release, **issue #64 must be resolved**:

1. Invite an independent reviewer with permission to review PRs.
2. Review and revise CODEOWNERS if necessary.
3. Enable at least one required approving review and, where feasible,
   require code-owner review for sensitive paths.
4. Prove an unapproved PR cannot merge and a properly approved PR can.
5. Require separate review of changes to cryptographic authentication,
   secret handling, trust boundaries and release controls.

Until then, do not claim independent review or release-qualified security.

## Alternatives considered

- One required approval with only one maintainer: unworkable.
- Bypass required checks for the owner: rejected.
- Temporary zero approvals plus mandatory checks and explicit risk:
  **accepted for bootstrap only**.

**Decision:** ACCEPTED, time-bounded by milestone scope, issue #64 open.
