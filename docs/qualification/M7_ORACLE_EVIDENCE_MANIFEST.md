# M7 Candidate Oracle Evidence Manifest

Date initiale : 2026-11-06
Milestone : M7 / PR-10
Statut : **CANDIDATE / NOT QUALIFIED**
Reference : \`M7_PYAUTHKIT_IMPLEMENTATION_PLAN.md\` fourni pour PR-10

Aucun oracle ci-dessous n'est marque PASS sur la base de la seule presence de son test. Des preuves de CI au SHA exact, logs, OS, Python et artefacts sont necessaires.

| Oracle | Sujet | Implementation de test candidate | Resultat de gate |
| --- | --- | --- | --- |
| M7-T01 | Import core sans extras | test_m7_sdk_public_api + wheel CI | NOT VERIFIED |
| M7-T02 | Python pur/host entry | examples/m7_pure_python.py | NOT VERIFIED |
| M7-T03 | Client non autoritatif pour tenant | tests M2 + M7 host test | NOT VERIFIED |
| M7-T04 | Policy finale exigee | tests M2 conserves | NOT VERIFIED |
| M7-T05 | Pas de principal hors succes | test_m7_plugin_admission.py | NOT VERIFIED |
| M7-T06 | Methode sans fallback | tests M2 conserves | NOT VERIFIED |
| M7-T07 | Entry etranger refuse | test_m7_sdk_public_api.py | NOT VERIFIED |
| M7-T08 | Authenticator composable sans edit domain | test_m7_plugin_admission.py | NOT VERIFIED |
| M7-T09 | Outcome malforme | test_m7_plugin_admission.py | NOT VERIFIED |
| M7-T10 | Exception plugin expurgee | test_m7_plugin_admission.py | NOT VERIFIED |
| M7-T11 | Timeout/cancellation | test timeout partiel ; cancellation a ajouter | PARTIAL |
| M7-T12 | Discovery n'importe aucun code | import sentinel | NOT VERIFIED |
| M7-T13 | Discovery OFF | test no metadata call | NOT VERIFIED |
| M7-T14 | Plugin non admis non execute | test deny/sentinel | NOT VERIFIED |
| M7-T15 | Allowlist hote exacte | tests de grants | NOT VERIFIED |
| M7-T16 | Distribution et version pinnees | parametrized mismatch | NOT VERIFIED |
| M7-T17 | Doublons/collision | tests duplicates partiels | PARTIAL |
| M7-T18 | Majeure SPI incompatible | test spi mismatch | NOT VERIFIED |
| M7-T19 | Methode/capability inconnue | method enum guard ; autres capabilities absentes | PARTIAL |
| M7-T20 | Freeze registry | tests M2 existants | NOT VERIFIED |
| M7-T21 | Plugin ne change pas final gate | tests M2, revue composition requise | PARTIAL |
| M7-T22 | Cross-scope/tenant | tests M2, tests tiers a ajouter | PARTIAL |
| M7-T23 | Fermeture ressources owned | ownership documente, tests a ajouter | NOT RUN |
| M7-T24 | No secrets dans exceptions | tests partial canary | PARTIAL |
| M7-T25 | Docs et API reellement executes | quickstart CI candidat | NOT VERIFIED |
| M7-T26 | PEP561 / extras wheel | smoke wheel candidat | NOT VERIFIED |
| M7-T27 | Installation core sans extras | smoke wheel candidat | NOT VERIFIED |
| M7-T28 | M6 required audit interdit | test_m7_sdk_public_api.py | NOT VERIFIED |
| M7-T29 | Non regression M3-M6 | CI complete a examiner | NOT VERIFIED |
| M7-T30 | Provenance SHA et decision | Ce manifest devra etre actualise | NOT VERIFIED |

Toute mise a jour doit indiquer SHA exact, workflow/job, OS, Python, verdict, preuve et reviewer. Ne pas convertir un test code en PASS sans execution.
