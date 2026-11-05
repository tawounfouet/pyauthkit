> **ATTENTION - ARCHIVE HISTORIQUE SUPERSEDEE.** La signification des identifiants
> M4-T01..T40 / G5-01..16 dans ce fichier n'est pas alignée avec le
> plan détaillé M4 du 05/11/2026. **NE PAS UTILISER POUR UNE DECISION.**
> Matrice fidèle à la source : `docs/qualification/M4_2026_11_05_SOURCE_MATRIX.md`.
> Catalogue réconcilié : `docs/qualification/M4_CANDIDATE_ORACLE_CATALOG_V2.md`.
> Les anciens chiffres/états ci-dessous décrivent uniquement les étapes historiques.
>
# Dossier de qualification securite M4 - API Key Authentication

> **Date :** 05 novembre 2026 | **Statut :** DOSSIER CANDIDAT / TECHNICAL TESTED, **GATE27-05 NO-GO**  
> **PR-07 :** [#76](https://github.com/tawounfouet/pyauthkit/pull/76) (Draft) | **Chantier de qualification :** [#77](https://github.com/tawounfouet/pyauthkit/issues/77) (Open)  
> **Perimetre :** WP27-023..WP27-026; taches proposees WP28-045..060. Les libelles M4-T01..T40 et G5-01..16 sont **des correspondances candidates** et doivent etre rapproches du plan M4 canonique avant approbation.  
> **Sources d'autorite :** `docs/qualification/M4_PR07_SECURITY_ORACLES.md`, `GATE27-05_M4_API_KEY_DECISION.md`, ADR-0016/0017/0018, code et CI GitHub.  
> **Convention d'apprentissage :** distinguer CONCEPTUAL, PROPOSED, IMPLEMENTED, TESTED, QUALIFIED et RELEASED. Aucune promotion silencieuse du statut.

## 1. Synthese et verdict

**Decision actuelle : NO-GO / NON FORMELLEMENT ADJUGE.**

Le moteur M2 orchestre une chaine API Key construite dans PR-07A/B/C : contexte hote de confiance, enregistrement d'une reference de credential dans un tenant approuve, HMAC-SHA-256 sur le secret complet, statut/fenetres temporelles, controle de version apres preuve, et decision finale par `AuthenticationPolicyGate`. Le lot D ajoute un **banc de reference** avec PostgreSQL, Redis et Uvicorn, pas un service de production.

| Nature de la preuve | Constat du 05/11/2026 | Ce que cela **ne prouve pas** |
|---|---|---|
| Commit source et CI | `5f908614e597ea358b69cd469ee3d5ebd30cbb2d`, [run 42060406108](https://github.com/tawounfouet/pyauthkit/actions/runs/42060406108), **8/8 SUCCESS** | Une revue independante, une conformite universelle ou un GO |
| Tests noyau | **207 passed** dans le job quality sur le SHA ci-dessus | La robustesse du deploiement final |
| Tests hote reference | **12 passed** PostgreSQL/Redis/HTTP sur le meme SHA | TLS, reverse proxy, KMS, SIEM, performances a forte charge |
| Enregistrement des oracles | 40 lignes candidates, 34 refs de fonctions de tests existantes, 4 autres cas d'hote candidates, 1 CI et 1 revue | **0/40** adjuge par une personne independante |
| Criteres G5 | 16 descriptions candidates et graphe de correspondance associe | **0/16** adopte ou signe |
| ADR-0016/0017/0018 | Rediges, statut PROPOSED | Aucune decision ACCEPTED par l'autorite prevue |

## 2. Frontieres de confiance et modele de preuve

```text
HTTP request: Authorization ApiKey <bearer secret>
   -> hote choisit la route approuvee et le TrustedEntryContext
   -> M2 preflight + guard Redis de l'hote (scope/peer/selector)
   -> PostgreSQL SELECT WHERE scope_id = $1 AND key_id = $2
   -> verifier HMAC-SHA-256 (reference de cle autorisee par tenant)
   -> PostgreSQL is_current(version, state, expiry)
   -> VerifiedOutcome interne lie a la tentative
   -> M2 AuthenticationPolicyGate.final_decision
   -> Authenticated | Rejected | AuthError
```

**Invariants a revoir :** un selecteur ne prouve pas la possession; le client ne fixe pas le tenant; un HMAC positif n'accorde ni droit IAM ni session; une cle revoquee/expiree ne peut produire un principal; une panne garde/store/KMS doit etre fail-closed; un log ne contient pas de secret bearer. Un echec apres la derniere lecture autoritaire reste un risque de coherence non elimine par le test CAS.

## 3. Registre des preuves, reproductibilite et provenance

Le fichier `M4_EVIDENCE_MANIFEST.json` indexe explicitement les **40 oracles candidats**, **16 criteres G5**, tests, job IDs et lacunes. `python scripts/check_m4_evidence.py` controle localement la forme et la coherence de ce registre avec le code, les specifications et la configuration CI. Il **ne valide pas** la veracite des resultats d'un service distant et **ne signe pas** une revue de securite.

**Preuve figee :**

- SHA GitHub : [5f908614](https://github.com/tawounfouet/pyauthkit/commit/5f908614e597ea358b69cd469ee3d5ebd30cbb2d).
- Workflow : [42060406108](https://github.com/tawounfouet/pyauthkit/actions/runs/42060406108). Jobs : quality `127360160012`, security `127360159499`, host `127360160208`. Cinq jobs packaging : Ubuntu Python 3.12/3.13/3.14, macOS 3.12 et Windows 3.12.
- Journal quality : `207 passed in 3.42s`; journal host : `12 passed in 7.52s`. Cote host, observation de timing sur 20 cas faux-secret et 20 cas selecteur absent : medianes 82.993 et 82.915 ms. Ce chiffre n'est ni une preuve d'equivalence statistique ni une promesse de temps constant.
- Tests host : `qualification/m4_host/tests` (exclus de l'invocation pytest par defaut). Le banc emploie une base ephemere PostgreSQL 17 et Redis 7. Aucun veritable secret de production n'est utilise.

**Verification par un examinateur :**

```bash
git fetch origin
git checkout --detach 5f908614e597ea358b69cd469ee3d5ebd30cbb2d
python scripts/check_architecture.py
python -m pytest -v
# Sur une machine avec des services de test isoles, variables M4_PG_DSN/M4_REDIS_URL:
python -m pytest -v -s qualification/m4_host/tests
# Verification du dossier courant sur la branche PR-07:
python scripts/check_m4_evidence.py
```

Le script de verification du dossier est introduit **apres** le checkpoint technique precedent. Il faut donc reexecuter la CI sur le nouveau SHA documentaire, sans attribuer ces nouveaux controles retroactivement au checkpoint `5f908614`.

**Limite de retention :** les URL des logs GitHub ne constituent pas un archivage perpetuel. Le relecteur doit exporter les journaux pertinents, leurs IDs, un hash SHA-256 des archives, leur emplacement immuable, et une signature de revue. **Archivage/signes : PENDING.**

## 4. Matrice de couverture M4-T01..M4-T40

Le tableau precedent `M4_PR07_SECURITY_ORACLES.md` demeure la source candidate des libelles. Le manifeste reprend ces 40 IDs sans inventer de canon.

- **M4-T01..T33 :** liens vers des tests du noyau (preuve `CODE_TEST` uniquement).
- **M4-T34 :** test de rejeu bearer observable, **non-prevention** : revue TLS/incident/mitigation non realisee.
- **M4-T35 :** CAS/rotation/revocation et recheck dans PostgreSQL de reference; pas de garantie de coherence apres la derniere lecture.
- **M4-T36 :** requete source-filtrante par scope, selecteurs identiques sur deux tenants, deux processus distincts Uvicorn; caches et deploiement tiers non testes.
- **M4-T37 :** reponses HTTP 401, quotas atomiques Redis, spoofing `X-Forwarded-For` ignore dans le banc, echantillon timing loopback; aucun test de proxy productif.
- **M4-T38 :** test de redaction evenement; **durabilite des audits non verifiee**.
- **M4-T39 :** jobs CI et journal; provenance conservee sous URL GitHub avec limite de retention.
- **M4-T40 :** signoff securite independent, ADR et decision de gate **absents**.

**Statut commun : 40/40 en attente d'adjudication independante.** Une ligne `CODE_TEST_PRESENT` ne doit jamais etre convertie par automatisme en `QUALIFIED`.

## 5. Criteres de sortie G5-01..G5-16

Le fichier JSON relie chaque critere candidat aux oracles supportant son examen. Les preuves se repartissent entre :

- **Technique candidate :** architecture M2, format `ak1`, secret complet et verification, horloge, statut, quotas Redis, SQL par scope, CAS, CI multi-OS.
- **Operations non prouvees :** gestion KMS effective, rotation et urgence d'exposition, TLS/proxy, charge et SLO, audit durable, traces securisees, fenetre de revocation mesurable en production.
- **Gouvernance absente :** acceptation de 3 ADR, revue securite independante, definitions canoniques, decisions explicites pour chacun des 16 criteres, identification d'une autorite GO.

La matrice `docs/qualification/GATE27-05_M4_API_KEY_DECISION.md` et le `M4_SECURITY_REVIEW_CHECKLIST.md` gouvernent le passage de la preuve technique a la decision. Aucun G5 n'est signe.

## 6. Risques, decisions et obligations

Lire `M4_SECURITY_RISK_REGISTER.md` pour l'evaluation provisoire R-M4-01..10. Gravite et priorite sont des estimations candidates, non des acceptations de risque. Aucun risque critique/eleve ne peut etre considere accepte sans nom, date, autorite, duree de validite, mesure compensatoire et preuve.

Decisions ouvertes : ADR-0016 (format, HMAC et KMS), ADR-0017 (proprietaire des credentials, isolation source), ADR-0018 (expiration obligatoire et autorite des versions), coordination avec le GATE27-04 M3, regles du proxy et politique anti-rejeu.

## 7. Passage au jugement independant

Le `M4_SECURITY_REVIEW_CHECKLIST.md` sert a verifier : identite du relecteur, independance de la revue, SHA unique, environnement, journaux, tests negatifs, carte des risques, ADR, criteres et verdict. Un avis doit inclure le texte de la decision et son lien GitHub immuable ou l'enregistrement officiel equivalent.

**Regle de cloture :** sans toutes ces preuves, verdict **NO-GO / NOT FORMALLY ADJUDICATED**. Ne pas fusionner PR #76, publier sur PyPI, declarer M4 qualifie ou deployer le banc de reference en production.

## 8. Design Learning Card

- [DDD] `ApiKeyVerifierRecord` : read model du credential; pas d'agregat proprietaire du cycle de vie.
- [Hexagonal / DIP] resolver et key-source ports, adapters PostgreSQL/Redis hors du noyau.
- [GoF: Strategy] `ApiKeyAuthenticator` s'inscrit dans le SPI M2; pas de moteur parallele.
- [Security] scope choisi par l'hote, preuve HMAC complete, revalidation de version, politique finale, refus fail-closed.
- [Testing / Runtime] preuves sur fuite, isolement, concurrence/CAS, deux processus OS et modes d'echec.
- [Transfer] Un test vert de l'adapter montre un comportement **dans un environnement**. La qualification exige une trace causale jusqu'aux menaces, limites, preuves et decisions.

## 9. Revue contradictoire technique et source normative (2026-11-05)

- **Crosswalk:** `M4_CANONICAL_REQUIREMENTS_CROSSWALK.md` distinguishes
  normative section 27 §17/§56 and section 28 §49 from the 40/16 candidate
  indexes. There are **zero** literal `M4-T01..T40` or `G5-01..16`
  entries in source specifications 27 and 28. Therefore no one-to-one
  canonical acceptance mapping can legitimately be asserted from those
  documents alone.
- **Reference-host hardening:** duplicate HTTP Authorization headers must
  be treated as malformed evidence and pass the same rate guard before
  returning generic 401. This changes only `qualification/m4_host`,
  not the distributable PyAuthKit authentication engine.
- **Security reviewer status:** this review is an assistant technical
  review, **not an independent qualified signer**. Formal GATE27-05
  remains NO-GO until the owner accepts actual oracles and risks.
