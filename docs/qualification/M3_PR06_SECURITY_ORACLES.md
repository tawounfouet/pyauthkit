# PyAuthKit M3 - Qualification matrix M3-T01 to M3-T40

- Date: 2026-11-02
- Source of truth: uploaded `2026-11-02_PYAUTHKIT_M3_PASSWORD_AUTHENTICATION_IMPLEMENTATION_PLAN.md` section 13.
- Candidate: [PR #75](https://github.com/tawounfouet/pyauthkit/pull/75), DRAFT.
- Gate: [GATE27-04 #74](https://github.com/tawounfouet/pyauthkit/issues/74), OPEN.
- Qualification state: **NOT QUALIFIED**.
- `NOT_RUN` means the individual oracle was not independently signed off, even if a related pytest function passed. Automated CI results are kept in the PR execution record. Each oracle needs explicit observed result, SHA, platform, run link and reviewer before being marked PASS.

| Oracle | Scenario | Independent expected outcome | Existing or missing evidence candidate | Qualified status |
|---|---|---|---|---|
| M3-T01 | Mot de passe correct, ACTIVE, décision finale ALLOW | AUTHENTICATED, sujet du record, une vérification KDF | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T02 | Secret correct, décision finale DENY | REJECTED malgré match crypto | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T03 | Mot de passe incorrect | REJECTED sans VerifiedOutcome | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T04 | Compte absent | REJECTED sans fuite du statut | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T05 | SUSPENDED/DISABLED | REJECTED sans succès | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T06 | REVOKED | REJECTED sans succès | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T07 | Expiré, frontière temporelle | REJECTED, vérification UTC | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T08 | Résolution ambiguë | REJECTED, aucun choix arbitraire | `tests/contract/test_m3_password_resolver_contract.py` | NOT_RUN |
| M3-T09 | Store indisponible | AuthError, aucun fallback | `PENDING` | NOT_RUN |
| M3-T10 | Hash corrompu | Aucun succès ni exception brute | `tests/integration/test_m3_password_engine.py` | NOT_RUN |
| M3-T11 | Argon2i/Argon2d | Refus avant KDF | `tests/crypto/test_m3_argon2id.py` | NOT_RUN |
| M3-T12 | PHC m/t/p supérieur aux limites | Refus avant KDF | `tests/crypto/test_m3_argon2id.py` | NOT_RUN |
| M3-T13 | PHC faible/version interdite | Refus sans downgrade | `tests/crypto/test_m3_argon2id.py` | NOT_RUN |
| M3-T14 | Vecteurs crypto Argon2id indépendants | Vecteurs reproductibles, corruption | `PARTIAL: generated with same library` | NOT_RUN |
| M3-T15 | Cross-tenant subject/credential | Jamais AUTHENTICATED pour autre tenant | `tests/security/test_m3_password_adversarial.py` | NOT_RUN |
| M3-T16 | claimed_tenant non approuvé | Rejet avant KDF | `tests/security/test_m3_password_adversarial.py` | NOT_RUN |
| M3-T17 | Route absente/contexte étranger | Pas de lookup/KDF | `M2 tests, M3-specific proof PENDING` | NOT_RUN |
| M3-T18 | Tentative de falsification VerifiedOutcome | Refus du policy gate | `M2 adversarial tests` | NOT_RUN |
| M3-T19 | Retour Authenticated par adaptateur | Moteur refuse | `M2 adversarial tests` | NOT_RUN |
| M3-T20 | Annulation pendant KDF | Aucun succès, capacité réservée | `tests/security/test_m3_kdf_capacity.py` | NOT_RUN |
| M3-T21 | Timeout pendant KDF | Pas de succès tardif | `M2 timeout tests + M3 PENDING` | NOT_RUN |
| M3-T22 | 100+ clients concurrents | Concurrence/mémoire bornées | `PENDING: load test` | NOT_RUN |
| M3-T23 | Guard absent ou indisponible | Bootstrap/admission fail-closed | `tests/security/test_m3_password_guard_and_revocation.py` | NOT_RUN |
| M3-T24 | Guard multi-tenant/multi-source | Compteurs et isolation de chaque tenant | `PENDING: host adapter` | NOT_RUN |
| M3-T25 | Tous refus publics | Codes/messages équivalents | `PARTIAL: outcomes; host HTTP PENDING` | NOT_RUN |
| M3-T26 | Analyse statistique des timings | Rapport d'énumération et limites | `PENDING: benchmark` | NOT_RUN |
| M3-T27 | Secret canary en exceptions/log/audit | Absence de secret exposé | `PARTIAL: repr tests` | NOT_RUN |
| M3-T28 | Hash ou login brut dans audit | Aucune fuite en event/audit | `PENDING: dedicated audit test` | NOT_RUN |
| M3-T29 | Registry sans PASSWORD | Aucun auto-enregistrement | `M2 registry tests` | NOT_RUN |
| M3-T30 | Wheel sans extra password | Import M2 sans Argon2 obligatoire | `scripts/smoke_wheel.py` | NOT_RUN |
| M3-T31 | Wheel avec extra, cinq plateformes | Argon2id réel dans wheel isolé | `scripts/smoke_wheel.py + CI matrix` | NOT_RUN |
| M3-T32 | needs_rehash true | Pas d'écriture pendant authenticate | `PARTIAL: readonly API` | NOT_RUN |
| M3-T33 | Révocation pendant KDF | Revalidation et refus | `tests/security/test_m3_password_guard_and_revocation.py` | NOT_RUN |
| M3-T34 | Identifiant/secret mal formés ou énormes | Validation bornée avant KDF | `M1/M2 validation, M3 PENDING` | NOT_RUN |
| M3-T35 | Octets Unicode, espaces, normalisation | Aucune transformation implicite | `PENDING: dedicated tests` | NOT_RUN |
| M3-T36 | Non-régression M1/M2 | 104 tests antérieurs inchangés et verts | `CI pytest tests; baseline count review` | NOT_RUN |
| M3-T37 | Deux implémentations de resolver | Contract tests identiques | `tests/contract/test_m3_password_resolver_contract.py` | NOT_RUN |
| M3-T38 | p50/p95/p99 KDF et RSS | Benchmark consigné | `PENDING: bench` | NOT_RUN |
| M3-T39 | Fault injection fermeture workers | Arrêt sans fuite non bornée | `PENDING: shutdown faults` | NOT_RUN |
| M3-T40 | Legacy needs_rehash | Lecture seule ou CAS qualifié | `PENDING: legacy policy` | NOT_RUN |

## Interpretation

The test-column entries are **candidate traceability**, NOT per-oracle certification. In particular, a dummy KDF only reduces simple username-enumeration differences; it does not establish constant-time transport behavior. The in-memory resolver's `is_current` callback cannot establish distributed revocation freshness. Per-process semaphore slots do not prove global brute-force rate limiting. The library cannot attest the semantics of an arbitrary host-supplied `PasswordAttemptGuard`.

The five wheel jobs must install both core without optional crypto and the native `[password]` extra in separate isolated environments and execute an Argon2id verification. Performance, denial-of-service, timing, external store consistency and mandatory durable audit remain distinct deployment decisions.

## Gate decision

`GATE27-04 = OPEN / NO GO FOR RELEASE` until all 40 scenarios have an explicit adjudication, P0 evidence requirements hold, ADRs are reviewed, security reviewer signoff is recorded and current HEAD plus post-merge CI evidence exists. No release, deployment or merge authorization is given here.
