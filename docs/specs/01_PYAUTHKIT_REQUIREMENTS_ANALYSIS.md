# 01_PYAUTHKIT_REQUIREMENTS_ANALYSIS

# PyAuthKit - Analyse des exigences

| Métadonnée | Valeur |
|---|---|
| Produit | **PyAuthKit** |
| Document | `01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md` |
| Type | Analyse des exigences (fonctionnelles, non fonctionnelles, sécurité et architecture) |
| Statut | **Proposition de spécification - à valider** |
| Version du document | `0.1.0-draft` |
| Date | 27 octobre 2026 |
| Source principale | `00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md` |
| Documents suivants | `02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md`, `03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md` |
| Langue | Français (vocabulaire technique anglais conservé) |

> **Mission** - Transformer l'expression du besoin PyAuthKit en un référentiel explicite, priorisé, vérifiable et traçable, sans confondre authentification, gestion des identités et autorisation.

> **Lecture importante** - Les capacités décrites dans `00` sont la **source du besoin**. Les identifiants, les priorités, la segmentation par release, certains invariants et les critères détaillés ci-dessous sont des **propositions de formalisation**. Leur présence dans ce document n'implique ni que l'API existe, ni que tous les choix techniques sont déjà arbitrés.

---

## 1. Objet, périmètre et méthode

### 1.1 Objet du document

Ce document doit servir de contrat de conception, d'implémentation, de qualification et d'évolution de PyAuthKit. Il permet :

1. de formaliser les attentes des utilisateurs et des intégrateurs ;
2. de distinguer les exigences centrales des extensions ;
3. de préserver le statut **framework-agnostic**, **provider-agnostic** et **storage-agnostic** ;
4. d'établir la frontière avec PyIAMKit et les autres frameworks Py**Kit ;
5. de rendre chaque comportement observable et testable ;
6. de structurer un MVP crédible et la progression vers une plateforme d'authentification avancée ;
7. d'identifier les arbitrages non encore décidés.

### 1.2 Référentiel de traçabilité

Les rubriques du document source les plus structurantes sont :

| Source `00` | Apport principal |
|---|---|
| §1-4 | Contexte, problème, vision, objectif du moteur |
| §5-6 | Frontières entre authentication et IAM |
| §7-9 | Principals, méthodes et social authentication |
| §10-14 | Pipeline, flows, modèle conceptuel, adaptive et step-up |
| §15-18 | Sessions, tokens, credentials, fédération |
| §19-25 | Agnosticisme, principes d'architecture, APIs, extensibilité |
| §26-28 | Sécurité, audit, multi-tenancy |
| §29-32 | Cas d'usage, PyIAMKit, PyAgentsKit, Synqentra |
| §33-36 | Hors périmètre, MVP, trajectoire, réussite |
| §37-39 | Synthèse et positionnement dans l'écosystème |

**Convention de source :** une référence comme `00 §15` désigne la section 15 de `00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md`.

### 1.3 Taxonomie des exigences

| Préfixe | Catégorie | Exemple |
|---|---|---|
| `FR-xxx` | Functional Requirement | Authentifier une requête normalisée |
| `NFR-xxx` | Non-Functional Requirement | Async-first, testabilité, performance |
| `SEC-xxx` | Security Requirement | Résistance au rejeu, validation des preuves |
| `ARC-xxx` | Architectural Requirement | Core indépendant du transport et du stockage |
| `INT-xxx` | Integration Requirement | Contrat PyIAMKit, adaptateurs Web |
| `ACC-xxx` | Acceptance Criterion | Scénario vérifiable de conformité |
| `DEC-xxx` | Decision Pending | Arbitrage requis avant implémentation |
| `RSK-xxx` | Risk | Risque produit ou technique |

### 1.4 Priorisation proposée

| Niveau | Sens | Règle |
|---|---|---|
| `P0` | Fondamental | Nécessaire au MVP ou à ses garanties de sécurité |
| `P1` | Étape structurante suivante | Conçu pour être intégré après validation du noyau |
| `P2` | Extension majeure | Reportée, sans casser les abstractions du noyau |
| `P3` | Option / recherche | Dépend d'une demande ou d'une décision ultérieure |

**Attention :** une fonctionnalité `P2` ne doit pas être implémentée pour considérer le MVP achevé. En revanche, certaines exigences architecturales `P0` doivent préparer son intégration future.

### 1.5 Statuts documentaires

- **Établi par `00`** : capacité ou contrainte explicitement présente dans l'expression du besoin.
- **Précision proposée** : interprétation testable d'un besoin de `00`, à confirmer pendant la conception.
- **Décision ouverte** : choix technique, quantitatif ou produit que `00` ne tranche pas.

Les tableaux d'exigences sont donc des **spécifications candidates** ; une revue doit les approuver avant de les traiter comme des engagements définitifs.

---

## 2. Besoin métier et proposition de valeur

### 2.1 Problème

Les applications multiplient les implémentations propriétaires de password login, validation d'API keys, JWT, OIDC, MFA ou sessions. Elles tendent à mélanger mécanisme de preuve, identité organisationnelle et contrôle d'accès, tout en couplant les flux au framework, au provider et au stockage.

Les conséquences identifiées dans `00 §1-2` comprennent : duplication de logique, difficulté à changer de fournisseur, sécurisation inégale, incohérence des tokens et sessions, faible réutilisabilité et couverture insuffisante des principals non humains.

### 2.2 Proposition centrale

> **PyAuthKit est un Authentication Engine Python autonome, modulaire, composable et agnostique, capable de vérifier les preuves d'authentification de principals humains et non humains et de rendre un résultat normalisé.**

Sa question de domaine est : **« Peux-tu prouver qui tu es ? »**

PyIAMKit adresse une autre question : **« Qui es-tu dans le système, à quelle organisation appartiens-tu et que peux-tu faire ? »**

### 2.3 Objectifs mesurables

| Objectif | Expression du succès | Type de preuve |
|---|---|---|
| O-01 Unification | Une API de haut niveau supporte plusieurs stratégies sans branchement métier spécifique | Tests d'intégration multi-authenticator |
| O-02 Autonomie | Le noyau fonctionne sans PyIAMKit ni framework Web | Import et tests Python pur |
| O-03 Extensibilité | Un authenticator tiers peut être ajouté sans modifier le noyau | Plugin externe de référence |
| O-04 Agnosticisme | Les implémentations de stockage et provider sont interchangeables via contrats | Contract tests |
| O-05 Sécurité | Les preuves invalides, expirées ou révoquées sont rejetées selon leur contrat | Tests négatifs et de sécurité |
| O-06 Normalisation | Les résultats utilisent un vocabulaire commun, y compris erreurs et challenges | Schéma/contract tests |
| O-07 Composabilité | Le design accepte ultérieurement MFA, federation et step-up | Spécifications et tests de composition |
| O-08 IAM | Un résultat peut être consommé par PyIAMKit sans couplage interne | Test d'adapter de contrat |
| O-09 Observabilité | Chaque tentative importante peut produire des événements non sensibles | Tests de publication/masquage |

**Pas de chiffres de latence, de débit, de couverture ou de disponibilité figés à ce stade** : leur établissement nécessite un profil de charge et une stratégie de qualification.

---

## 3. Parties prenantes et acteurs

### 3.1 Parties prenantes

| Partie prenante | Besoin dominant |
|---|---|
| Développeur Python | API simple, typée, cohérente, testable |
| Intégrateur FastAPI/Django/Flask | Adaptateurs sans duplication de logique |
| Architecte logiciel | Faible couplage, isolation des responsabilités |
| Responsable sécurité | Contrôles vérifiables, defaults sécurisés, auditabilité |
| Équipe IAM | Principal fiable en entrée, frontière nette des autorisations |
| Équipe plateforme / DevOps | Configuration, rotation, stockage et métriques adaptables |
| Concepteur d'agents | Authentification des identités techniques et déléguées |
| Mainteneur open source | Contrats publics stables et extensibilité maîtrisée |

### 3.2 Catégories de principals

| Type | Illustrations | Preuves possibles | Source |
|---|---|---|---|
| `HUMAN` | utilisateur, administrateur, collaborateur, partenaire | Password, MFA, passkey, OIDC, magic link | `00 §7.1` |
| `SERVICE` | API, microservice, worker | API key, signed token, mTLS, client credentials | `00 §7.2` |
| `APPLICATION` | application cliente | client credentials, assertions, certificat | `00 §7.3` |
| `AGENT` | agent IA, agent métier, automation | workload identity, credential délégué, token bref | `00 §7.4` |
| `DEVICE` | poste, serveur, IoT | certificat, mécanisme adapté au device | `00 §7.5` |
| `WORKLOAD` | container, VM, job CI/CD, fonction serverless | workload assertion, token, certificat | `00 §7.6` |
| `EXTERNAL` | utilisateur d'un IdP externe | OIDC, SAML, fournisseur social | `00 §7.7` |

**Distinction importante :** `EXTERNAL` peut décrire l'origine de l'identité plutôt qu'une nature de principal. Le modèle définitif doit choisir entre un `PrincipalType` exclusif et une combinaison `principal_type` + `identity_origin` (`DEC-05`).

### 3.3 Contextes d'utilisation

- Bibliothèques et applications Python autonomes.
- APIs et applications Web.
- Outils CLI et desktop.
- Background workers, services et microservices.
- Runtimes d'agents.
- Plateformes multi-tenant.
- Applications métiers, dont Synqentra à titre de cible d'intégration.

---

## 4. Périmètre et frontières de responsabilité

### 4.1 Responsabilités de PyAuthKit

- Recevoir et normaliser une demande d'authentification.
- Identifier une stratégie d'authentification compatible.
- Vérifier des secrets, tokens, assertions ou preuves cryptographiques.
- Gérer, par contrats abstraits, credentials, challenges, facteurs, sessions et artefacts associés.
- Exécuter les flows d'authentification et, à terme, les compositions MFA et step-up.
- Intégrer des fournisseurs externes par adapters.
- Évaluer un contexte et des contraintes de confiance propres à l'authentification.
- Produire un **résultat d'authentification normalisé** et des événements exploitables.

### 4.2 Responsabilités de PyIAMKit

- Référentiel et cycle de vie des utilisateurs, comptes et identités.
- Groupes, organisations, tenants, rôles et permissions.
- Décisions d'autorisation, politiques de permissions et gouvernance.
- Provisioning et deprovisioning.
- Revues d'accès et audit de gouvernance IAM.

### 4.3 Hors périmètre de PyAuthKit

Selon `00 §33`, PyAuthKit **ne vise pas** un serveur IAM complet, un annuaire LDAP, un concurrent complet de Keycloak, un moteur général d'autorisation, une interface globale de gestion des comptes, une gouvernance IAM, une solution de détection de fraude, un SIEM, un gestionnaire de mots de passe ou une PKI complète.

**Précision proposée :** la vérification d'une preuve, la création d'une session d'authentification et l'émission éventuelle d'un token technique ne signifient pas que PyAuthKit décide quelles ressources sont accessibles. Un `scope` présent dans un token peut être validé en tant que donnée de preuve ou contrainte du token sans transformer le moteur en décideur d'autorisation.

### 4.4 Chaîne de responsabilité cible

```text
Transport / Application / Agent
             |
             v
AuthenticationRequest + Evidence + Context
             |
             v
        PyAuthKit
  authenticator / flow / policy
             |
             v
AuthenticationResult
  - principal authentifié OU rejet/challenge
  - contexte d'assurance
  - preuve/metadata sûres
             |
             v
  PyIAMKit (optionnel)
  résolution identité / groupes / rôles / permissions
             |
             v
  Décision d'autorisation par la couche compétente
             |
             v
  Ressource / Action métier
```

**Contrainte fondamentale :** PyAuthKit ne requiert **ni la présence ni l'exécution** de PyIAMKit pour authentifier un principal (`00 §6.3`).

---

## 5. Exigences fonctionnelles : noyau et contrats

Les colonnes « Source » relient les exigences à `00`. Le niveau est une **proposition** de priorisation.

### 5.1 API et orchestration d'authentification

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-001` | Le moteur accepte une `AuthenticationRequest` normalisée et retourne une `AuthenticationResult` normalisée. | P0 | §3-4, §24 |
| `FR-002` | Le moteur expose un contrat public d'authentification compatible avec un usage asynchrone (`await ...authenticate(...)`). | P0 | §3, §24 |
| `FR-003` | Chaque demande peut porter une méthode explicite ou être confiée à un mécanisme de résolution d'authenticator. | P0 | §10, §24 |
| `FR-004` | Le registre accepte l'enregistrement de plusieurs authenticators distincts. | P0 | §23-25 |
| `FR-005` | Le moteur rejette sans ambiguïté une méthode absente, inconnue ou impossible à résoudre. | P0 | §10, §24 ; précision proposée |
| `FR-006` | Le résultat distingue une réussite, un échec et, pour les flows évolués, un challenge ou une continuation requise. | P0 (contrat), P1 (challenge runtime) | §11-12 |
| `FR-007` | Chaque tentative dispose d'un identifiant traçable distinct de ses secrets. | P0 | §12, §27 |
| `FR-008` | Le résultat expose le principal authentifié, sans supposer que les rôles et permissions ont été calculés. | P0 | §6, §12 |
| `FR-009` | L'API fournit des erreurs de domaine cohérentes sans exposer les détails sensibles d'un échec. | P0 | §26-27 ; précision proposée |
| `FR-010` | Un nouvel authenticator peut être installé sans ajouter des conditions centralisées spécifiques à son fournisseur. | P0 | §25 |

### 5.2 Principal, contexte et preuve

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-011` | Le modèle représente au minimum les principals humains, services, applications, agents, devices et workloads, sans imposer un sous-système IAM. | P0 (modèle) | §7, §12 |
| `FR-012` | Le moteur reçoit des credentials ou des preuves d'authentification via une abstraction commune. | P0 | §4, §12 |
| `FR-013` | La demande peut transporter un `AuthenticationContext` détaché des détails HTTP. | P0 | §12, §19 |
| `FR-014` | Le contexte peut être enrichi avec application, channel, device, IP, tenant et signaux externes selon les intégrations disponibles. | P1 | §12, §28 |
| `FR-015` | Le modèle de résultat peut associer identité déclarée/résolue, facteurs et assurance sans les exiger pour chaque stratégie. | P0 (contrat extensible) | §12 |
| `FR-016` | Les données de tenant, organization ou realm sont des attributs de contexte ; PyAuthKit n'impose pas leur cycle de vie. | P0 | §28 |

### 5.3 Credentials et cycle de vie

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-017` | Les contrats de credential permettent une validation sans imposer un stockage concret. | P0 | §17, §21 |
| `FR-018` | Les implémentations applicables peuvent gérer création, expiration et révocation de credentials. | P1 | §17 |
| `FR-019` | Les implémentations applicables peuvent gérer rotation et invalidation de credentials. | P1 | §17 |
| `FR-020` | Les métadonnées et états des credentials ne divulguent pas les secrets en représentation ou observabilité. | P0 | §17, §26-27 |
| `FR-021` | La gestion d'un credential compromis dispose d'un chemin d'invalidation ou de délégation explicite. | P1 | §17, §26 |

### 5.4 Authenticators du MVP

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-022` | Un `PasswordAuthenticator` vérifie un mot de passe au moyen d'un contrat de vérification sécurisé interchangeable. | P0 | §8.1, §34 |
| `FR-023` | La vérification de password n'impose pas à l'API domaine un algorithme de hashage unique. | P0 | §8.1 |
| `FR-024` | Un `APIKeyAuthenticator` vérifie les clés d'API via un contrat de recherche et de validation sécurisé. | P0 | §8.3, §34 |
| `FR-025` | Un `JWTAuthenticator` vérifie signature et claims attendus, dont issuer, audience et validité temporelle lorsqu'applicables. | P0 | §8.5, §34 |
| `FR-026` | La validation JWT peut résoudre des clés de confiance selon un contrat configurable, sans présupposer un fournisseur unique. | P0 | §8.5, §20 |
| `FR-027` | Le moteur supporte l'ajout d'autres mécanismes au-delà des trois authenticators initiaux sans changement de contrat métier. | P0 | §25, §34 |

### 5.5 Méthodes avancées

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-028` | Un authenticator peut prendre en charge PIN selon une politique adaptée au contexte/device. | P2 | §8.2 |
| `FR-029` | Le moteur peut valider des bearer tokens indépendamment du format JWT. | P1 | §8.4, §16 |
| `FR-030` | Le système peut supporter OTP email/SMS ou provider tiers via adapters. | P1 | §8.6 |
| `FR-031` | Le système peut vérifier TOTP compatible avec des applications d'authentification standards. | P1 | §8.7 |
| `FR-032` | Un flow MFA peut composer plusieurs facteurs plutôt que déléguer toute la logique à un authenticator monolithique. | P1 | §8.8, §11 |
| `FR-033` | Le moteur sait créer, valider, expirer et consommer un challenge d'authentification. | P1 | §10-12 |
| `FR-034` | Le moteur peut gérer un flow passwordless par magic link à durée de vie limitée. | P2 | §8.11 |
| `FR-035` | Le moteur peut initier et vérifier une authentification WebAuthn. | P2 | §8.9 |
| `FR-036` | Le moteur peut prendre en charge les passkeys fondées sur WebAuthn/FIDO. | P2 | §8.10 |
| `FR-037` | Le moteur peut élever l'assurance d'une session existante pour une opération sensible (step-up). | P2 | §14 |

### 5.6 Sessions et tokens

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-038` | Une abstraction `SessionStore` permet les opérations adaptées au cycle de vie des sessions. | P1 | §15 |
| `FR-039` | Une session peut être créée, lue/validée, expirée, renouvelée et révoquée selon les capacités du store. | P1 | §15 |
| `FR-040` | Une session peut porter des métadonnées et le contexte d'assurance d'authentification. | P1 | §15 |
| `FR-041` | Les implémentations concernées permettent rotation et invalidation globale des sessions. | P1 | §15 |
| `FR-042` | La représentation des tokens ne présuppose pas le format JWT. | P0 (modèle) | §16 |
| `FR-043` | Le moteur prévoit les access, refresh, ID, session, one-time et challenge tokens selon leur usage et leur phase d'adoption. | P1/P2 | §16 |
| `FR-044` | L'émission, la vérification, la rotation et la révocation de tokens sont des responsabilités distinctes et configurables lorsqu'applicables. | P1 | §16, §26 ; précision proposée |

### 5.7 Fédération et social login

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-045` | Un adapter OIDC peut prendre en charge un parcours fédéré et valider un ID Token selon son contrat de confiance. | P2 | §8.12, §18 |
| `FR-046` | Un provider social est un adapter, non une dépendance conceptuelle du core. | P0 (architecture), P2 (connecteurs) | §9, §20 |
| `FR-047` | Le moteur peut accepter des providers Google, Microsoft, GitHub, Apple ou custom sans les rendre obligatoires. | P2 | §9 |
| `FR-048` | Le moteur peut intégrer des scénarios OAuth 2.0 nécessaires aux flux délégués et machine-to-machine, sans qualifier OAuth 2.0 seul de protocole d'authentification utilisateur. | P2 | §8.13 |
| `FR-049` | Un adapter SAML peut vérifier des preuves fédérées d'un fournisseur entreprise. | P2 | §8.14, §18 |
| `FR-050` | Le résultat fédéré conserve une identification explicite de l'origine et de la preuve, sans créer automatiquement un compte IAM. | P2 | §6, §7.7, §11 ; précision proposée |

### 5.8 Authentification machine, device, workload et agent

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-051` | Le modèle représente un `SERVICE`, `APPLICATION`, `AGENT`, `DEVICE` ou `WORKLOAD` comme principal authentifiable. | P0 (modèle) | §7 |
| `FR-052` | Le moteur peut vérifier une identité machine par API key ou token sans dépendre d'une session Web humaine. | P0 | §7.2, §34 |
| `FR-053` | Le moteur peut intégrer OAuth 2.0 client credentials. | P2 | §8.17 |
| `FR-054` | Le moteur peut vérifier des certificats et, via intégration adaptée, une authentification mTLS. | P2 | §8.15-16 |
| `FR-055` | Le moteur peut vérifier des signed assertions et workload identity assertions. | P2 | §8.18 |
| `FR-056` | Les intégrations agentiques peuvent transmettre des credentials délégués ou tokens à durée de vie courte via contrats explicites. | P2 | §7.4, §31 |

### 5.9 Contextualisation, politiques et adaptive authentication

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-057` | Une policy d'authentification peut imposer des conditions relatives au mécanisme, au contexte ou à l'assurance. | P1 | §4, §13-14 |
| `FR-058` | Le moteur peut recevoir des signaux de risque calculés hors du core. | P2 | §13 |
| `FR-059` | Une policy peut demander un facteur supplémentaire en cas de niveau d'assurance insuffisant. | P2 | §13-14 |
| `FR-060` | Le système sait distinguer refus d'authentification, challenge supplémentaire et authentification réussie. | P1 | §11-14 |

### 5.10 Audit et observabilité

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `FR-061` | Les tentatives d'authentification peuvent produire des événements typés de début, succès et échec. | P0 | §27 |
| `FR-062` | Les extensions publient les événements pertinents de validation, challenge, session, token et credential. | P1 | §27 |
| `FR-063` | Les consommateurs externes (logs, SIEM, monitoring, analytics, workflow) utilisent un contrat d'événement indépendant du domaine. | P1 | §27 |
| `FR-064` | La publication des événements n'expose ni credentials ni secrets ni tokens bruts. | P0 | §27 |

---

## 6. Exigences architecturales

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| `ARC-001` | Le core PyAuthKit est une bibliothèque Python autonome et ne dépend ni de Django, FastAPI, Flask ni d'un conteneur HTTP. | P0 | §19 |
| `ARC-002` | Les mécanismes d'authentification sont implémentés via des stratégies et/ou contrats d'authenticator explicites. | P0 | §22-23 |
| `ARC-003` | Les dépendances externes sont derrière des **ports** ; leurs implémentations sont des **adapters**. | P0 | §21-23 |
| `ARC-004` | L'orchestration et la résolution des authenticators sont séparées de leur logique spécifique. | P0 | §10, §22-25 |
| `ARC-005` | Les objets domaine ne dépendent pas de modèles ORM, objets request Web ni SDK de provider. | P0 | §19-22 |
| `ARC-006` | L'ajout d'un provider ne nécessite pas l'édition d'une cascade centrale de `if/elif`. | P0 | §25 |
| `ARC-007` | Le cœur expose des objets et événements normalisés indépendants des transports. | P0 | §12, §27 |
| `ARC-008` | Les magasins de sessions, credentials et tokens sont interchangeables par contrats. | P0 (contrats), P1 (backends) | §15-17, §21 |
| `ARC-009` | Le noyau distingue preuve, authenticator, flow, policy, résultat, session et token. | P0 | §12, §22-23 |
| `ARC-010` | Les interfaces publiques évitent les hypothèses structurelles JWT-only ou OAuth-only. | P0 | §8.13, §16 |
| `ARC-011` | Les modes de fonctionnement synchrone ou asynchrone sont délimités et documentés ; le chemin public async est supporté. | P0 | §3, §24 ; précision proposée |
| `ARC-012` | Le système conserve une séparation explicite entre authentification, résolution d'identité et décision d'autorisation. | P0 | §6, §22 |
| `ARC-013` | Les politiques d'authentification sont distinctes des permissions IAM et des règles de ressource. | P0 | §4, §6, §13 |
| `ARC-014` | La configuration de provider, tenant et stockage n'est pas codée en dur dans le domaine. | P0 | §20-21, §28 |
| `ARC-015` | L'intégration avec un framework ou un fournisseur est facultative et isolable par extra/package/adaptateur. | P1 | §19-20 ; modalité à décider |
| `ARC-016` | Les contrats publics ont une politique explicite de compatibilité et de dépréciation. | P1 | §25, §36 ; précision proposée |
| `ARC-017` | L'architecture permet de composer MFA et challenges à terme, sans imposer dès le MVP un moteur de workflows généraliste. | P0 (design), P1 (fonction) | §10-11, §34-35 |
| `ARC-018` | Le core n'importe pas PyIAMKit ; leur relation est définie au moyen d'un contrat public minimal. | P0 | §6.3, §30 |

### 6.1 Principes de conception et patterns

| Principe / pattern | Application proposée | Anti-pattern à éviter |
|---|---|---|
| Separation of Concerns | `domain`, `application`, `ports`, `adapters` | Un authenticator qui gère utilisateurs, sessions HTTP et permissions |
| Dependency Inversion | Ports pour les stores, validateurs et providers | Imports du SDK Google/ORM dans le domaine |
| Open/Closed Principle | Ajout par registry/plugin | Modifier le core pour chaque provider |
| Strategy | Un authenticator par mécanisme | Une fonction gigantesque à paramètres conditionnels |
| Adapter | OIDC provider, JWT verifier, store, Web adapter | Modèle interne dicté par le fournisseur |
| Factory / Registry | Résolution contrôlée des authenticators | Instanciation dispersée dans les endpoints |
| Pipeline / Chain of Responsibility | Enchaînement de vérification et de challenges | Flow rigide incorporé à la méthode HTTP |
| Hexagonal Architecture | Cœur pur, ports sortants, interfaces entrantes | Dépendance du core envers l'infrastructure |
| DDD | Ubiquitous language cohérent | Synonymes imprécis `user`, `account`, `identity`, `principal` |
| KISS / YAGNI (précision proposée) | MVP restreint et contrats futurs | Implémenter tous les protocoles au bootstrap |

Ces patterns ne constituent **pas** une obligation d'introduire une classe pour chacun : ils guident les responsabilités et seront validés dans `02` et `03`.

---

## 7. Exigences de sécurité

**Note :** `00 §26` liste les thèmes de sécurité fondamentaux. Les règles opérationnelles ci-dessous sont des spécifications candidates approfondissant cette liste. Elles devront être revues avec les normes et recommandations de sécurité applicables lors de la conception détaillée.

### 7.1 Protection des secrets et preuves

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `SEC-001` | Aucun secret, password, API key ou token brut n'apparaît dans les exceptions, traces, `repr`, journaux ou événements. | P0 | §26-27 |
| `SEC-002` | Les vérifications de secrets adaptées utilisent une comparaison résistante aux fuites temporelles pertinentes. | P0 | §26 |
| `SEC-003` | Les passwords sont vérifiés avec un mécanisme de hashage de mot de passe robuste, salé et configurable, et non conservés en clair. | P0 | §8.1, §26 |
| `SEC-004` | Les API keys ne nécessitent pas un stockage récupérable en clair pour leur validation ; le modèle prévoit des empreintes sûres. | P0 | §8.3, §26 ; précision proposée |
| `SEC-005` | Les secrets de providers et clés cryptographiques sont fournis par interfaces de configuration sécurisées, jamais codés en dur. | P0 | §26 ; précision proposée |

### 7.2 Validation cryptographique et tokens

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `SEC-006` | Un token signé n'est accepté que si l'algorithme et la clé sont autorisés par une configuration de confiance explicite. | P0 | §8.5, §26 ; précision proposée |
| `SEC-007` | Les claims requis sont validés (au minimum temporels, issuer et audience lorsque le contrat les exige). | P0 | §8.5 |
| `SEC-008` | La validation échoue de façon fermée en cas de signature invalide, donnée malformée, clé inconnue ou conditions de confiance non satisfaites. | P0 | §8.5, §26 ; précision proposée |
| `SEC-009` | L'architecture prévoit la rotation de clés et leur résolution (dont JWKS selon les adapters). | P0 (contrat), P1 (adapters) | §8.5, §26 |
| `SEC-010` | Un mécanisme de révocation ou de limitation de vie est défini pour les types de tokens qui en ont besoin. | P1 | §16, §26 |

### 7.3 Protection des flows

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `SEC-011` | Les flows à challenge possèdent un mécanisme d'expiration, d'association au contexte et de limitation de rejeu. | P1 | §10-11, §26 |
| `SEC-012` | Les intégrations OIDC/OAuth concernées vérifient `state`, `nonce` et PKCE lorsqu'applicables. | P2 | §26 |
| `SEC-013` | Les flows Web concernés disposent d'une défense CSRF adaptée et ne la délèguent pas implicitement au core Python pur. | P1 | §26 ; précision proposée |
| `SEC-014` | Les sessions concernées supportent expiration, révocation et protection contre la fixation. | P1 | §15, §26 |
| `SEC-015` | Les challenges à usage unique ne peuvent pas être validés plusieurs fois après consommation. | P1 | §8.11, §26 ; précision proposée |

### 7.4 Abus, policy et traçabilité

| ID | Exigence vérifiable | Priorité | Source |
|---|---|---|---|
| `SEC-016` | Des points d'extension existent pour rate limiting, limitation d'essais et politiques de lockout. | P0 (hooks), P1 (providers) | §26 |
| `SEC-017` | Les réponses publiques ne doivent pas faciliter la divulgation d'existence d'un compte ou d'un secret ; la politique exacte dépend du contexte. | P0 | §26 ; précision proposée |
| `SEC-018` | Une erreur technique non prévue ne doit jamais être convertie en authentification réussie. | P0 | §26 ; précision proposée |
| `SEC-019` | Toute réussite est liée à une preuve effectivement validée, et non à la seule présence d'un identifiant déclaré. | P0 | §2, §4 ; précision proposée |
| `SEC-020` | Les événements d'audit permettent de corréler les tentatives sans exposer les preuves sensibles. | P0 | §27 |
| `SEC-021` | Le moteur distingue échec de credential, échec de confiance, indisponibilité externe et policy de refus pour l'audit interne, sans fuite de détails vers le client. | P1 | §26-27 ; précision proposée |
| `SEC-022` | En mode multi-tenant, la résolution de credentials, clés et providers est isolée par le contexte de confiance attendu. | P1 | §28 ; précision proposée |
| `SEC-023` | Les intégrations externes encadrent explicitement les redirections, URLs de callback et origines de confiance. | P2 | §18, §26 ; précision proposée |
| `SEC-024` | Les algorithmes et paramètres cryptographiques ne sont pas figés dans les entités métier. | P0 | §8.1, §26 |

### 7.5 Invariants de sécurité candidats

```text
S-INV-01  AuthenticationResult.success implique une preuve vérifiée.
S-INV-02  Un échec de validation n'émet pas un principal authentifié.
S-INV-03  Les secrets ne franchissent pas les frontières de logs/audit.
S-INV-04  Une méthode inconnue ne provoque aucun fallback implicite faible.
S-INV-05  Une clé ou un issuer non approuvé ne valide pas un token.
S-INV-06  Un challenge consommé/expiré ne peut pas être réutilisé.
S-INV-07  La provenance d'un principal externe reste identifiable.
S-INV-08  Le tenant attendu fait partie du contexte de confiance.
S-INV-09  Un résultat d'authentification n'accorde pas automatiquement une permission.
```

Ce sont des **invariants proposés** à préciser dans `07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md`.

---

## 8. Exigences non fonctionnelles

| ID | Exigence | Critère de vérification / arbitrage | Priorité |
|---|---|---|---|
| `NFR-001` | Portabilité Python | Support vérifié sur la matrice de versions Python à décider (`DEC-01`). | P0 |
| `NFR-002` | Independency / framework agnosticism | Aucun framework Web requis pour installer et utiliser le core. | P0 |
| `NFR-003` | Provider agnosticism | Test de remplacement d'un authenticator/provider par un adapter compatible. | P0 |
| `NFR-004` | Storage agnosticism | Contrats de stockage testables avec implementation mémoire de référence et adapter alternatif. | P0 (contrat) |
| `NFR-005` | Composabilité | Registry et flows ne nécessitent pas de modification métier lors d'une extension. | P0/P1 |
| `NFR-006` | Ergonomie de l'API | Cas simple réalisable avec une séquence documentée courte ; revue développeur. | P0 |
| `NFR-007` | Typage | Signatures et modèles publics typés ; vérification statique sur périmètre défini. | P0 |
| `NFR-008` | Testabilité | Domaine et engine testables sans serveur, réseau ni base de données. | P0 |
| `NFR-009` | Déterminisme | Horloge et sources de hasard injectables lorsque nécessaires aux tests et validations. | P1 |
| `NFR-010` | Performance | Benchmark auth password, API key, JWT ; budgets quantitatifs à décider (`DEC-02`). | P0 (mesure) |
| `NFR-011` | Concurrence | Pas de fuite d'état de tentative entre appels asynchrones concurrents. | P0 |
| `NFR-012` | Robustesse | Exceptions, timeouts et erreurs de provider ne corrompent ni résultat ni état. | P0/P1 |
| `NFR-013` | Observabilité | Événements et traces corrélables via tentative/request ID, sans secrets. | P0 |
| `NFR-014` | Maintenabilité | Modules à responsabilités définies ; revues des dépendances et contract tests. | P0 |
| `NFR-015` | Documentation | Guide d'installation, démarrage, extensions, erreurs, sécurité et limites. | P0 |
| `NFR-016` | Compatibilité | Politique de versionnement/dépréciation documentée avant les releases stables. | P1 |
| `NFR-017` | Interopérabilité | Contrats pour OIDC/OAuth/SAML/WebAuthn lorsque les modules correspondants sont livrés. | P2 |
| `NFR-018` | Configuration | Valeurs par défaut sûres et configuration explicite des dépendances sensibles. | P0 |
| `NFR-019` | Distribution | Packaging Python installable/testable avec dépendances optionnelles adaptées. | P0 |
| `NFR-020` | Déploiement | Aucun service distant obligatoire pour utiliser les authenticators locaux du MVP. | P0 |
| `NFR-021` | Documentation des limites | Features non implémentées et hypothèses de sécurité signalées sans ambiguïté. | P0 |
| `NFR-022` | Scalabilité | Le core n'impose pas un état de processus unique pour sessions/flow futurs. | P1 |

### 8.1 Indicateurs de qualité à définir

Les cibles chiffrées **ne figurent pas** dans l'expression du besoin ; ne pas les présenter comme établies.

| Indicateur | Mesure envisagée | Cible |
|---|---|---|
| Temps de validation password | Distribution des latences selon paramètres de hash | TBD (sécurité prioritaire) |
| Temps de validation JWT | Médiane / percentile haut avec clés chaudes | TBD |
| Temps de validation API key | Selon adapter/store | TBD |
| Débit authentifications | Authentifications/s sur environnement de référence | TBD |
| Couverture de tests | Unitaires, intégration, sécurité, contrats | TBD |
| Versions Python/OS | Matrice CI | TBD |
| Taille du core | Dépendances obligatoires et empreinte d'installation | TBD |
| Durée de rotation/révocation | Selon stores et cohérence exigée | TBD |

---

## 9. Exigences d'intégration

| ID | Exigence | Priorité | Source |
|---|---|---|---|
| `INT-001` | Une API Python pure peut appeler PyAuthKit sans dépendre de PyIAMKit. | P0 | §6.3, §19 |
| `INT-002` | PyIAMKit consomme un contrat minimal de `AuthenticatedPrincipal` / `AuthenticationResult`, sans importer les implémentations de providers. | P1 | §30 |
| `INT-003` | Une intégration FastAPI adapte la requête HTTP, le contexte et les réponses d'erreur aux contrats du core. | P1 | §19 |
| `INT-004` | Une intégration Django suit la même frontière sans faire du modèle Django le modèle domaine. | P1 | §19 |
| `INT-005` | Des intégrations Flask et Starlette peuvent exister sans changer le moteur. | P2 | §19 |
| `INT-006` | PyAgentsKit peut transmettre une identité technique à authentifier et consommer un principal vérifié. | P2 | §31 |
| `INT-007` | Synqentra peut utiliser le moteur pour ses utilisateurs, agents et services, sans imposer sa structure au core. | P2 | §32 |
| `INT-008` | Les adapters de provider présentent un comportement normalisé face aux erreurs et indisponibilités. | P1/P2 | §18, §20 ; précision proposée |
| `INT-009` | Les backends memory, SQL, Redis ou custom peuvent se conformer à des interfaces indépendantes. | P1/P2 | §15, §21 |
| `INT-010` | Les événements peuvent être transmis à logs, monitoring, SIEM ou workflows par un port d'émission. | P1 | §27 |

### 9.1 Matrice de dépendances entre kits

```text
                Application / Service / CLI / Agent
                              |
                              v
                          PyAuthKit
                       (authentication)
                              |
                  AuthenticationResult
                              |
                              v
                     PyIAMKit (optionnel)
                (identity and access management)
                              |
                              v
                    Application / Resource

PyAgentsKit ------> client d'authentification d'agents
Synqentra --------> intégrateur métier de ces contrats
```

- **Dépendance interdite au core** : `PyAuthKit -> PyIAMKit` obligatoire.
- **Dépendance permise chez l'intégrateur** : une application peut composer les deux.
- **Relation à détailler** : qui résout le subject et comment un tenant est validé dans le contexte de confiance.

---

## 10. Modèle de domaine : exigences sémantiques

### 10.1 Vocabulaire conceptuel

| Concept | Définition dans ce document | Distinction importante |
|---|---|---|
| `Principal` | Sujet humain ou non humain qui cherche à s'authentifier ou a été authentifié | Ne signifie pas « compte utilisateur IAM » |
| `Identity` | Identité connue, déclarée ou issue d'un provider | Sa gouvernance appartient à la couche IAM |
| `Credential` | Secret, donnée ou moyen associé à la participation à l'authentification | Ne garantit pas seul la réussite |
| `AuthenticationEvidence` | Preuve présentée ou vérifiée pendant la tentative (proposition) | Plus général que le credential stocké |
| `Authenticator` | Composant vérifiant un mécanisme donné | N'est pas nécessairement un flow complet |
| `AuthenticationRequest` | Entrée normalisée du moteur | Indépendante des objets HTTP |
| `AuthenticationAttempt` | Tentative identifiable et traçable | N'est pas une session persistante |
| `AuthenticationFactor` | Composante/facteur de la cérémonie d'authentification | Ne pas traiter « contextuel » comme second facteur indépendant par défaut |
| `AuthenticationChallenge` | Étape demandant une preuve supplémentaire | A un cycle de vie distinct |
| `AuthenticationFlow` | Orchestration d'étapes de vérification | Peut être simple ou multi-étapes |
| `AuthenticationContext` | Contexte technique, client, risque et tenancy | Certains attributs sont non fiables tant que non vérifiés |
| `AuthenticationPolicy` | Règles relatives à la preuve et à l'assurance | Différente d'une policy d'accès à la ressource |
| `AuthenticationResult` | Résultat normalisé succès/échec/continuation | N'octroie pas de rôles |
| `AuthenticationSession` | État d'un flow ou d'une session authentifiée | Pas synonyme de token |
| `AuthenticationAssurance` | Niveau d'assurance attribué selon les preuves et les règles | Niveau revendiqué distinct du niveau démontré |
| `Token` | Artefact technique pouvant porter preuve, session ou claims | JWT est un format possible, pas le concept |
| `ProviderAdapter` | Connecteur d'un IdP ou mécanisme externe | Ne fait pas partie du domaine pur |
| `CredentialStore` | Port de résolution/gestion des credentials | N'impose pas SQL, Redis ni un ORM |

### 10.2 Conventions de modélisation candidates

1. **Une identité déclarée ne constitue pas une identité authentifiée.**
2. **Un principal authentifié découle d'un chemin de preuve vérifié.**
3. **Une authentification peut être sans session persistante**, par exemple validation d'un token par un service.
4. **Un principal humain peut posséder plusieurs credentials et authentifiers**, sans assimilation obligatoire à un seul fournisseur.
5. **L'identité externe doit conserver sa provenance** (provider et identifiant externe lorsque pertinents).
6. **Un token peut être opaque ou structuré.**
7. **`PrincipalType` et `identity_origin` doivent être séparables** si le besoin multi-provider le justifie.
8. **Le tenant déclaré n'est pas nécessairement le tenant de confiance.** L'adapter/engine doit établir la provenance de ce contexte.
9. **Un facteur TOTP n'implique pas à lui seul un niveau d'assurance déterminé.** Le calcul d'assurance doit intégrer les caractéristiques de la cérémonie.
10. **Les erreurs internes et les réponses client sont deux vues différentes** d'un échec d'authentification.

### 10.3 Questions conceptuelles à traiter ensuite

- `Principal` est-il une entité ayant son propre ID, un value object, ou un `AuthenticatedPrincipal` immuable distinct ?
- L'`Identity` du résultat est-elle facultative si seul un `subject` vérifié est connu ?
- Les `AuthenticationFactor` décrivent-ils uniquement les facteurs de connaissance/possession/inhérence, ou aussi les moyens fédérés et signaux contextuels via une autre classification ?
- La gestion du challenge appartient-elle à une machine d'état interne, un port vers un runtime, ou un flow coordinator minimal ?
- Quelle structure commune de référence entre `subject`, `issuer`, `provider`, `tenant` et `audience` ?

Les réponses seront spécifiées dans `04`, `05`, `06`, `07` et `11`.

---
## 11. Cas d'usage et parcours fonctionnels

Les onze cas d'usage de `00 §29` sont conservés, avec des critères complémentaires proposés pour rendre leur exécution testable.

| UC | Scénario | Principal | Preuve / protocole | Résultat attendu | Priorité proposée |
|---|---|---|---|---|---|
| `UC-01` | Login classique | HUMAN | Email + password | Principal authentifié ou échec sûr | P0 |
| `UC-02` | MFA | HUMAN | Password puis TOTP | Authentification à facteurs composés | P1 |
| `UC-03` | Social login | HUMAN / EXTERNAL | Google / OIDC | Principal externe authentifié | P2 |
| `UC-04` | Enterprise SSO | HUMAN / EXTERNAL | IdP d'entreprise / OIDC-SAML | Preuve fédérée validée | P2 |
| `UC-05` | Passkey | HUMAN | WebAuthn | Authentification passwordless | P2 |
| `UC-06` | API key | SERVICE / APPLICATION | API key | Principal technique authentifié | P0 |
| `UC-07` | Machine-to-machine | SERVICE / APPLICATION | Client credentials | Service authentifié | P2 |
| `UC-08` | mTLS | SERVICE / DEVICE | Certificat + preuve TLS | Identité du pair validée | P2 |
| `UC-09` | Agent authentication | AGENT | Credential/token technique | Agent authentifié | P0 (modèle), P2 (flows spécifiques) |
| `UC-10` | Step-up authentication | HUMAN | Facteur additionnel | Assurance relevée | P2 |
| `UC-11` | Custom provider | Tout principal compatible | Authenticator personnalisé | Résultat standard sans modifier le core | P0 |

### 11.1 Parcours A - Password (MVP)

```text
Client Python
   |
   | AuthenticationRequest(method="password", evidence=...)
   v
AuthenticationEngine
   |
   +--> Resolve PasswordAuthenticator
   |
   +--> Resolve trusted credential material
   |
   +--> Verify password using configured verifier
   |
   +--> Build AuthenticationResult
   |
   +--> Emit safe audit event
   v
AuthenticatedPrincipal OR authentication failure
```

**Postconditions :** le password brut n'est jamais restitué ; le principal ne peut être marqué authentifié qu'après validation effective ; une identité IAM n'est pas requise.

### 11.2 Parcours B - API key (MVP)

```text
Service / CLI / Agent
   |
   +--> Submit API key as evidence
   |
   +--> Resolve APIKeyAuthenticator
   |
   +--> Lookup key verifier / status by trusted store contract
   |
   +--> Validate evidence, expiry and revocation if supported
   |
   +--> Produce service/agent principal + result
   v
Allow application to continue toward its own authorization layer
```

**Point de vigilance :** la validation de l'API key ne confère pas en elle-même des permissions sur les ressources métier.

### 11.3 Parcours C - JWT (MVP)

```text
Bearer JWT
   |
   +--> Parse token in bounded, defensive mode
   |
   +--> Resolve explicitly trusted issuer/keys/algorithms
   |
   +--> Validate cryptographic signature
   |
   +--> Validate required claims and temporal constraints
   |
   +--> Convert verified subject to principal
   v
AuthenticationResult
```

**Point de vigilance :** la consommation d'un JWT d'authentification doit préciser le type et la finalité du token accepté ; on ne considère pas indifféremment tous les JWT comme des preuves valides.

### 11.4 Parcours D - MFA (phase ultérieure)

```text
AuthenticationRequest
   |
   v
Primary credential verification
   |
   +--> rejected -------------> failure
   |
   v
Challenge required
   |
   v
Challenge issued + state persisted
   |
   v
Additional evidence submitted
   |
   +--> invalid/expired ------> failure
   |
   v
Factor verified + assurance evaluated
   |
   v
AuthenticatedPrincipal / Session optional
```

**Point de vigilance :** les `attempt_id`, `challenge_id` et `session_id` ne sont pas interchangeables ; le challenge doit être corrélé au flow et ne pas permettre de rejeu.

### 11.5 Parcours E - Fédération OIDC (phase ultérieure)

```text
Application
   |
   v
OIDC Adapter -> trusted external IdP
   |
   v
Authorization Code Flow (when applicable)
   |
   v
State/nonce/PKCE checks + tokens validation
   |
   v
Trusted federated identity evidence
   |
   v
AuthenticationResult(external principal, provider provenance)
   |
   v
Optional IAM account/identity linkage outside PyAuthKit
```

**Précision protocolaire :** OAuth 2.0 est principalement un cadre d'autorisation ; dans le cas fédéré utilisateur décrit ici, OIDC apporte la couche d'authentification (`00 §8.13`).

### 11.6 Parcours F - Authentification adaptative et step-up (phase ultérieure)

```text
Existing authentication context
   |
   v
Required assurance / risk policy
   |
   +--> sufficient ----------> retain successful context
   |
   +--> insufficient --------> additional factor challenge
   |
   +--> rejected ------------> failure
   |
   v
Updated verified authentication context
```

La logique de risque peut être fournie par un évaluateur externe (`00 §13`), sans obligation d'embarquer une plateforme complète d'analyse comportementale.

---

## 12. Contrats publics candidats

Cette section est **illustrative**, et ne fige ni les classes Python ni la signature définitive de l'API. Le rôle de ce document est de spécifier le *quoi* ; l'API détaillée sera conçue dans `24_PYAUTHKIT_PUBLIC_API_AND_SDK_DESIGN.md`.

### 12.1 Entrée de haut niveau

```python
# Pseudocode conceptuel - classes et noms à confirmer.
request = AuthenticationRequest(
    method="api_key",
    evidence=ApiKeyEvidence(value=api_key),
    context=AuthenticationContext(
        application_id="service-a",
        tenant_id="tenant-a",
    ),
)

result = await engine.authenticate(request)
```

**Règles de contrat proposées :**

- `method` est explicite ou résolue par une stratégie contrôlée ;
- `evidence` est séparée du contexte HTTP et de la configuration de provider ;
- `context` ne devient pas automatiquement « trusted » ;
- l'identifiant de tentative est créé/propagé selon un contrat défini ;
- tout secret est exclu de la sérialisation par défaut des modèles publics.

### 12.2 Résultat commun

```python
# Pseudocode conceptuel - aucun nom ici n'est encore une API stable.
AuthenticationResult(
    status=AuthenticationStatus.AUTHENTICATED,
    principal=AuthenticatedPrincipal(
        subject="service-a",
        principal_type=PrincipalType.SERVICE,
    ),
    attempt_id="...",
    assurance=None,
    challenge=None,
)
```

États recommandés pour la modélisation initiale :

| État | Signification | Principal authentifié ? |
|---|---|---|
| `AUTHENTICATED` | Preuve suffisante, règles remplies | Oui |
| `REJECTED` | Preuve ou condition refusée | Non |
| `CHALLENGE_REQUIRED` | Preuve supplémentaire nécessaire | Pas encore |
| `ERROR` | Incident technique ne permettant pas d'établir la preuve | Non |

Ces états sont **proposés**. Leur relation avec les exceptions, retries et challenges sera tranchée dans les documents domaine/flows. Un échec technique n'est jamais assimilé à une réussite.

### 12.3 Contracts d'extension

```python
# Pseudocode d'un port, non destiné à être exécuté tel quel.
class Authenticator(Protocol):
    @property
    def method(self) -> str: ...

    async def authenticate(
        self,
        request: AuthenticationRequest,
    ) -> AuthenticationResult: ...
```

**Invariant d'extension :** une implémentation tierce conforme à ce contrat doit pouvoir être enregistrée sans modifier le moteur et produire des résultats indiscernables, au niveau du contrat public, de ceux des authenticators internes.

### 12.4 Ports candidatés

| Port / protocole | Responsabilité | Adoption |
|---|---|---|
| `Authenticator` | Vérifier une preuve et retourner un résultat | MVP |
| `AuthenticatorRegistry` | Enregistrer et résoudre une stratégie | MVP |
| `PasswordVerifier` | Vérifier un hash password fourni par un store | MVP |
| `CredentialResolver` | Résoudre les informations nécessaires à la validation | MVP |
| `JWTVerifier` / `KeyResolver` | Vérifier un JWT selon une configuration de confiance | MVP |
| `AuthenticationEventSink` | Recevoir événements d'audit sans secrets | MVP (minimal) |
| `Clock` | Contrôler les validations temporelles | MVP ou phase de durcissement |
| `SessionStore` | Stocker et gérer l'état d'une session | P1 |
| `ChallengeStore` | Stocker/consommer un challenge de flow | P1 |
| `TokenIssuer` | Émettre un artefact signé ou opaque | P1 |
| `RiskEvaluator` | Produire des signaux externes de contexte/risque | P2 |
| `FederationProvider` | Initier/vérifier des flows fédérés | P2 |
| `IdentityBridge` | Convertir une preuve externe en référence connue d'un IAM | P2, hors core IAM |

**Arbitrage requis :** la liste est un inventaire de ports candidats, pas une injonction à créer une interface pour chaque ligne dès le bootstrap.

### 12.5 Catégories d'erreur candidates

| Catégorie | Sens | Exposition publique |
|---|---|---|
| `INVALID_CREDENTIAL` | Preuve insuffisante/invalide | Message générique |
| `UNSUPPORTED_METHOD` | Stratégie non prise en charge | Code neutre |
| `EXPIRED_EVIDENCE` | Artefact périmé | Message neutre selon contexte |
| `CHALLENGE_REQUIRED` | Flow incomplet | Contrat structuré |
| `UNTRUSTED_ISSUER` | Émetteur externe non approuvé | Détail réservé à l'audit |
| `POLICY_REJECTED` | Règle d'authentification non satisfaite | Message neutre |
| `DEPENDENCY_UNAVAILABLE` | Store/provider temporairement indisponible | Aucune authentification implicite |
| `INTERNAL_ERROR` | Erreur non anticipée | Aucune fuite de secret |

La taxonomie, le transport des erreurs et leur granularité seront définis dans `08` et `24`.

---

## 13. MVP : périmètre d'implémentation et non-objectifs

### 13.1 Périmètre fondé sur `00 §34`

L'expression du besoin propose explicitement comme premier MVP :

- `AuthenticationEngine` ;
- `Principal` ;
- `Credential` ;
- `AuthenticationRequest` ;
- `AuthenticationResult` ;
- `Authenticator Protocol` ;
- `Authenticator Registry` ;
- `AuthenticationContext` ;
- `PasswordAuthenticator` ;
- `APIKeyAuthenticator` ;
- `JWTAuthenticator`.

**Compléments proposés pour rendre ce MVP réellement qualifiable :** contrats minimaux de vérification/stockage, gestion d'erreurs, validations négatives, événements d'audit non sensibles, tests de sécurité, documentation de configuration et exemples d'intégration Python pure. Ces compléments ne sont pas une extension du périmètre fonctionnel : ils rendent la première version exploitable de façon contrôlée.

### 13.2 Ce que le MVP doit démontrer

| Capacité | Démonstration minimale |
|---|---|
| Noyau autonome | Import et exécution sans Django/FastAPI/PyIAMKit |
| Authentification unique | `await engine.authenticate(request)` |
| Password | Validation d'un bon/mauvais mot de passe, pas de stockage clair |
| API key | Validation d'une clé correcte, incorrecte ou invalidée selon adapter |
| JWT | Validation de signature, issuer, audience, expiration et cas invalides |
| Registre | Plusieurs stratégies coexistent et sont résolues sans dépendance au fournisseur |
| Extensibilité | Authenticator tiers de démonstration, sans modification du core |
| Principal | Résultat normalisé pour humain et non-humain |
| Audit | Événements de succès/échec sans exposition de credentials |
| Sécurité | Échecs fermés et matrice de tests négatifs |
| Storage-agnostic | Contrat testé avec un backend de test mémoire ; autre backend non requis d'emblée |

### 13.3 Hors-MVP intentionnel

| Capacité | Pourquoi la repousser | Préparation dès le MVP |
|---|---|---|
| MFA, TOTP, OTP | Requiert un modèle de challenge, d'état et de facteurs | `AuthenticationResult` extensible |
| Sessions complètes | Cycle de vie/révocation/store plus large | Séparer le résultat de la session |
| Emission/refresh tokens | Politique et cycle de vie propres | Ne pas lier authentication et JWT |
| OIDC / social login | Protocoles de redirect/state/provider | Ports d'adapters |
| SAML | Forte complexité de validation fédérée | Provenance des preuves |
| WebAuthn / passkeys | Cérémonie cryptographique et challenge | API request/result neutre |
| Magic links | Token ponctuel + transport/outbound | Abstraction de challenge et token |
| mTLS, certificats | Frontière transport et trust store | Principal machine, ports d'evidence |
| Client credentials | Parcours d'autorisation technique séparé | Principal SERVICE/APPLICATION |
| Adaptive risk / step-up | Requiert policies, niveaux et state | Context/assurance extensibles |
| Multi-tenant avancé | Résolution de confiance et isolation | `tenant_id` contextualisé |
| UI d'administration | Ce n'est pas le métier du core | Aucun couplage aux vues |

### 13.4 Exclusions absolues du MVP

Le MVP **ne doit pas** embarquer : système de comptes IAM complet, moteur RBAC/ABAC, console d'administration complète, annuaire, gouvernance d'identités, moteur antifraude, SIEM, PKI complète, implémentation universelle de fournisseurs sociaux, ou runtime générique d'agents.

### 13.5 Jalons candidats

| Phase | Contenu | Critère de passage |
|---|---|---|
| `M0 - Bootstrap` | Packaging, domaine minimal, configuration, qualité | Install/import/tests du core |
| `M1 - Kernel` | Engine, registry, request/result, erreurs | Contract tests du kernel |
| `M2 - Core Authenticators` | Password, API key, JWT | Scénarios positifs/négatifs |
| `M3 - Security Qualification` | Durcissement, audit, tests d'extension | Critères P0 satisfaits |
| `M4 - MVP Review` | Documentation, compatibilité, décision de release | Revue formelle GO / NO-GO |

Ces jalons sont **un découpage de travail suggéré**, distinct d'une roadmap de versions définitive. La roadmap sera construite dans `27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md`.

---

## 14. Matrice de validation et critères d'acceptation

Chaque critère peut être traduit en tests unitaires, tests d'intégration, tests contractuels et tests de sécurité.

### 14.1 Critères MVP

| ID | Given | When | Then | Exigences couvertes |
|---|---|---|---|---|
| `ACC-001` | Un core installé sans framework Web | Une API Python pure invoque le moteur | L'authentification s'exécute sans imports Web obligatoires | FR-001, ARC-001 |
| `ACC-002` | Password vérifiable et principal connu d'un resolver | Le password correct est soumis | Le résultat est `AUTHENTICATED` et référence le principal vérifié | FR-022, SEC-019 |
| `ACC-003` | Password invalide | Le password erroné est soumis | Pas de principal authentifié ni exposition du secret | FR-022, SEC-001 |
| `ACC-004` | API key valide | Une application la présente | Le moteur retourne un principal technique | FR-024, FR-052 |
| `ACC-005` | API key non reconnue/invalide | La clé est présentée | La tentative est rejetée de façon sûre | FR-024, SEC-018 |
| `ACC-006` | JWT signé par une clé approuvée avec claims valides | Le JWT est présenté | Le moteur retourne un principal dérivé de claims vérifiés | FR-025, SEC-006-007 |
| `ACC-007` | JWT avec signature modifiée | Le JWT est présenté | Le résultat n'est pas authentifié | FR-025, SEC-008 |
| `ACC-008` | JWT expiré / audience inattendue / issuer non autorisé | Le JWT est présenté | Le résultat est rejeté selon la politique de confiance | FR-025, SEC-007-008 |
| `ACC-009` | Authenticator inconnu | Une méthode inconnue est demandée | Échec contrôlé, sans fallback vers un autre mécanisme | FR-005, SEC-018 |
| `ACC-010` | Deux authenticators enregistrés | Des requests de méthodes différentes sont exécutées | Chaque request utilise la stratégie adéquate | FR-003-004 |
| `ACC-011` | Un plugin tiers conforme au contrat public | Il est ajouté au registre | Le core n'est pas modifié et le résultat demeure normalisé | FR-010, ARC-006 |
| `ACC-012` | Un composant de stockage mémoire remplace un autre resolver | Les mêmes tests contractuels sont rejoués | Les invariants de validation restent identiques | FR-017, ARC-008 |
| `ACC-013` | Un échec d'authentification | Un événement est émis | On peut corréler la tentative sans retrouver le credential | FR-061, FR-064, SEC-020 |
| `ACC-014` | PyIAMKit absent de l'environnement | Le moteur est initialisé et utilisé | Aucune erreur de dépendance IAM | INT-001, ARC-018 |
| `ACC-015` | Deux requests concurrentes avec evidences distinctes | Elles sont traitées simultanément | Aucun principal, secret ou contexte n'est croisé | NFR-011 |
| `ACC-016` | Un vérificateur externe lève une erreur | Le moteur traite la tentative | Aucune réussite n'est produite implicitement | SEC-018, NFR-012 |
| `ACC-017` | Un principal AGENT ou WORKLOAD | Une preuve adaptée à un authenticator du MVP est présentée | Un résultat normalisé peut décrire ce type sans classe Web user | FR-011, FR-051 |
| `ACC-018` | Logs/debug/exceptions activés | Une authentification est exécutée | Les secrets et tokens bruts sont absents des sorties | SEC-001, FR-064 |

### 14.2 Critères avancés (non bloquants pour le MVP)

| ID | Scénario | Résultat attendu | Conditions préalables |
|---|---|---|---|
| `ACC-019` | Password correct suivi d'un TOTP requis | Pas de réussite avant validation du facteur demandé | ChallengeStore, flow MFA |
| `ACC-020` | TOTP correct mais challenge expiré | Refus du challenge | Expiration et horloge |
| `ACC-021` | Réutilisation d'un magic link à usage unique | Rejeu rejeté | One-time store |
| `ACC-022` | OIDC renvoie un ID token d'un issuer inattendu | Principal externe non authentifié | OIDC adapter |
| `ACC-023` | Échec de `state`/`nonce` OIDC | Flow rejeté | OIDC adapter |
| `ACC-024` | Une session est révoquée | La validation ultérieure ne reconnaît plus la session | SessionStore |
| `ACC-025` | Un flow exige un niveau d'assurance supérieur | Challenge complémentaire ou refus contrôlé | Policy engine |
| `ACC-026` | Contexte tenant A et preuve tenant B | Aucun franchissement de frontière de confiance | Multi-tenant trust design |
| `ACC-027` | Un backend Redis remplace un store mémoire | Les contract tests de session passent | Session persistence |
| `ACC-028` | Une requête FastAPI et une requête CLI équivalentes | Les résultats du core respectent le même contrat | Intégrations |
| `ACC-029` | Un agent utilise un token éphémère | La validation crée un principal AGENT sans accès IAM implicite | Machine/agent auth |
| `ACC-030` | Authenticator mTLS avec certificat non approuvé | Échec explicite sans confiance par défaut | Cert adapter |

### 14.3 Stratégie de tests candidate

```text
                       Acceptance tests
                             /\
                            /  \
                   Integration & contract tests
                          /        \
                         /          \
                Unit / domain / negative tests
```

**Tests unitaires :** value objects, validations de paramètres, mapping des résultats, politiques et registry.

**Tests contractuels :** chaque authenticator, resolver, store, adapter et event sink satisfait une suite commune.

**Tests d'intégration :** engine + authenticator + resolver + audit ; puis adapters Web/IdP lorsqu'ils existent.

**Tests de sécurité :** signatures invalides, rejets, expiration, mutations de preuves, fuzzing d'entrées, secret redaction, replay et isolation multi-tenant selon fonctionnalités livrées.

**Tests de concurrence :** appels asynchrones multiples et isolation des variables de contexte.

**Tests de compatibilité :** matrice Python et OS à décider.

**Tests de packaging :** installation minimale puis extras optionnels.

---

## 15. Menaces, risques et mesures de conception

Les éléments ci-dessous sont une **analyse préliminaire**, pas un audit de sécurité ni un threat model exhaustif.

| ID | Risque | Impact potentiel | Mesure candidate | Exigences liées |
|---|---|---|---|---|
| `RSK-001` | Confusion authentication/authorization | Accès accordé sans décision IAM | Frontière domaine et tests contractuels | ARC-012, SEC-019 |
| `RSK-002` | Authenticator fallback silencieux | Bypass par mécanisme plus faible | Résolution explicite et rejet par défaut | FR-005, SEC-018 |
| `RSK-003` | JWT accepté avec mauvaise clé/issuer/algorithme | Usurpation d'identité | Configuration de confiance et tests négatifs | SEC-006-009 |
| `RSK-004` | Credential exposé dans logs | Compromission de compte/service | Redaction et validation des événements | SEC-001, FR-064 |
| `RSK-005` | Hashage password insuffisant | Compromission facilitée après fuite du store | Contrat de vérification robuste | SEC-003 |
| `RSK-006` | Challenge réutilisé | Replay ou takeover | Expiration + consommation unique | SEC-011, SEC-015 |
| `RSK-007` | Mauvaise isolation multi-tenant | Authentification croisée entre tenants | Partition de confiance vérifiée | SEC-022 |
| `RSK-008` | Provider tiers indisponible | Authentifications refusées ou états incomplets | Échec fermé, retries bornés selon contrat | SEC-018, NFR-012 |
| `RSK-009` | Core trop généraliste | Complexité/retard/risques cachés | MVP borné, API minimale | ARC-017 |
| `RSK-010` | Couplage aux SDK providers | Maintenance coûteuse, lock-in | Adapters et ports | ARC-003, ARC-006 |
| `RSK-011` | Erreurs d'API ambiguës | Mauvaises décisions d'intégration | Résultats/erreurs typés et documentés | FR-006, FR-009 |
| `RSK-012` | Confiance excessive dans `tenant_id` d'entrée | Escalade de contexte | Distinguer déclaré/vérifié | SEC-022 |
| `RSK-013` | Confusion des types de tokens | JWT non destiné à l'authentification accepté | Contrats de token, typage/usage explicites | FR-025, ARC-010 |
| `RSK-014` | Dépendances cryptographiques non maintenues | Vulnérabilités de supply chain | Dépendances auditées, mises à jour et CI | NFR-014 ; précision proposée |
| `RSK-015` | API stable prématurément | Ruptures ou mauvais modèle durable | Qualification alpha + arbitrages de domaine | ARC-016 |

### 15.1 Hypothèses de confiance à expliciter

- **Application appelante :** certaines métadonnées sont déclaratives et doivent être distinguées des données fiables.
- **Store de credentials :** conserve ou résout uniquement le matériel indispensable, selon son niveau de confiance.
- **IdP externe :** nécessite une configuration explicite des issuers, clés, audiences et protocoles.
- **Reverse proxy / TLS terminator :** responsable de certaines preuves de transport ; ne pas considérer n'importe quel header client comme preuve mTLS.
- **Service d'horloge :** influe sur expiration, émission et rejeu.
- **Tenant resolver :** établit une frontière de confiance ; ne s'appuie pas uniquement sur une chaîne librement fournie par le client.

Ces hypothèses doivent être cartographiées formellement dans `20_PYAUTHKIT_SECURITY_THREAT_MODEL.md`.

---

## 16. Dépendances, contraintes et arbitrages ouverts

### 16.1 Contraintes établies

- Langage cible : Python.
- Core réutilisable hors Web.
- Indépendance de PyIAMKit.
- Support progressif des humains et des machines.
- Sécurité et modularité structurantes.
- Contrats de stockage et adapters réutilisables.
- Architecture évolutive vers MFA, passwordless, fédération et adaptive authentication.

### 16.2 Registre de décisions

| ID | Décision à prendre | Alternatives / points de discussion | Moment recommandé |
|---|---|---|---|
| `DEC-01` | Versions Python et OS supportés | Matrice de support, versions en fin de vie | Avant bootstrap |
| `DEC-02` | Budgets quantitatifs de qualité | Latence, débit, couverture, concurrency, CI | Avant qualification MVP |
| `DEC-03` | Typage/runtime des modèles | Dataclasses, attrs, Pydantic optionnel, autre | Dans `04-05` |
| `DEC-04` | `Authenticator` abstraction | `Protocol`, ABC, composition, modèle hybride | Dans `03`, `10` |
| `DEC-05` | Modélisation `EXTERNAL` | PrincipalType dédié ou identity origin | Dans `04-06` |
| `DEC-06` | États du résultat | `status` vs exception vs subtypes | Dans `04`, `08` |
| `DEC-07` | Résolution des authenticators | Sélecteur explicite, registry, auto-detection contrôlée | Dans `10` |
| `DEC-08` | Contracts de credentials | Store, verifier, evidence object, secret reference | Dans `05`, `10` |
| `DEC-09` | Hash password et politiques par défaut | Implémentation(s) et paramètres de sécurité | Avant authenticator Password |
| `DEC-10` | Source de confiance pour JWT | Local keys, JWKS, policies, caching | Avant authenticator JWT |
| `DEC-11` | Forme des tokens et leur émission | Validation-only MVP ou émission ultérieure | Dans `13` |
| `DEC-12` | Modèle de session | Stateful/stateless, session vs flow session | Dans `11`, `13` |
| `DEC-13` | Moteur de flows | Pipeline local minimal ou orchestrateur stateful | Dans `11` |
| `DEC-14` | Multi-tenant trust boundary | Contexte, realm resolver, configuration par tenant | Dans `03`, `20` |
| `DEC-15` | Synchrone vs async | Async public seul ou facade sync optionnelle | Avant design API |
| `DEC-16` | Distribution des extras | Modules embarqués, extras PyPI ou packages séparés | Avant packaging stable |
| `DEC-17` | Fournisseurs et stockage initial | Memory-only/reference, SQL/Redis prioritaires | Avant releases post-MVP |
| `DEC-18` | Assurance | Standards, niveaux custom, relation aux facteurs | Dans `12` |
| `DEC-19` | Interface avec PyIAMKit | Minimal subject + provenance, types communs ou adapter | Dans `23` |
| `DEC-20` | Politique de compatibilité/version | SemVer, statut alpha, dépréciations | Avant premier release public |
| `DEC-21` | Événements et données personnelles | Schéma, retention et minimisation | Dans `21` |
| `DEC-22` | Responsabilité des adapters Web | CSRF, cookies, headers, sessions HTTP | Dans `22` |

### 16.3 Points nécessitant recherche ou expertise externe

Le document source ne définit pas les versions précises des normes, les suites cryptographiques, les profils de conformité ni les recommandations opérationnelles applicables. Avant toute annonce de conformité, il faudra vérifier la version courante des spécifications pertinentes (par exemple OIDC/OAuth, WebAuthn/FIDO, SAML, JWT/JWS/JWK, et référentiels d'assurance) ainsi que la bibliothèque cryptographique retenue. **Ce document ne revendique aucune certification de conformité.**

---

## 17. Cartographie de traçabilité

### 17.1 Exigences, capacités et documents de conception

| Groupe d'exigences | Sources initiales | Cible de conception | Qualification principale |
|---|---|---|---|
| FR-001 à FR-010 | `00 §3-4, §10, §23-25` | `03`, `08`, `09`, `24` | ACC-001, 009-011 |
| FR-011 à FR-016 | `00 §7, §12, §28` | `04`, `05`, `06` | ACC-017 |
| FR-017 à FR-021 | `00 §17, §21` | `05`, `10`, `19` | ACC-003, 005, 012, 018 |
| FR-022 à FR-027 | `00 §8, §34` | `09`, `10` | ACC-002-008 |
| FR-028 à FR-037 | `00 §8, §11, §14` | `11`, `12`, `15` | ACC-019-021, 025 |
| FR-038 à FR-044 | `00 §15-16` | `13`, `19` | ACC-024, 027 |
| FR-045 à FR-050 | `00 §9, §18` | `14`, `18` | ACC-022-023 |
| FR-051 à FR-056 | `00 §7, §31` | `16` | ACC-004, 017, 029-030 |
| FR-057 à FR-060 | `00 §13-14` | `12`, `17` | ACC-025 |
| FR-061 à FR-064 | `00 §27` | `21` | ACC-013, 018 |
| ARC-001 à ARC-018 | `00 §19-25, §30` | `02`, `03`, `18`, `23` | ACC-001, 010-012, 014 |
| SEC-001 à SEC-024 | `00 §26-28` | `07`, `20` | ACC-003, 005, 007-009, 013, 015-016, 018 |
| NFR-001 à NFR-022 | `00 §19-27, §36` | `02`, `25`, `26` | CI, benchs, contract tests |
| INT-001 à INT-010 | `00 §19, §30-32` | `18`, `22`, `23` | ACC-001, 014, 028 |

Les noms numériques abrégés `03`, `08`, etc. renvoient aux documents `NN_PYAUTHKIT_...` de la série documentaire.

### 17.2 Couverture des critères de réussite de `00 §36`

| Critère source `00 §36` | Reprise dans cette analyse |
|---|---|
| 1. Intégration sans framework Web | ARC-001, INT-001, ACC-001 |
| 2. Plusieurs stratégies coexistent | FR-004, ACC-010 |
| 3. Ajout sans changer le core | FR-010, ARC-006, ACC-011 |
| 4. Humains et machines | FR-011, FR-051-052, ACC-017 |
| 5. Composition multi-facteurs | FR-032-033, ACC-019 |
| 6. Résultats normalisés | FR-001, FR-006, ACC-002, ACC-004, ACC-006 |
| 7. Stockage remplaçable | FR-017, ARC-008, ACC-012 |
| 8. Providers derrière adapters | FR-046, ARC-003, INT-008 |
| 9. Contrat IAM indépendant | ARC-018, INT-002, ACC-014 |
| 10. Sécurité explicite et testable | SEC-001 à SEC-024, ACC-003-009, ACC-018 |
| 11. Événements auditables | FR-061-064, SEC-020, ACC-013 |
| 12. Évolution passkeys/fédération/adaptatif | ARC-017, FR-035-036, FR-045-050, FR-057-060 |

**Note :** la présence d'une référence ne signifie pas que le critère est déjà satisfait par du code ; elle signifie que l'exigence et une voie de validation sont spécifiées.

---

## 18. Règles de gouvernance des exigences

### 18.1 Versionnement des exigences

- Un identifiant (`FR-024`, `SEC-007`, etc.) est stable une fois validé.
- Un changement sémantique majeur crée une révision tracée dans l'historique documentaire.
- Une suppression laisse une trace de dépréciation plutôt que de réutiliser l'identifiant.
- Chaque exigence possède au minimum une source, un niveau de priorité et un critère de validation.
- Un scénario n'est déclaré **implémenté** qu'avec un test et une preuve d'exécution ; être « documenté » ne suffit pas.

### 18.2 Définition de Ready (pour implémenter)

Une exigence est prête lorsque :

1. la responsabilité PyAuthKit/PyIAMKit est tranchée ;
2. les types d'entrée et de sortie sont connus ;
3. le comportement de succès et d'échec est sans ambiguïté ;
4. les propriétés de sécurité et de confiance sont précisées ;
5. les dépendances et le stockage sont identifiés ;
6. au moins un test positif et un test négatif sont possibles ;
7. les décisions bloquantes (`DEC-*`) sont résolues.

### 18.3 Définition de Done (pour une capacité)

Une capacité est terminée lorsque :

- le contrat public documenté est livré ;
- les tests unitaires, contractuels, de sécurité et d'intégration pertinents passent ;
- les erreurs et la redaction des secrets sont vérifiées ;
- les modes d'échec techniques sont traités ;
- les exemples d'utilisation fonctionnent ;
- le changelog reflète la capacité ajoutée ;
- la compatibilité annoncée est qualifiée ;
- les limitations connues figurent dans la documentation.

### 18.4 Conditions de décision GO / NO-GO du MVP

**GO proposé uniquement si** :

- le core fonctionne réellement en Python pur ;
- password, API key et JWT satisfont leurs scénarios critiques ;
- les tests négatifs de confiance, expiration et validation passent ;
- le plugin de référence fonctionne sans modification du core ;
- les logs et événements ne divulguent pas de secrets ;
- aucune décision IAM n'est effectuée implicitement ;
- les dépendances et limites de sécurité sont documentées ;
- les exigences P0 applicables sont vérifiées ou ont une dérogation explicite et justifiée.

**NO-GO** si un bypass connu permet une authentification non vérifiée, si un secret est divulgué dans les logs, ou si le JWT accepte une configuration de confiance non autorisée.

---

## 19. Organisation proposée de la conception documentaire

```text
PYAUTHKIT DOCUMENTATION
|
+-- A. Cadrage
|   +-- 00 Expression du besoin
|   +-- 01 Analyse des exigences (présent document)
|   +-- 02 Vision et principes architecturaux
|
+-- B. Architecture et domaine
|   +-- 03 Architecture système
|   +-- 04 Objets du domaine
|   +-- 05 Entities et Value Objects
|   +-- 06 Relations et ERD
|   +-- 07 Invariants et règles
|   +-- 08 Commands, Queries et Use Cases
|
+-- C. Sous-domaines d'authentification
|   +-- 09 Authentication Engine
|   +-- 10 Authenticators et Credentials
|   +-- 11 Flows et Challenges
|   +-- 12 MFA et Assurance
|   +-- 13 Sessions et Tokens
|   +-- 14 Federation, OIDC, OAuth, SAML
|   +-- 15 WebAuthn, Passkeys, Passwordless
|   +-- 16 Machine, Workload et Agent Authentication
|   +-- 17 Adaptive Auth et Risk
|
+-- D. Infrastructure et intégrations
|   +-- 18 Ports, Adapters et Plugins
|   +-- 19 Storage et Persistence
|   +-- 20 Security Threat Model
|   +-- 21 Audit, Events et Observability
|   +-- 22 Framework Integrations
|   +-- 23 PyIAMKit Integration Contract
|   +-- 24 Public API et SDK
|   +-- 25 Configuration Model
|
+-- E. Qualification et delivery
    +-- 26 Testing and Qualification Strategy
    +-- 27 Implementation Roadmap
    +-- 28 Implementation Bootstrap Plan
```

Le découpage est une **proposition de plan documentaire**, non une affirmation que ces documents existent déjà.

---

## 20. Synthèse décisionnelle

### 20.1 Ce qui est établi

- PyAuthKit résout **l'authentification**, pas l'IAM complet.
- Il peut fonctionner seul, sans PyIAMKit.
- Il doit servir les humains, services, applications, agents, workloads, devices et identités externes.
- Il est conçu pour accepter plusieurs méthodes et providers sans les encoder dans son modèle métier.
- Son cœur doit rester Python pur et indépendant des frameworks Web et des stores concrets.
- Son MVP est centré sur le kernel, les modèles, la registry et trois authenticators : **Password, API Key, JWT**.
- MFA, sessions, fédération, WebAuthn, machine advanced auth et adaptive authentication sont des objectifs de progression.
- La sécurité, l'audit, l'extensibilité et la testabilité sont transverses à toutes les phases.

### 20.2 Ce qui est proposé dans ce document

- Un registre d'exigences numérotées et traçables (`FR`, `NFR`, `SEC`, `ARC`, `INT`).
- Une priorisation par phases `P0` à `P3`.
- Des invariants de sécurité et des états normalisés candidats.
- Des contrats de ports et une taxonomie d'erreurs candidats.
- Trente scénarios d'acceptation, dont dix-huit orientés MVP.
- Des jalons MVP sans numérotation de release figée.
- Un registre de décisions et de risques à instruire.

### 20.3 Les prochaines décisions essentielles

1. **Définir le domaine** : `Principal`, `Identity`, `AuthenticatedPrincipal`, `Credential`, `Evidence`, `AuthenticationResult`.
2. **Choisir les contrats d'extension** : `Authenticator`, registry, resolvers, stores, event sinks.
3. **Figer les garanties du MVP** : password verification, API keys, JWT trust, fail-closed, audit.
4. **Sécuriser le périmètre** : pas d'IAM complet, pas de flow universel prématuré.
5. **Arbitrer la surface publique** : async, erreurs, types, compatibilité, extras.

---

## 21. Conclusion

PyAuthKit doit être conçu non comme une juxtaposition de bibliothèques de login, mais comme un **moteur d'authentification cohérent** disposant de contrats de domaine stables, de stratégies remplaçables, d'une surface d'intégration agnostique et de garanties de sécurité vérifiables.

La condition de réussite n'est **pas** d'implémenter immédiatement toutes les méthodes. Elle est de livrer un noyau restreint et sûr, suffisamment bien défini pour ajouter plus tard MFA, passkeys, OIDC, SAML, sessions, authentication machine et mécanismes adaptatifs sans casser les responsabilités du domaine.

> **Principe directeur :** *Authentication establishes a verified principal; identity management and authorization decide how that principal is represented and what it can do.*

**Document suivant recommandé :**

`02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md`

---

## Annexe A - Glossaire abrégé

| Terme | Sens |
|---|---|
| Authentication | Vérification d'une preuve liée à un principal |
| Authorization | Décision d'accès à une ressource ou action |
| IAM | Identity and Access Management |
| Principal | Sujet authentifiable / authentifié |
| Credential | Secret ou élément de preuve associé à l'authentification |
| Authenticator | Implémentation d'un mécanisme de vérification |
| Challenge | Étape supplémentaire de vérification |
| MFA | Multi-Factor Authentication |
| Step-up | Élévation ponctuelle du niveau d'authentification |
| OIDC | OpenID Connect |
| OAuth 2.0 | Framework d'autorisation déléguée, non synonyme d'authentification utilisateur |
| SAML | Security Assertion Markup Language |
| WebAuthn | API standard d'authentification cryptographique Web |
| Passkey | Credential passwordless fondé sur les technologies FIDO/WebAuthn |
| JWT | JSON Web Token, un format de token |
| JWK / JWKS | Représentation de clés / jeu de clés JSON |
| mTLS | Mutual Transport Layer Security |
| IdP | Identity Provider |
| Provider adapter | Connecteur d'un mécanisme ou fournisseur externe |
| Port | Contrat d'interaction avec une dépendance |
| Assurance | Niveau d'assurance résultant d'une cérémonie de preuve |
| Tenant | Contexte d'isolation logique d'une organisation ou d'un client |
| Fail-closed | Refuser l'authentification lorsque les conditions de confiance ne sont pas satisfaites |

## Annexe B - Historique documentaire

| Version | Date | Évolution |
|---|---|---|
| `0.1.0-draft` | 2026-10-27 | Première formalisation, à partir de `00`, du registre d'exigences, des scénarios d'acceptation, du MVP, des risques et des décisions ouvertes. |
