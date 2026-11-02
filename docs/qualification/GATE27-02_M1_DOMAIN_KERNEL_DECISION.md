# GATE27-02 - M1 Domain Kernel & Invariants: formal decision

- **Decision:** GO - DOMAIN MODEL ONLY
- **Date:** 2026-11-02
- **Decision authority:** Repository maintainer @tawounfouet, who requested formal closure and entry into M2
- **Scope:** WP27-007 through WP27-012, no runtime authentication proof
- **Implementation:** https://github.com/tawounfouet/pyauthkit/pull/66 (MERGED)
- **Gate issue:** https://github.com/tawounfouet/pyauthkit/issues/67
- **Source:** roadmap 27 section 14 and bootstrap 28 section 45, plus Software Design & Learning Convention

## Reviewed qualified baseline

| Source | Observed result |
|---|---|
| Protected main | `9823bef47137b7837717c4a754031d5ca39326d4` |
| CI on merged main | https://github.com/tawounfouet/pyauthkit/actions/runs/41434368832 - SUCCESS, 7/7 |
| PR CI | https://github.com/tawounfouet/pyauthkit/actions/runs/41425128544 - 7/7 plus GitGuardian SUCCESS |
| Automated tests | 58 PASS on PR and merged main across the configured test and build jobs |
| Strict type checking | 13 source files, no mypy errors |
| Lint and architecture | Ruff lint/format and import-boundary fitness PASS |
| Platform packaging | Ubuntu Py3.12/13/14, macOS Py3.12, Windows Py3.12 - isolated wheel import PASS |
| Supply-chain checks | pip-audit, Bandit, scoped detect-secrets PASS; no unreviewed secrets |
| Additional local confirmation | macOS Apple Silicon Python 3.14.5: Ruff/mypy/58 tests PASS; unisolated environment |

## Traceability to GATE27-02

1. **Untrusted input is not a subject** - ClaimedIdentity, PresentedEvidence and AuthenticationRequest convey caller input, not authority. Payload size is bounded, and representations are redacted. Tests cover invalid input and serialization.
2. **No non-success principal** - Rejected, AuthError and ChallengeRequired do not include a principal, are falsey and can be serialized with explicit safe allowlists. No generic `success=True` carrier exists.
3. **Cross-scope isolation** - ScopedSubjectRef identifies subject + issuer + scope, avoiding conflation across tenants. TrustProfileRef and ScopeProfileRef only enforce structural consistency; they are not trusted host authorization.
4. **Positive-path transition guarded** - VerifiedSubject, VerifiedOutcome and Authenticated cannot be instantiated through normal public constructors. normalize_non_success maps only negative AuthenticatorOutcome variants and raises on unknown/verified outcomes. **No conversion to a final positive decision exists in M1.**
5. **Time and failure semantics** - CorrelationId validates bounded trace format; ObservedAt normalizes an injected, aware clock to UTC. TechnicalErrorCode is separate from generic RejectionCode and excludes raw exception details.
6. **Domain isolation** - Domain imports remain independent from Web, IAM, persistence, adapters and plugins.
7. **Pedagogical trace** - `docs/learning/M1_DOMAIN_KERNEL_DESIGN_LEARNING_CARD.md` explains DDD Value Objects, Result Object, fail-closed design, rejected overengineered universal principal, and required trust boundary.

## Review and risk decision

The code and tests were examined against the M1 exit requirements and their limits. The maintainer's express instruction to close M1 is recorded as the project-level acceptance decision. This **does not** represent a second independent human reviewer or a completed cryptographic security audit. GitHub currently requires zero approving reviews under the temporary bootstrap governance exception ADR-0005 / issue #64.

Three boundaries remain non-negotiable for M2:

- **Host authority:** a syntactically valid `TrustedScopeRef` or `TrustProfileRef` does not imply trusted provenance. A host-owned binding must be established; client-controlled tenant or token claims cannot choose an approved profile.
- **Positive minting:** Python privacy, `__new__` guards, frozen data and type hints cannot defend against arbitrary privileged local code. PR-04/05 must design the provenance-carrying verifier and non-bypassable application-level policy gate, with negative tests. No final positive authentication object can be considered secure at this gate.
- **Release restrictions:** Password/API Key/JWT validation and cryptography have not been implemented or tested. No SDK success path, production authorization claims or public package release is approved.

The pre-existing M8 blockers #63 (build reproducibility) and #64 (independent review) remain open. The trusted-host/policy architecture decision must be made and checked in PR-04 before positive outcomes are allowed.

## Gate decision and permitted next step

**GATE27-02 = GO FOR M1 DOMAIN MODEL ONLY.** The six work packages may be closed as implementation-complete after this decision file is merged and the protected-main CI returns SUCCESS. The milestone M1 can then be closed administratively; M2 - Authentication Engine & Ports may start with **PR-04 (Trusted Host Context + AuthenticationPolicyGate)**.

No engine, authenticator or production security gate is qualified by this M1 GO.
