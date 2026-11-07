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

1. `test_entry_point_changed_after_batch_preflight_never_imports` simule une mutation de l'objet `EntryPoint.value` **après** le preflight batch. Le chargeur doit refuser avant d'exécuter du code tiers. Critère : aucune sentinelle d'import créée.
2. `test_distribution_metadata_alone_does_not_attest_import_origin` place un module de test homonyme dans un répertoire prioritaire de `sys.path`, sans changer les métadonnées du grant. Le test montre que la résolution peut choisir ce module. Le résultat **illustre une vulnérabilité non résolue**, il ne prouve pas la sécurité du dispositif.

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

**CI / SHA :** à rattacher après réussite vérifiée de la nouvelle suite sur le commit de code et sur le HEAD documentaire. Les runs précédents ne prouvent pas cette nouvelle tranche.
