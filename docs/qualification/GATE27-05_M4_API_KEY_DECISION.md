# GATE27-05 - Decision securite formelle M4 (version active v2)

- Date : 2026-11-05
- Branch : `feat/m4-api-key-authentication-pr07`
- PR : https://github.com/tawounfouet/pyauthkit/pull/76
- **Verdict : NO-GO / NOT FORMALLY ADJUDICATED**
- Source exacte : plan detaille M4 05/11/2026, sections **20 et 22**;
  transcription `M4_2026_11_05_SOURCE_MATRIX.md`.
- Le gate historique utilisait de mauvaises significations d'oracles et
  est **entierement remplace par le present document**.

## Qualification technique precedente

Le code au SHA `f96690a7663a7b63ddd50dec58bb09c1d80bae16`
a [8/8 jobs successful au run 42076715449](https://github.com/tawounfouet/pyauthkit/actions/runs/42076715449),
**218 tests Python** et **20 tests PostgreSQL/Redis/HTTP** passes.
Ce sont des tests de laboratoire et de wheel, pas un reviewer sign-off.
Ce document a son propre nouveau SHA a verifier ensuite.

## G5-01..16 selon le plan officiel

| Critere | Source G5 | Preuve attendue | Statut officiel |
| --- | --- | --- | --- |
| G5-01 | Préconditions M2/M3 satisfaites selon base | HEAD main et gates amont | **PENDING** |
| G5-02 | Scope/source autoritatifs | Test SQL/callback et cross-tenant | **PENDING** |
| G5-03 | Full-key only | Prefix-only et secret incomplet refusés | **PENDING** |
| G5-04 | Crypto choisie et explicitée | ADR, vecteurs HMAC, rotation key_ref | **PENDING** |
| G5-05 | États et UTC sûrs | Active/not-before/expiry/status | **PENDING** |
| G5-06 | Version/révocation cohérentes | is_current real store, race tests | **PENDING** |
| G5-07 | Séparation AuthN/AuthZ et type acteur | SPI M2/policy, no RBAC | **PENDING** |
| G5-08 | Échecs sûrs et absence de secrets | Canary + typed errors + audit | **PENDING** |
| G5-09 | Anti-abus selon exposition | Guard + tests fail-closed | **PENDING** |
| G5-10 | Isolation multi-tenant | 2 scopes, 2 processes, collisions | **PENDING** |
| G5-11 | Anti-énumération qualifiée selon host | HTTP comparateur + timing report | **PENDING** |
| G5-12 | Concurrence et résilience | Stress, timeout, chaos | **PENDING** |
| G5-13 | Qualité CI multi-OS sur SHA final | 7/7, source, wheel, scans | **PENDING** |
| G5-14 | ADR et contrats publics approuvés | Review écrite sur ADR et API | **PENDING** |
| G5-15 | Risques et revue indépendante | Reviewer éligible, owners signés | **PENDING** |
| G5-16 | Décision formelle et post-merge | GO signé, merge autorisé, main CI | **PENDING** |

## Registre des decisions manquantes

- [ ] Owner ratifie le plan M4 source, la matrice 39 P0 / 1 P1 et ses
  ecarts possibles (issue #78).
- [ ] G5-01 : owner tranche dependance M3 PR #75 / base M2.
- [ ] T28 : owner decide NO_OVERLAP ou BOUNDED_OVERLAP et signe
  `NOT_APPLICABLE` motive si NO_OVERLAP.
- [ ] T25/T35 : contrat autoritatif de coherence de revocation et limites
  de la derniere relecture DB.
- [ ] T29/T31 : profil reseau TLS/proxy, journaux et mesure timing sous un
  protocole defini avec criteres de suffisance explicites.
- [ ] T32/T33 : charge et timeout/resilience pour le host cible.
- [ ] ADR-0016/0017/0018/0019 ACCEPTED avec comptes rendus et objections.
- [ ] Reviewer independant eligible identifie et review rattachee au HEAD
  et enregistre dans GitHub (issue #79).
- [ ] P0 individuellement valides, P1 arbitre, chaque G5 signee.
- [ ] Autorite de gate enregistre GO/NO-GO motive, risques residuels,
  owner, role, date et SHA exact.
- [ ] Avant merge : test du ruleset, checks requis, Draft leve si autorise.
- [ ] Apres merge : checks sur `main` et verification du SHA final.
- [ ] Publication/release examinee seulement dans son gate distinct.

## Revue et decision

| Role | Nom / login | Conclusion | Date, SHA, lien |
| --- | --- | --- | --- |
| Owner / arbitre du gate | **NON RENSEIGNE** | **NO-GO maintenu** | **PENDING** |
| Reviewer crypto independant | **NON RENSEIGNE** | **PENDING** | **PENDING** |
| Reviewer host/security | **NON RENSEIGNE** | **PENDING** | **PENDING** |

**La demande de l'owner de finaliser le chantier n'est pas,
en elle-meme, une acceptation circonstanciee des risques.
Aucun GO, aucune fusion, aucun publish ne sont imputes au dossier.**
