# M4 - Checklist de revue independante v2

> **Source de reference :** `M4_2026_11_05_SOURCE_MATRIX.md`, extrait des sections 20 et 22 du plan M4 detaille. Anciennes interpretations V1 : SUPERSEDED.
> **Statut : PENDING / GATE27-05 NO-GO**. Aucun auteur du code ne se declare reviewer independant.

## Identification et conditions

- SHA exact : **NON RENSEIGNE**
- Owner des exigences : **NON RENSEIGNE**
- Reviewer crypto/securite independant, role, date : **NON RENSEIGNE**
- Environnement cible, TLS/proxy/KMS : **NON RENSEIGNE**
- CI exacte, export des logs, empreinte SHA-256, retention : **NON RENSEIGNE**
- M3 PR #75 / GATE27-04 : **A ARBITRER** par l'owner avant G5-01
- ADR-0016/0017/0018/0019 : **PROPOSED / NOT ACCEPTED**

## Checklist et gates

- [ ] L'owner ratifie les 39 P0 et T28 P1 issus du plan detaille (issue #78).
- [ ] Chaque oracle M4-T01..40 inclut `expected/observed/test/SHA/CI/OS/backend/reviewer/limitations/formal_status`.
- [ ] M4-T28 a un test `BOUNDED_OVERLAP` ou un `NOT_APPLICABLE` justifie et signe sous `NO_OVERLAP`.
- [ ] Reviewer confronte les resultats des tests a des invariants P0, et non au seul code `pytest`.
- [ ] Reviewer examine limites de la fenetre revoke-to-deny et le risque apres dernier `is_current`.
- [ ] Revue de l'origine host, de l'isolement tenant source et des 2 resolvers.
- [ ] Revue de la rotation KMS/key_ref, du bearer replay, des secrets et du logging.
- [ ] Revue du guard Redis, provenances peer/TLS/proxy, DoS et anti-enumeration.
- [ ] Revue du rapport timing sans pretention d'equivalence statistique.
- [ ] Revue charge, timeout, cancellation, caches et absence de promotion tardive.
- [ ] Controle M2/M3 non-regression selon la base d'integration effectivement approuvee.
- [ ] Wheel M4 valide sur 5 jobs et tous les checks au SHA final.
- [ ] Les 10 risques du registre et F-M4-01 ont une decision par un owner habilite.
- [ ] Decisions d'ADR et des 16 G5 signees au SHA exact.
- [ ] GO/NO-GO officiel signe, puis validation merge et `main` post-merge.
- [ ] Publication PyPI/production conserve son gate distinct.

## GATE27-05, dispositions a signer

| ID | Exigence provenant du plan M4 | NO-GO si | Verdict/reviewer/date |
| --- | --- | --- | --- |
| G5-01 | Préconditions M2/M3 satisfaites selon base | Dépendance non qualifiée masquée | **PENDING** |
| G5-02 | Scope/source autoritatifs | Lookup global permissif | **PENDING** |
| G5-03 | Full-key only | Selector authentifiant seul | **PENDING** |
| G5-04 | Crypto choisie et explicitée | Fallback inconnu / digest naïf | **PENDING** |
| G5-05 | États et UTC sûrs | Révoquée/expirée acceptée | **PENDING** |
| G5-06 | Version/révocation cohérentes | Garantie revendiquée non démontrée | **PENDING** |
| G5-07 | Séparation AuthN/AuthZ et type acteur | Service key -> permission implicite | **PENDING** |
| G5-08 | Échecs sûrs et absence de secrets | Fuite brute ou succès sur erreur | **PENDING** |
| G5-09 | Anti-abus selon exposition | Quota revendiqué sans preuve | **PENDING** |
| G5-10 | Isolation multi-tenant | Foreign credential accepté | **PENDING** |
| G5-11 | Anti-énumération qualifiée selon host | Fuite d'identifiant exploitable non traitée | **PENDING** |
| G5-12 | Concurrence et résilience | Succès tardif / cache stale | **PENDING** |
| G5-13 | Qualité CI multi-OS sur SHA final | Run SHA incorrect/skipped | **PENDING** |
| G5-14 | ADR et contrats publics approuvés | ADR encore PROPOSED | **PENDING** |
| G5-15 | Risques et revue indépendante | Auto-approval ou risques sans owner | **PENDING** |
| G5-16 | Décision formelle et post-merge | Déclaration « closed » sans preuve | **PENDING** |

## Gabarit d'adjudication

```
oracle_id, threat_id, invariant_id, implementation_path, test_path,
expected, observed, evidence_level, head_sha, action_run_url,
python_version, os, backend_version, reviewer, formal_status,
limitations, waiver_id_if_applicable
```

**Aucun de ces champs n'autorise un agent a forger une signature humaine.**

## Verdict actuel

**NO-GO / NOT FORMALLY ADJUDICATED.** Les tests techniques ne remplacent
ni les owners ni la revue independante. Pas de fusion ni de release sans
decisions reelles, verifiables et rattachees au SHA exact.
