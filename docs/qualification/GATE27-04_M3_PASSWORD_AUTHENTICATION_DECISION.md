# GATE27-04 - M3 Password Authentication - Rapport de qualification

> **Date de coupe :** 3 novembre 2026
> **Statut :** **NO-GO FORMEL / CODE CANDIDAT TESTÉ / PAS DE RELEASE**
> **Autorité :** dossier de preuve technique, **PAS une signature de revue indépendante**
> **PR :** [#75](https://github.com/tawounfouet/pyauthkit/pull/75), DRAFT
> **Gate :** [#74](https://github.com/tawounfouet/pyauthkit/issues/74), OPEN
> **Référence :** `2026-11-02_PYAUTHKIT_M3_PASSWORD_AUTHENTICATION_IMPLEMENTATION_PLAN.md` §13 et §15
> **Conventions :** Problem First, Trust First, Invariant Before API, Evidence Before Claim.

## 1. Décision exécutoire

**NO-GO pour fusion, release ou déploiement d'authentification.** L'implémentation M3 a passé les contrôles automatiques disponibles, mais le périmètre demandé inclut des risques et preuves qui nécessitent un host réel, des décisions opérateur et une revue indépendante. L'assistant ne peut les signer à la place du responsable de sécurité ou du propriétaire du dépôt.

Le constat « tests au vert » ne signifie ni « security-qualified », ni « production-ready », ni « 100 % sans risque ». Aucun résultat NIST AAL, OWASP certifié, FIPS ou SOC 2 n'est revendiqué.

## 2. Chaîne de preuves vérifiée

| Élément | Preuve constatée |
|---|---|
| M2 initial | GATE27-03 #70 CLOSED / GO scope ENGINE+PORTS; `main` SHA `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92` |
| M3 candidat avant ce rapport | SHA `126fd2eb3e0858ce18218a78b8adf02c46a94937`; PR #75 DRAFT |
| PR CI sur le SHA candidat | [Run #41607548865](https://github.com/tawounfouet/pyauthkit/actions/runs/41607548865) : **7/7 SUCCESS** |
| Tests | **160 PASS**, dont **104 tests historiques M1/M2** et 56 exécutions de tests M3 |
| Quality | Ruff lint/format PASS; mypy strict PASS (35 source files); architecture fitness PASS |
| Security | pip-audit, Bandit et detect-secrets : job SUCCESS sur le SHA candidat |
| Cross-platform | Wheel/sdist installés et vérifiés sous Ubuntu Python 3.12/3.13/3.14, macOS 3.12, Windows 3.12 |
| Crypto optionnelle | Vérification positive et négative Argon2id depuis wheel isolé avec `[password]`; core sans extra importable |
| Provenance crypto | `argon2-cffi` 25.1.0 sur le runner qualité; PHC `argon2id` v19 seulement |
| Vecteur fixe | Exemple publié dans https://argon2-cffi.readthedocs.io/en/stable/index.html, test positif/négatif + corruption |
| Protection main | Ruleset `PYAUTHKIT_PROTECT_MAIN` active, sept statuts requis, pas de bypass; reviewer obligatoire = **0** |
| Revue externe | PR #75 : **0 approbation indépendante**, issue [#64](https://github.com/tawounfouet/pyauthkit/issues/64) ouverte |
| Main après M3 | **NON FUSIONNÉ**, post-merge CI non applicable à ce stade |

**Important :** toute modification à cette PR après le SHA cité nécessite une nouvelle CI sur le HEAD final. Un verdict d'un commit antérieur ne se transfère pas automatiquement à un commit ultérieur.

## 3. KDF, capacités et mesures

Politique candidate : Argon2id v19, `m=19456 KiB`, `t=2`, `p=1`; la configuration de démonstration limite les workers et les jobs en attente par processus. Des tests adversariaux ont validé saturation (120 tentatives, deux workers, trois slots), timeout, annulation, rétention des permis et shutdown.

Benchmark informatif sous Ubuntu GitHub Actions, Python 3.12.15, `argon2-cffi 25.1.0`, 18 échantillons par cas, [run #41607548865](https://github.com/tawounfouet/pyauthkit/actions/runs/41607548865) :

| Chemin | p50 ms | p95 ms | p99 ms |
|---|---:|---:|---:|
| Password correct | 21.724 | 22.278 | 22.844 |
| Password incorrect | 21.601 | 22.245 | 22.328 |
| Identifiant absent | 21.634 | 22.043 | 22.167 |

RSS max processus observé : **66 180 KiB**. Ratio p50 absent/incorrect : **1.002**. Ces mesures NE démontrent PAS l'indiscernabilité statistique, l'absence d'énumération sur HTTP, la sûreté sous 1000 clients réels, le dimensionnement d'un cluster ni un SLO de production. Refaire le benchmark sur l'hôte cible, avec mémoire, CPU, quotas globaux, multi-instance, coût historique et chemins réseau.

## 4. Décisions G4-01..G4-16

| Gate | Verdict | Evidence / blocage |
|---|---|---|
| G4-01 | PASS | M2 GO confirmé, 104 tests historiques passés |
| G4-02 | TECHNICAL PASS / OPEN | WP27-019/020/021/022 implémentés candidat, issues encore ouvertes |
| G4-03 | PASS | Contrats resolver scoped, deux adapters, cross-tenant réels |
| G4-04 | PASS | Argon2id 25.1.0 et vecteur public |
| G4-05 | PASS | PHC type/version/coûts bornés avant KDF |
| G4-06 | PASS | wrong/missing/ambiguous/disabled/revoked/expired -> aucun principal |
| G4-07 | PASS | final policy M2 obligatoire, deny explicite |
| G4-08 | PARTIAL | Résultats et événements library neutres; réponse HTTP host non qualifiée |
| G4-09 | BLOCKED | Guard injecté et fail-closed, mais limites multi-instance/source non qualifiées |
| G4-10 | PASS FOR PROCESS | Tests 120 tentatives, timeout/cancellation/shutdown; pas de préemption native |
| G4-11 | PARTIAL | Race de révocation simulée, pas de stockage autoritatif réel |
| G4-12 | BLOCKED | T24 absent, T25/T26 incomplets pour les canaux host |
| G4-13 | PARTIAL | CI PR 7/7 sur HEAD testé, CI main post-merge absente |
| G4-14 | BLOCKED | ADR-0010..0015 encore PROPOSED, validation opérateur requise |
| G4-15 | BLOCKED | Pas de revue externe attribuée ni d'acceptation formelle des risques |
| G4-16 | BLOCKED | Aucun sign-off GO autorisé; issue gate ouverte |

Les critères PASS ici démontrent des propriétés **dans le périmètre du composant, des stores de test et du workflow cité**, sans extrapolation au host.

## 5. Registre des risques bloquants

| Risque | Owner responsable à confirmer | Preuve/action nécessaire | Décision |
|---|---|---|---|
| Quotas anti-bruteforce multi-source/multi-tenant | Host / framework integrator | Adapter host réel, compteurs partagés et tests adversariaux distribués | BLOCKED |
| Temps de réponse et canaux HTTP d'énumération | Host / security | Statut/corps/headers/latence, distributions et revue statistique | BLOCKED |
| Cohérence du store et révocation entre noeuds | Credential owner | Backend authentique, contraintes transactionnelles, tests de course multi-instance | BLOCKED |
| Dimensionnement réel et p99 de production | SRE / Host owner | CPU/RSS sous charge, profil KDF, saturation, SLO et budget global | OPEN |
| Audit durable et exploitation | Ops / security | Contrat de sink et politique d'incident host, pas de secret | OPEN |
| ADRs et politiques de sécurité | Maintainer / reviewer | Approbation écrite des ADR-0010..0015, scope/restrictifs | BLOCKED |
| Revue indépendante | Maintainer | Reviewer éligible, approbation sur PR, pas d'auto-approbation fictive | BLOCKED (#64) |
| Reproductibilité/lock des artefacts | Supply chain owner | Qualification M8 avant PyPI, ticket [#63](https://github.com/tawounfouet/pyauthkit/issues/63) | RELEASE BLOCKED |

Aucun risque n'est déclaré `ACCEPTED` par l'assistant. L'acceptation nécessite un propriétaire, un périmètre, une justification, une expiration et un sign-off explicite.

## 6. Oracle register et décision

Voir [M3_PR06_SECURITY_ORACLES.md](M3_PR06_SECURITY_ORACLES.md). Les tests spécifiques apportent les preuves de nombreux scénarios, mais **T24 est non exécuté en conditions host et T25/T26 sont seulement partiels**. Les autres oracles doivent être revus et acceptés individuellement par une personne autorisée. Aucune comparaison de simples statuts `REJECTED` ne démontre une protection anti-énumération côté HTTP.

## 7. Actions de sortie non automatiques

1. Désigner une personne indépendante pour la revue de cryptographie, trust boundaries, concurrence et sécurité, sans prétendre qu'une auto-revue est indépendante.
2. Brancher un host de qualification avec source de route fiable, stockage credential réel, AttemptGuard distribué et audit; exécuter T24/T25/T26 et scénarios de consistance.
3. Refaire le benchmark sur le matériel cible, documenter ressources, RSS, p50/p95/p99 et SLO.
4. Faire approuver les ADRs et tout risque explicitement dérogé.
5. Réévaluer les 40 oracles avec expected, observed, SHA, CI run, reviewer et statut.
6. Autoriser ensuite seulement une fusion soumise aux sept checks, vérifier `main` après merge, signer GATE27-04 et clôturer WP/M3 si réellement satisfaits. Aucun auto-release.

**Décision documentaire :** NO-GO M3 formel; PR #75 reste DRAFT; #74 OPEN; aucun changement de `main`, aucune publication. Ce rapport n'est pas une autorisation de production.
