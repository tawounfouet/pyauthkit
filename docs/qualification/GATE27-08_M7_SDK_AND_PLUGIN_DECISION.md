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

## Controle pre-import et exceptions de ports - T17/T24

L'interface candidate ajoute `reserved_methods` avant chargement, avec test sentinel pour prevenir l'import d'un plugin qui collide avec un authenticator reserve par le host. La validite de cet inventaire reste la responsabilite de l'hote. Les exceptions courantes de descripteurs/mappings de ports et services sont expurgees. Les logs arbitraires de plugins in-process ne peuvent pas etre contenus ici.

Preuve technique : code SHA `7a98e4545e7fccfd1c696d2555a7499b61be5394`, run https://github.com/tawounfouet/pyauthkit/actions/runs/42317026300 (13/13 jobs success). **T17/T24 PARTIAL, GATE27-08 NO-GO SECURITE** jusqu'a audit et revue independante.


## T19/T25 - Role allowlist et documentation executable

L'API candidate `PluginGrant.port_roles` borne l'ensemble des ports v2 d'apres la methode d'authentification, puis exige la correspondance exacte du bundle avant import. Un script de CI execute un bloc de guide autonome depuis une wheel installee. Ces controles ameliorent la traçabilite de capabilities et l'exactitude de la documentation, mais ne prouvent ni la securite d'un port, ni la provenance d'un plugin. T19 et T25 demeurent PARTIAL (CI), en attente de revue independante et couverture complementaire. ADR 0041 PROPOSED.

## T30 - Revue de readiness au SHA exact

- Source de preuve : `docs/qualification/M7_T30_INDEPENDENT_REVIEW_READINESS_2026-11-07.md`.
- PR #84 Draft, non fusionnée, 0 review et 0 reviewer request.
- Workflow https://github.com/tawounfouet/pyauthkit/actions/runs/42320391541 : 13/13 jobs SUCCESS sur SHA `573334f7fe372ef07659dd6c85e02801ac529891`; 14 check-runs verts.
- Ruleset de `main` actif, strict, mais zéro approbation requise et GitGuardian non obligatoire. La protection classique n'est pas accessible (403). Voir issue #88.
- Le dossier est prêt pour examen documentaire, **pas** qualifié par une autorité indépendante. 5 oracles restent PARTIAL (CI) : T17, T19, T24, T25, T30. Statut NO-GO maintenu.

## Risque additionnel - Shadowing de module Python (issue #89)

Des métadonnées de distribution exactes ne constituent pas une preuve d'origine du module exécuté. Une démonstration adversariale du chargement d'un module homonyme via `sys.path` est ajoutée à la suite M7. Le recontrôle juste avant `EntryPoint.load()` limite uniquement la dérive **observable** des métadonnées, pas la substitution de code par le système d'import. Un modèle de provenance des artefacts et de restriction de l'environnement d'import est exigé avant GO. Dossier `M7_PLUGIN_ORIGIN_AND_IMPORT_SHADOWING_2026-11-07.md`, issue #89, ADR 0042 PROPOSED.

## Vérification de wheel hôte et provenance de module (ADR 0043)

Au code SHA `28e0d7ff4ae6b4c59d0080e73c0950a9be7a557a`, le contrôle candidat de SHA-256 d'une wheel **avant installation** a passé la CI https://github.com/tawounfouet/pyauthkit/actions/runs/42327812346 (13/13 jobs, 700 tests globaux, 72 M7). Ce contrôle ne lie pas automatiquement les octets vérifiés aux modules résolus ultérieurement par Python, et ne fournit pas de signature ni de confinement. Les risques #89 et #88 restent ouverts. L'oracle T30 reste PARTIAL et GATE27-08 **NO-GO SECURITY/PRODUCTION**.
