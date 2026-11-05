# GATE27-04 - M3 Password Authentication - Rapport de qualification

> **Date de coupe :** 5 novembre 2026  
> **Verdict :** **NO-GO FORMEL / TECHNIQUE DE RÉFÉRENCE QUALIFIÉE PAR CI**  
> **PR :** [#75](https://github.com/tawounfouet/pyauthkit/pull/75), sans merge ni publication  
> **Gate :** [#74](https://github.com/tawounfouet/pyauthkit/issues/74), OPEN  
> **Code testé :** `2c6ea7173b44ce314c61f680b436d493c994de3c`  
> **CI code exact :** [42031794016](https://github.com/tawounfouet/pyauthkit/actions/runs/42031794016), **7/7 SUCCESS**  
> **Important :** ce rapport n'est **pas** une signature de revue indépendante.

## 1. Portée de la décision

L'implémentation de l'authentificateur Argon2id est qualifiée techniquement sur le périmètre de ses tests et du **banc hôte de référence**. Nous avons exécuté **160 tests du cœur** et **9 tests d'intégration** sur des instances PostgreSQL/Redis démarrées par GitHub Actions, avec des serveurs Uvicorn sur socket local et deux processus OS distincts. Ruff, mypy strict, architecture fitness, audit des dépendances optionnelles, Bandit sur `src` + `qualification/host`, détecteur de secrets et les cinq vérifications de wheel ont réussi.

**NO-GO pour la clôture formelle de M3 et pour une exploitation authentifiée en production.** L'absence de revue indépendante, la non-approbation des ADR et les garanties de déploiement réel non évaluées ne peuvent être converties en PASS par un agent de code.

Aucune affirmation d'indiscernabilité de timing, de révocation instantanée multi-région, de conformité NIST/FIPS/SOC 2, ou de rate limiting universel n'est autorisée.

## 2. Résumé des preuves observées

| Dimension | Observation |
|---|---|
| M2 de départ | GATE27-03 #70 CLOSED, `main` `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92` |
| M3 code | `2c6ea7173b44ce314c61f680b436d493c994de3c`, CI [42031794016](https://github.com/tawounfouet/pyauthkit/actions/runs/42031794016) |
| Matrice qualité | 7/7 contrôles CI SUCCESS, 160 tests code, 9 tests host |
| Plateformes wheel | Ubuntu Python 3.12/3.13/3.14, macOS 3.12, Windows 3.12 |
| Cryptographie | Argon2id PHC v19, vecteur fixe publié, coûts bornés, `argon2-cffi` 25.1.0 |
| Stockage | PostgreSQL scoping dans SQL, statut/version/expiry revalidation après KDF |
| Défaillances | PostgreSQL indisponible => 503; Redis indisponible => 503; aucun succès |
| T24 | Tests de quotas Lua atomiques : 64 appels concurrents, deux objets FastAPI, **deux processus Uvicorn OS distincts** avec Redis partagé, tenant isolation |
| T25 | HTTP/1.1 sur socket loopback : mêmes statuts 401, corps, types, longueurs et en-têtes de refus par cause |
| T26 | 60 échantillons wrong/missing sur HTTP/1.1, 500 permutations et 500 bootstrap, **marge pratique 5% testée**; p-value significative possible |
| Revue indépendante | **0 APPROVAL** constatée sur PR #75 |
| Approbation ADR-0010..0015 | **PROPOSED**, propriétaire et reviewer à confirmer |
| `main` / PyPI | non modifiés |

**Règle de traçabilité :** tout nouveau commit exige une nouvelle CI sur son SHA exact avant que les décisions n'utilisent cette preuve. Les documents produits après la CI citée déclenchent une vérification supplémentaire.

## 3. Résultats T24-T26 et fenêtres de sécurité

T24 a été exercé dans un environnement GitHub avec Redis/PostgreSQL réels, deux objets FastAPI et deux processus OS distincts. Cela prouve le partage de quotas dans le banc fourni, mais ne prouve pas un cluster géodistribué, les métadonnées reverse-proxy ou une défense anti-bot.

T25 a vérifié les réponses de refus d'une API Uvicorn HTTP/1.1 sur loopback. Les réponses host malformées (400), hors catalogue (404) et pannes (503) restent volontairement distinctes. La qualité de la chaîne de proxy, de TLS et de caches de production reste à qualifier.

T26 a mis en évidence une **différence statistiquement détectable** au cours d'une première mesure du banc : mauvaise preuve p50 60.924 ms, utilisateur absent p50 60.041 ms, delta -0.883 ms, p=0.004, bootstrap [-0.940,-0.443]. Le banc a alors reçu un **plancher de réponse de 100 ms** pour les rejets. Sur [42031794016](https://github.com/tawounfouet/pyauthkit/actions/runs/42031794016), mauvaises preuves p50 **142.058 ms**, utilisateur absent **141.995 ms**, delta **-0.063 ms**; l'intervalle bootstrap 95% **[-0.892, +0.008] ms** est inclus dans une marge de 5% du p50 (7.103 ms), mais la valeur **p=0.0279** continue de suggérer une différence détectable sur cet échantillon. Il serait faux de conclure « constant time », « aucun signal exploitable » ou « conformité anti-énumération de production ».

**T26 demeure PARTIAL pour la revendication sécurité en production.** Il présente une exécution expérimentale positive dans une marge pratique bornée à un banc local; son risque est à accepter ou à corriger dans la politique hôte cible.

Pour la vérification Argon2id seule, le benchmark de la CI est distinct du benchmark HTTP et ne doit pas être mélangé avec celui-ci.

## 4. G4-01..G4-16, critère par critère

| Gate | Vérification technique | Décision |
|---|---|---|
| G4-01 | M2 prérequis qualifié, non-régression 104 cas historiques | TECH PASS |
| G4-02 | WP27-019..022 implémentés et traçables | TECH PASS / issues OPEN |
| G4-03 | Port resolver scopé, deux adapters et source PostgreSQL filtrée | TECH PASS |
| G4-04 | Argon2id réel et vecteurs fixes | TECH PASS |
| G4-05 | Format PHC, coût m/t/p borné, pas de downgrade | TECH PASS |
| G4-06 | Refus tous credentials non admissibles | TECH PASS |
| G4-07 | M2 final policy obligatoire | TECH PASS |
| G4-08 | Refus génériques et événements library sans secrets; HTTP local | TECH PASS LAB / host réel non qualifié |
| G4-09 | Guard partagé par Redis, deux processus OS, pannes fail-closed | TECH PASS LAB / infra réelle non qualifiée |
| G4-10 | 120 demandes concurrentes, timeout, annulation, shutdown | TECH PASS PROCESS |
| G4-11 | Révocation PostgreSQL entre KDF et relecture | TECH PASS LAB / fenêtre post-check ouverte |
| G4-12 | T24/T25 exécutés sur host de référence, T26 expérimental | PARTIAL / étude anti-énumération réelle requise |
| G4-13 | 7/7 CI PR sur SHA code; CI main après merge non exécutée | PARTIAL GATE |
| G4-14 | ADR-0010..0015 étudiés, **non approuvés** | BLOCKED |
| G4-15 | Risques attribuables, **pas acceptés**, aucun reviewer indépendant | BLOCKED |
| G4-16 | Décision GO non signée, issue gate ouverte | BLOCKED |

Les verdicts « TECH PASS » prouvent un comportement local; ils ne constituent PAS un GO formel.

## 5. Registre de risques ouverts et ownership proposé

| Risque | Owner à confirmer | Exigence de clôture |
|---|---|---|
| Reverse proxy, TLS, vraie origine réseau | Framework integrator | Tester trusted proxy/forwarded policy et trafic réseau réel |
| T26, formes temporelles et body/header externes | Security + Host owner | Étude sous charge, réseaux/proxy cible, interprétation/mitigation |
| Dernier `is_current` puis réponse (TOCTOU) | Credential owner | Définir et faire accepter bornes de révocation par backend |
| Quotas fixed-window, HMAC, rotation, usurpation et botnets | SRE + Security | Revue d'architecture et limites globales du host |
| Capacité mémoire/CPU multi-instance | SRE | Benchmarks profil coût, SLO p50/p95/p99 sur matériel cible |
| Audit best-effort non durable | Ops | Politique durable pour authentification réelle |
| ADR-0010..0015 non approuvés | Maintainer + reviewer | Revue explicite et APPROVED |
| Revue indépendante absente | Maintainer | Obtenir reviewer humain éligible, issue #64 |
| Publication PyPI, hashes/reproductibilité | Supply chain owner | Issue #63, qualification release M8 |

**Aucun risque ne devient ACCEPTED** sans identité de propriétaire, justification, portée limitée, date d'expiration éventuelle et signature.

## 6. Décision finale

- Candidat **prêt pour revue formelle** : oui.
- Tests du moteur et du banc d'intégration : **PASS dans le périmètre prouvé**.
- **GATE27-04 : NO-GO FORMEL** tant qu'ADR/reviewer/risques ne sont pas signés et les exigences hôte ciblées non qualifiées.
- Aucune fusion, aucun déploiement et aucune publication autorisés par ce document.
- Rapport de revue technique : [M3_SECURITY_AND_ADR_REVIEW_2026-11-05.md](M3_SECURITY_AND_ADR_REVIEW_2026-11-05.md).
- Registre 40 oracles : [M3_PR06_SECURITY_ORACLES.md](M3_PR06_SECURITY_ORACLES.md).
- Runbook : [../../qualification/host/README.md](../../qualification/host/README.md).

**Ne pas déclarer M3 officiellement clôturé par une CI seule.**
