# M7 - Revue adversariale : provenance d'artefact et shadowing d'import

Date : 2026-11-07
Statut : RISK CONFIRMED / IMPLEMENTED PARTIAL MITIGATION / SECURITY NO-GO
Projet : PyAuthKit, PR #84, GATE27-08, issue #89

## 1. Problème

Le grant hôte compare les métadonnées `Name`, `Version`, `EntryPoint.group`, `EntryPoint.name` et `EntryPoint.value`. L'implémentation finale appelle `EntryPoint.load()`, qui résout le module selon le système d'import Python normal. Cette résolution n'est pas liée cryptographiquement aux fichiers de la distribution indiquée par ses métadonnées.

Conséquence : une distribution autorisée peut déclarer `m7_fixture_plugin:create` pendant que Python importe un autre `m7_fixture_plugin` placé plus tôt dans `sys.path`. `sys.modules` et les loaders personnalisés sont d'autres surfaces à modéliser. La signature de métadonnées n'est pas une signature d'artefact et la validation du grant n'est pas une sandbox.

## 2. Correction partielle candidate

La fonction `_instantiate_approved` appelle de nouveau `_candidate_for(candidate._entry_point)` immédiatement avant `EntryPoint.load()`. Les champs sont recomparés au snapshot du candidat et à l'identité du grant. Toute dérive visible entraîne `PluginAdmissionRejected` avant import.

Ce contrôle complète `_preflight_candidates`, qui reste obligatoire pour **tous** les grants avant chargement du premier plugin. Il peut détecter une mutation d'entry point intervenue durant une précédente factory ou entre validation et activation. Il ne garantit pas la stabilité du système d'import ou des fichiers durant et après le contrôle.

## 3. Tests adversariaux

`tests/security/test_m7_plugin_admission.py` :

1. `test_entry_point_changed_after_batch_preflight_never_imports` modifie la **version dans le fichier `METADATA`** de la distribution après le preflight batch. `EntryPoint` est immuable et n'est jamais modifié. Le chargeur doit refuser avant d'importer le plugin. Critère : aucune sentinelle d'import créée.
2. `test_distribution_metadata_alone_does_not_attest_import_origin` place un module homonyme dans un répertoire prioritaire de `sys.path`, sans changer les métadonnées du grant. `find_spec` démontre que le nom résout vers ce chemin, **sans importer ni exécuter le module**. Ce résultat établit une discordance de provenance possible, mais ne constitue ni un exploit exécuté ni un mécanisme de protection.

Les modules sont des fixtures de refus `RejectedOutcome`. Aucun code offensif ou secret de production n'est nécessaire.

## 4. Options de remédiation à arbitrer

| Option | Apport | Limites |
| --- | --- | --- |
| Digest de wheel approuvé hors bande | Associe le déploiement à un artefact exact | Ne lie pas automatiquement `EntryPoint.load()` au module réellement importé |
| Vérification des fichiers d'installation | Détecte certaines modifications post-installation | Races du filesystem, zip/namespace packages, caches et loaders à traiter |
| Environnement de déploiement immuable | Limite `sys.path`, `sys.modules` et chemins modifiables | Garantie opérationnelle sous responsabilité hôte |
| Processus séparé à privilèges réduits | Limite potentiellement l'impact d'un plugin | Contrat IPC, isolation, permissions et audit supplémentaires |
| Validation pré-import du module réel | Refuse certaines substitutions si résolution maîtrisée | Certains appels à `find_spec` peuvent importer des packages parents, donc requièrent une conception spécifique |

Décision d'architecture **NON PRISE** : ne pas ajouter une simple vérification de hash donnant l'impression erronée d'une attestation complète.

## 5. Threat boundaries

- `PluginCandidate` : une photo de métadonnées non fiable, pas une preuve d'identité des octets.
- `PluginGrant` : une décision hôte sur l'identité déclarée, pas une signature.
- `EntryPoint.load()` : frontière d'exécution de code Python tiers avec privilèges hôte.
- `PluginHostServices` : ports et permissions hôte, pas un mécanisme de confinement Python.
- `AuthenticationEngine` : seul détenteur du passage d'un outcome interne à la décision finale.

## 6. Gate

**M7-T16** conserve la preuve de comparaison de version/distribution, sans attestation de provenance. **M7-T30** reste PARTIAL (CI) car un risque de supply chain démontré et les validations de gouvernance (#88) ne sont pas résolus. GATE27-08 demeure **NO-GO SECURITY / NO-GO PRODUCTION** jusqu'à l'approbation indépendante d'un modèle de provenance.

**Code SHA vérifié :** `28e0d7ff4ae6b4c59d0080e73c0950a9be7a557a`. **CI GitHub Actions :** https://github.com/tawounfouet/pyauthkit/actions/runs/42327812346, 13/13 jobs SUCCESS, 700 tests globaux, 72 M7, Ruff PASS et mypy strict sur 86 fichiers. Cette preuve reste une qualification de développement et non une revue indépendante de sécurité.

## 7. Pré-installation d'une wheel à digest approuvé (candidat ADR 0043)

Le module `pyauthkit.plugins.artifacts.verify_preinstall_wheel_digest` vérifie hors import un digest SHA-256 explicite issu d'une source hôte indépendante, et confronte nom/version et cible d'entry point aux valeurs du `PluginGrant`. Le ZIP n'est jamais extrait ou exécuté. Tests : `tests/security/test_m7_wheel_artifact_identity.py`. **Limite :** cette preuve porte sur le fichier `.whl` fourni au contrôle, pas sur les octets du module réellement importé après installation. Aucune provenance cryptographique n'est établie si l'hôte n'a pas obtenu le digest d'un canal de confiance; les modifications d'environnement, races et shadowing restent ouverts. Issue #89 et GATE27-08 NO-GO.

## 8. Précondition de provenance indépendante

La valeur `expected_sha256` doit provenir d'une source de confiance indépendante (registre d'artefacts approuvé, manifeste de release signé et vérifié ou autre canal contrôlé par l'opérateur). Une valeur SHA-256 recalculée uniquement sur la wheel téléchargée ne fournit **aucune approbation**. Après contrôle du fichier, le host doit aussi empêcher la substitution de fichiers installés et contraindre le chemin d'import. Aucun de ces derniers contrôles n'est apporté par `verify_preinstall_wheel_digest`.
