# M4 - Matrice extraite du plan d'implémentation du 05/11/2026

> **Source documentaire précise :** fichier de référence fourni dans le projet
> `2026-11-05_PYAUTHKIT_M4_API_KEY_AUTHENTICATION_IMPLEMENTATION_PLAN.md`, sections **20** et **22**.
> **Statut : SPECIFIED / non encore approuvé comme décision de gate.**
> Les intitulés ci-dessous préservent les situations, résultats attendus, priorités
> et critères de sortie de ce plan. La typographie inline a été normalisée.
> Les spécifications générales 27 et 28 ne contiennent pas cette numérotation;
> le plan détaillé M4 la fournit. Le plan entier doit être mis à disposition du reviewer.
> **EXPECTED signifie exigé, non exécuté ni approuvé.**

## Section 20 - Oracles M4-T01..M4-T40

| Oracle | Priorité | Situation | Résultat attendu / preuve |
| --- | --- | --- | --- |
| M4-T01 | P0 | Clé complète active, source et scope valides, policy ALLOW | Authenticated seulement après policy M2 |
| M4-T02 | P0 | Clé complète valide, policy DENY | Rejected, aucun principal |
| M4-T03 | P0 | Secret complet incorrect, selector existant | Rejected, aucune preuve interne positive |
| M4-T04 | P0 | Selector valide mais secret absent | Rejet avant tentative de promotion |
| M4-T05 | P0 | Selector inconnu | Rejet générique, aucune fuite de présence |
| M4-T06 | P0 | Lookup ambigu/collision non admissible | Refus sans arbitrage arbitraire |
| M4-T07 | P0 | Clé SUSPENDED/DISABLED | Refus indépendamment du secret |
| M4-T08 | P0 | Clé REVOKED | Refus, pas de stale accept |
| M4-T09 | P0 | Instant now == expires_at | Refus à la borne exclusive |
| M4-T10 | P0 | now < not_before puis égalité | Refus puis admission conditionnelle à égalité |
| M4-T11 | P0 | Clé tenant A sous scope B | Refus malgré selector/secret correct pour A |
| M4-T12 | P0 | Même key_id dans A et B | Lookup source-scoped, aucune collision globale |
| M4-T13 | P0 | claimed_tenant ou X-Tenant forgé | Scope effectif inchangé ou refus préflight |
| M4-T14 | P0 | VerificationContext étranger / forgé | Aucun succès et aucun fallback |
| M4-T15 | P0 | Retour illégal Authenticated par adapter | Engine M2 rejette la promotion |
| M4-T16 | P0 | Record subject_ref.scope_ref étranger | Refus / erreur de trust, jamais succès |
| M4-T17 | P0 | key_ref inconnue, algorithme absent | Refus fail-closed, pas de downgrade |
| M4-T18 | P0 | MAC/digest 1 bit modifié | Comparaison négative avec vecteurs indépendants |
| M4-T19 | P0 | Format non canonique, mauvaise base64url | Refus avant lookup/crypto |
| M4-T20 | P0 | Clé énorme, vide, Unicode inattendu | Bornes d'entrée, pas d'allocation illimitée |
| M4-T21 | P0 | Store offline/timeout | AuthError, aucun principal |
| M4-T22 | P0 | Secret manager/verifier indisponible | AuthError, pas de bypass |
| M4-T23 | P0 | Révocation entre lookup et full-secret compare | is_current refuse l'ancien record |
| M4-T24 | P0 | Révocation entre compare et relecture autoritative | Refus sur vrai PostgreSQL |
| M4-T25 | P0 | Reprise après revoke multi-processus | Pas d'acceptation au-delà de la fenêtre revendiquée |
| M4-T26 | P0 | Clé de dev présentée sur prod | Refus par scope/env approuvé |
| M4-T27 | P0 | Ancien secret pendant rotation NO_OVERLAP | Refus après commit de revoke, sous contrat owner |
| M4-T28 | P1 | Overlap explicitement borné | Deux records acceptés seulement dans fenêtre approuvée |
| M4-T29 | P0 | Secret canary en repr/exception/log/audit/response | Zéro fuite détectable |
| M4-T30 | P0 | HTTP refus missing/wrong/revoked/inactive | Codes/corps/headers host comparables selon profil |
| M4-T31 | P0 | Timing HTTP missing vs wrong en laboratoire | Rapport statistique reproductible + limites, sans faux claim |
| M4-T32 | P0 | 100+ requêtes concurrentes, store slow | Ressources bornées, aucun succès illégal |
| M4-T33 | P0 | Requête annulée/timeout au cours d'un appel externe | Aucune promotion tardive; cleanup connu |
| M4-T34 | P0 | Guard indisponible ou quota épuisé | Fail-closed si guard requis, pas de lookup coûteux après refus |
| M4-T35 | P0 | Cache stale et backend unavailable | Aucun succès sous politique stricte |
| M4-T36 | P0 | Registry sans API_KEY | Méthode inconnue, pas d'enregistrement implicite |
| M4-T37 | P0 | Contract tests sur deux resolvers | Mêmes outcomes et invariants de scope |
| M4-T38 | P0 | M1/M2/M3 non-régression selon base autorisée | Aucun test d'autorité cassé |
| M4-T39 | P0 | Wheel sans extras | Import core sans FastAPI/Redis/PG/crypto optionnels |
| M4-T40 | P0 | Wheel + extension API Key sur 5 jobs matrice | Fonctionne avec vrais vecteurs; scans/typing/packaging PASS |

## Section 22 - GATE27-05 : critères G5-01..G5-16

| Gate | Critère de sortie | Preuve exigée | NO-GO si |
| --- | --- | --- | --- |
| G5-01 | Préconditions M2/M3 satisfaites selon base | HEAD main et gates amont | Dépendance non qualifiée masquée |
| G5-02 | Scope/source autoritatifs | Test SQL/callback et cross-tenant | Lookup global permissif |
| G5-03 | Full-key only | Prefix-only et secret incomplet refusés | Selector authentifiant seul |
| G5-04 | Crypto choisie et explicitée | ADR, vecteurs HMAC, rotation key_ref | Fallback inconnu / digest naïf |
| G5-05 | États et UTC sûrs | Active/not-before/expiry/status | Révoquée/expirée acceptée |
| G5-06 | Version/révocation cohérentes | is_current real store, race tests | Garantie revendiquée non démontrée |
| G5-07 | Séparation AuthN/AuthZ et type acteur | SPI M2/policy, no RBAC | Service key -> permission implicite |
| G5-08 | Échecs sûrs et absence de secrets | Canary + typed errors + audit | Fuite brute ou succès sur erreur |
| G5-09 | Anti-abus selon exposition | Guard + tests fail-closed | Quota revendiqué sans preuve |
| G5-10 | Isolation multi-tenant | 2 scopes, 2 processes, collisions | Foreign credential accepté |
| G5-11 | Anti-énumération qualifiée selon host | HTTP comparateur + timing report | Fuite d'identifiant exploitable non traitée |
| G5-12 | Concurrence et résilience | Stress, timeout, chaos | Succès tardif / cache stale |
| G5-13 | Qualité CI multi-OS sur SHA final | 7/7, source, wheel, scans | Run SHA incorrect/skipped |
| G5-14 | ADR et contrats publics approuvés | Review écrite sur ADR et API | ADR encore PROPOSED |
| G5-15 | Risques et revue indépendante | Reviewer éligible, owners signés | Auto-approval ou risques sans owner |
| G5-16 | Décision formelle et post-merge | GO signé, merge autorisé, main CI | Déclaration « closed » sans preuve |

## Note de contrôle de source

Le plan détaillé qualifie `M4-T28` en P1 et les 39 autres oracles en P0.
La décision de gate précise une **revue indépendante et approbation des
owners** pour les critères G5, au SHA exact, avant fusion. Les garanties
de production et de release relèvent d'une décision séparée.

Les anciens registres `M4_PR07_SECURITY_ORACLES.md` et
`M4_CANDIDATE_ORACLE_CATALOG_V1.md` comportent des collisions
sémantiques sur les mêmes identifiants : **ils sont historiques, pas normatifs**.
