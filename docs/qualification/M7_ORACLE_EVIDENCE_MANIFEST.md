# M7 Candidate Oracle Evidence Manifest

Date initiale : 2026-11-06
Milestone : M7 / PR-10
Statut : **TESTED / CI CANDIDATE - NOT SECURITY QUALIFIED**
Reference : `M7_PYAUTHKIT_IMPLEMENTATION_PLAN.md` fourni pour PR-10

Aucun oracle ne reçoit ici de PASS de securite. La colonne `TESTED (CI)` indique uniquement la presence d'un test executé et d'une preuve CI au SHA mentionne ci-dessous. `PARTIAL (CI)` signifie qu'au moins une garantie reste non couverte. Toutes les decisions finales du gate demandent revue independante et signature.

| Oracle | Sujet | Implementation de test candidate | Resultat de gate |
| --- | --- | --- | --- |
| M7-T01 | Import core sans extras | test_m7_sdk_public_api + wheel CI | TESTED (CI) |
| M7-T02 | Python pur/host entry | examples/m7_pure_python.py | TESTED (CI) |
| M7-T03 | Client non autoritatif pour tenant | tests M2 + M7 host test | TESTED (CI) |
| M7-T04 | Policy finale exigee | tests M2 conserves | TESTED (CI) |
| M7-T05 | Pas de principal hors succes | test_m7_plugin_admission.py | TESTED (CI) |
| M7-T06 | Methode sans fallback | tests M2 conserves | TESTED (CI) |
| M7-T07 | Entry etranger refuse | test_m7_sdk_public_api.py | TESTED (CI) |
| M7-T08 | Authenticator composable sans edit domain | test_m7_plugin_admission.py | TESTED (CI) |
| M7-T09 | Outcome malforme | test_m7_plugin_admission.py | TESTED (CI) |
| M7-T10 | Exception plugin expurgee | test_m7_plugin_admission.py | TESTED (CI) |
| M7-T11 | Timeout/cancellation | test_m7_plugin_lifecycle.py + test_m7_plugin_scope.py | TESTED (CI) |
| M7-T12 | Discovery n'importe aucun code | import sentinel | TESTED (CI) |
| M7-T13 | Discovery OFF | test no metadata call | TESTED (CI) |
| M7-T14 | Plugin non admis non execute | test deny/sentinel | TESTED (CI) |
| M7-T15 | Allowlist hote exacte | tests de grants | TESTED (CI) |
| M7-T16 | Distribution et version pinnees | parametrized mismatch | TESTED (CI) |
| M7-T17 | Doublons/collision | test_m7_plugin_admission.py + test_m7_plugin_services.py : reserved_methods avant import | PARTIAL (CI) |
| M7-T18 | Majeure SPI incompatible | test spi mismatch | TESTED (CI) |
| M7-T19 | Methode/capability inconnue | tests/security/test_m7_plugin_services.py, role-method allowlist, grant.port_roles et matching exact avant import | PARTIAL (CI) |
| M7-T20 | Freeze registry | tests M2 existants | TESTED (CI) |
| M7-T21 | Plugin ne change pas final gate | tests/security/test_m7_plugin_positive_proof.py + installed wheel synthetic positive | TESTED (CI) |
| M7-T22 | Cross-scope/tenant | M7 SPI v2 host-scope wrapper + positive declared proof cross-scope tests | TESTED (CI) |
| M7-T23 | Fermeture ressources owned | test_m7_plugin_lifecycle.py (reverse cleanup / failures) | TESTED (CI) |
| M7-T24 | No secrets dans exceptions | tests SPI v2 descriptors/mappings canary et activation/sanitization | PARTIAL (CI) |
| M7-T25 | Docs et API reellement executes | scripts/check_m7_doc_examples.py + docs/guides/m7-capability-contract.md depuis wheel et quickstart Python | PARTIAL (CI) |
| M7-T26 | PEP561 / extras wheel | smoke wheel candidat | TESTED (CI) |
| M7-T27 | Installation core sans extras | smoke wheel candidat | TESTED (CI) |
| M7-T28 | M6 required audit interdit | test_m7_sdk_public_api.py | TESTED (CI) |
| M7-T29 | Non regression M3-M6 | CI complete a examiner | TESTED (CI) |
| M7-T30 | Provenance SHA et decision | Ce manifest devra etre actualise | PARTIAL (CI) |

Toute mise a jour doit indiquer SHA exact, workflow/job, OS, Python, verdict, preuve et reviewer. Ne pas convertir un test code en PASS sans execution.

## Evidence CI issue de PR #84 - 7 novembre 2026

- **PR head SHA verifie** : `3c8ee33e3511d20b9eef842d25d68947b8351983`.
- **Workflow** : https://github.com/tawounfouet/pyauthkit/actions/runs/42311006285 . Resultat : **13/13 jobs SUCCESS**, sur le PR merge ref associe au head.
- **Suite qualite (Ubuntu Python 3.12)** : 672 tests pytest PASS; Ruff check PASS, Ruff format 285 fichiers; mypy strict 84 fichiers source sans erreur; checks d'architecture inclus dans ce job.
- **Suite M7 (Ubuntu Python 3.12)** : 44 tests PASS, avec snapshot API, admission des entry points, tests SPI positifs et negatifs, fermeture, timeout, annulation, cross-tenant et final gate DENY.
- **Smoke wheel M7** : import sans extras, packaging wheel/sdist, installation d'une distribution synthetique independante, voie DENY, fermeture asynchrone, puis `SYNTHETIC VERIFIED / POLICY DENY / INVALID REJECTED`.
- **Matrice de compatibilite** : Linux Python 3.12/3.13/3.14, macOS Python 3.12 et Windows Python 3.12, jobs de packaging reussis.
- **Regressions** : reference M3, M4, M5, M6 et scans source/dependances/secrets PASS dans le workflow du head.

Les tests executees utilisent les fakes et fixtures du depot, non une qualification de fournisseur, de vrais secrets de production, une preuve d'integrite de la distribution ou une revue de code tierce. Les lignes `TESTED (CI)` ne deviennent pas `QUALIFIED` du seul fait d'une CI verte.

## Reserves du gate

1. **M7-T17 (collisions)** : collisions de metadata et de grants testees, mais l'analyse de l'ensemble des collisions d'authenticators internes/externes et generations est a parfaire.
2. **M7-T19 (capabilities)** : la methode enum est bornee, mais l'accord sur les capabilities et une factory recevant des ports hote reste ouvert (issue #87).
3. **M7-T24 (confidentialite)** : sanitation des exceptions testee avec canary, sans garantie generale sur toute extension chargee.
4. **M7-T25 (documentation)** : quickstart et smoke wheel executes, mais tous les extraits documentaires et scenarios de consommateurs ne sont pas des doctests.
5. **M7-T30 (decision)** : provenance de la CI verifiee, mais signature d'un reviewer independant absente et autres gates M3-M6 non encore qualifies.
6. **Extension positive** : fixture volontairement forgeable avec des bytes publics; prouve uniquement la separation outcome/final policy, jamais une authentification sure. SPI positif (issue #86) et ports hote (issue #87) attendent la revue.
7. **Admission** : le nom de distribution et sa version ne constituent pas une preuve cryptographique de provenance. Les plugins restent du code Python in-process.

**Decision en l'etat : GO DEVELOPPEMENT / NO-GO SECURITE / NO-GO PRODUCTION.** Voir issue #85 et le dossier `GATE27-08_M7_SDK_AND_PLUGIN_DECISION.md`.

## Extension candidate SPI v2 / issue #87

Le code candidate v2 est livre dans PR #84 : `PluginHostServices` immuable et lie a une route approuvee du snapshot M6, groupe d'entry points v2, SPI_MAJOR=2, injection de ports exacts et wrapper par scope/profil/methode. Tests dedies `tests/security/test_m7_plugin_services.py` et smoke d'une wheel avec port HMAC synthetique. **Ces nouveaux tests ont ete executes en CI au commit `a4e12634c3dae2938516010fbfae022447311ef6` : 13/13 jobs verts, 50/50 tests M7 PASS.** Les preuves du manifeste precedent demeurent valides pour les executions precedentes.

Reste a auditer : restriction multi-tenant liee a la registry par methode, provenance du port fourni, ownership des ressources, statut de la supply chain, review independante. HMAC de demonstration a cle publique = non production.

## Evidence CI SPI v2 - head code 2026-11-07

- **HEAD source valide** : `a4e12634c3dae2938516010fbfae022447311ef6`.
- **Run** : https://github.com/tawounfouet/pyauthkit/actions/runs/42314651520 . **13/13 jobs SUCCESS** (run GitHub Actions sur PR merge ref pour ce head).
- **Qualite Ubuntu Python 3.12** : 678 tests globaux PASS, Ruff lint/format PASS (290 fichiers formates), mypy strict PASS (85 fichiers sources), fitness architecture PASS.
- **Suite M7** : 50 tests PASS, incluant `tests/security/test_m7_plugin_services.py` (absence d'import lors de discovery, admission exacte, absence de services v2, v1 maintenu, coherence group/major, ports bornes, HMAC synthetique revoke, scope cross-tenant refuse).
- **Smoke wheel independante** : `M7 SPI v2 installed wheel: HOST MAC / REVOCATION / SCOPE CHECKS`; integration avec groupe `pyauthkit.authenticators.v2`, injection par hote, positive interne et final rule, `aclose` gere.
- **Compatibilite** : wheel/sdist et tests sur Linux Python 3.12/3.13/3.14, macOS 3.12, Windows 3.12; scans de securite et jobs M3-M6 verts.

Les preuves couvrent des fixtures/test doubles de confiance limitee. Le secret HMAC de qualification est PUBLIC et ne prouve ni cryptographie de production, ni supply-chain attestation, ni isolation du plugin.

**Toujours NO-GO GATE27-08** : arbitrage des privileges de ports, limites mono-scope par factory, origine des packages, verification de tous les oracles P0 et signature independante encore necessaires. Voir #85, #86 et #87.

## Renforcement adversarial T17/T24 - preuve du 7 novembre 2026

- **Code HEAD teste** : `7a98e4545e7fccfd1c696d2555a7499b61be5394`.
- **Workflow CI** : https://github.com/tawounfouet/pyauthkit/actions/runs/42317026300 ; **13/13 jobs SUCCESS** sur le PR merge ref de ce head.
- **Tests** : 57/57 tests M7 PASS, 685 tests globaux PASS, Ruff PASS, mypy strict 85 fichiers PASS.
- **T17** : `reserved_methods` facultatif pour le host est verifie en preflight avant `EntryPoint.load()` (v1 et v2). L'absence d'import lors d'un conflit de methode est demontree par sentinel; les methodes inconnues sont refusees. La registry M2 garde son test final de collision.
- **T24** : descripteur de port malveillant, mapping de ports malveillant, mapping de service bindings malveillant : exceptions expurgees avant activation. Une exception brute potentiellement sensible n'est pas incluse dans `str(PluginAdmissionRejected)`.
- **Packaging** : smoke M7 wheel independente et integrations reference M3/M4/M5/M6 PASS, jobs de compatibilite Linux Python 3.12/3.13/3.14, macOS 3.12 et Windows 3.12 PASS.

**Statuts conserves :** M7-T17 = PARTIAL (CI) car l'inventaire des methodes internes doit etre fourni par le host; la composition rejette les doublons meme sans cet inventaire, mais apres une eventuelle execution du plugin. M7-T24 = PARTIAL (CI) car l'expurgation des erreurs aux frontieres connues ne peut ni isoler un plugin in-process ni empecher ses logs ou effets de bord volontaires. La qualification independante GATE27-08 reste NO-GO.

Voir `M7_T17_T24_ADVERSARIAL_HARDENING.md` et ADR 0040 PROPOSED.


## T19/T25 - Nouvelle tranche candidate de qualification

- **Code SHA propose** : `469c5ea4a6edb8942207aa69646d1056d30cbdb7`.
- **CI associee** : https://github.com/tawounfouet/pyauthkit/actions/runs/42320213182 . Lire la conclusion reelle du run; cette ligne n'accorde aucun PASS sans execution.
- **T19** : `PluginGrant.port_roles` non vide pour v2, vide pour v1, compatible avec la methode `EvidenceMethod`. Le preflight compare cet ensemble au mapping exact des ports host-owned avant import. Tests adversariaux pour role inconnu, role non permis, port manquant ou supplementaire, avec sentinelle d'import.
- **T25** : `docs/guides/m7-capability-contract.md` fournit un bloc Python autonome. `scripts/check_m7_doc_examples.py` l'execute depuis la wheel isolee dans le job `m7_sdk_plugins`. D'autres extraits de documentation restent illustratifs et ne sont pas des doctests.
- **Statut** : T19 = PARTIAL (CI), car les permissions reelles de chaque port et son origine fiable ne peuvent pas etre demontrees par la validation de roles. T25 = PARTIAL (CI), car un sous-ensemble cible des guides est execute, pas toute la reference SDK.
- **Decision** : pas de GO GATE27-08 sur cette seule tranche. Revue independente, supply chain, limites du Python in-process et qualification cryptographique de plugins reels restent ouvertes.
