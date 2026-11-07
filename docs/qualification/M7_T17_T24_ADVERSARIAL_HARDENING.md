# M7 - Revue adversariale T17 et T24

Date : 2026-11-07
Milestone : M7, PR #84, GATE27-08
Statut : **DEVELOPMENT TESTED / INDEPENDENT SECURITY REVIEW PENDING**
Reference source : `7a98e4545e7fccfd1c696d2555a7499b61be5394`
CI : https://github.com/tawounfouet/pyauthkit/actions/runs/42317026300

## T17 - Collisions et priorite avant import

**Constat avant correctif.** La registry M2 rejette les doublons de `EvidenceMethod` pendant la composition, mais un authenticator tiers peut deja avoir ete importe et instancie. Cela expose le processus hote a des effets de bord pour une extension qui ne devrait jamais etre activee.

**Changement propose.** Le host fournit `reserved_methods`, liste de methodes des authenticators internes deja planifies. `_preflight_candidates` les prend en compte dans sa validation des grants. Un conflit refuse **avant tout chargement de factory**, sur v1 ou v2. Les methodes hors enumeration sont refusees avec message stable.

**Preuves.** `tests/security/test_m7_plugin_admission.py` et `tests/security/test_m7_plugin_services.py` utilisent des sentinelles d'import. Le code source et les tests sont executes dans la CI au SHA ci-dessus.

**Risque residuel.** Le parametre est fourni par l'hote. S'il est omis ou incomplet, la registry refusera toujours le doublon a composition mais ne peut pas garantir l'absence d'execution prealable de code tiers. Aucune detection automatique des methodes internes n'est deduite des plugins installes.

## T24 - Confidentalite des exceptions

**Constat avant correctif.** Un descripteur Python `verify` malveillant ou un mapping `items()` malveillant peut lever `RuntimeError` contenant une valeur sensible pendant la validation des ports. Idem pour la conversion d'un mapping de grants avant preflight.

**Changement propose.** Capturer les erreurs ordinaires de construction des ports et des services, refuser avec `PluginAdmissionRejected` a message fixe, sans interpoler le texte d'origine; `raise ... from None` empeche l'affichage du contexte initial dans le traceback standard.

**Preuves.** Tests avec valeurs canary de descripteurs et mappings; aucune valeur sensible dans `str(error)`.

**Risque residuel.** Ces controles ne neutralisent pas les effets de bord d'un descripteur execute ni le code Python in-process malveillant. Les objets de port peuvent journaliser eux-memes, emettre des donnees sur le reseau ou exposer des secrets par leur propre API. Une revue de provenance, de privileges, de journaux et de politique hote est indispensable.

## Decision

| Oracle | Developpement | Qualification independante |
| --- | --- | --- |
| M7-T17 | TESTED (CI), avec inventaire host explicite | PARTIAL / REVIEW REQUIRED |
| M7-T24 | TESTED (CI), frontieres d'exception connues | PARTIAL / REVIEW REQUIRED |

GATE27-08 reste **NO-GO SECURITE / NO-GO PRODUCTION**. Ne pas fusionner ni publier PR-10 sur la seule base de ces tests.
