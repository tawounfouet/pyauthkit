# M7 - GATE27-08 - Audit T30 de préparation à la revue indépendante

> Projet : PyAuthKit
> Date : 2026-11-07
> Type : qualification / preuve de gouvernance / review readiness
> Statut : **TESTED (CI) / T30 PARTIAL (CI) / NO-GO SECURITY**
> Autorité de décision : reviewer de sécurité indépendant, non désigné dans la PR
> PR : https://github.com/tawounfouet/pyauthkit/pull/84
> Issue gate : https://github.com/tawounfouet/pyauthkit/issues/85
> Remédiation de gouvernance : https://github.com/tawounfouet/pyauthkit/issues/88

## 0. Règle de qualification

`TESTED != QUALIFIED`. Cette collecte utilise la lecture GitHub effectuée le 7 novembre 2026. Aucune signature de reviewer indépendant n'a été observée. Ce document n'est ni une approbation de code, ni une autorisation de fusion, de release ou de déploiement.

La source de vérité du statut T01..T30 est le manifeste `M7_ORACLE_EVIDENCE_MANIFEST.md`. La CI prouve les tests exécutés sur le SHA cité, non l'absence de vulnérabilité ni la conformité de la supply chain du plugin.

## 1. Snapshot de provenance vérifié

| Champ | Preuve observée |
| --- | --- |
| Repository | `tawounfouet/pyauthkit` |
| PR | `#84`, `open=true`, `draft=true`, `merged=false` |
| Branche | `feat/m7-public-sdk-plugin-admission-pr10` |
| Head vérifié | `573334f7fe372ef07659dd6c85e02801ac529891` |
| Base vérifiée | `main@ac4669e86cd690170ab5f3c2b0c7945258e35f9d` |
| CI source | https://github.com/tawounfouet/pyauthkit/actions/runs/42320391541 |
| Event | `pull_request`, head SHA associé à `#84`, conclusion `success` |
| Jobs Actions | **13/13 success** |
| Checks API | **14/14 success** (13 jobs + `GitGuardian Security Checks`) |
| Reviews PR | **0**, aucun approbateur |
| Review requests | **0**, ni utilisateur ni équipe |
| PR review comments | **0** |
| Mergeability REST | `mergeable=true`, `mergeable_state=clean` : **information GitHub, pas GO sécurité** |
| Gate indépendant | **NO-GO / REVIEW NOT PERFORMED** |

Le statut de l'API traditionnelle `commits/{sha}/status` a été `pending` avec zéro ancien `statuses`; les `Check Runs` modernes affichent, eux, 14 conclusions `success`. Ne pas confondre ces deux mécanismes.

## 2. Jobs CI attestés, SHA ci-dessus

| Preuve / plateforme | Job Actions | Verdict |
| --- | --- | --- |
| Ruff, mypy strict, pytest global, architecture | `128243269924` | SUCCESS - **689 passed**, mypy **85 fichiers** |
| M7 SDK + admission + wheel indépendante | `128243270230` | SUCCESS - **61 passed**, guide exécuté |
| Scans dépendances, source, secrets | `128243270087` | SUCCESS - pip-audit : no known vulnerabilities |
| M3 PostgreSQL / Redis / HTTP de référence | `128243270198` | SUCCESS, sans qualification indépendante M3 |
| M4 PostgreSQL / Redis / HTTP de référence | `128243270176` | SUCCESS, sans qualification indépendante M4 |
| M5 JWT / JWKS de référence | `128243270125` | SUCCESS, sans qualification indépendante M5 |
| M6 configuration / secret / audit de référence | `128243270205` | SUCCESS, sans qualification indépendante M6 |
| M6 real HTTP receipt reference | `128243270284` | SUCCESS |
| Linux Py3.12 | `128243270158` | SUCCESS |
| Linux Py3.13 | `128243270242` | SUCCESS |
| Linux Py3.14 | `128243270469` | SUCCESS |
| macOS Py3.12 | `128243270179` | SUCCESS |
| Windows Py3.12 | `128243270307` | SUCCESS |

Logs du job M7 : construction wheel/sdist de `pyauthkit 0.1.0a1`, import SDK sans extras, exemple Python pure-denial, documentation capability exécutée, installation d'une **distribution synthétique indépendante** et vérification `HOST MAC / REVOCATION / SCOPE CHECKS`. Le HMAC utilise une clé de fixture publique, pas une preuve cryptographique de production.

## 3. Protection de main, contrôle de gouvernance

Ruleset identifié : `PYAUTHKIT_PROTECT_MAIN`, identifiant `26350656`, `enforcement=active`, cible `refs/heads/main`. Source : endpoint GitHub REST `/repos/tawounfouet/pyauthkit/rulesets/26350656`.

| Propriété | Observation | Implication |
| --- | --- | --- |
| Suppression de main | Rule `deletion` | Interdiction déclarée active |
| Historique main | Rule `non_fast_forward` | Force push/non fast-forward interdits par le ruleset |
| Checks stricts | `strict_required_status_checks_policy=true` | Sept checks définis comme obligatoires |
| Review threads | `required_review_thread_resolution=true` | Conversations à résoudre si présentes |
| Reviews obligatoires | **`required_approving_review_count=0`** | **Écart P0 pour gate indépendant** |
| Reviewer nominatif | `required_reviewers=[]` | Aucun reviewer désigné dans le ruleset |
| Last push approval | `require_last_push_approval=false` | Pas de validation spécifique du dernier pousseur |
| CODEOWNERS review | `require_code_owner_review=false` | Pas de contrainte CODEOWNERS constatée ici |
| Bypass actors | `[]` | Aucun contournement listé dans ce ruleset |
| GitGuardian | Check-run `success`, **non required** | Protection d'analyse non bloquante dans ce ruleset |

Les **sept** checks obligatoires exacts sont :

1. `Lint, types, unit and architecture`
2. `Dependency, source and secret scans`
3. `Wheel / sdist / smoke (ubuntu-latest Py3.12)`
4. `Wheel / sdist / smoke (ubuntu-latest Py3.13)`
5. `Wheel / sdist / smoke (ubuntu-latest Py3.14)`
6. `Wheel / sdist / smoke (macos-latest Py3.12)`
7. `Wheel / sdist / smoke (windows-latest Py3.12)`

L'endpoint de protection classique `branches/main/protection` a répondu HTTP **403 Resource not accessible by integration**. On ne peut donc ni conclure qu'une protection classique supplémentaire existe, ni qu'elle est absente. Il faut un contrôle par un administrateur autorisé avant la clôture du gate.

Le ruleset actif ne requiert pas le job M7 lui-même comme statut obligatoire. **Recommandation à arbitrer** : ajouter le check M7 aux contrôles bloquants tant que M7 est une composante critique de la PR, et imposer un reviewer indépendant avec au moins une approbation. Examiner GitGuardian avant d'en faire un contrôle bloquant, notamment sa disponibilité et la politique de faux positifs. Aucun changement d'administration n'a été effectué.

## 4. Matrice de préparation des 30 oracles

Les preuves `TESTED (CI)` ne sont **pas** des verdicts de sécurité. Un oracle P0 ne devient pas qualifié uniquement parce que sa suite pytest est verte.

| Groupe | Identifiants | État constaté | Action avant gate |
| --- | --- | --- | --- |
| SDK, host trust et final policy | T01-T10 | TESTED (CI) | Revue des invariants M2/M6 et chemins d'échec |
| Cancellation, discovery, grants | T11-T16 | TESTED (CI) | Relecture de side effects et d'admission pré-import |
| Collisions / réservation de méthodes | T17 | **PARTIAL (CI)** | Preuve de complétude de `reserved_methods` côté host |
| Compatibilité SPI | T18 | TESTED (CI) | Validation de version et refus de downgrade |
| Capabilities | T19 | **PARTIAL (CI)** | Examiner permissions effectives et origine de chaque port |
| Freeze registry, outcome, scope, fermeture | T20-T23 | TESTED (CI) | Audit du trust boundary et shutdown |
| Confidentialité | T24 | **PARTIAL (CI)** | Évaluer logs, side effects et code Python in-process |
| Documentation / API | T25 | **PARTIAL (CI)** | Couvrir les exemples SDK non exécutés |
| Wheel, extras, audit, régressions | T26-T29 | TESTED (CI) | Audit des artefacts, OS et dépendances |
| SHA, gate, indépendance du reviewer | T30 | **PARTIAL (CI)** | Reviewer indépendant + décision signée, check protection |

**Total : 25 TESTED (CI) et 5 PARTIAL (CI). Aucune ligne QUALIFIED.**

## 5. Registre de risques résiduels et blockers

| ID | Risque | Impact | État / propriétaire de décision |
| --- | --- | --- | --- |
| M7-RISK-T30-01 | Aucun reviewer indépendant ni approbation requise | CRITICAL governance | BLOCKED, issue #88 |
| M7-RISK-T30-02 | GitGuardian et job M7 non requis par ruleset | HIGH enforcement gap | PROPOSED remédiation admin, #88 |
| M7-RISK-T30-03 | Provenance code/package plugin non attestée, shadowing `sys.path` reproductible | HIGH supply chain | OPEN, issues #85 et #89 |
| M7-RISK-T30-04 | Code tiers Python dans le processus host, sans sandbox | HIGH isolation | ACCEPTABLE seulement après décision de trust explicite |
| M7-RISK-T30-05 | Outcome positif de fixture publique et plugin positif non qualifié | HIGH verification | OPEN, #86 |
| M7-RISK-T30-06 | Port privileges / scope hôte / registry indexée par méthode | HIGH cross-tenant misuse | OPEN, #87 |
| M7-RISK-T30-07 | Shutdown asynchrone best-effort | MEDIUM/HIGH resource safety | OPEN, revue #85 |
| M7-RISK-T30-08 | Gates M3-M6 distincts non qualifiés | HIGH dependency | OPEN, GATE27-04..07 |
| M7-RISK-T30-09 | État classique de protection non consultable via intégration | MEDIUM evidence gap | VERIFY par administrateur |

Les impacts sont des **classifications de revue proposées**, non des CVSS calculés ou une analyse d'exploitation exhaustive.

## 6. Conditions préalables à une décision indépendante

- [ ] Reviewer indépendant **identifié et demandé** sur la PR ; revue signée au SHA correct.
- [ ] Protection effective examinée avec droits admin ; politique d'approbation revue et appliquée.
- [ ] T17, T19, T24, T25 et T30 : preuves complémentaires ou dérogations motivées, signées par l'autorité habilitée.
- [ ] Provenance de distribution et stratégie de confiance des plugins documentées et vérifiées.
- [ ] Real positive verifier évalué au regard des garanties crypto / key / freshness / revocation ; fixture publique explicitement exclue.
- [ ] Résolution du modèle multi-tenant, du cycle de vie et des permissions effectives des ports host-owned.
- [ ] Gates M3-M6 examinés comme dépendances distinctes, pas déclarés GO par transitivité.
- [ ] SHA, workflow, job, OS/Python, preuve, auteur et reviewer consignés dans la décision.
- [ ] Décision de sécurité prise explicitement, avec périmètre, restrictions et risques résiduels ; la décision de merge/release reste distincte.

## 7. Décision provisoire

| Décision | Verdict |
| --- | --- |
| Continuer travaux de développement | **GO DEV** |
| Qualifier le code M7 pour un usage de production | **NO-GO SECURITY** |
| Utiliser plugin synthétique comme authenticator réel | **NO-GO** |
| Clore GATE27-08 | **NO-GO - indépendant non signé** |
| Lever Draft / fusionner PR-10 | **NO-GO sous gouvernance actuelle** |
| Publier wheel SDK M7 / déployer | **NO-GO** |

**Aucune fusion, release, modification du ruleset ou publication réalisée par ce dossier.**

## 8. Design Learning Card intégrée

Problème : un résultat `CI SUCCESS` est une preuve de tests, **pas** une décision de confiance. Le gate formalise la différence entre `IMPLEMENTED`, `TESTED` et `QUALIFIED`.

Principes : Separation of Duties, Defense in Depth, Fail Closed, Evidence-Based Qualification, Traceability et Least Privilege. Le ruleset est un garde-fou d'ingénierie ; le reviewer qualifie les frontières, le risque résiduel et les exceptions. Ni l'un ni l'autre ne remplace les tests.

Anti-pattern : convertir une PR `mergeable_state=clean` ou une ligne `TESTED (CI)` en `SECURITY GO`. Les données observées montrent précisément pourquoi ces notions doivent rester distinctes.

## 9. Provenance et périmètre de lecture

Requêtes GitHub en lecture seule au 2026-11-07 : PR #84, revue PR, reviewer requests, workflow #42320391541, jobs, check-runs au SHA `573334f7...`, ruleset #26350656, issues #85/#86/#87. Résultats plus récents ou modifications des protections nécessitent un audit renouvelé. L'accès classic branch protection est bloqué par HTTP 403.

## Annexe - Découverte adversariale de provenance (#89)

L'identité et la version d'une distribution installée ne contraignent pas, à elles seules, le système d'import Python à charger les fichiers de cette distribution. Le test M7 de shadowing reproduit ce risque avec un module homonyme de test. Le recontrôle des metadata immédiatement avant import ne ferme pas cette faille de provenance. Une politique d'artefact fiable et des contraintes de déploiement doivent être ratifiées avant la revue indépendante. Dossier : `M7_PLUGIN_ORIGIN_AND_IMPORT_SHADOWING_2026-11-07.md`.

## Annexe de qualification technique : wheel SHA-256 (2026-11-07)

La nouvelle tranche source `28e0d7ff4ae6b4c59d0080e73c0950a9be7a557a` a 13/13 jobs verts sur https://github.com/tawounfouet/pyauthkit/actions/runs/42327812346, dont 700 tests globaux et 72 M7. Un digest SHA-256 externe et la correspondance name/version/entry point sont vérifiés avant installation. **Ni cette preuve ni les 30 oracles de CI n'établissent une revue indépendante**, un chemin d'import immuable ou une signature de provenance. L'ancien snapshot de gouvernance de ce rapport reste historiquement daté; les règles de main doivent être revérifiées par un administrateur avant toute décision GO.
