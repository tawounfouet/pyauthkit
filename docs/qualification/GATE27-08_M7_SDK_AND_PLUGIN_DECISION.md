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

## Evolution candidate du SPI positif (issue #86)

Un helper de declaration de resultat interne est propose dans `pyauthkit.plugins.verification` et un verificateur de fixture positif a bytes **publics** est utilise uniquement dans une wheel de qualification. Ce test demontre le chemin du gate final, **pas** une preuve de securite cryptographique, une admission de plugins inconnus ni un GO M7. Les questions d'injection des ports host-owned et de verification cryptographique d'un verificateur tiers restent ouvertes a la revue independante.

Le helper ne retourne jamais un `Authenticated` final. Le moteur refuse les incoherences d'attempt token et la policy finale peut refuser un outcome verifie. Voir ADR 0038 proposee, sans decision d'acceptation.

## SPI v2 host services (#87)

Une evolution candidate introduit un contrat factory v2 distinct de v1, un bundle de ports approuves par l'hote et un refus avant delegation en cas de scope/profil/methode/correlation non conforme. La registry reste indexee par methode et ne permet donc **pas** de router de multiples instances v2 sur des tenants differents sans composition dediee. Le risque in-process et la provenance du code demeurent inchanges. Aucune qualification de cette evolution ne peut etre deduite des seules preuves CI de l'ancienne tranche.
