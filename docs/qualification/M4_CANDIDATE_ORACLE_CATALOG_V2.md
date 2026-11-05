# M4 - Catalogue de qualification aligné sur le plan détaillé (v2)

> **Status : SPECIFIED / PENDING OWNER ADOPTION / NO-GO**
> Source : `docs/qualification/M4_2026_11_05_SOURCE_MATRIX.md` et plan M4 détaillé du 05/11/2026.
> **Remplace intégralement V1 et les significations candidates initiales.**
> Le statut `EVIDENCE_REFERENCED` confirme une référence de test, pas
> une adjudication indépendante ni une autorisation de fusion.
> Le plan décrit **39 P0, 1 P1 (M4-T28)**.

| ID | Priorité | Oracle du plan | État technique candidat | Limite particulière |
| --- | --- | --- | --- | --- |
| M4-T01 | P0 | Clé complète active, source et scope valides, policy ALLOW | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T02 | P0 | Clé complète valide, policy DENY | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T03 | P0 | Secret complet incorrect, selector existant | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T04 | P0 | Selector valide mais secret absent | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T05 | P0 | Selector inconnu | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T06 | P0 | Lookup ambigu/collision non admissible | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T07 | P0 | Clé SUSPENDED/DISABLED | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T08 | P0 | Clé REVOKED | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T09 | P0 | Instant now == expires_at | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T10 | P0 | now < not_before puis égalité | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T11 | P0 | Clé tenant A sous scope B | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T12 | P0 | Même key_id dans A et B | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T13 | P0 | claimed_tenant ou X-Tenant forgé | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T14 | P0 | VerificationContext étranger / forgé | PARTIAL | Le contexte étranger est testé via le gate M2 et une incohérence de méthode. Une falsification complète de contexte validée par le host catalog n'a pas de mécanisme de trust autonome côté SPI. |
| M4-T15 | P0 | Retour illégal Authenticated par adapter | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T16 | P0 | Record subject_ref.scope_ref étranger | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T17 | P0 | key_ref inconnue, algorithme absent | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T18 | P0 | MAC/digest 1 bit modifié | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T19 | P0 | Format non canonique, mauvaise base64url | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T20 | P0 | Clé énorme, vide, Unicode inattendu | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T21 | P0 | Store offline/timeout | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T22 | P0 | Secret manager/verifier indisponible | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T23 | P0 | Révocation entre lookup et full-secret compare | PARTIAL | Les tests actuels révoquent après preuve, pas explicitement entre lookup et comparaison. Test de course dédié à ajouter. |
| M4-T24 | P0 | Révocation entre compare et relecture autoritative | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T25 | P0 | Reprise après revoke multi-processus | PARTIAL | Deux processus et révocation après commit testés dans le banc local; aucune fenêtre de propagation de production revendiquée ni instrumentée. |
| M4-T26 | P0 | Clé de dev présentée sur prod | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T27 | P0 | Ancien secret pendant rotation NO_OVERLAP | PARTIAL | La rotation versionnée NO_OVERLAP est simulée dans le propriétaire de test, sans procédure réelle d'émission/rotation KMS. |
| M4-T28 | P1 | Overlap explicitement borné | MISSING | Aucun mécanisme BOUNDED_OVERLAP retenu ou approuvé dans le credential owner. P1 non dispensé: choix NOT_APPLICABLE à signer si NO_OVERLAP est adopté. |
| M4-T29 | P0 | Secret canary en repr/exception/log/audit/response | PARTIAL | L'événement M2 et le corps HTTP sont testés, mais pas les logs reverse-proxy/SIEM de production ni l'injection canary de bout en bout. |
| M4-T30 | P0 | HTTP refus missing/wrong/revoked/inactive | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T31 | P0 | Timing HTTP missing vs wrong en laboratoire | PARTIAL | Rapport local reproductible sur 20+20 réponses, sans équivalence statistique ni proxy réel. |
| M4-T32 | P0 | 100+ requêtes concurrentes, store slow | PARTIAL | 128 tentatives concurrentes en laboratoire avec store ralenti et sémaphore, pas de SLO charge ni saturation multi-noeuds production. |
| M4-T33 | P0 | Requête annulée/timeout au cours d'un appel externe | PARTIAL | Annulation de guard et timeout du moteur M2 testés, cleanup pendant une opération PostgreSQL/Redis réelle non prouvé. |
| M4-T34 | P0 | Guard indisponible ou quota épuisé | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T35 | P0 | Cache stale et backend unavailable | PARTIAL | Adapter strict sans cache positif, sources PG indisponibles testées. Contrat de cohérence cache/prod non identifié. |
| M4-T36 | P0 | Registry sans API_KEY | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T37 | P0 | Contract tests sur deux resolvers | EVIDENCE_REFERENCED | Preuve liée au code/labo; revue de l'assertion, de la source et des limites requise avant APPROVED. |
| M4-T38 | P0 | M1/M2/M3 non-régression selon base autorisée | PARTIAL | Tests M1/M2 re-exécutés, mais M3 PR #75 non fusionnée sur la base M2 et GATE27-04 pas GO. |
| M4-T39 | P0 | Wheel sans extras | PARTIAL | Nouveau smoke depuis le wheel installé et sans extras ajouté. Réussite exacte des cinq jobs à revalider sur HEAD après ces commits. |
| M4-T40 | P0 | Wheel + extension API Key sur 5 jobs matrice | PARTIAL | Nouveau smoke HMAC complet sur wheel installé ajouté. Matrice cinq plateformes et résultats exact-SHA à revalider. |

## Gate formel G5-01..G5-16

| ID | Critère exact du plan | Preuve requise | NO-GO si | Statut |
| --- | --- | --- | --- | --- |
| G5-01 | Préconditions M2/M3 satisfaites selon base | HEAD main et gates amont | Dépendance non qualifiée masquée | PENDING |
| G5-02 | Scope/source autoritatifs | Test SQL/callback et cross-tenant | Lookup global permissif | PENDING |
| G5-03 | Full-key only | Prefix-only et secret incomplet refusés | Selector authentifiant seul | PENDING |
| G5-04 | Crypto choisie et explicitée | ADR, vecteurs HMAC, rotation key_ref | Fallback inconnu / digest naïf | PENDING |
| G5-05 | États et UTC sûrs | Active/not-before/expiry/status | Révoquée/expirée acceptée | PENDING |
| G5-06 | Version/révocation cohérentes | is_current real store, race tests | Garantie revendiquée non démontrée | PENDING |
| G5-07 | Séparation AuthN/AuthZ et type acteur | SPI M2/policy, no RBAC | Service key -> permission implicite | PENDING |
| G5-08 | Échecs sûrs et absence de secrets | Canary + typed errors + audit | Fuite brute ou succès sur erreur | PENDING |
| G5-09 | Anti-abus selon exposition | Guard + tests fail-closed | Quota revendiqué sans preuve | PENDING |
| G5-10 | Isolation multi-tenant | 2 scopes, 2 processes, collisions | Foreign credential accepté | PENDING |
| G5-11 | Anti-énumération qualifiée selon host | HTTP comparateur + timing report | Fuite d'identifiant exploitable non traitée | PENDING |
| G5-12 | Concurrence et résilience | Stress, timeout, chaos | Succès tardif / cache stale | PENDING |
| G5-13 | Qualité CI multi-OS sur SHA final | 7/7, source, wheel, scans | Run SHA incorrect/skipped | PENDING |
| G5-14 | ADR et contrats publics approuvés | Review écrite sur ADR et API | ADR encore PROPOSED | PENDING |
| G5-15 | Risques et revue indépendante | Reviewer éligible, owners signés | Auto-approval ou risques sans owner | PENDING |
| G5-16 | Décision formelle et post-merge | GO signé, merge autorisé, main CI | Déclaration « closed » sans preuve | PENDING |

## Règles de promotion

1. `NOT_OBSERVED` ou `PARTIAL` ne peut jamais être compté comme P0 réussi.
2. Une preuve de laboratoire ne couvre pas automatiquement le véritable host.
3. `M4-T28` nécessite une décision explicite de politique de rotation :
   `NO_OVERLAP` peut conduire à un `NOT_APPLICABLE` documenté,
   jamais automatique.
4. `M4-T38` dépend de la stratégie acceptée pour la branche M3 PR #75,
   qui n'est pas fusionnée sur `main`.
5. `G5-14`, `G5-15` et `G5-16` nécessitent ADR,
   revue indépendante, décision humaine et vérification post-merge.
6. Le manifest JSON sert de pointeur vers preuves; sa validation automatisée
   ne remplace pas les décisions nominatifs.
