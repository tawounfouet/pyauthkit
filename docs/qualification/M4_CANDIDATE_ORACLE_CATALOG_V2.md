# M4 - Catalogue des 40 oracles et 16 G5 (v2 active, plan detaille)

> Source : `M4_2026_11_05_SOURCE_MATRIX.md`, plan d'implementation
> M4 du 05/11/2026 §§20/22. **39 P0, 1 P1 : M4-T28.**
> Les ID V1 preexistants etaient mal attribues et sont SUPERSEDED.
> Ces lignes retracent un plan, pas une review independante.

| Oracle | Priorite | Situation du plan | Couverture candidate | Limites restantes |
| --- | --- | --- | --- | --- |
| M4-T01 | P0 | Clé complète active, source et scope valides, policy ALLOW | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T02 | P0 | Clé complète valide, policy DENY | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T03 | P0 | Secret complet incorrect, selector existant | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T04 | P0 | Selector valide mais secret absent | EVIDENCE_REFERENCED (3 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T05 | P0 | Selector inconnu | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T06 | P0 | Lookup ambigu/collision non admissible | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T07 | P0 | Clé SUSPENDED/DISABLED | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T08 | P0 | Clé REVOKED | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T09 | P0 | Instant now == expires_at | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T10 | P0 | now < not_before puis égalité | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T11 | P0 | Clé tenant A sous scope B | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T12 | P0 | Même key_id dans A et B | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T13 | P0 | claimed_tenant ou X-Tenant forgé | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T14 | P0 | VerificationContext étranger / forgé | EVIDENCE_REFERENCED (3 test(s)) | Ciblage du cas explicite en test local; signoff indépendant, host réel et validation du périmètre restent requis. |
| M4-T15 | P0 | Retour illégal Authenticated par adapter | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T16 | P0 | Record subject_ref.scope_ref étranger | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T17 | P0 | key_ref inconnue, algorithme absent | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T18 | P0 | MAC/digest 1 bit modifié | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T19 | P0 | Format non canonique, mauvaise base64url | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T20 | P0 | Clé énorme, vide, Unicode inattendu | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T21 | P0 | Store offline/timeout | EVIDENCE_REFERENCED (3 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T22 | P0 | Secret manager/verifier indisponible | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T23 | P0 | Révocation entre lookup et full-secret compare | EVIDENCE_REFERENCED (2 test(s)) | Ciblage du cas explicite en test local; signoff indépendant, host réel et validation du périmètre restent requis. |
| M4-T24 | P0 | Révocation entre compare et relecture autoritative | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T25 | P0 | Reprise après revoke multi-processus | PARTIAL (1 test(s)) | Deux processus et révocation après commit testés dans le banc local; aucune fenêtre de propagation de production revendiquée ni instrumentée. |
| M4-T26 | P0 | Clé de dev présentée sur prod | EVIDENCE_REFERENCED (1 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T27 | P0 | Ancien secret pendant rotation NO_OVERLAP | PARTIAL (2 test(s)) | La rotation versionnée NO_OVERLAP est simulée dans le propriétaire de test, sans procédure réelle d'émission/rotation KMS. |
| M4-T28 | P1 | Overlap explicitement borné | MISSING (0 test(s)) | Aucun mécanisme BOUNDED_OVERLAP retenu ou approuvé dans le credential owner. P1 non dispensé: choix NOT_APPLICABLE à signer si NO_OVERLAP est adopté. |
| M4-T29 | P0 | Secret canary en repr/exception/log/audit/response | PARTIAL (2 test(s)) | L'événement M2 et le corps HTTP sont testés, mais pas les logs reverse-proxy/SIEM de production ni l'injection canary de bout en bout. |
| M4-T30 | P0 | HTTP refus missing/wrong/revoked/inactive | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T31 | P0 | Timing HTTP missing vs wrong en laboratoire | PARTIAL (1 test(s)) | Rapport local reproductible sur 20+20 réponses, sans équivalence statistique ni proxy réel. |
| M4-T32 | P0 | 100+ requêtes concurrentes, store slow | PARTIAL (1 test(s)) | 128 tentatives concurrentes en laboratoire avec store ralenti et sémaphore, pas de SLO charge ni saturation multi-noeuds production. |
| M4-T33 | P0 | Requête annulée/timeout au cours d'un appel externe | PARTIAL (3 test(s)) | Annulation de guard et timeout du moteur M2 testés, cleanup pendant une opération PostgreSQL/Redis réelle non prouvé. |
| M4-T34 | P0 | Guard indisponible ou quota épuisé | EVIDENCE_REFERENCED (3 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T35 | P0 | Cache stale et backend unavailable | PARTIAL (3 test(s)) | Adapter strict sans cache positif, sources PG indisponibles testées. Contrat de cohérence cache/prod non identifié. |
| M4-T36 | P0 | Registry sans API_KEY | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T37 | P0 | Contract tests sur deux resolvers | EVIDENCE_REFERENCED (2 test(s)) | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T38 | P0 | M1/M2/M3 non-régression selon base autorisée | PARTIAL (1 test(s)) | Tests M1/M2 re-exécutés, mais M3 PR #75 non fusionnée sur la base M2 et GATE27-04 pas GO. |
| M4-T39 | P0 | Wheel sans extras | PARTIAL (0 test(s)) | Nouveau smoke depuis le wheel installé et sans extras ajouté. Réussite exacte des cinq jobs à revalider sur HEAD après ces commits. |
| M4-T40 | P0 | Wheel + extension API Key sur 5 jobs matrice | PARTIAL (0 test(s)) | Nouveau smoke HMAC complet sur wheel installé ajouté. Matrice cinq plateformes et résultats exact-SHA à revalider. |

## G5 de reference

| G5 | Critere du plan | Preuve exigee | Decision |
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

**0/40** adjudications independantes et **0/16** decisions G5
enregistrees. Le statut `EVIDENCE_REFERENCED` n'est pas
`PASS_TECHNICAL` ni `APPROVED`. Pour toute divergence
de test/attendu, ouvrir un finding lie a l'ID source.
