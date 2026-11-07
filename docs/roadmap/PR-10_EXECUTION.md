# PR-10 - M7 Public SDK & Plugin Admission - Execution Record

> Date : 2026-11-06
> Branch : `feat/m7-public-sdk-plugin-admission-pr10`
> Pull request : https://github.com/tawounfouet/pyauthkit/pull/84
> Baseline : `main@ac4669e86cd690170ab5f3c2b0c7945258e35f9d`
> Milestone : M7, GATE27-08
> Statut : DEVELOPMENT IN PROGRESS / SECURITY NOT QUALIFIED

## Mission

Rendre le SDK Python consommable sans invention de nouvelle autorite et introduire une admission explicite pour les authenticators plugins. L'API M2 et la composition M6 restent responsables de la decision finale.

## Execution et work packages

| Package | Travail | Statut |
| --- | --- | --- |
| M7-WP-01 | Baseline, inventaire et branche PR-10 | IMPLEMENTED (voir commits de PR) |
| M7-WP-02 | Surface publique SDK et quickstart | IMPLEMENTED / TESTED CI head a4e12634 |
| M7-WP-03 | SPI v1/v2 explicite et port M2 existant | IMPLEMENTED CANDIDATE : declaration positive (#86), injection host-bound v2 (#87), revue requise |
| M7-WP-04 | Contrats et tests negatifs SPI | TESTED CI 7a98e454 : 57 tests M7, revue independante requise |
| M7-WP-05 | Metadata discovery, sans `EntryPoint.load` | IMPLEMENTED / TESTED CI v1 et v2 |
| M7-WP-06 | Grants hote, versions, collisions, refus | TESTED CI 7a98e454 : pre-import reserved_methods v1/v2, revue independante requise |
| M7-WP-07 | Loader post-admission et registry M6 | IMPLEMENTED / TESTED CI, scope v2 mono-route |
| M7-WP-08 | Lifecycle et fermeture de ressources | IMPLEMENTED CANDIDATE : managed async activation, tests et revue requise |
| M7-WP-09 | Guides d'usage et auteur plugin | IMPLEMENTED, docstests a verifier |
| M7-WP-10 | Packaging wheel/sdist/extras | TESTED CI Linux 3.12/3.13/3.14, macOS et Windows 3.12 |
| M7-WP-11 | ADR, learning cards et oracles | PARTIAL, NO-GO securite |
| M7-WP-12 | CI, review et dossier de fusion | PENDING, PR DRAFT |

Les mentions IMPLEMENTED correspondent a du code propose dans PR-10, pas a une qualification de securite. La matrice d'oracles constitue la source de verite du gate.

## Decisions de conception

- Pas de nouveau `SdkAuthenticator` ni moteur de decision.
- Surface publique explicite `pyauthkit.sdk`; la racine du paquet reste minimale.
- `pyauthkit.authenticators.v1` ne s'active jamais automatiquement.
- Un grant approuve la distribution, la version exacte, l'entry point, la cible et la methode, avant import.
- Metadata seule : pas d'attestation de signature / digest, pas de sandbox.
- `SPI_MAJOR=1` et factory zero-argument; methode `EvidenceMethod` du domaine existant.
- La composition M6 continue de refuser les paths secret/JWT generiques non admis.
- Le SPI positif reutilise `_issue_verified_outcome` uniquement via un helper explicite pour plugins deja admis. Il n'effectue aucune preuve cryptographique.
- SPI v2 separe pour factory recevant un bundle de ports hote, scope/profil/methode pinned, sans changement v1. Registry M2 toujours par methode : pas de routage multi-tenant generique.
- Les gates GATE27-04 a GATE27-07 demeurent NO-GO independant de la CI M7.

## Limites et chantiers ouverts

- Qualifier les oracles encore non couverts : notamment trust review du SPI positif, provenance supply chain, couverture M3/M4/M5 specialisee et authenticators externes de production. Le plugin positif actuel est une fixture non sure.
- Verifier les artefacts wheel installes sur Python 3.12/3.13/3.14 et les OS prevus.
- Revue de supply chain et plugin authenticity hors de la seule metadata.
- Ports hote scopes a qualifier independamment; demo HMAC synthetique non production, absence de sandbox.
- Obtenir une revue de securite independante avant tout GO de GATE27-08.
- Pas de merge, pas de release, pas de deploiement sans decision explicite.

## Preuves d'execution SPI v2 (code head `a4e12634`)

- Workflow : https://github.com/tawounfouet/pyauthkit/actions/runs/42314651520, **13/13 jobs SUCCESS**.
- Quality : 678 tests pytest PASS, Ruff PASS, mypy 85 fichiers PASS.
- M7 dedicated : 50 tests PASS; wheel independante host-scoped SPI v2 + revocation et tenant croise PASS.
- Decisions de securite : **non qualifie**; issue #85 ouverte, SPI v2 #87 candidat, ADR 0039 proposed, aucun merge ni publication.

## Tranche T17/T24 - hardening avant revue externe

Source validee : `7a98e4545e7fccfd1c696d2555a7499b61be5394` ; CI : https://github.com/tawounfouet/pyauthkit/actions/runs/42317026300 ; 13/13 SUCCESS, 57 M7 PASS, 685 pytest PASS.

- Preflight `reserved_methods` pour stopper les collisions de methodes deja utilisees par les authenticators host avant import, sur SPI v1 et SPI v2.
- Erreurs de construction de `PluginHostServices` et de mappings de grants expurgees, tests canary.
- Nouvelles preuves pour M7-T17 et M7-T24, **statuts PARTIAL** maintenus.
- ADR 0040 et dossier adversarial proposes. Aucune decision GO securite.

La fiabilite de l'inventaire des methodes reservees appartient a l'hote. La library ne peut pas prouver que le plugin respecte les obligations de confidentialite de maniere generale.
