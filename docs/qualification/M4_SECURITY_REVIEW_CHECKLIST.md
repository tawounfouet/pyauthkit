> **ATTENTION - ARCHIVE HISTORIQUE SUPERSEDEE.** La signification des identifiants
> M4-T01..T40 / G5-01..16 dans ce fichier n'est pas alignée avec le
> plan détaillé M4 du 05/11/2026. **NE PAS UTILISER POUR UNE DECISION.**
> Matrice fidèle à la source : `docs/qualification/M4_2026_11_05_SOURCE_MATRIX.md`.
> Catalogue réconcilié : `docs/qualification/M4_CANDIDATE_ORACLE_CATALOG_V2.md`.
> Les anciens chiffres/états ci-dessous décrivent uniquement les étapes historiques.
>
# M4 - Protocole de revue independante et fiche de decision GATE27-05

**Statut : A COMPLETER PAR DES PERSONNES HABILITEES.** Ce document est un **gabarit** et ne constitue aucune approbation.

## I. Identification et separation des devoirs

| Champ | Valeur requise |
|---|---|
| Referentiel / PR | `tawounfouet/pyauthkit` / PR #76 (Draft) |
| SHA exact soumis a approbation | **A RENSEIGNER AU MOMENT DE LA REVUE** |
| Date et environnement | **A RENSEIGNER** |
| Mainteneur responsable du gate | **A RENSEIGNER** |
| Relecteur securite independant | **A RENSEIGNER** |
| Conflits d'interets / independence | **A EVALUER** |
| Preuves CI, IDs, logs archives + SHA256 | **A RENSEIGNER** |
| Plan canonique M4 / version / diff mapping | **A RENSEIGNER** |

## II. Checklist du relecteur

- [ ] Le commit recu et la cible de la PR sont stables pendant la revue.
- [ ] Les 40 oracles du plan source sont rapproches un par un du registre candidat : statut, preconditions, assertions, source de preuve, limites, auteur et approbateur.
- [ ] Les 16 criteres G5 du plan source sont rapproches un par un; aucun resultat technique ne signifie approbation.
- [ ] Les 207+12 tests du checkpoint historique sont relus sur le SHA qui les a produits; les tests du SHA final sont reexecutés.
- [ ] Les journaux CI bruts sont archives et hashes, y compris checks quality, security, OS matrix, PostgreSQL/Redis/HTTP.
- [ ] La permission des workflows, les images de services, secrets ephemeres et versions de dependances sont audites.
- [ ] Les queries SQL sont verifiees par le reviewer : scope contraint a la source, collision selector cross-tenant, CAS/status/version et indexes.
- [ ] L'etat de revocation stale et les risques TOCTOU sont testes dans un profil de deploiement cible avec une limite temporelle approuvee.
- [ ] Le controle anti-abus s'appuie sur une source peer approuvee sous TLS/proxy, sans entetes client arbitraires.
- [ ] Les refus HTTP, timeouts, erreurs, fuites de logs et mesures de timing sont testes sur un reseau representatif; les hypotheses et seuils sont definis.
- [ ] Les secrets serveur HMAC sont recuperes via une source KMS approuvee; rotation/reissue et compromission sont traitees.
- [ ] L'observabilite et l'audit durables sont prouves, avec retention, latence, redaction, alertes et scenario incident.
- [ ] Le registre des risques R-M4-01..10 a un responsable et une decision sur chaque residu.
- [ ] ADR-0016 / ADR-0017 / ADR-0018 ont une approbation explicite, datée et attribuable.
- [ ] L'interaction avec M3 PR #75 / GATE27-04 NO-GO a ete tranchee par le mainteneur.
- [ ] Les gates G5-01..G5-16 sont acceptes ou refuses **individuellement**, avec preuves et auteur.
- [ ] Le verdict final est attribuable et le processus de merge autorise; la release reste un acte distinct.

## III. G5 - fiche de revue a remplir

| Critere candidat | Decision | URL preuve et SHA | Approbateur / date |
|---|---|---|---|
| G5-01 - Architecture scope and M2 authority unchanged | **PENDING** | A renseigner | A renseigner |
| G5-02 - Immutable scoped record, ownership and contract review | **PENDING** | A renseigner | A renseigner |
| G5-03 - 70-byte canonical parsing and public selector | **PENDING** | A renseigner | A renseigner |
| G5-04 - Full-secret HMAC and anti-downgrade | **PENDING** | A renseigner | A renseigner |
| G5-05 - Approval, rotation and key-source error semantics | **PENDING** | A renseigner | A renseigner |
| G5-06 - Status, expiry and clock validation | **PENDING** | A renseigner | A renseigner |
| G5-07 - Authoritative revocation/version CAS guarantee | **PENDING** | A renseigner | A renseigner |
| G5-08 - M2 explicit policy, no shadow Authenticated | **PENDING** | A renseigner | A renseigner |
| G5-09 - Distributed abuse control, peer provenance | **PENDING** | A renseigner | A renseigner |
| G5-10 - Tenant isolation at persistence source | **PENDING** | A renseigner | A renseigner |
| G5-11 - Audit and telemetry privacy, operational contracts | **PENDING** | A renseigner | A renseigner |
| G5-12 - Concurrency, crash/retry and overload behavior | **PENDING** | A renseigner | A renseigner |
| G5-13 - 40 independently adjudicated M4 oracles | **PENDING** | A renseigner | A renseigner |
| G5-14 - All CI/test/build/security checks on exact SHA | **PENDING** | A renseigner | A renseigner |
| G5-15 - Independent crypto/security review and ADR owner signoff | **PENDING** | A renseigner | A renseigner |
| G5-16 - Explicit owner GO/NO-GO and residual risks | **PENDING** | A renseigner | A renseigner |

## IV. ADR a arbitrer

- **ADR-0016 :** approuver/refuser le format `ak1`, les 32 octets aleatoires, HMAC domaine-separe, key reference et source approuvee ; trancher le KMS, la rotation et le cycle de vie des cles.
- **ADR-0017 :** approuver/refuser la frontiere source-scoped et le credential owner; valider requetes SQL, caches, collisions et provenance du scope.
- **ADR-0018 :** approuver/refuser `expires_at` obligatoire, la source temporelle, `is_current` et la signification du risque TOCTOU; regler le lien vers le gate M2.

Chaque ADR requiert statut, responsable, relecteur, objections, alternatives, conditions et lien a la decision.

## V. Decision a signer

**Verdict courant : NO-GO (NOT FORMALLY ADJUDICATED).**

- Verdict nouveau : [ ] GO / [ ] NO-GO / [ ] REPORT
- SHA exact, tags, protections et CI : **NON RENSEIGNES**.
- Conditions bloquantes / risques refuses : **NON RENSEIGNES**.
- Reservations, restrictions de deploiement et expiration : **NON RENSEIGNEES**.
- Auteur de la decision, role, date, lien officiel : **NON RENSEIGNES**.
- Autorisation de merge : **NON DONNEE**.
- Autorisation de publication PyPI : **NON DONNEE**.

**Ce fichier ne peut etre utilise pour simuler une signature. Une edition documentaire ne fait pas evoluer GATE27-05.**
