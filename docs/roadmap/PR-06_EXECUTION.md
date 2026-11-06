# PR-06 Execution - M3 Password Authentication

- Date: 2026-11-02
- Milestone: M3 (#4), WP27-019..022 / WP28-029..044
- Branch: `feat/m3-password-authentication-pr06`
- Pull request: [#75](https://github.com/tawounfouet/pyauthkit/pull/75), **READY FOR INDEPENDENT SECURITY REVIEW, NOT MERGED**
- Gate: [GATE27-04 #74](https://github.com/tawounfouet/pyauthkit/issues/74), **OPEN / NO GO**
- Entry M2 SHA: `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`

## Work completed in the candidate branch

| Slice | Contents | Evidence |
|---|---|---|
| PR-06A | Scoped record/resolver contracts, in-memory and callback adapters, contract tests, ADR-0010 | `e38ca483` |
| PR-06B | Argon2id-only PHC verifier, parameter bounds, worker capacity and optional `password` extra, ADR-0011/0012 | `a8cb29eb` |
| PR-06C | PasswordAuthenticator using M2 SPI, final gate, negative integration tests, audit and redaction | `625511ce` |
| Hardening | Ruff, mypy and synthetic-secret remediation | `39cb90bd`, `5fb1727f`, `ac35bb30` |
| Security | Mandatory host attempt guard, revocation/guard negative tests and ADR-0013 | `6b91b811`, `ada059c7` |

## Qualification notes

The intermediate candidate `ac35bb30d9bbb23990c2ec4434dd32c9110e9603`
reached **7/7 successful CI jobs** at [GitHub Actions run 41510028088](https://github.com/tawounfouet/pyauthkit/actions/runs/41510028088). This predates the mandatory attempt guard; **do not use the intermediate green check to qualify later code**.

The final PR requires a new green run on its CURRENT head, complete M3-T01..T40 evidence, ADR review and explicit GATE27-04 sign-off.

## Out of scope

No main merge, PyPI publication, production deployment, IAM authorization,
credential lifecycle mutations, MFA or session/token issuance. The in-memory
store and the dummy-hash technique do not establish distributed revocation,
online anti-enumeration timing guarantees or global rate limits.

## Qualification technique complémentaire - 2026-11-03

- Baseline code testé : `126fd2eb3e0858ce18218a78b8adf02c46a94937`.
- CI [#41607548865](https://github.com/tawounfouet/pyauthkit/actions/runs/41607548865) : 7/7 SUCCESS, 160 pytest PASS, Ruff, mypy strict, architecture et scans PASS, cinq plateformes wheel avec et sans crypto.
- Ajouts : vecteur Argon2id public, 120 vérifications concurrentes, timeout sans succès tardif, shutdown borné, expiration UTC, Unicode, rehash lecture seule, révocation post-KDF simulée, deux tenants réels, store différé, audit canary et codes génériques.
- Benchmark CI (18 échantillons par scénario) : p50 correct 21.724 ms, incorrect 21.601 ms, absent 21.634 ms; RSS max 66 180 KiB sur GitHub Linux. **Aucune garantie de timing constant ou de production.**
- Dossier formel : `docs/qualification/GATE27-04_M3_PASSWORD_AUTHENTICATION_DECISION.md` = **NO-GO** tant que T24/T25/T26 host, ADRs, risques et revue indépendante non soldés.
- Ne pas fusionner ou publier sans sign-off ni post-merge main CI.

## Qualification banc réel de référence - 2026-11-05

- Code `2c6ea7173b44ce314c61f680b436d493c994de3c`, CI [42031794016](https://github.com/tawounfouet/pyauthkit/actions/runs/42031794016) : 7/7 SUCCESS; 160 tests source + 9 tests host; cinq plateformes wheel.
- Infrastructure isolée `qualification/host` : FastAPI + PostgreSQL 16.6 + Redis 7.4; résolution SQL scoped, Argon2id et policy M2.
- T24 : 2 instances FastAPI, **2 processus Uvicorn OS** utilisant une même clé HMAC et Redis, 64 admissions concurrentes et anti-spoof XFF, tests PASS.
- T25 : réponses de refus uniformes sur véritable TCP HTTP/1.1 local, tests PASS.
- T26 : 60 mesures par groupe, 500 permutations et 500 bootstraps; plancher 100 ms. Delta médian wrong/missing -0.063 ms, marge CI 5% satisfaite; **p-value 0.0279** : effet statistiquement détectable, aucune promesse de non-énumération en production.
- Pannes PostgreSQL/Redis => 503; révocation PostgreSQL au milieu de la KDF => refus.
- Le scanner de secrets inclut les fixtures; Bandit inclut `qualification/host`; deps facultatives incluses au pip-audit CI.
- ADR technical review `docs/qualification/M3_SECURITY_AND_ADR_REVIEW_2026-11-05.md`; **aucune approbation indépendante**, risques non signés.
- **NO-GO GATE27-04** jusqu'à la validation formelle; aucune fusion ni release.

## Revue de sortie technique - 2026-11-05

- HEAD dossier `08eecce6913a7a12cd928cf5be0e8ae89ccc818c`, [CI 42032506665](https://github.com/tawounfouet/pyauthkit/actions/runs/42032506665) **7/7 SUCCESS**. Les éléments du dossier sont disponibles dans `qualification/host` et `docs/qualification`.
- La PR #75 a été mise **READY FOR REVIEW**, mais ni la PR ni `main` n'ont été fusionnés. L'issue #64 demande une **revue indépendante humaine** et la protection associée.
- T24 / T25 sont couverts par le banc de référence, T26 reste limité par une différence parfois statistiquement détectable. Sans propriétaire des risques ni déploiement cible, aucune garantie universelle anti-énumération n'est établie.
- **GATE27-04 #74 reste NO-GO formel** et n'a pas été signé. Handoff conditionnel vers M4 : `docs/roadmap/M3_TO_M4_HANDOFF.md`.
