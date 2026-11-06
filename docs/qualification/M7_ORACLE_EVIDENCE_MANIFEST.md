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
| M7-T17 | Doublons/collision | tests duplicates partiels | PARTIAL (CI) |
| M7-T18 | Majeure SPI incompatible | test spi mismatch | TESTED (CI) |
| M7-T19 | Methode/capability inconnue | Validation des roles host ports SPI v2 et enum; capabilities fines restant a revoir | PARTIAL (CI) |
| M7-T20 | Freeze registry | tests M2 existants | TESTED (CI) |
| M7-T21 | Plugin ne change pas final gate | tests/security/test_m7_plugin_positive_proof.py + installed wheel synthetic positive | TESTED (CI) |
| M7-T22 | Cross-scope/tenant | M7 SPI v2 host-scope wrapper + positive declared proof cross-scope tests | TESTED (CI) |
| M7-T23 | Fermeture ressources owned | test_m7_plugin_lifecycle.py (reverse cleanup / failures) | TESTED (CI) |
| M7-T24 | No secrets dans exceptions | tests partial canary | PARTIAL (CI) |
| M7-T25 | Docs et API reellement executes | quickstart CI candidat | PARTIAL (CI) |
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

Le code candidate v2 est livre dans PR #84 : `PluginHostServices` immuable et lie a une route approuvee du snapshot M6, groupe d'entry points v2, SPI_MAJOR=2, injection de ports exacts et wrapper par scope/profil/methode. Tests dedies `tests/security/test_m7_plugin_services.py` et smoke d'une wheel avec port HMAC synthetique. **Ne pas comptabiliser ces nouveaux tests comme PASS CI avant leur execution au SHA final**. Les preuves du manifeste ci-dessus se rapportent au SHA precedent du code v1.

Reste a auditer : restriction multi-tenant liee a la registry par methode, provenance du port fourni, ownership des ressources, statut de la supply chain, review independante. HMAC de demonstration a cle publique = non production.
