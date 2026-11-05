# M4 - Rapprochement avec les exigences canoniques, sans fausse qualification

- Date : 2026-11-05
- Portee : PR #76, issue #77, revue contradictoire technique
- Sources canoniques disponibles dans le depot :
  - [27 - Roadmap, section 17, lignes 266-276](../specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md)
  - [27 - Work Packages, lignes 857-860](../specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md)
  - [27 - Gates P0/P1 et GATE27-05, section 56](../specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md)
  - [28 - Bootstrap, section 49 PR-07](../specs/28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md)
- **Statut : analyse de correspondance provisoire. NON CANONIQUE / NON APPROUVEE.**

## 1. Resultat de la confrontation documentaire

Le plan 27 definit le probleme, les ports `PORT-OUT-03` et
`PORT-OUT-04`, les comportements de cle active/inactive/revoquee,
l'isolation multi-tenant, les limites d'entree, la rotation sous politique
explicite et le gate global `GATE27-05`. Le plan 28 §49 ajoute les tests
suffixe/prefixe, record corrompu, timeout, race de revocation et le besoin
d'un backend reel si une coherence `read-after-revoke` est revendiquee.

**Absences constatees dans ces deux fichiers :** aucun identifiant
`M4-T01` a `M4-T40`, aucun `G5-01` a `G5-16`, aucune definition
individuelle ayant statut de norme acceptee. Les fichiers de qualification
preexistants exposent un **decoupage candidat** de 40/16, et non une
transcription du plan 27/28. Il n'est pas possible de declarer que tous les
oracles individuels sont "reconcilies" sans source canonique additionnelle ou
decision explicite de l'owner sur un nouveau referentiel.

## 2. Matrice de correspondance des exigences qualitatives

Les IDs `XW-M4-*` sont uniquement des **reperes de revue** inventes pour
cette analyse. Ils ne remplacent aucun ID du plan source.

| Repere de revue | Exigence du plan source, reformulee | Preuve technique identifiable | Lacune / decision requise |
|---|---|---|---|
| XW-M4-01 | 27 §17, selector/prefix seul n'est pas preuve | Parser strict, HMAC secret complet, M4-T05..10 candidats | Revue de l'algorithme et de l'ADR-0016 |
| XW-M4-02 | 27 §17, lookup scope-bound et aucune cle tenant A en B | Port resolver; SQL `WHERE scope_id=$1 AND key_id=$2`; test 2 tenants | Prove only reference SQL, pas owner/ORM production |
| XW-M4-03 | 27 §17, active/inactive/expired/revoked denies | M4-T21..26, version read-back, CAS PostgreSQL | Coherence apres dernier read non garantie |
| XW-M4-04 | 27 §17, collision et resultat ambigu ne peuvent etre accepte | M4-T11..15, typed `ApiKeyAmbiguous` | Prouver sous DB cible / cache effectif |
| XW-M4-05 | 27 §17, limites d'entree et compteurs d'utilisation | Parser borne, guard Redis Lua, concurrent quota | Politique de budget verifiee sous charge reelle |
| XW-M4-06 | 27 §17, rotation/parallel keys seulement sous regle explicite | Approved key-ref allowlist et `rotate_cas` fixture | Protocole de reissue/rotation du KMS non approuve |
| XW-M4-07 | 27 §17, panne store traitée sans fallback | 503 reference, `ErrorOutcome` M2 | RTO/incident et type de panne production manquants |
| XW-M4-08 | 27 §17, preuve robuste et trace minimisee | `compare_digest`, test redacted event | Traces ingress/SIEM et logs durables non prouves |
| XW-M4-09 | 28 §49, prefix/suffix, record corrompu, timeout refus | tests parser, verification guard, timeout M2 | Oracle independant corruption/timeout a qualifier |
| XW-M4-10 | 28 §49, race de revocation et backend reel | deux Uvicorn, PostgreSQL CAS/recheck, Redis | SLO de revocation dans deploiement cible absent |
| XW-M4-11 | 27 §56, tests P0/P1 applicables avant GO | 209 core tests + 12 host tests au dernier checkpoint de dossier | Definition complete P0/P1 / owner signoff absents |
| XW-M4-12 | 27 §56, gate refuse si revoked/expired/foreign accepte | tests rejet + policy gate | Reviewer independant et gate formalise absents |
| XW-M4-13 | 28 §49, absence d'API de provisionnement de cles | package M4 ne fournit pas d'API issuer; reference host fixture | Revue API publique et garantie SDK a confirmer |

## 3. Divergences / zones hors du cadre des textes canoniques

1. **40 oracles et 16 G5 :** utiles pour une approche defense-in-depth,
   mais les textes 27/28 ne definissent pas ces subdivisions. Le responsable
   doit soit fournir leur source autoritaire, soit approuver leur adoption
   formelle comme nouvelles exigences a versionner.
2. **Expiration requise par le code :** politique MVP plus restrictive
   dans ADR-0018 PROPOSED; le plan source demande de verifier l'expiration,
   sans imposer dans ses extraits `expires_at` obligatoire dans chaque
   record. Trancher la decision et la compatibilite.
3. **Protection anti-rejeu :** non prevue comme garantie forte des cles
   bearer par le plan source; le test de rejeu illustre une limitation et
   implique une politique TLS, de surveillance et de revocation.
4. **Timing et reverse proxy :** la CI locale ne permet pas une conclusion
   anti-enumeration generale ni une certification de perimetre reseau.
5. **Preuve du deploiement :** la sous-composition FastAPI de test est
   hors wheel et ne vaut pas certification d'un hote de production.

## 4. Decision a obtenir

- [ ] Mainteneur: adopter/rectifier chaque `XW-M4-01..13`.
- [ ] Identifier les definitions officielles des `M4-T01..40` et
      `G5-01..16` ou approuver formellement le nouveau catalogue candidat.
- [ ] Faire signer ADR-0016/0017/0018 par les roles competents.
- [ ] Qualifier les risques du registre R-M4 et le nouveau finding F-M4-01.
- [ ] Assigner des oracles a un reviewer independant (nom, role, date, SHA,
      compte rendu et preuve).
- [ ] Decision formelle GO/NO-GO sur le SHA exact; M3 Gate27-04 a clarifier.

**Verdict de cette confrontation : CORRESPONDANCE QUALITATIVE PARTIELLE.
SOURCE NORMATIVE INDIVIDUELLE ABSENTE. FORMAL GATE27-05 NO-GO.**
