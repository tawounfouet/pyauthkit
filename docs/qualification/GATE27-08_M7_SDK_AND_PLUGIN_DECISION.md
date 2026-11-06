# GATE27-08 - M7 Public SDK & Plugin Architecture

Date : 2026-11-06
Statut : **NO-GO SECURITY / INDEPENDENT REVIEW PENDING**
Phase : PR-10 Draft, implementation de developpement pre-alpha
Baseline de depart : `main@ac4669e86cd690170ab5f3c2b0c7945258e35f9d`
Cible : https://github.com/tawounfouet/pyauthkit/pull/84

## Decision provisoire

GO DEV pour la proposition code et les tests de PR-10. Aucun GO SECURITE ni GO PRODUCTION n'est accorde. Le resultat d'une CI verte ne peut remplacer la revue externe des frontieres de confiance. En particulier, les gates GATE27-04, GATE27-05, GATE27-06 et GATE27-07 restent NO-GO / revue independante en attente.

## Critere d'acceptation

- Les 30 oracles M7-T01..M7-T30 doivent posseder un statut fonde sur une preuve au SHA et dans l'environnement indiques.
- Aucun P0 applicable avec FAIL/BLOCKED/INCONCLUSIVE ne doit etre clos artificiellement.
- Demonstrer metadata discovery sans execution, deny avant admission, SPI v1, collision, final gate et absence d'AuthZ.
- Evaluer les effets de bord au chargement, la provenance non attestee des distributions et les responsabilites de shutdown.
- Verifier la wheel/sdist et le comportement des extras non presents.
- L'autorite independante consigne une decision sur un scope precis, sans etendre la qualification M3-M6.

## Risque residuel deja identifie

Le code d'un plugin approuve s'execute dans le processus hote avec ses privileges. Un `PluginGrant` ne constitue ni une signature cryptographique, ni une sandbox, ni une verification de securite de l'algorithme. L'execution d'une factory ne peut pas etre annulee retroactivement. Les verifications structurelles ne suffisent pas a etablir que l'authenticator realise une vraie verification cryptographique.

Voir `M7_ORACLE_EVIDENCE_MANIFEST.md` et `PR-10_EXECUTION.md`. Les oracles non executes ne doivent jamais recevoir le statut PASS.
