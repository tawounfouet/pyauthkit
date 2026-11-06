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
| M7-WP-02 | Surface publique SDK et quickstart | IMPLEMENTED, CI a verifier |
| M7-WP-03 | SPI v1 via port M2 existant | IMPLEMENTED, revue requise |
| M7-WP-04 | Contrats et tests negatifs SPI | PARTIAL, preuve CI requise |
| M7-WP-05 | Metadata discovery, sans `EntryPoint.load` | IMPLEMENTED, preuve CI requise |
| M7-WP-06 | Grants hote, versions, collisions, refus | IMPLEMENTED, preuve CI requise |
| M7-WP-07 | Loader post-admission et registry M6 | IMPLEMENTED, preuve CI requise |
| M7-WP-08 | Lifecycle et fermeture de ressources | PARTIAL : ownership documente, cleanup async differe |
| M7-WP-09 | Guides d'usage et auteur plugin | IMPLEMENTED, docstests a verifier |
| M7-WP-10 | Packaging wheel/sdist/extras | PENDING CI |
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
- Les gates GATE27-04 a GATE27-07 demeurent NO-GO independant de la CI M7.

## Limites et chantiers ouverts

- Implementer et qualifier les oracles encore non couverts, en particulier resource cleanup/cancellation et couverture M3/M4/M5 specialisee.
- Verifier les artefacts wheel installes sur Python 3.12/3.13/3.14 et les OS prevus.
- Revue de supply chain et plugin authenticity hors de la seule metadata.
- Obtenir une revue de securite independante avant tout GO de GATE27-08.
- Pas de merge, pas de release, pas de deploiement sans decision explicite.
