> **ATTENTION - ARCHIVE HISTORIQUE SUPERSEDEE.** La signification des identifiants
> M4-T01..T40 / G5-01..16 dans ce fichier n'est pas alignée avec le
> plan détaillé M4 du 05/11/2026. **NE PAS UTILISER POUR UNE DECISION.**
> Matrice fidèle à la source : `docs/qualification/M4_2026_11_05_SOURCE_MATRIX.md`.
> Catalogue réconcilié : `docs/qualification/M4_CANDIDATE_ORACLE_CATALOG_V2.md`.
> Les anciens chiffres/états ci-dessous décrivent uniquement les étapes historiques.
>
# GATE27-05 - M4 API Key Authentication decision record

- Date: 2026-11-05
- Milestone: M4 / PR-07
- **Verdict: NO-GO (NOT FORMALLY ADJUDICATED)**
- Branch: `feat/m4-api-key-authentication-pr07`
- PR: https://github.com/tawounfouet/pyauthkit/pull/76 (draft)
- M2 base: `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`
- Technical checkpoint: `d4a2346de60d7f9ca05409dac4b18a6a65eca5c4`
- CI evidence: https://github.com/tawounfouet/pyauthkit/actions/runs/42052986729 (7/7, 207 pytest PASS in quality job)
- Formal reviewer: **NONE RECORDED**
- ADR-0016, ADR-0017, ADR-0018: **PROPOSED**, not accepted
- Related: `docs/qualification/M4_PR07_SECURITY_ORACLES.md`, `docs/roadmap/PR-07_EXECUTION.md`

## Demonstrated candidate capabilities

PR-07A/B/C introduce scoped lookup, typed record outcomes, canonical
70-byte `ak1` parsing, full 32-byte-secret HMAC-SHA-256 comparison,
scope-approved protection keys, a mandatory host attempt guard, UTC
status/expiry checks, a source-freshness recheck and the M2
`AuthenticationPolicyGate` decision. The code remains a **candidate**:
valid HMAC and positive internal outcome never authorize IAM actions.

## Entry blockers / unfinished work

- [ ] WP27-026 / PR-07D: real, source-scoped PostgreSQL verifier store and
      versioned revoke/rotate CAS tests (including cross-process race).
- [ ] Deployment-appropriate Redis quota guard, trusted proxy provenance,
      401/503 refusal semantics, anti-enumeration timing samples and budgets.
- [ ] Full candidate 40-oracle mapping confirmed against canonical plan and
      **independently adjudicated** with environment, SHA, artifacts and signoff.
- [ ] Threat/risk review of bearer replay, leaked key, algorithm/key ref
      rotation, remote key source, revocation lag and operational DoS.
- [ ] Security/owner approval of ADR-0016/0017/0018, especially the proposed
      `expires_at` required rule and missing-selector timing behavior.
- [ ] Per-criterion G5-01..G5-16 evidence and formal gate decision.
- [ ] Clarify merge sequencing with M3 PR #75 (GATE27-04 formal NO-GO).

## Candidate G5 criteria - proposed tracker, not an adopted acceptance record

| Criterion | Gate evidence required | Status |
|---|---|---|
| G5-01 | Architecture scope and M2 authority unchanged | PENDING REVIEW |
| G5-02 | Immutable scoped record, ownership and contract review | PENDING REVIEW |
| G5-03 | 70-byte canonical parsing and public selector | TECHNICAL TEST ONLY |
| G5-04 | Full-secret HMAC and anti-downgrade | TECHNICAL TEST ONLY |
| G5-05 | Approval, rotation and key-source error semantics | PENDING HOST |
| G5-06 | Status, expiry and clock validation | TECHNICAL TEST ONLY |
| G5-07 | Authoritative revocation/version CAS guarantee | PENDING HOST |
| G5-08 | M2 explicit policy, no shadow Authenticated | TECHNICAL TEST ONLY |
| G5-09 | Distributed abuse control, peer provenance | PENDING HOST |
| G5-10 | Tenant isolation at persistence source | PENDING HOST |
| G5-11 | Audit and telemetry privacy, operational contracts | PENDING HOST |
| G5-12 | Concurrency, crash/retry and overload behavior | PENDING HOST |
| G5-13 | 40 independently adjudicated M4 oracles | PENDING REVIEW |
| G5-14 | All CI/test/build/security checks on exact SHA | TECHNICAL CI ONLY |
| G5-15 | Independent crypto/security review and ADR owner signoff | PENDING REVIEW |
| G5-16 | Explicit owner GO/NO-GO and residual risks | **NO-GO** |

**These criterion descriptions are candidate gate tracking language derived
from the visible implementation plan; confirm against the actual G5 register
before marking them accepted.**

## Current decision and prohibition

NO-GO / NOT ADJUDICATED means **do not merge, publish, deploy or describe M4 as
production-secure.** A draft PR and 7/7 CI are insufficient. Post-GO merging
and post-merge main CI are distinct subsequent actions, not performed here.

## Reference-host implementation checkpoint (candidate, not gate approval)

A PR-07D reference harness now proposes SQL-scoped records and CAS,
Redis distributed quotas, HTTP refusals, post-proof revocation tests
and two separate OS processes. These are **proposed technical tests**,
not signed evidence until corresponding exact-SHA CI logs are linked.

No production deployment profile, trusted-proxy policy, independent
security reviewer, ADR approvals or residual-risk acceptance is
established by including test code. **Formal verdict remains NO-GO.**

## Verified PR-07D reference-host CI evidence, without gate promotion

- Candidate reference-host SHA: `0738fb740630a3aba45dc4c98466feb6d2e30b7e`.
- CI: https://github.com/tawounfouet/pyauthkit/actions/runs/42059926314
  **8/8 SUCCESS**, 207 default pytest PASS and 12 isolated
  PostgreSQL/Redis/HTTP qualification tests PASS.
- Demonstrates PostgreSQL source-scope queries and atomic revoke/rotate CAS
  within a disposable schema; cross-process Redis quota; loopback HTTP
  denial equivalence by status/body/selected headers; tested outages and
  post-HMAC revoke before freshness check.
- Does not establish linearizable revocation after the final check,
  generalizable anti-enumeration, production peer/proxy/TLS,
  real KMS-secret lifecycles, operational SIEM/audit durability,
  real deployment SLOs or independent security signoff.
- G5-07, G5-09, G5-10, G5-12 now have reference-lab technical evidence;
  their full host/production policies and independent reviews remain
  pending. No signed G5-01..16 or accepted ADR is implied.

**GATE27-05 remains NO-GO / NOT FORMALLY ADJUDICATED.**
