# M4 - Registre de risques de securite (proposition de revue)

> **05/11/2026 | Etat : PROPOSED, non accepte par une autorite de risque.**  
> Ce registre relie les risques aux oracles candidats et aux preuves de laboratoire. Les severites sont des estimations conservatrices, non un score normalise, non une acceptation et non une certification.

| ID | Gravite candidate | Risque | Preuve actuelle | Action / preuve attendue |
|---|---|---|---|---|
| R-M4-01 | CRITICAL | Rejeu d'une cle bearer exposee | Le test host montre deux authentifications valides avec le meme bearer | Exiger TLS termine en confiance, non-log, detection d'anomalies et procedure de revoquer/reemettre; Politique de detection/reponse + test sous TLS/proxy |
| R-M4-02 | HIGH | Fenetre TOCTOU apres is_current | CAS et is_current testent seulement un sous-intervalle; aucune linearizabilite finale | Contrat de coherence revocation borne avec IAM owner, instrumentation sur 2 processus; SLO de delai de revocation, tests de concurrence dans deploiement cible |
| R-M4-03 | HIGH | Usurpation d'adresse reseau via proxy | Banc no-proxy ignore l'entete, ne modele pas production | Liste de proxies de confiance, enforcement edge et test end-to-end; Diagramme de chaine TLS/proxy + test de spoofing deploye |
| R-M4-04 | HIGH | Disponibilite Redis/KMS/Postgres et surcharge | Redis/Postgres 503 verifies au banc; KMS reel non teste | Circuit breaker sans fail-open, limites de pools, quotites, SLO et chaos; Tests de saturation multi-noeuds et MTTD/MTTR |
| R-M4-05 | HIGH | Vol/rotation de cle serveur HMAC | Policy host allowlist et HMAC testes; integration KMS absente | KMS/Vault avec IAM minimal, rotation et reissue, audit acces; ADR-0016 accepte + simulation de rotation source reelle |
| R-M4-06 | HIGH | Fuite de secret ou identifiant dans logs/metrics | repr/erreurs verifies; audit durable et redaction HTTP infra non preuves | Politique de redaction end-to-end et tests contre canary dans logs; Export de journaux filtrables SIEM et retention verifiee |
| R-M4-07 | HIGH | Enumeration de selecteurs par temps de reponse | 20+20 mesures loopback; pas d'equivalence statistique | Concevoir mesure multi-echecs, intervalles, seuils, budgets, anti-abus; Etude preenregistree avec tests sur architecture reelle |
| R-M4-08 | MEDIUM | Derive du modele de tenants/caches | SQL WHERE scope teste dans schema ephemere; prod/ORM non audites | Revue de requetes avec isolation DDL/row security et cache namespacing; DB de destination et 2 versions controlees + plan d'isolation |
| R-M4-09 | MEDIUM | Decalage entre plan M4 et registre candidat | 40 lignes et 16 criteres presents mais candidats | Relecture ligne a ligne du plan canonique et approbation du mapping; Diff signe des oracles et criteres officiels |
| R-M4-10 | HIGH | Absence d'autorite independante et GO formel | 0 adjudications; ADR propos; PR draft | Interdire merge/release et exiger decision, revue, checks sur HEAD; Review GitHub APPROVED + owner gate signe au SHA exact |

## Cartes de decision par risque

### R-M4-01 - Rejeu d'une cle bearer exposee

- **Priorite proposee :** CRITICAL ; **statut :** PENDING.
- **Scenario / surface :** Transport/stockage client non maitrise.
- **Preuve actuelle :** Le test host montre deux authentifications valides avec le meme bearer.
- **Mitigation proposee :** Exiger TLS termine en confiance, non-log, detection d'anomalies et procedure de revoquer/reemettre.
- **Condition de levée :** Politique de detection/reponse + test sous TLS/proxy.
- **Oracles candidats :** M4-T34.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-02 - Fenetre TOCTOU apres is_current

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** Revoquer pendant ou juste apres la tentative.
- **Preuve actuelle :** CAS et is_current testent seulement un sous-intervalle; aucune linearizabilite finale.
- **Mitigation proposee :** Contrat de coherence revocation borne avec IAM owner, instrumentation sur 2 processus.
- **Condition de levée :** SLO de delai de revocation, tests de concurrence dans deploiement cible.
- **Oracles candidats :** M4-T25 M4-T35.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-03 - Usurpation d'adresse reseau via proxy

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** X-Forwarded-For provenant d'un client ou proxy mal configure.
- **Preuve actuelle :** Banc no-proxy ignore l'entete, ne modele pas production.
- **Mitigation proposee :** Liste de proxies de confiance, enforcement edge et test end-to-end.
- **Condition de levée :** Diagramme de chaine TLS/proxy + test de spoofing deploye.
- **Oracles candidats :** M4-T37.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-04 - Disponibilite Redis/KMS/Postgres et surcharge

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** Attaquant spam de fausses cles et erreurs ressources.
- **Preuve actuelle :** Redis/Postgres 503 verifies au banc; KMS reel non teste.
- **Mitigation proposee :** Circuit breaker sans fail-open, limites de pools, quotites, SLO et chaos.
- **Condition de levée :** Tests de saturation multi-noeuds et MTTD/MTTR.
- **Oracles candidats :** M4-T17 M4-T20 M4-T33 M4-T37.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-05 - Vol/rotation de cle serveur HMAC

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** Materiel serveur expose ou ref mal mappee.
- **Preuve actuelle :** Policy host allowlist et HMAC testes; integration KMS absente.
- **Mitigation proposee :** KMS/Vault avec IAM minimal, rotation et reissue, audit acces.
- **Condition de levée :** ADR-0016 accepte + simulation de rotation source reelle.
- **Oracles candidats :** M4-T16 M4-T19 M4-T35.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-06 - Fuite de secret ou identifiant dans logs/metrics

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** Logs ingress, traces, exception, dump process.
- **Preuve actuelle :** repr/erreurs verifies; audit durable et redaction HTTP infra non preuves.
- **Mitigation proposee :** Politique de redaction end-to-end et tests contre canary dans logs.
- **Condition de levée :** Export de journaux filtrables SIEM et retention verifiee.
- **Oracles candidats :** M4-T38.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-07 - Enumeration de selecteurs par temps de reponse

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** Difference entre missing et wrong key au reseau.
- **Preuve actuelle :** 20+20 mesures loopback; pas d'equivalence statistique.
- **Mitigation proposee :** Concevoir mesure multi-echecs, intervalles, seuils, budgets, anti-abus.
- **Condition de levée :** Etude preenregistree avec tests sur architecture reelle.
- **Oracles candidats :** M4-T13 M4-T37.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-08 - Derive du modele de tenants/caches

- **Priorite proposee :** MEDIUM ; **statut :** PENDING.
- **Scenario / surface :** Cache global ou owner ignore le scope.
- **Preuve actuelle :** SQL WHERE scope teste dans schema ephemere; prod/ORM non audites.
- **Mitigation proposee :** Revue de requetes avec isolation DDL/row security et cache namespacing.
- **Condition de levée :** DB de destination et 2 versions controlees + plan d'isolation.
- **Oracles candidats :** M4-T11 M4-T36.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-09 - Decalage entre plan M4 et registre candidat

- **Priorite proposee :** MEDIUM ; **statut :** PENDING.
- **Scenario / surface :** Correspondances M4-T et G5 redigees sans adoption formelle.
- **Preuve actuelle :** 40 lignes et 16 criteres presents mais candidats.
- **Mitigation proposee :** Relecture ligne a ligne du plan canonique et approbation du mapping.
- **Condition de levée :** Diff signe des oracles et criteres officiels.
- **Oracles candidats :** M4-T40.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.

### R-M4-10 - Absence d'autorite independante et GO formel

- **Priorite proposee :** HIGH ; **statut :** PENDING.
- **Scenario / surface :** Fusion/deploiement sur seule CI verte.
- **Preuve actuelle :** 0 adjudications; ADR propos; PR draft.
- **Mitigation proposee :** Interdire merge/release et exiger decision, revue, checks sur HEAD.
- **Condition de levée :** Review GitHub APPROVED + owner gate signe au SHA exact.
- **Oracles candidats :** M4-T39 M4-T40.
- **Responsable, date d'approbation, profil de deploiement, risque residuel, signature :** NON RENSEIGNES.


## Conditions de validite

Une CI du banc de reference ne ferme pas un risque residuel en production. Le relecteur doit documenter pour chaque risque : probabilite, impact, detectabilite, profil exact, mitigation mise en oeuvre, preuve de verification, responsable, validite temporelle et acceptation/NO-GO. **Aucun risque n'est accepte dans ce fichier.**

## F-M4-01 - Ambiguous duplicate Authorization headers (adversarial review)

- **Observed during desk review:** the initial reference host retrieved a single
  `request.headers.get("authorization")` value and did not explicitly reject
  multiple Authorization fields. Different HTTP intermediaries can disagree on
  header selection; no production reverse proxy is qualified here.
- **Mitigation candidate:** reject multiple Authorization fields through the
  same guarded `Rejected` path without reflecting field contents; never
  select first/last/comma-joined bearer.
- **Regression evidence:** `qualification/m4_host/tests/test_m4_http.py::
  test_m4_duplicate_authorization_headers_never_authenticate` (after
  this review's exact-HEAD CI completes).
- **Residual risk:** header normalization/smuggling across real proxies,
  HTTP/2-to-HTTP/1 translation, TLS termination and ingress limits remain
  **UNQUALIFIED**. Associate this finding with R-M4-03 and M4-T37.
- **Disposition:** remediation submitted for reference host; not an
  independent production security acceptance.
