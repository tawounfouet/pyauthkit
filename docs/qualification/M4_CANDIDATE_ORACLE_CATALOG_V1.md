# M4 - Proposition de catalogue d'oracles et de criteres G5 v1.0

> **Statut : PROPOSED - NOT CANONICAL / NOT APPROVED**
> Date de preparation : 2026-11-05 | Emplacement : branche Draft PR #76
> Provenance : documentation 27 (sections 17, 56, WP27-023..026), documentation 28 (section 49), M4_EVIDENCE_MANIFEST.json et tests presents au SHA technique qualifie.
> **Avertissement :** les sources 27/28 ne numerotent ni 40 oracles M4-T ni 16 criteres G5. Cette proposition est une nouvelle subdivision de travail. Elle ne prend autorite qu'apres decision explicite de l'owner et revue de securite independante. Aucune signature/acceptation n'est fournie ici.

## 1. Statuts et discipline de qualification

- `PROPOSED`: description candidate soumise a une decision.
- `CODE_TEST`: test nomme dans le depot ; n'implique pas une assertion correcte ni une revue independante.
- `REFERENCE_HOST`: preuve limitee au laboratoire PostgreSQL/Redis et HTTP loopback, hors wheel.
- `CI_RUN`: etat Github Actions sur un SHA precise ; les journaux peuvent expirer.
- `NOT_OBSERVED`: aucune preuve technique suffisante visible.
- `ADJUDICATED`: reserve a une decision nominative d'un relecteur independant, avec decision et source verifiable; **aucune ligne ne l'est aujourd'hui**.

## 2. Catalogue candidat des 40 oracles

Chaque ligne doit etre revue contre la menace, l'entree, le resultat attendu, les limites de preuve et le responsable. Un test vert ne vaut pas qualification de la propriete dans tous les environnements.

| ID candidat | Comportement / oracle de securite propose | Preuve existante dans le registre | Statut d'adjudication |
| --- | --- | --- | --- |
| M4-T01 | SPI M2 route API_KEY, une unique verification et un resultat final uniquement depuis le moteur | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T02 | Preuve cryptographique valide mais policy finale defavorable -> refus sans principal | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T03 | Contexte hote scope B + claim tenant A -> aucun principal ni switch de scope | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T04 | Evidence malformee, tronquee ou > limites -> aucun succes; aucun lookup permissif | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T05 | ak1, 16 octets selector + 32 octets secret, encodage exact et longueur stricte | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T06 | Alias base64url (spare bits, padding, unicode) rejetes sans seconde interpretation | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T07 | Selector seul ou modifie ne donne aucun acces ni comparaison HMAC positive | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T08 | Vecteur HMAC positif independant sur secret complet; comparaison du digest 32 octets | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T09 | Mutation de chaque octet testee du bearer -> mismatch; pas d'acceptation partielle | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T10 | Verifier digest modifie -> comparaison false, aucun principal | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T11 | Selector identique sur tenants distincts -> seuls les records du scope hote sont lus | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T12 | Record trouve dans un autre scope -> indisponibilite ou refus, jamais confiance | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T13 | Selector absent -> refus sans verification et sans signal d'existence | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T14 | Resultat ambigu -> erreur de confiance, jamais choix implicite d'un premier candidat | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T15 | Store injoignable -> erreur technique sans fallback cross-scope | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T16 | key_ref non allowliste par scope -> configuration invalide, pas de lecture de cle | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T17 | Materiel HMAC approuve manquant -> erreur technique, aucune cle par defaut | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T18 | Algorithme hors allowlist -> refus d'activation; pas de downgrade | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T19 | Snapshot politique scopes/keys ne change pas apres composition | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T20 | Panne source de cle -> pas d'Authenticated, erreur technique | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T21 | Credential disabled/suspended/revoked -> refus avant preuve exploitable | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T22 | Horodatage nbf futur selon clock de confiance -> refus | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T23 | Instant t >= expires_at -> refus, limite incluse | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T24 | expires_at absent selon politique MVP proposee -> refus conservateur | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T25 | Revoquer apres HMAC avant relecture autoritaire -> refus | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T26 | Remplacement/version stale -> is_current false, aucun principal | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T27 | Horloge fournie par caller non authoritative; clock systeme/injectee seule admise | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T28 | Verifier positif sans policy finale -> Rejected, jamais Authenticated | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T29 | Preuve complete + policy explicite + scope concordant -> Authenticated uniquement par M2 | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T30 | Claim tenant ne remplace pas scope/TrustProfile hote | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T31 | Absence de guard a la composition -> impossible de construire authenticator | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T32 | Guard denied ou truthy non-bool -> aucune consultation resolver/proof ni succes | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T33 | Guard panne -> ErrorOutcome fail-closed, pas de bypass | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T34 | Rejeu bearer observe au banc; le protocole ne promet pas d'anti-rejeu; protocole TLS/incident reste a qualifier | REFERENCE_HOST (1 noeud(s)) | **PENDING** |
| M4-T35 | Revoke/rotate CAS sous concurrence : seul winner version; stale proof refuse; linearizabilite apres dernier read non prouvee | REFERENCE_HOST (3 noeud(s)) | **PENDING** |
| M4-T36 | SELECT scope_id + key_id dans PostgreSQL; collision deux tenants et 2 processus ; caches prod non prouves | REFERENCE_HOST (2 noeud(s)) | **PENDING** |
| M4-T37 | Refus HTTP uniformes selectionnes, quota Redis partage, Authorization duplique rejete; proxy/timing global non prouves | REFERENCE_HOST (4 noeud(s)) | **PENDING** |
| M4-T38 | Evenement audit redige; pas de secret dans repr; audit durable/SIEM restant a qualifier | CODE_TEST (1 noeud(s)) | **PENDING** |
| M4-T39 | CI exact SHA et matrice OS + scan PASS, journaux et provenance a conserver hors retention | CI_RUN (0 noeud(s)) | **PENDING** |
| M4-T40 | 40 oracles individuellement examines et signes; 16 G5/ADR/risk signes au SHA; autorite humaine GO/NO-GO | NOT_OBSERVED (0 noeud(s)) | **PENDING** |

## 3. Catalogue candidat des 16 criteres d'admission G5

| Critere candidat | Contenu du gate propose | Preuves et revue necessaires | Decision |
| --- | --- | --- | --- |
| G5-01 | Architecture scope and M2 authority unchanged | Revue de code du chemin M2, aucun authenticator final autonome, scope et policy invariants; oracles candidats : M4-T01, M4-T28, M4-T29 | **PENDING** |
| G5-02 | Immutable scoped record, ownership and contract review | Ownership IAM/host et isolation du read model approuves, cache et version documentes; oracles candidats : M4-T11, M4-T12, M4-T26 | **PENDING** |
| G5-03 | 70-byte canonical parsing and public selector | Format ak1 et canonicalite acceptes dans ADR-0016, rejets malformes verifies; oracles candidats : M4-T04, M4-T05, M4-T06 | **PENDING** |
| G5-04 | Full-secret HMAC and anti-downgrade | Vecteurs independants, test secret complet et comparaison de digest constant-time locale; oracles candidats : M4-T07, M4-T08, M4-T09, M4-T10, M4-T18 | **PENDING** |
| G5-05 | Approval, rotation and key-source error semantics | Plan KMS/secret ref, rotation/reissue, erreurs et limites de disponibilite approuves; oracles candidats : M4-T16, M4-T17, M4-T19, M4-T20, M4-T35 | **PENDING** |
| G5-06 | Status, expiry and clock validation | Statuts, UTC nbf/expiry, expiry absente et source temporelle approuves dans ADR-0018; oracles candidats : M4-T21, M4-T22, M4-T23, M4-T24, M4-T27 | **PENDING** |
| G5-07 | Authoritative revocation/version CAS guarantee | Contrat mesurable de revocation, concurrence et stale source sous profil cible; oracles candidats : M4-T25, M4-T26, M4-T35 | **PENDING** |
| G5-08 | M2 explicit policy, no shadow Authenticated | Preuve cryptographique ne peut bypass le gate final M2 sous erreur et timeout; oracles candidats : M4-T02, M4-T28, M4-T29 | **PENDING** |
| G5-09 | Distributed abuse control, peer provenance | Guard anti-abus distribue avec provenance peer de confiance sous proxy/TLS; oracles candidats : M4-T31, M4-T32, M4-T33, M4-T37 | **PENDING** |
| G5-10 | Tenant isolation at persistence source | Isolation source SQL/owner/caches pour plusieurs tenants dans l'environnement cible; oracles candidats : M4-T03, M4-T11, M4-T12, M4-T30, M4-T36 | **PENDING** |
| G5-11 | Audit and telemetry privacy, operational contracts | Politique minimisation, durabilite audit, SIEM/redaction/retention testee; oracles candidats : M4-T38 | **PENDING** |
| G5-12 | Concurrency, crash/retry and overload behavior | Tests fault injection, retry/overload, timeout, RTO et limites avec criteres explicites; oracles candidats : M4-T15, M4-T25, M4-T35, M4-T37 | **PENDING** |
| G5-13 | 40 independently adjudicated M4 oracles | Catalogue M4-T01..T40 ratifie et 40 verdicts nominatifs independants; oracles candidats : M4-T01, M4-T40 | **PENDING** |
| G5-14 | All CI/test/build/security checks on exact SHA | Tous jobs, scans, wheels et hash artefacts sur exact HEAD et logs archives; oracles candidats : M4-T39 | **PENDING** |
| G5-15 | Independent crypto/security review and ADR owner signoff | ADR-0016/0017/0018 acceptes + revue securite/crypto independante et risques residuels; oracles candidats : M4-T34, M4-T40 | **PENDING** |
| G5-16 | Explicit owner GO/NO-GO and residual risks | GO/NO-GO par autorite identifiee, date, exact SHA, risques, conditions et autorisation de merge separee; oracles candidats : M4-T40 | **PENDING** |

## 4. Journal d'arbitrage requis

| Champ | Valeur a completer par l'autorite |
| --- | --- |
| Version des textes 27/28 adoptee | NON RENSEIGNE |
| Source officielle d'identifiants M4-T/G5, si deja existante | NON IDENTIFIEE |
| Decision : adopter / amender / rejeter ce nouveau catalogue | PENDING |
| Ecarts et justifications par oracle | PENDING |
| Proprietaire de l'exigence et date | PENDING |
| Relecteur securite independant et date | PENDING |
| Lien vers decision GitHub / dossier signe / SHA | PENDING |
| Date d'effet et profil de deploiement couvert | PENDING |

## 5. Consignes aux signataires

Le responsable doit prendre une decision **sur le catalogue** distincte de toute approbation technique ou d'un GO pour M4. Le relecteur securite doit objecter ou amender chaque oracle de nature P0/P1 et demander des preuves hors labo si necessaires. Sans les deux etapes, GATE27-05 reste NO-GO. Ne jamais faire porter au script de controle le role de relecteur.

## 6. Regles d'evolution et apprentissage

[Problem First] L'absence de specifications individuelles formelles rend impossible une equivalence automatique entre tests et criteres. [DDD: Ubiquitous Language] Numeroter ne rend pas normatif; la definition et la responsabilite sont la source de verite. [Security: Evidence Before Claim] Chaque ligne distingue assertion testee, environnement et approbation. [Clean Architecture] La gouvernance controle les adapters sans modifier arbitrairement le moteur.
