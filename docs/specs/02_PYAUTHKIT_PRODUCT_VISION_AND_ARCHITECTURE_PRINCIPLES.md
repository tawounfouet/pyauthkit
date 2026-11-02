# 02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES

# PyAuthKit - Vision produit et principes d'architecture

| Métadonnée | Valeur |
|---|---|
| Produit | **PyAuthKit** |
| Document | `02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md` |
| Type | Vision produit, doctrine d'architecture et principes de conception |
| Statut | **Proposition de conception - à valider** |
| Version documentaire | `0.1.0-draft` |
| Date | 27 octobre 2026 |
| Sources internes | `00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md` ; `01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md` |
| Prochain document | `03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md` |
| Langue | Français, noms des abstractions et patterns en anglais |

> **Product statement** - PyAuthKit is a framework-agnostic, provider-agnostic Python authentication engine for human, machine, workload, device and agent identities.

> **Mission architecturale** - Concevoir une primitive d'infrastructure Python capable de **vérifier des preuves d'authentification**, d'établir un **principal authentifié**, d'exposer des **résultats normalisés** et de rester indépendante de l'IAM, des transports et des implémentations d'infrastructure.

> **Portée de ce document** - Il formalise des orientations et des règles de conception. Il ne constitue ni une description d'un code existant, ni une certification de sécurité, ni une décision définitive pour toutes les options du projet. Les choix encore ouverts sont explicitement signalés.

---

## 1. Objet du document

### 1.1 Pourquoi un document de vision après l'analyse des exigences ?

Le document `00` répond à la question **pourquoi construire PyAuthKit et pour quels usages ?**

Le document `01` transforme cette ambition en **exigences traçables** : `FR-*`, `NFR-*`, `SEC-*`, `ARC-*`, `INT-*`, `ACC-*`, ainsi qu'en décisions `DEC-*` et risques `RSK-*`.

Le présent document `02` répond à une troisième question :

> **Selon quelles convictions produit, quelles frontières de responsabilité et quels principes d'ingénierie allons-nous concevoir PyAuthKit ?**

Son rôle est de stabiliser la pensée architecturale **avant** de fixer les composants détaillés, objets du domaine, signatures d'interfaces, schémas de persistance et versions de release.

### 1.2 Résultats attendus

Ce document doit permettre de :

1. décrire la proposition de valeur et l'identité du produit ;
2. établir ce que PyAuthKit **fait** et **ne fait pas** ;
3. distinguer les principes non négociables des options de mise en œuvre ;
4. guider la conception avec SOLID, DDD, Ports & Adapters et des patterns sélectionnés ;
5. organiser les contraintes de sécurité par frontières de confiance ;
6. définir les conditions d'évolutivité sans sur-ingénierie du MVP ;
7. orienter les documents `03` à `28` ;
8. proposer des tests de conformité architecturale et des arbitrages à traiter.

### 1.3 Convention de traçabilité

- `00 §n` : section de `00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md`.
- `01 §n` : section de `01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md`.
- `FR-001`, `SEC-018`, etc. : identifiants définis dans `01`, **non réinventés ici**.
- `PRN-xx` : principe architectural proposé dans ce document.
- `ADRC-xx` : *Architecture Decision Candidate* ; proposition en attente de validation, **pas** un ADR accepté.
- `P0`, `P1`, `P2`, `P3` : priorités proposées dans `01` ; une capacité future n'est pas considérée comme livrée.

### 1.4 Niveaux de certitude

| Marqueur | Sens | Exemple |
|---|---|---|
| **Établi** | Explicitement demandé dans `00` et conservé par `01` | Core indépendant de PyIAMKit |
| **Orientation retenue pour la conception** | Choix recommandé ici, vérifiable et révisable | Organiser les dépendances selon Hexagonal Architecture |
| **Candidat** | Variante proposée à trancher en conception détaillée | `Protocol` Python pour un port |
| **Différé** | Capacité souhaitée mais non incluse dans le MVP | OIDC, SAML, passkeys, MFA runtime |
| **Interdit par principe** | Anti-pattern incompatible avec les exigences | Fallback automatique vers un authenticator plus faible |

---

## 2. Vision produit

### 2.1 Vision longue

**PyAuthKit doit devenir le moteur d'authentification réutilisable de l'écosystème `Py**Kit` et, au-delà, un composant Python intégrable dans des applications Web, APIs, CLIs, services, agents et workloads.**

Sa valeur ne provient pas du nombre de logos d'Identity Providers supportés. Elle provient de la **cohérence de ses contrats de confiance** et de sa capacité à intégrer progressivement de nouveaux mécanismes sans dissoudre ses frontières de responsabilité.

### 2.2 Mission et questions auxquelles le produit répond

| Question | Responsable | Résultat attendu |
|---|---|---|
| Une preuve est-elle recevable et authentique ? | **PyAuthKit** | Preuve vérifiée ou refusée |
| Quel sujet cette preuve établit-elle ? | **PyAuthKit**, selon un contrat de confiance | Subject / `AuthenticatedPrincipal` vérifié |
| Quel utilisateur, compte ou objet IAM correspond à ce sujet ? | **PyIAMKit** ou application intégratrice | Résolution d'identité organisationnelle |
| À quels groupes, rôles et organisations est-il rattaché ? | **PyIAMKit** | Représentation et relations IAM |
| Peut-il exécuter cette action sur cette ressource ? | **Moteur d'autorisation / application** | Décision d'accès |
| Comment présente-t-on le login, le consentement ou le challenge ? | **Framework/UI/adapters** | Interaction utilisateur ou service |

**Règle fondamentale : une authentification réussie n'est jamais, à elle seule, une autorisation d'accès.**

### 2.3 Promesses produit

1. **Unification** : une entrée et une sortie conceptuelles communes pour les méthodes supportées.
2. **Autonomie** : utilisable en Python pur, sans framework Web ni serveur IAM obligatoire.
3. **Agnosticisme** : protocoles, providers, storages et transports ne dictent pas le domaine.
4. **Composition** : mécanismes interchangeables, flows évolutifs, résultats homogènes.
5. **Extensibilité** : nouveaux authenticators et adapters sans modifier le noyau.
6. **Sécurité explicite** : configurations de confiance déclarées, refus sûrs, audit sans secrets.
7. **Multi-principal** : mêmes concepts fondamentaux pour humains et identités non humaines.
8. **Intégrabilité** : relation claire avec PyIAMKit et l'écosystème applicatif.
9. **Lisibilité** : concepts, décisions, erreurs et limites documentés et testables.

### 2.4 Ce que PyAuthKit n'est pas

PyAuthKit n'a pas vocation à être :

- une application de login avec interface graphique obligatoire ;
- une base globale d'utilisateurs et d'organisations ;
- un serveur IAM complet comparable en périmètre à Keycloak ;
- un moteur général d'autorisation RBAC, ABAC ou ReBAC ;
- un gestionnaire universel des permissions d'agents ;
- une PKI, un coffre-fort de secrets ou un password manager complet ;
- un SIEM, une plateforme de fraude ou une console de gouvernance des identités ;
- un framework Web, un ORM, un workflow engine universel ou un agent runtime ;
- une implémentation maison de primitives cryptographiques lorsque des composants spécialisés et éprouvés existent.

### 2.5 Différenciation recherchée

La différenciation visée n'est **pas démontrée commercialement à ce stade**. Elle constitue une hypothèse de positionnement :

| Dimension | Hypothèse de différenciation |
|---|---|
| Python pur | Fonctionnement hors contexte HTTP et serveur |
| Domaine cohérent | Même langage pour password, API key, JWT et extensions futures |
| Agents & workloads | Principals non humains pris en compte dès le modèle, sans marketing de sécurité implicite |
| IAM optionnel | PyIAMKit intégrable sans dépendance réciproque imposée |
| Extensibilité disciplinée | Plugins sous contrats vérifiables et politique de confiance |
| Éducation architecturale | Concepts et patterns documentés, tests associés, décisions explicites |

### 2.6 Test de la vision

Une équipe doit pouvoir répondre **oui** aux questions suivantes :

- Puis-je authentifier un service sans instancier de `Request` HTTP ?
- Puis-je remplacer la vérification d'une API key par un adapter compatible ?
- Puis-je installer uniquement le noyau et ses dépendances nécessaires ?
- Puis-je refuser une preuve invalide sans produire de principal authentifié ?
- Puis-je ajouter un authenticator tiers sans modifier un `if provider == ...` central ?
- Puis-je consommer le résultat depuis PyIAMKit sans donner à PyAuthKit la responsabilité des rôles ?
- Puis-je identifier les hypothèses de confiance et les limites de chaque mécanisme ?

Si une réponse est négative, le design doit être réexaminé avant d'étendre le catalogue fonctionnel.

---

## 3. Acteurs, expériences et scénarios structurants

### 3.1 Les utilisateurs de la bibliothèque

| Persona | Priorité | Attente produit |
|---|---|---|
| Développeur d'API Python | MVP | Valider password, API key ou JWT via un contrat simple |
| Mainteneur d'une bibliothèque | MVP | Ajouter un authenticator et le tester indépendamment |
| Développeur d'intégration FastAPI/Django | Après noyau | Convertir les entrées/sorties Web sans dupliquer les règles |
| Équipe sécurité | Transverse | Vérifier les conditions de confiance et les échecs sûrs |
| Exploitant plateforme | Transverse | Configurer, corréler et auditer sans fuite de secrets |
| Développeur IAM | Après noyau | Consommer un principal prouvé sans dépendre des providers |
| Développeur d'agents | Progressif | Représenter un agent ou workload et son mode de preuve |
| Intégrateur entreprise | Progressif | Ajouter federation, MFA, passkeys, mTLS et politiques |

### 3.2 Scénarios de référence

**S1 - Web backend :** l'application extrait un credential dans l'adapter HTTP ; le moteur le vérifie ; l'application décide ensuite de la représentation utilisateur et de l'accès.

**S2 - Microservice :** un client présente une API key ; le moteur vérifie la preuve ; le résultat contient un principal de type `SERVICE` ou `APPLICATION`.

**S3 - Validation de jeton :** un service reçoit un JWT prévu pour le contexte d'authentification configuré ; un authenticator valide sa signature, sa provenance, son audience, sa temporalité et son usage autorisé.

**S4 - CLI / worker :** une tâche non Web fournit une demande normalisée et reçoit un résultat sans session HTTP.

**S5 - Authentification renforcée future :** un mécanisme primaire est vérifié, mais le flow ne se termine pas avant la satisfaction des facteurs demandés.

**S6 - Fédération future :** un adapter valide une assertion issue d'un IdP approuvé ; la provenance est conservée ; le compte IAM n'est pas automatiquement créé.

**S7 - Agent futur :** un workload ou agent apporte une preuve technique ou déléguée ; PyAuthKit vérifie cette preuve ; l'autorisation de l'action reste externe.

### 3.3 Expérience développeur cible

L'API doit être intelligible sans exposer les détails de transports ou de persistance.

```python
# API illustrative seulement : signatures et classes non figées.
request = AuthenticationRequest(
    method="api_key",
    evidence=ApiKeyEvidence(value=presented_key),
    context=AuthenticationContext(application_id="billing-worker"),
)

result = await engine.authenticate(request)

if result.status is AuthenticationStatus.AUTHENTICATED:
    principal = result.principal
    # Les autorisations sont ensuite évaluées par l'application / IAM.
```

**Attention :** cette forme représente une **aspiration d'API**. Le document `24` tranchera les noms, états et signatures.

### 3.4 Critère de simplicité

La simplicité vise **l'intégrateur**, sans masquer la complexité intrinsèque de la sécurité. Une API courte ne doit pas empêcher l'expression d'un `issuer`, d'une `audience`, d'un `tenant` vérifié ou d'une politique explicite quand le mécanisme les exige.

---

## 4. Frontières fonctionnelles et responsabilités

### 4.1 Vue d'ensemble

```text
  Entrées / preuves
  Humans | Services | Applications | Agents | Devices | Workloads
                              |
                              v
  +-------------------------------------------------------------+
  | PyAuthKit                                                    |
  |                                                             |
  | Request -> Authenticator -> Validation -> AuthenticationResult|
  |                 |                      |                    |
  |           Trust configuration         Audit                  |
  |                                                             |
  | [Future] Challenges | MFA | Sessions | Federation | Step-up  |
  +-------------------------------+-----------------------------+
                                  |
                         AuthenticatedPrincipal
                                  |
                                  v
  +-------------------------------------------------------------+
  | Optional identity / access integration                       |
  | PyIAMKit -> identity resolution, accounts, roles, permissions|
  | Application -> resource-specific authorization decisions     |
  +-------------------------------------------------------------+
```

Cette figure représente des responsabilités logiques, **pas** la topologie définitive des modules ou services.

### 4.2 Responsibility Matrix

| Capacité | PyAuthKit | PyIAMKit / intégrateur | Remarque |
|---|---|---|---|
| Extraction HTTP d'un header / cookie | Adapter d'intégration | Application peut adapter | Pas dans le domaine pur |
| Vérification password | Oui | Fournit éventuellement compte / référence | Hash backend interchangeable |
| Validation API key / JWT | Oui | Fournit trust configuration ou store adapté | Une preuve vérifiée n'accorde pas d'accès |
| MFA / WebAuthn / OIDC / SAML | Oui, à terme | Intégration adaptée | Hors MVP initial |
| Authentification d'agent ou workload | Oui, par preuves adaptées | Autorisations et identité métier | Le type `AGENT` ne prouve rien à lui seul |
| Résolution organisation / groupe / rôle | Non | Oui | IAM |
| Décision d'accès ressource | Non | Oui, selon application | Authorization |
| Gestion de session d'authentification | Oui, à terme | Application gère les besoins Web | Séparer session et compte IAM |
| Création / provisioning de compte IAM | Non | Oui | Hors périmètre |
| Publication d'événement d'authentification | Oui | Consommateurs externes | Pas de secret en événement |
| Sélection de politique de confiance | Oui, selon contrat | Configuration fiable fournie par hôte | Ne pas faire confiance au client seul |

### 4.3 Frontière authentication / identity / authorization

```text
  DECLARED SUBJECT        VERIFIED EVIDENCE          AUTHENTICATED PRINCIPAL
       "alice"      +      password valid       ->       subject="alice"

  AUTHENTICATED PRINCIPAL + IAM IDENTITY MAPPING   ->       Account / Tenant / Roles

  ACCOUNT / ROLES / CONTEXT + RESOURCE POLICY      ->       Access Decision
```

- L'identifiant déclaré **n'est pas** une preuve.
- La preuve validée établit un **sujet selon une relation de confiance configurée**.
- L'établissement du sujet ne transforme pas une chaîne arbitraire en compte IAM actif.
- La décision d'accès dépend d'une **autorisation distincte**.

### 4.4 La notion de principal

L'expression initiale envisage notamment `HUMAN`, `SERVICE`, `APPLICATION`, `AGENT`, `DEVICE`, `WORKLOAD` et `EXTERNAL`.

Il faut séparer deux axes :

1. **Nature du principal** : humain, agent, service, etc.
2. **Origine de l'identité** : locale, fédérée, déléguée ou externe.

Un humain fédéré reste un **humain** ; un agent portant un jeton externe reste un **agent**. Modéliser `EXTERNAL` comme origine plutôt que comme nature du principal est une **hypothèse de conception**, à arbitrer dans `04-06` (`DEC-05`).

### 4.5 Provider et mécanisme ne sont pas synonymes

- `Password` est un mécanisme de preuve.
- `TOTP` est un mécanisme de facteur additionnel.
- `JWT` est un format de jeton signé ou non selon son profil ; sa validité dépend de la politique de confiance et de son usage.
- `OIDC` est un protocole de fédération d'identité.
- `OAuth 2.0` est d'abord un cadre d'autorisation déléguée ; **un access token OAuth seul n'est pas une authentification utilisateur universelle**.
- `SAML` est une famille de protocoles d'assertions/fédération d'identité.
- `Google`, `Microsoft`, `GitHub` et autres sont des fournisseurs potentiels, avec des capacités et protocoles qui peuvent différer.
- `mTLS` relève d'une preuve liée à la couche de transport et à une chaîne de confiance de certificats.

Cette taxonomie doit empêcher la conception d'une liste plate d'« authentifications » dont les garanties seraient supposées interchangeables.

---

## 5. Doctrine architecturale : principes directeurs

Les principes suivants sont des **règles candidates normatives pour la conception**. Leur validation formelle appartient à une revue d'architecture ; ils ne signifient pas que les composants existent déjà.

### PRN-01 - Authentication is a bounded responsibility

**Énoncé :** PyAuthKit ne gère que l'établissement, la continuation ou le refus de l'authentification et les artefacts nécessaires à celle-ci.

**Justification :** protéger la frontière avec IAM et authorization.

**Conséquence :** le domaine ne contient pas de moteur d'attribution de rôles ni de policies d'accès métier.

**Anti-pattern :** `authenticate()` charge les permissions et décide si l'utilisateur peut modifier une facture.

**Traçabilité :** `ARC-012`, `ARC-013`, `ARC-018`, `INT-001`, `INT-002`.

### PRN-02 - Domain first, technology second

**Énoncé :** objets, vocabulaires, règles et invariants sont définis avant le choix d'un ORM, SDK, provider ou framework.

**Conséquence :** aucune entité de domaine ne dérive d'un modèle Django ni ne contient de dépendance à `Request`, Redis ou à un client OAuth.

**Anti-pattern :** prendre un modèle ORM de compte comme classe mère de `Principal`.

**Traçabilité :** `ARC-001`, `ARC-003`, `ARC-005`.

### PRN-03 - Depend on abstractions, not providers

**Énoncé :** le noyau décrit ses besoins à travers des ports et contrats ; l'infrastructure en fournit les implémentations.

**Conséquence :** hashers, stores, key resolvers, authenticators externes et event sinks sont substituables sous contrat.

**Anti-pattern :** importer un SDK de fournisseur directement dans `domain/`.

**Traçabilité :** `ARC-003`, `ARC-008`, `NFR-003`, `NFR-004`.

### PRN-04 - Explicit trust, never implicit trust

**Énoncé :** aucune preuve, clé, issuer, audience, méthode, origine réseau ou valeur de tenant ne devient fiable par simple présence.

**Conséquence :** la validation utilise un contexte de confiance configuré et une stratégie de résolution autorisée.

**Anti-pattern :** accepter `alg`, `iss` ou `tenant_id` transmis par le demandeur comme décision de confiance.

**Traçabilité :** `SEC-006` à `SEC-008`, `SEC-019`, `SEC-022`.

### PRN-05 - Fail closed with typed outcomes

**Énoncé :** une erreur inattendue, une preuve indéchiffrable, une méthode inconnue ou un provider indisponible ne créent jamais un principal authentifié.

**Conséquence :** résultat de refus / erreur opérationnelle explicite selon une taxonomie publique à définir.

**Anti-pattern :** `except Exception: return success` ; fallback automatique vers password.

**Traçabilité :** `FR-005`, `FR-006`, `FR-009`, `SEC-018`.

### PRN-06 - Every success has verified evidence

**Énoncé :** une réussite implique un chemin vérifiable allant d'une preuve recevable jusqu'à un subject établi, sous politique appropriée.

**Conséquence :** le `AuthenticatedPrincipal` n'est créé en tant que sortie fiable qu'au terme des vérifications attendues.

**Anti-pattern :** traiter un header `X-User` ou un `user_id` de requête comme preuve d'identité.

**Traçabilité :** `SEC-019`, `FR-008`, `ACC-002`.

### PRN-07 - One core, many authenticators

**Énoncé :** chaque mécanisme est encapsulé sous un contrat commun ; le moteur coordonne, il n'implémente pas les spécificités de tous les protocoles.

**Conséquence :** enregistrement explicite des stratégies et résolution contrôlée.

**Anti-pattern :** immense fonction `authenticate` où chaque provider est traité par `if/elif`.

**Traçabilité :** `FR-003`, `FR-004`, `FR-010`, `ARC-002`, `ARC-006`.

### PRN-08 - Normalize contracts, preserve proof semantics

**Énoncé :** uniformiser les résultats sans prétendre que toutes les méthodes de preuve ont les mêmes garanties.

**Conséquence :** méthode, provenance, contexte fiable, éventuels facteurs et niveau d'assurance restent représentables et distincts.

**Anti-pattern :** une API `bool is_authenticated` qui gomme un challenge, la provenance et les restrictions.

**Traçabilité :** `FR-006`, `FR-015`, `FR-050`.

### PRN-09 - Mechanisms are replaceable, policies are independent

**Énoncé :** l'authenticator vérifie une preuve ; la policy d'authentification formule les exigences de la cérémonie et du contexte.

**Conséquence :** politique et implémentation cryptographique n'évoluent pas dans une unique classe monolithique.

**Anti-pattern :** condition métier de transfert bancaire codée dans `PasswordAuthenticator`.

**Traçabilité :** `ARC-009`, `ARC-013`, `FR-057`.

### PRN-10 - Composable flows, incremental implementation

**Énoncé :** le modèle prévoit challenges, continuations et multi-facteurs sans construire d'emblée un workflow engine généraliste.

**Conséquence :** contrat de résultat extensible ; implémentation initiale limitée à l'authentification simple.

**Anti-pattern :** dépendance obligatoire à un moteur de workflow distribué pour valider une API key.

**Traçabilité :** `ARC-017`, `FR-032`, `FR-033`.

### PRN-11 - Storage is a port, not a product decision

**Énoncé :** les stores sont interchangeables par capacités contractuelles, pas seulement par interfaces identiques.

**Conséquence :** prévoir ce qui exige atomicité, expiration, révocation, comparaison et cohérence, selon le store.

**Anti-pattern :** supposer que `dict` mémoire et Redis offrent les mêmes garanties de multi-processus.

**Traçabilité :** `ARC-008`, `NFR-004`, `FR-038`.

### PRN-12 - Async-capable, concurrency-safe

**Énoncé :** le chemin public d'authentification sait être asynchrone et ne partage pas d'état mutable entre tentatives.

**Conséquence :** contexte par requête, timeouts bornés pour I/O et ports async là où nécessaires ; façade sync éventuelle différée.

**Anti-pattern :** `engine.current_user` ou `engine.current_tenant` comme état global de l'instance.

**Traçabilité :** `FR-002`, `ARC-011`, `NFR-011`, `DEC-15`.

### PRN-13 - Observability without disclosure

**Énoncé :** les tentatives sont corrélables, mais aucun secret ou jeton brut n'est présent dans les événements.

**Conséquence :** schémas d'événements whitelistés, redaction, identifiants de tentative, gestion explicite de l'impact des erreurs d'audit.

**Anti-pattern :** logger l'objet `AuthenticationRequest` entier.

**Traçabilité :** `SEC-001`, `FR-061`, `FR-064`, `NFR-013`.

### PRN-14 - Safe extension is part of the security model

**Énoncé :** un plugin n'est pas automatiquement fiable parce qu'il implémente un `Protocol`.

**Conséquence :** intégration avec confiance explicite, contrôle des capacités, revue des dépendances, tests contractuels et politique de chargement.

**Anti-pattern :** découvrir et exécuter silencieusement tout plugin installé dans l'environnement.

**Traçabilité :** `FR-010`, `ARC-006`, `SEC-005`, `RSK-014`.

### PRN-15 - Multi-tenancy is a trust boundary

**Énoncé :** un tenant déclaré et un tenant authentifié/configuré ne sont pas équivalents.

**Conséquence :** résolution des clés, stores, mécanismes et émetteurs de jetons dans la partition de confiance attendue.

**Anti-pattern :** lookup global d'une API key à partir du tenant fourni sans validation préalable.

**Traçabilité :** `SEC-022`, `FR-016`, `DEC-14`.

### PRN-16 - No security by marketing label

**Énoncé :** les qualificatifs « MFA », « passwordless », « AAL2 », « compliant » ou « enterprise-ready » ne se déduisent pas de la présence d'une fonctionnalité.

**Conséquence :** différencier capacités, exigences de cérémonie, évaluations, conformité démontrée et certifications externes.

**Anti-pattern :** supposer que tout TOTP ou toute passkey confère automatiquement un même niveau d'assurance.

**Traçabilité :** `FR-015`, `FR-032`, `DEC-18`, `SEC-019`.

### PRN-17 - Secure defaults with explicit dangerous choices

**Énoncé :** absence de configuration de confiance ne doit pas activer une vérification permissive.

**Conséquence :** confiance explicitement définie, aucune validation JWT sans algorithmes/clefs/issuer/audience adéquats au profil choisi, refus des options risquées par défaut.

**Anti-pattern :** `verify_signature=False` disponible comme chemin normal en production.

**Traçabilité :** `SEC-006` à `SEC-008`, `NFR-018`.

### PRN-18 - Documentation and tests are part of the interface

**Énoncé :** un contrat public ne se limite pas à une signature ; il inclut sémantique, hypothèses, erreurs et tests de conformité.

**Conséquence :** chaque nouveau port et authenticator dispose de fixtures, exemples, tests négatifs et notes de sécurité.

**Anti-pattern :** ajouter un plugin sans expliquer dans quel contexte sa preuve est suffisante.

**Traçabilité :** `NFR-007`, `NFR-008`, `NFR-015`, `ACC-011`.

### 5.1 Matrice de priorité des principes

| Principes | Applicabilité MVP | Applicabilité extensions |
|---|---|---|
| PRN-01 à 08 | **Obligatoire en conception P0** | Maintien |
| PRN-09 et 10 | Frontières P0, capacités avancées P1/P2 | Composition détaillée |
| PRN-11 à 15 | Contrats / protections P0 appropriées | Garanties de stockage, tenancy et flux supplémentaires |
| PRN-16 à 18 | **Obligatoire dès la documentation et le noyau** | Maintien |

Cette matrice qualifie des **objectifs de conception**, pas un état d'avancement du dépôt.

---

## 6. Principes de qualité du code : SOLID, DRY, KISS, YAGNI et SoC

L'objectif n'est pas de « cocher » des acronymes. Chaque principe doit expliquer une décision observable de conception.

### 6.1 SRP - Single Responsibility Principle

Une unité doit posséder une raison cohérente de changer.

| Composant | Raison légitime de changer | Ce qu'il ne doit pas absorber |
|---|---|---|
| `AuthenticationEngine` | Coordination du traitement | Détails de hashage password |
| `AuthenticatorRegistry` | Enregistrement/résolution | Gestion de session |
| `PasswordAuthenticator` | Contrat de vérification password | HTTP, RBAC, IAM |
| `JWTAuthenticator` | Validation de jeton selon profil de confiance | Émission de tous les tokens |
| `CredentialStore` | Recherche / persistance selon contrat | Politique d'autorisation |
| `AuditEventSink` | Livraison d'événements | Sérialisation de credentials bruts |

**Symptôme d'échec :** chaque ajout d'une méthode oblige à modifier simultanément `engine.py`, la session Web et les modèles ORM.

### 6.2 OCP - Open/Closed Principle

Le noyau doit être **ouvert à l'extension et fermé à la modification spécifique aux providers**.

```text
AuthenticationEngine
       |
       v
AuthenticatorRegistry
       |
       +-- PasswordAuthenticator
       +-- ApiKeyAuthenticator
       +-- JwtAuthenticator
       +-- CustomAuthenticator
```

Une extension peut être enregistrée en composition root ou installée par une procédure contrôlée. **OCP n'exige pas** de discovery automatique de plugins.

### 6.3 LSP - Liskov Substitution Principle

Un authenticator substituable respecte les mêmes promesses contractuelles :

- il retourne un résultat conforme au type déclaré ;
- il ne produit pas de succès sans preuve vérifiée ;
- il documente les formes d'evidence qu'il accepte ;
- il ne change pas secrètement de contexte de confiance ;
- il distingue conditions non supportées et preuves refusées ;
- il ne divulgue pas de secrets dans ses erreurs ou événements.

LSP est ici une **discipline comportementale**, démontrée par des **contract tests**.

### 6.4 ISP - Interface Segregation Principle

Éviter une interface universelle comme :

```python
# Anti-pattern conceptuel
class EverythingStore:
    async def verify_password(self, ...): ...
    async def save_session(self, ...): ...
    async def revoke_token(self, ...): ...
    async def send_email(self, ...): ...
    async def get_jwks(self, ...): ...
```

Préférer des capacités limitées et explicitement composables, par exemple `CredentialReader`, `PasswordVerifier`, `VerificationKeyResolver`, `EventSink` et, ultérieurement, `SessionStore` ou `ChallengeStore`.

### 6.5 DIP - Dependency Inversion Principle

```text
  Application layer                     Infrastructure
  -----------------                     --------------
  AuthenticationEngine ---> CredentialReader <--- SqlCredentialAdapter
  PasswordAuthenticator -> PasswordVerifier <--- SecurePasswordAdapter
  JWTAuthenticator -----> VerificationKeyResolver <- JWKSAdapter
  Engine / services ----> AuthenticationEventSink <- LogAdapter
```

La flèche de dépendance **du code** vise les abstractions du noyau, et non les SDK concrets.

### 6.6 DRY - Don't Repeat Yourself

Mutualiser :

- les concepts de résultat et d'erreur ;
- la propagation d'identifiants de tentative ;
- la politique de redaction ;
- les contrats de trust configuration ;
- les tests communs de conformité.

Ne **pas** chercher à unifier artificiellement toutes les étapes cryptographiques de mécanismes différents. Deux méthodes semblables peuvent exiger des garanties distinctes.

### 6.7 KISS - Keep It Simple

Le MVP doit pouvoir traiter une authentification simple sans :

- base de données obligatoire ;
- conteneur d'injection de dépendances obligatoire ;
- serveur distant obligatoire ;
- FSM distribuée ou orchestrateur de workflows généraliste ;
- système global de plugins activé par défaut.

Une `AuthenticationRequest` typée et un `AuthenticatorRegistry` contrôlé sont une cible plus adéquate qu'un runtime pluggable universel prématuré.

### 6.8 YAGNI - You Aren't Gonna Need It

Ne pas implémenter la totalité des cas futurs sous prétexte d'extensibilité.

| À concevoir tôt | À construire lorsque justifié |
|---|---|
| Résultat pouvant distinguer continuation et succès | Challenge runtime complet |
| Modèle de principal non limité à `User` | IdP federation catalogue |
| Contrat JWT indépendant d'un issuer codé en dur | Provider-specific discovery et caching avancé |
| Port pour une dépendance concrète du MVP | Multiples stores SQL / Redis |
| Séparation token / authentification | OAuth authorization server |

### 6.9 Separation of Concerns et Information Hiding

- **SoC** : le protocole de transport, la sélection d'une stratégie, la vérification d'une preuve et l'autorisation sont des préoccupations distinctes.
- **Information Hiding** : un adapter cache les détails spécifiques au provider et n'expose au noyau que le comportement contractuel nécessaire.
- **Encapsulation** : les valeurs sensibles ne deviennent ni publiques ni sérialisables par accident.

### 6.10 Pythonic design

Les outils Python envisagés incluent `typing.Protocol`, `dataclasses`, `Enum`, modules légers, exceptions de domaine, `async` / `await` et injection explicite.

Il ne s'agit **pas d'une décision finale** pour chaque type (`DEC-03`, `DEC-04`). Une `ABC`, un objet callable ou une classe simple peuvent être préférables lorsque leurs garanties sont plus lisibles.

---

## 7. DDD - Domain-Driven Design

### 7.1 Pourquoi DDD ?

Le principal risque sémantique de PyAuthKit est la confusion entre **identité**, **compte**, **principal**, **credential**, **preuve**, **facteur**, **session**, **token** et **autorisation**.

DDD fournit ici une discipline de modélisation, **pas** une obligation d'utiliser un aggregate ou un repository pour chaque nom métier.

### 7.2 Bounded Context : Authentication

Le bounded context principal est **Authentication**.

```text
                        Authentication Context
  +-------------------------------------------------------+
  | Authentication                                       |
  |                                                       |
  | Request, Evidence, Authenticator, Attempt, Principal |
  | Result, Trust Configuration, Authentication Policy    |
  |                                                       |
  | [Future] Flow, Challenge, Factor, Session, Token       |
  +--------------------------+----------------------------+
                             |
                     Explicit integration contract
                             |
                +------------v--------------+
                | Identity & Access         |
                | PyIAMKit / host system    |
                | Accounts, Groups, Roles,  |
                | Permissions, Governance   |
                +---------------------------+
```

### 7.3 Sous-domaines candidats

| Sous-domaine | Responsabilité | Phase de conception |
|---|---|---|
| Authentication Kernel | Demandes, orchestration, résultats | MVP |
| Credential Verification | Preuves, hash, clés, validations | MVP |
| Principal Establishment | Sujet et provenance vérifiés | MVP |
| Trust Configuration | Définition des autorités et usages admissibles | MVP |
| Authentication Events | Audit et corrélation sans secrets | MVP |
| Challenges & Flows | Continuation multi-étapes | Après MVP |
| Factors & Assurance | MFA, exigences de preuve et niveau | Après MVP |
| Sessions & Tokens | Cycle de vie d'artefacts | Après MVP |
| Federation | OIDC, SAML, social login | Après MVP |
| Risk & Adaptive Auth | Context/risk, step-up | Après MVP |
| Machine / Workload Profiles | Certificats, assertions et délégation | Après MVP |

Ces sous-domaines ne préjugent pas du découpage en packages Python ou en bounded contexts déployables.

### 7.4 Ubiquitous Language - glossaire de travail

| Terme | Sens dans PyAuthKit | Non-sens à éviter |
|---|---|---|
| `Subject` | Identifiant du sujet établi dans un contexte de confiance | Alias universel d'email |
| `Principal` | Acteur humain ou non humain concerné | Compte ORM obligatoire |
| `AuthenticatedPrincipal` | Représentation fiable établie après preuve | Rôle ou permission accordée |
| `Identity` | Représentation d'identité déclarée, fédérée ou résolue | Modèle IAM imposé |
| `Credential` | Donnée ou secret utilisé pour authentifier | Toute preuve forcément persistée |
| `Evidence` | Élément présenté et soumis à vérification | Preuve fiable dès l'entrée |
| `Authenticator` | Vérificateur d'une famille de preuves | Flow complet dans tous les cas |
| `Attempt` | Tentative traçable | Session persistante |
| `Context` | Données de la tentative avec niveaux de fiabilité | Provenance systématiquement vérifiée |
| `AuthenticationPolicy` | Conditions de la preuve et de l'assurance | Décision RBAC |
| `Challenge` | Obligation de poursuivre une cérémonie | Authentification déjà achevée |
| `AuthenticationResult` | Issue normalisée | Simple booléen pour tous les usages |
| `Session` | État lié au parcours ou au maintien d'authentification | JWT nécessaire |
| `Token` | Artefact représentant une preuve, une session ou une autorisation selon usage | Format nécessairement JWT |
| `Assurance` | Garantie attribuée selon propriétés du parcours | Constante automatiquement déduite de `MFA=True` |
| `Tenant` | Frontière logique et potentiellement frontière de confiance | Paramètre non fiable utilisable tel quel |

### 7.5 Entity, Value Object, Service et Aggregate

**Hypothèse**, à préciser dans `04`, `05` et `06` :

| Catégorie DDD | Candidats | Justification / réserve |
|---|---|---|
| Entity | `AuthenticationAttempt` | Identité de tentative et cycle de vie traçable |
| Entity future | `AuthenticationSession`, `AuthenticationChallenge` | Cycle de vie, version, expiration et consommation |
| Value Object | `PrincipalReference`, `EvidenceDescriptor`, `AuthenticationContext` | Représentations définies par leurs valeurs, idéalement immuables |
| Value Object | `AuthenticationResult` | Résultat produit sans cycle de vie propre, sous réserve de son contenu |
| Domain Service | `AuthenticationPolicyEvaluator` | Règle métier de vérification transversale |
| Application Service | `AuthenticationEngine` | Orchestration et appel des dépendances |
| Aggregate Root | À déterminer selon besoin de cohérence | Ne pas inventer un aggregate pour une validation JWT stateless |

**Important :** la classification n'est pas figée. `AuthenticatedPrincipal` peut être un value object plutôt qu'une entité ; l'existence d'un `subject` ne commande pas un `UserRepository` local.

### 7.6 Identité déclarée et identité établie

Le modèle devra distinguer les valeurs :

```text
ClaimedSubject
     |
     |  + PresentedEvidence
     v
Authenticator + TrustPolicy
     |
     v
VerifiedSubjectReference (issuer / subject / tenant as applicable)
     |
     v
AuthenticatedPrincipal
```

Pour des identités fédérées, une paire comme `(trusted issuer, subject)` est généralement plus significative qu'un `sub` isolé. Il ne faut pas fusionner des sujets de fournisseurs distincts uniquement parce que leurs emails se ressemblent.

### 7.7 Context Map avec PyIAMKit

Relation visée : **Published Language / contrat public minimal** et **adapter d'intégration explicite**.

PyAuthKit publie le fait authentifié (sujet, nature, provenance, garanties, restrictions éventuelles). PyIAMKit résout les concepts IAM à partir de ce contrat.

Aucune classe interne d'un package ne doit être importée de manière réciproque pour établir le lien.

### 7.8 Événements de domaine et intégration

Un événement tel que `AuthenticationSucceeded` est une **notification d'un fait**. Il ne doit pas contenir le credential et ne constitue pas une délégation implicite de droits.

Le format interne d'événement, son schéma d'intégration et sa livraison peuvent relever de contrats différents.

---

## 8. Architecture Hexagonale / Ports & Adapters

### 8.1 Intention

Isoler le noyau de PyAuthKit des frameworks, fournisseurs et infrastructures remplaçables.

```text
                       PRIMARY / DRIVING ADAPTERS
           +---------------+---------------+---------------+
           | Python SDK    | CLI adapter   | Web adapters  |
           |               |               | FastAPI/Django|
           +---------------+---------------+---------------+
                                   |
                            Authentication API
                                   |
         +-------------------------v---------------------------+
         |                    PYAUTHKIT CORE                    |
         |                                                     |
         |    Application                                      |
         |    AuthenticationEngine / Registry / Use Cases      |
         |                   |                                 |
         |    Domain         v                                 |
         |    Requests / Principal / Evidence / Result         |
         |    Policies / Trust Rules / Invariants              |
         |                   |                                 |
         |            OUTBOUND PORTS                           |
         |    CredentialReader, PasswordVerifier, KeyResolver  |
         |    EventSink, Clock, [Future] Stores                |
         +-------------------------+---------------------------+
                                   |
                      SECONDARY / DRIVEN ADAPTERS
           +---------------+---------------+---------------+
           | Memory / SQL  | Crypto / JWKS | Logs / SIEM   |
           | Redis later   | providers     | monitoring    |
           +---------------+---------------+---------------+
```

### 8.2 Ce qu'est un port

Un port exprime une **capacité attendue par le core**, avec :

- des paramètres et résultats typés ;
- des préconditions et postconditions ;
- des erreurs définies ;
- des garanties de confidentialité ;
- des conditions de concurrence, d'atomicité et de timeout si applicables ;
- des contract tests.

**Un port n'est pas nécessairement une classe abstraite**, et chaque dépendance ne justifie pas son propre port public.

### 8.3 Exemples de ports candidats

| Port conceptuel | Responsabilité | Phase |
|---|---|---|
| `Authenticator` | Vérifier une famille de preuves | MVP |
| `CredentialReader` | Lire la référence de vérification requise | MVP, si nécessaire |
| `PasswordVerifier` | Appliquer la vérification sécurisée des mots de passe | MVP |
| `VerificationKeyResolver` | Fournir une clé autorisée par le profil de confiance | MVP |
| `AuthenticationEventSink` | Exposer les faits d'authentification sans secrets | MVP |
| `Clock` | Fournir le temps à une vérification testable | Candidat MVP |
| `EntropySource` | Générer de l'aléa cryptographiquement approprié | Si émission de secrets |
| `SessionStore` | Sessions, expiration et révocation | Future |
| `ChallengeStore` | Challenges, usage unique et transitions | Future |
| `RiskSignalProvider` | Évaluer le risque hors domaine | Future |
| `FederationProviderAdapter` | Interopérer avec un IdP | Future |

### 8.4 Inversion de dépendance en Python

```python
# Exemple conceptuel : ne préjuge pas du contrat final.
from typing import Protocol


class PasswordVerifier(Protocol):
    async def verify(self, *, presented: str, stored_hash: str) -> bool:
        ...


class AuthenticationEventSink(Protocol):
    async def publish(self, event: "SafeAuthenticationEvent") -> None:
        ...
```

La définition du port doit être indépendante d'une librairie cryptographique particulière. **La librairie utilisée pour vérifier** reste un choix explicite de confiance, testé et maintenu.

### 8.5 Composition Root

C'est à l'application, à une factory configurée ou à un mécanisme de bootstrap **explicite** de relier ports et adapters.

```python
# Pseudocode non exécutable tel quel : détails réservés à 03, 18 et 24.
engine = AuthenticationEngine(
    authenticators=[
        PasswordAuthenticator(verifier=password_verifier, reader=credential_reader),
        ApiKeyAuthenticator(reader=api_key_reader),
        JwtAuthenticator(trust_policy=jwt_trust, key_resolver=key_resolver),
    ],
    event_sink=safe_event_sink,
)
```

### 8.6 Règle de dépendance

```text
Framework adapter ------> Application contract ------> Domain
Infrastructure adapter -> Port / Protocol ---------> Domain contract
Domain ---------------------------------------------> Standard Python only
```

Aucun module de domaine ne doit dépendre de `django`, `fastapi`, `redis`, d'un SDK d'IdP ou d'un modèle ORM de l'application hôte.

### 8.7 Modulaire ne signifie pas microservices

Hexagonal Architecture est applicable **à une bibliothèque monolithique modulaire**. PyAuthKit n'exige ni service réseau distinct, ni queue, ni déploiement autonome.

---

## 9. Catalogue de patterns retenus, différés et évités

### 9.1 Classification pédagogique

| Famille | Nature | Utilité pour PyAuthKit |
|---|---|---|
| Principes de conception | SOLID, DRY, KISS, YAGNI, SoC, DIP | Décider comment répartir les responsabilités |
| GoF - Behavioral | Strategy, State, Chain of Responsibility, Observer | Variabilité des mécanismes, évolutions des flows, événements |
| GoF - Structural | Adapter, Facade, Decorator | Interopérabilité et simplification de l'API |
| GoF - Creational | Factory Method / Abstract Factory selon besoin | Assemblage contrôlé de composants |
| Patterns d'application | Registry, Pipeline, Dependency Injection, Unit of Work éventuel | Coordination et extension |
| Patterns architecturaux | Hexagonal, Clean Architecture, Layers | Directions des dépendances et frontières |
| DDD | Bounded Context, Entity, Value Object, Domain Service | Sémantique et invariants |
| Styles d'intégration | Event-Driven, CQRS lorsque pertinent | Audit et séparation des lectures/écritures futures |

**Précision :** Registry, Pipeline, Dependency Injection et CQRS ne sont pas tous des patterns GoF.

### 9.2 Strategy - retenu pour les authenticators

**Problème :** différentes familles de preuves exigent des vérifications différentes.

**Solution :** un `Authenticator` implémente un contrat comportemental commun.

**Conditions :** chaque implémentation déclare ses preuves admissibles, ses exigences de confiance et ses résultats possibles.

**Limite :** une stratégie de vérification ne remplace pas, à elle seule, un flow MFA.

### 9.3 Adapter - retenu pour providers et infrastructures

**Problème :** plusieurs systèmes fournissent des formes incompatibles de données et de vérification.

**Solution :** l'adapter traduit le monde extérieur vers les ports, sans imposer ses détails au core.

**Exemples :** `SqlCredentialAdapter`, `FastAPIAuthenticationAdapter`, `OidcProviderAdapter` (future).

### 9.4 Factory / Registry - retenu avec prudence

**Factory :** assemble un authenticator avec les dépendances correctes.

**Registry :** tient les stratégies enregistrées et les résout selon une clé ou une sélection autorisée.

**Contraintes :**

- pas de sélection automatique d'un authenticator plus faible ;
- pas de double enregistrement ambigu non détecté ;
- pas de plugin exécuté automatiquement sans décision de l'intégrateur ;
- résolution de méthode séparée de la vérification de la preuve.

### 9.5 Chain of Responsibility et Pipeline - différés en runtime

**Pertinence :** les flows complexes peuvent chaîner extraction, résolution, vérification, policy, challenge, assurance et résultat.

**Risque :** une chaîne de handlers peut rendre invisibles les frontières de confiance et les changements d'état.

**Approche :** garder un **pipeline conceptuel** clair dès le MVP ; introduire un orchestrateur runtime uniquement quand les flows multi-étapes l'exigent.

### 9.6 State - différé pour challenges et sessions

Des transitions telles que :

```text
CREATED -> PENDING -> VERIFIED -> CONSUMED
                 \-> EXPIRED
                 \-> REJECTED
```

ne seront modélisées qu'avec leurs règles d'atomicité et d'expiration. Le schéma est illustratif, pas une FSM validée.

### 9.7 Observer / Domain Events - retenu sous contrôle

Un événement de succès, échec ou challenge peut être observé sans que la logique de sécurité dépende d'un consommateur analytique externe.

Cependant, **la politique en cas d'indisponibilité de l'audit** devra être explicitée : la livraison asynchrone opportuniste et l'audit obligatoire n'offrent pas les mêmes garanties.

### 9.8 Facade - recommandée pour l'API développeur

L'appel de haut niveau `engine.authenticate(...)` constitue une façade potentielle sur registry, vérification et résultat. Il n'efface pas la nécessité de fournir des options sûres pour les mécanismes sensibles.

### 9.9 Decorator / Middleware - sous conditions

Des décorateurs peuvent ajouter des métriques, des traces et des protections transversales, **à condition** de préserver le résultat, de masquer les secrets et de ne pas contourner les invariants du cœur.

### 9.10 Repository - seulement si la persistance l'exige

Un repository exprime l'accès à un **agrégat métier**. Tous les ports de stockage ne sont pas des repositories : un `VerificationKeyResolver` ou un `CredentialReader` peut être plus précis qu'un `GenericRepository[T]` universel.

### 9.11 CQRS - non requis pour le MVP

La distinction conceptuelle commandes/queries peut être utile pour les cas d'usage d'admin, les sessions et les credentials. Une infrastructure CQRS ou Event Sourcing n'est **pas nécessaire** pour la validation simple d'un password, d'une API key ou d'un JWT.

### 9.12 Patterns explicitement non requis

- `Singleton` global pour le moteur ou le contexte courant ;
- `Service Locator` cachant la résolution de clés de confiance ;
- framework d'injection automatique imposé ;
- `Abstract Factory` à niveaux multiples sans variante concrète ;
- `Event Sourcing` systématique de chaque tentative ;
- une classe par étape de pipeline sans comportement ;
- un bus d'événements distribué obligatoire au bootstrap.

---

## 10. Modèle logique du noyau

### 10.1 Composants conceptuels

```text
                 AuthenticationRequest
                         |
                         v
                AuthenticationEngine
                         |
            +------------+-----------------+
            |                              |
            v                              v
     Method / Strategy                Attempt Context
       Resolution                     + Trust Policy
            |                              |
            +------------+-----------------+
                         |
                         v
                  Authenticator
                         |
              Credential / Evidence
                  Verification
                         |
                         v
                 Subject Establishment
                         |
                         v
                AuthenticationResult
                         |
                  Safe Audit Event
```

Le schéma ne représente pas encore les classes ni les séquences d'appels réelles.

### 10.2 Entrée normalisée

Candidats à représenter :

- méthode demandée ou mécanisme de sélection contrôlé ;
- preuve présentée (`Evidence`) avec type explicite ;
- contexte de la tentative et origine des attributs ;
- scope de confiance connu du serveur hôte ;
- identifiant de corrélation et deadlines éventuelles.

**Exclusion :** `AuthenticationRequest` ne doit pas encapsuler obligatoirement un objet HTTP.

### 10.3 Résultat normalisé

L'analyse des exigences propose quatre catégories :

| État candidat | Sémantique | Principal authentifié |
|---|---|---|
| `AUTHENTICATED` | Preuve suffisante et acceptée | Oui |
| `REJECTED` | Conditions de preuve/policy non satisfaites | Non |
| `CHALLENGE_REQUIRED` | Continuation nécessaire | Non à ce stade |
| `ERROR` | Incident technique empêchant de prouver | Non |

Le statut `CHALLENGE_REQUIRED` est **un besoin de contrat** dès la conception ; son runtime est différé.

`ERROR` pourrait être représenté par une variante de résultat ou des exceptions d'application contrôlées. Ce point reste **ouvert (`DEC-06`)**.

### 10.4 Invariants minimaux

```text
INV-01  AUTHENTICATED => principal vérifié non nul.
INV-02  REJECTED / ERROR => aucun nouveau principal authentifié.
INV-03  CHALLENGE_REQUIRED => pas de finalisation prématurée du flow.
INV-04  Unknown method => rejet ou erreur contrôlée, jamais fallback faible.
INV-05  Aucune sortie de log ou événement ne contient le secret brut.
INV-06  Une identité ou un tenant déclaré ne devient pas fiable sans validation.
INV-07  L'authentification n'accorde aucune permission IAM implicite.
INV-08  Les preuves et politiques sont vérifiées dans le contexte de confiance attendu.
```

Ce sont des **invariants candidats**, à formaliser dans `07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md`.

### 10.5 Types de responsabilité

| Type | Ce qu'il sait | Ce qu'il ne décide pas |
|---|---|---|
| Engine | Quelle stratégie invoquer, comment former le résultat | Qui est administrateur métier |
| Authenticator | Comment valider une catégorie de preuve | Quels rôles octroyer |
| Resolver | Comment obtenir référence de credential / clé selon confiance | Accepter n'importe quelle source demandée par le client |
| Policy evaluator | Quel niveau/preuve le contexte requiert | Permissions sur une facture |
| Session component | Cycle de vie session si activé | L'identité IAM globale |
| Integration adapter | Transformer une entrée/sortie externe | Court-circuiter la vérification du core |

---

## 11. Architecture de sécurité : la confiance avant les fonctionnalités

### 11.1 Sécurité par conception

Le moteur exécute du code dont les erreurs peuvent devenir des contournements d'authentification. La sécurité n'est donc pas un module optionnel ajouté à la fin.

Elle influence les contrats, les valeurs par défaut, le contrôle des dépendances, les modes d'échec et la qualification.

### 11.2 Frontières de confiance

```text
 UNTRUSTED                            CONTROLLED / TRUSTED
 ----------                           --------------------
 User input / Credential  ----->  Evidence Parser / Authenticator
 Claimed tenant            ----->  Trusted Tenant Resolution
 JWT headers & claims      ----->  Explicit JWT Trust Profile
 Remote provider response  ----->  Federated Assertion Validation
 Proxy-auth headers        ----->  Trusted Proxy / mTLS Binding
 Plugin metadata           ----->  Approved Plugin Configuration
```

Un attribut n'est pas de confiance par sa **localisation** dans un objet Python, mais par son origine, sa validation et les hypothèses explicitement acceptées.

### 11.3 Principaux risques à empêcher

- contournement par méthode non enregistrée ou fallback ;
- validation cryptographique insuffisante ;
- confusion d'algorithme, issuer, audience ou type de jeton ;
- acceptation d'un access token dans un usage non autorisé ;
- confusion entre sujet déclaré et sujet établi ;
- fuite de credentials, secrets, OTP ou tokens dans les logs ;
- mélange d'état entre deux tentatives concurrentes ;
- accès inter-tenant à une clé ou à un credential ;
- rejeu de challenge futur ;
- confiance abusive dans des headers proxy ;
- extension de plugin non contrôlée ;
- erreurs de provider entraînant une réussite implicite.

### 11.4 Password - orientation MVP

- Utiliser un schéma de hachage de mots de passe spécialisé, moderne et maintenu ; la sélection et les paramètres restent à arbitrer (`DEC-09`).
- Vérifier via un `PasswordVerifier` dont le contrat rend possible l'évolution des algorithmes.
- Ne jamais stocker ni logger le mot de passe brut.
- Prendre en compte limitation d'essais, messages non révélateurs et risques d'énumération des comptes.
- Éviter les fonctions de hachage généralistes rapides utilisées seules comme *password hashing*.
- Toute politique de migration de hashes doit expliciter les conditions d'acceptation de formats hérités.

### 11.5 API Key - orientation MVP

- Concevoir séparation entre identifiant de recherche éventuel, secret et empreinte de vérification.
- Prévoir expiration, statut et révocation selon capacités du store, sans imposer un serveur de gestion des clés complet.
- Ne pas confondre identifiant public d'une clé et preuve secrète.
- Ne pas supposer qu'un identifiant de clé absent impose un scan de toutes les clés.
- Documenter les conséquences des différents schémas d'indexation et de hashing.

### 11.6 JWT - orientation MVP

Un JWT ne constitue pas une preuve universelle d'identité. Son acceptation dépend d'un **profil de vérification autorisé**, incluant suivant le cas :

- signatures et algorithmes autorisés ;
- clés de vérification et provenance approuvée ;
- issuer autorisé ;
- audience attendue ;
- validité temporelle (`exp`, `nbf`, `iat` selon contrat) ;
- usage du jeton, type et éventuels claims de liaison ;
- contraintes de tenant et de contexte ;
- règles de rotation / cache des clés lorsqu'un resolver distant est utilisé.

**Ne pas faire confiance** aux paramètres libres du token pour sélectionner une autorité ou un algorithme sans limitation par configuration du vérificateur.

**Ne pas assimiler** la validation de n'importe quel access token OAuth à la connexion d'un utilisateur.

### 11.7 OIDC / OAuth 2.0 / SAML - préparation, pas MVP

- OIDC : prévoir validation d'ID Token, de provenance, de `state`, `nonce` et de la liaison au flow, selon le profil retenu.
- OAuth 2.0 : définir précisément si PyAuthKit agit comme client OAuth, resource server ou autre rôle ; ne pas prétendre implémenter tous les rôles implicitement.
- SAML : préférer des composants de validation spécialisés ; signatures, conditions, audience et anti-replay doivent être vérifiés selon le profil adopté.
- Social login : le fournisseur et sa capacité réelle de preuve doivent être explicites ; tous les providers cités ne disposent pas nécessairement des mêmes conventions OIDC.

### 11.8 MFA, passkeys et assurance - préparation

- MFA est une **composition de facteurs**, pas un simple booléen.
- Les catégories de facteurs et les propriétés cryptographiques réelles doivent être distinguées.
- Le niveau d'assurance ne peut pas être déduit d'un label de provider ni de `factors.length`.
- Un challenge doit être lié au flow, expirer et être consommé selon sa sémantique de rejeu.
- Les propriétés spécifiques WebAuthn (origin, RP ID, challenges, signatures, flags, etc.) sont à spécifier dans `15`.

### 11.9 Agent, workload et délégation - préparation

Un `PrincipalType.AGENT` décrit la **nature du sujet** et non une permission élevée.

Dans un système agentique :

- distinguer l'identité du service, de l'agent et de l'utilisateur délégant ;
- distinguer preuve d'identité, délégation d'autorité et autorisation d'action ;
- privilégier les preuves courtes et à audience restreinte lorsque la méthode le permet ;
- ne pas réutiliser automatiquement le credential humain d'un utilisateur pour un agent ;
- rendre traçable l'issuer, le subject et l'éventuelle chaîne de délégation ;
- conserver les restrictions et le contexte vérifiés sans les confondre avec des rôles IAM.

### 11.10 Contrôles transversaux

| Contrôle | Règle architecturale |
|---|---|
| Secrets | Pas de représentation sensible par défaut ; minimiser leur durée de vie |
| Comparaison | Comparaison adaptée et résistante aux fuites temporelles applicables |
| Cryptographie | Bibliothèques maintenues et configuration approuvée, pas de crypto maison |
| Replay | Nonces, expiration et consommation atomique selon le flow |
| Brute force | Points d'extension pour limitation d'essais et throttling |
| Sessions | Protection contre fixation, rotation, expiration, révocation, à terme |
| CSRF / Redirects | Responsabilité de l'adapter Web / flow concerné |
| Erreurs | Détails internes séparés des réponses publiques |
| Audit | Événements structurés et minimisés |
| Supply chain | Dépendances suivies et contrôlées |

### 11.11 Ce que signifie « secure by design » dans ce projet

Ce slogan n'est pas une preuve de conformité. Pour PyAuthKit, il signifie : **menaces examinées**, **frontières de confiance explicitées**, **invariants de refus testés**, **dépendances maintenues**, **hypothèses documentées** et **revue des mécanismes avant publication**.

Aucune certification NIST, FIDO, SOC 2, ISO ou autre n'est revendiquée. La sélection des versions pertinentes des standards sera traitée au moment des modules concernés.

---

## 12. Extensibilité et écosystème de plugins

### 12.1 Objectif d'extensibilité

Ajouter une capacité sans modifier le cœur du moteur, et sans permettre qu'une extension en dégrade les garanties.

### 12.2 Types d'extension

| Type | Exemple | Propriétés contractuelles |
|---|---|---|
| Authenticator | Nouveau mécanisme de preuve | Evidence admise, confiance, résultat |
| Credential adapter | Store SQL, Redis, autre | Isolation, expiration, erreurs |
| Crypto verifier | Password hash ou signature validator | Algorithmes autorisés, erreurs et validation |
| Federation adapter | OIDC / SAML | Profil et trust configuration |
| Framework integration | Django, FastAPI, CLI | Extraction d'entrée et mapping de sortie |
| Event sink | Logs, SIEM, monitoring | Redaction et politique de livraison |
| Risk evaluator | Service de risque externe | Provenance du signal et délais |
| Policy component | Sélection d'exigences de preuve | Interdiction des accès métiers implicites |

### 12.3 Contrat d'authenticator candidat

```python
# Esquisse uniquement : le contrat final sera décrit dans 10 et 24.
from typing import Protocol


class Authenticator(Protocol):
    @property
    def method(self) -> str:
        ...

    async def authenticate(
        self,
        request: "AuthenticationRequest",
    ) -> "AuthenticatorOutcome":
        ...
```

Le `AuthenticatorOutcome` n'est pas nécessairement le `AuthenticationResult` final. Cette séparation est **une option importante** pour permettre au moteur d'appliquer une policy transversale ou une continuation ultérieure ; elle reste à arbitrer (`DEC-04`, `DEC-06`, `DEC-13`).

### 12.4 Stratégie de découverte

**Candidat privilégié pour le MVP :** enregistrement explicite à l'initialisation.

**Plus tard éventuellement :** entry points Python ou registry dynamique, uniquement sous activation volontaire et politique de confiance adaptée.

Le but n'est pas d'exécuter du code tiers arbitraire par découverte automatique.

### 12.5 Capacités déclarées

Un authenticator pourra déclarer des métadonnées telles que : mécanisme, version de contrat, type de preuve, exigences de configuration et possibilité de challenge.

Ces déclarations **ne remplacent pas** la validation réelle : elles améliorent la résolution et les erreurs de configuration.

### 12.6 Compatibilité

- Toute interface publique doit documenter sa version / stabilité.
- Les plugins doivent avoir un jeu de tests de conformité.
- Les changements incompatibles demandent une décision de versionnement (`DEC-20`).
- Les garanties de sécurité ne doivent pas être relâchées pour préserver la compatibilité d'un adapter non conforme.

---

## 13. Concurrence, état et déterminisme

### 13.1 Stateless core lorsque possible

Une authentification JWT en validation locale peut ne requérir aucune session persistante. Une authentification password peut nécessiter l'accès à un store sans que le moteur conserve d'état de session.

La présence de flows complexes **ne doit pas** rendre tout le core stateful.

### 13.2 État par tentative

Les éléments suivants ne doivent pas fuiter d'un appel à un autre :

- `attempt_id`, `tenant_context`, `authenticated_principal` ;
- evidence et credentials ;
- configuration de vérification dépendante d'une requête ;
- état d'un challenge futur ;
- contexte de traçage sensible.

### 13.3 Async et blocages

Le chemin asynchrone doit éviter d'exposer des opérations I/O bloquantes au sein de l'event loop sans politique d'exécution adaptée.

Les opérations cryptographiques coûteuses doivent être traitées selon une stratégie de ressources et de concurrence compatible avec la disponibilité du service. La décision d'offrir une façade synchrone reste ouverte.

### 13.4 Temps, hasard et reproductibilité

- Horloge injectable si la vérification dépend de timestamps.
- Aléa cryptographiquement sûr pour les secrets/challenges émis, lorsque ces capacités existeront.
- Tests déterministes permettant de reproduire expiration, rotation et erreurs.
- Les faux générateurs d'aléa de tests ne doivent jamais être sélectionnables silencieusement en production.

### 13.5 Atomicité future

La consommation à usage unique, la rotation ou la révocation peuvent nécessiter des opérations atomiques. Le contrat `ChallengeStore` devra définir précisément les garanties, sans faire passer une implémentation mémoire mono-processus pour équivalente à un store distribué.

---

## 14. Multi-tenant, providers et configuration de confiance

### 14.1 Pourquoi le tenant appartient au modèle de sécurité

Dans un environnement multi-tenant, une même chaîne de `subject`, une même `kid` JWT ou un identifiant de clé peuvent exister sous plusieurs autorités. Leur signification dépend du contexte de confiance.

### 14.2 Attribut déclaré versus validé

```text
Client-supplied tenant_id  --- not trusted by default ---> TenantResolver
Trusted host configuration ------------------------------> TenantResolver
Provider / credential validated context ----------------> TenantResolver
                                                            |
                                                            v
                                                    Trusted Trust Scope
                                                            |
                                                            v
                                               Keys / Credential Store / Policy
```

### 14.3 Invariants candidats

- Une clé JWT d'un tenant n'est pas automatiquement autorisée pour un autre.
- Un `issuer` externe est comparé à la configuration de confiance attendue, pas seulement au claim entrant.
- La résolution d'un credential prend en compte la partition appropriée.
- La politique de sélection de provider ne peut pas être détournée par un champ libre.
- Un résultat conserve les attributs de provenance pertinents pour les vérifications suivantes.

### 14.4 Configuration

Séparer :

1. paramètres non sensibles du moteur ;
2. références de secrets et clés ;
3. profils de confiance (issuer, audience, usages, algorithmes) ;
4. règles de résolution tenant/realm ;
5. capacités de stockage et transport ;
6. politiques d'authentification.

Les valeurs de configuration ne doivent pas être codées en dur dans les classes du domaine.

### 14.5 Provider-agnostic n'est pas provider-unaware

Le domaine connaît la **provenance vérifiée** quand elle est pertinente, mais n'importe pas de SDK Google, Microsoft, GitHub, Okta ou autre.

Les différences de profils de providers sont encapsulées dans les adapters et configs, jamais dissimulées au point de perdre les garanties de la preuve.

---

## 15. Sessions, tokens et flows : trajectoire sans confusion de responsabilités

### 15.1 Principe de séparation

```text
Authentication Result != Session != Token != Authorization Decision
```

- Le résultat établit l'issue de la vérification.
- La session modélise un état de parcours ou de maintien d'authentification.
- Le token est un artefact portant un usage, un format et une politique de vérification.
- L'autorisation est une décision externe sur une ressource ou action.

### 15.2 Pourquoi JWT ne doit pas structurer le système

Le domaine ne doit pas supposer que tout token est un JWT, ni qu'une authentification produit nécessairement un access token. Tokens opaques, sessions serveur, tickets, challenges et tokens spécialisés demandent des sémantiques distinctes.

### 15.3 State machine future

Le flow MFA, magic link ou passkey pourra nécessiter :

- création de challenge ;
- liaison à une tentative et à un principal candidat ;
- expiration et tentatives autorisées ;
- validation de la réponse ;
- consommation à usage unique si applicable ;
- émission du résultat définitif ;
- journalisation sans preuve brute.

Le moteur générique d'authentification reste distinct de PyRuntimeKit / d'un runtime de workflow généraliste.

### 15.4 Assurance et step-up

L'assurance reflète des garanties effectivement établies. Un step-up exige une preuve supplémentaire adaptée à la politique courante et ne signifie pas qu'un rôle IAM a changé.

La politique de durée de validité de cette assurance, son lien à une session et les profils standards éventuels restent à concevoir dans `12` et `13`.

---

## 16. Observabilité, audit et exploitation

### 16.1 Intentions

L'observabilité doit permettre de répondre à :

- Quelle tentative s'est déroulée ?
- Quelle méthode était demandée ?
- La preuve a-t-elle été rejetée, validée ou un challenge est-il nécessaire ?
- Quel provider ou profil de confiance a été utilisé, dans la mesure où son identifiant peut être exposé sans risque ?
- Quel type d'erreur s'est produit ?
- Quelle opération a été lente ou indisponible ?

### 16.2 Événements envisagés

```text
AuthenticationStarted
CredentialValidated
CredentialRejected
AuthenticationSucceeded
AuthenticationRejected
AuthenticationFailed
[Future] ChallengeIssued / Completed / Expired
[Future] SessionCreated / Revoked
[Future] TokenIssued / Revoked
```

Les noms exacts, les champs et les schémas seront précisés dans `21` ; cette liste est illustrative et compatible avec l'intention de `00 §27`.

### 16.3 Schéma minimal candidat

```python
# Délibérément sans secret ni token brut.
SafeAuthenticationEvent(
    event_type="authentication.rejected",
    attempt_id="...",
    method="api_key",
    reason_code="invalid_evidence",
    timestamp="...",
)
```

Un `subject`, une IP ou un `tenant_id` constituent potentiellement des données personnelles ou sensibles selon le contexte ; ils ne doivent pas être publiés systématiquement. La minimisation, la rétention et l'accès devront être documentés (`DEC-21`).

### 16.4 Modes de défaillance audit

À définir selon usage :

- **best effort** : perte d'événement possible, authentification non bloquée ;
- **durable / obligatoire** : traitement et delivery conditionnés par les garanties du dispositif ;
- **hybride** : événements critiques soumis à des règles spécifiques.

Le mode par défaut et les compromis de sécurité/disponibilité restent ouverts ; ne pas introduire un bus de messages externe obligatoire dans le MVP.

### 16.5 Métriques sans secrets

Catégories envisageables : compte de succès/échec par mécanisme, latences, erreurs de key resolver, timeout provider, distribution de challenges, causes de refus agrégées, versions de contrats et échecs de plugin.

Les étiquettes ne doivent pas contenir de secrets ni induire une cardinalité non maîtrisée en production.

---

## 17. Packaging, intégrations et compatibilité

### 17.1 Produit livrable

Le noyau sera une **bibliothèque Python installable**, pas un serveur obligatoire.

### 17.2 Répartition candidate

```text
pyauthkit/
  __init__.py
  domain/                  # Concepts et invariants
  application/             # Cas d'usage et coordination
  ports/                   # Contrats sortants et interfaces utiles
  authenticators/          # Implementations supportees
  infrastructure/          # Adapters locaux et integration technique
  integrations/            # Facades externes optionnelles
```

Ce plan est **illustratif uniquement**. Le découpage définitif et les dépendances inter-modules appartiennent à `03` et au plan de bootstrap `28`.

### 17.3 Dépendances optionnelles

Des extras ou packages d'intégration pourront fournir Django, FastAPI, Redis, OIDC, SAML, passkeys ou providers spécialisés. La méthode de packaging (`DEC-16`) reste à décider.

### 17.4 Politique de versionnement

- Annoncer explicitement le statut expérimental des APIs initiales.
- Stabiliser les **contrats** avant de stabiliser la syntaxe.
- Qualifier les changements de sémantique de sécurité comme des changements potentiellement incompatibles.
- Associer exemples et contract tests aux versions des extensions.
- Définir ultérieurement dépréciations et compatibilité (`DEC-20`).

### 17.5 Support des versions Python

La matrice Python / OS est **ouverte (`DEC-01`)**. Ne pas promettre une version précise avant validation de l'ensemble des bibliothèques cryptographiques et de leurs capacités de distribution.

---

## 18. MVP et architecture évolutive

### 18.1 Le MVP vise une preuve d'architecture, pas une couverture universelle

**Périmètre MVP tiré de `00 §34` et précisé dans `01 §13` :**

| Bloc | Capacité | Justification |
|---|---|---|
| Core domain | Request, Evidence/Credential, Principal, Result, Context | Langage commun |
| Kernel | `AuthenticationEngine` | Coordination |
| Extensibilité | `Authenticator` + Registry | Remplaçabilité |
| Password | Vérification sécurisée interchangeable | Use case humain classique |
| API Key | Vérification de secret technique | Use case service |
| JWT | Vérification sous trust profile | Use case token |
| Safety | Fail-closed, redaction, erreurs contrôlées | Invariants P0 |
| Audit minimal | Tentatives corrélées sans secrets | Visibilité de l'auth |
| Quality | Unit, integration, security et contract tests | Démonstration de fiabilité |
| Documentation | Démarrage et extension | Réutilisation réelle |

### 18.2 Ce qui est délibérément différé

- moteur MFA et gestion persistée de challenges ;
- sessions, rotation, refresh et émission complète de tokens ;
- OIDC social, OAuth avancé et SAML ;
- WebAuthn / passkeys / magic links ;
- vérification mTLS et certificats avancés ;
- identities workload et délégation avancées ;
- adaptive risk / step-up ;
- admin UI, IAM complet et policies de ressources.

L'architecture doit **laisser la place** à ces fonctionnalités, sans leur faire supporter le coût du MVP.

### 18.3 Jalons logiques non versionnés

```text
M0 - Bootstrap and Contracts
          |
          v
M1 - Authentication Kernel
          |
          v
M2 - Password / API Key / JWT
          |
          v
M3 - Security and Contract Qualification
          |
          v
M4 - MVP Architecture Review
          |
          v
Future - Challenges / MFA / Sessions / Federation / Passkeys / Machine
```

Les numéros de version PyPI et les milestones définitifs ne sont **pas fixés** ici.

### 18.4 Règle de progression

Une nouvelle capacité n'entre dans la roadmap que si :

1. son besoin et sa menace sont identifiés ;
2. ses interfaces peuvent être explicitées ;
3. son effet sur les invariants est compris ;
4. les dépendances additionnelles sont justifiées ;
5. les scénarios positifs, négatifs et de concurrence sont testables ;
6. les risques d'incompatibilité sont documentés.

---

## 19. Compromis architecturaux et anti-patterns

### 19.1 Compromis à assumer

| Tension | Préférence proposée | Risque à surveiller |
|---|---|---|
| Simplicité vs configurabilité | API courte + trust profile explicite | Config trop permissive |
| Généralité vs sûreté | Contrats partagés, sémantique propre à chaque méthode | Abstraction mensongère |
| Extension vs supply chain | Plugins opt-in et qualifiés | Plugins malveillants / non maintenus |
| Async vs adoption | Async principal, façade sync éventuelle | I/O bloquante cachée |
| État vs stateless | Stateless si le flow le permet | Absence de révocation lorsque requise |
| Performance vs password security | Sécurité de hash prioritaire | Coût CPU mal dimensionné |
| Audit vs confidentialité | Événements minimisés | Ré-identification et secrets |
| Multi-tenancy vs simplicité | Trust boundaries explicites | Cross-tenant acceptance |
| DDD vs cérémonial | DDD proportionné | Classes/aggregates sans besoin |
| Compatibilité vs corrections de sécurité | Corrections prioritaires et versionnées | Breaking changes non annoncés |

### 19.2 Anti-patterns bloquants

| Anti-pattern | Pourquoi il est bloquant |
|---|---|
| `authenticate()` décide des rôles | Mélange authentication / authorization |
| `Principal` dérive d'un modèle Django | Couplage au framework |
| `JWTAuthenticator` accepte une clé déduite librement du token | Bypass de confiance |
| `JWT == AuthenticatedUser` | Confusion du format avec la preuve et l'usage |
| `unknown method -> password fallback` | Downgrade d'authentification |
| `event = request.__dict__` | Fuite de credentials |
| `engine.current_principal` mutable et partagé | Fuite de contexte concurrent |
| Import de PyIAMKit obligatoire | Violation du bounded context autonome |
| Plugin auto-exécuté sans contrôle | Supply chain / exécution indésirable |
| `EXTERNAL` comme rôle ou privilège | Confusion provenance / autorisation |
| `MFA=True -> AAL2` | Assurance déduite sans preuve de cérémonie |
| `challenge used` non atomique | Rejeu en concurrence |
| Ré-implémenter des algorithmes cryptographiques | Risques évitables de validation et maintenance |

---

## 20. Architecture Decision Candidates (ADRC)

Ces décisions ne sont **pas acceptées**. Elles encadrent la conception détaillée et renvoient au registre `DEC-01..DEC-22` du document `01`.

| ADRC | Orientation proposée | Décisions `01` concernées | Validation attendue |
|---|---|---|---|
| `ADRC-01` | Core Python pur organisé selon des dépendances hexagonales | `DEC-03`, `DEC-04` | Import graph + tests sans framework |
| `ADRC-02` | `authenticate` async en API de référence | `DEC-15` | Tests concurrence et intégration |
| `ADRC-03` | Authenticator par Strategy + Registry explicite | `DEC-04`, `DEC-07` | Plugin tiers et résolution non ambiguë |
| `ADRC-04` | Types séparés : Evidence, Principal, Result, Trust Context | `DEC-03`, `DEC-05`, `DEC-06`, `DEC-08` | Revue du modèle de domaine |
| `ADRC-05` | Password/API key/JWT, aucun protocole fédéré au MVP | `DEC-09`, `DEC-10`, `DEC-11` | Tests de sécurité positifs et négatifs |
| `ADRC-06` | Validation JWT pilotée par un trust profile explicite | `DEC-10`, `DEC-14` | Tests issuer/audience/key/alg/tenant |
| `ADRC-07` | Sessions et challenges hors MVP, ports futurs | `DEC-12`, `DEC-13`, `DEC-17` | Revue d'extensibilité |
| `ADRC-08` | Assurance distincte du nombre de facteurs | `DEC-18` | Critères d'assurance documentés |
| `ADRC-09` | Contrat PyIAMKit minimal et non circulaire | `DEC-19` | Test avec/sans PyIAMKit |
| `ADRC-10` | Plugins opt-in et packaging modulaire | `DEC-16`, `DEC-20` | Install minimal + contract tests |
| `ADRC-11` | Événements audit minimisés | `DEC-21` | Tests de redaction et schéma |
| `ADRC-12` | Web/CSRF/cookies hors domaine pur | `DEC-22` | Revue d'intégrations |
| `ADRC-13` | Matrice support / performance fondée sur mesures | `DEC-01`, `DEC-02` | CI et benchmarks reproductibles |

### 20.1 Décisions différées, sans implication automatique

- `DEC-03` : `dataclass` et `Protocol` sont des candidats, non des obligations.
- `DEC-05` : `EXTERNAL` est actuellement cité comme type dans `00`, mais un axe d'origine séparé semble plus cohérent.
- `DEC-06` : résultat de refus versus exceptions de transport reste à fixer.
- `DEC-11` : validation de JWT au MVP ne signifie pas émission JWT ou autorisation server.
- `DEC-12` : distinguer flow session et session authentifiée.
- `DEC-17` : l'adapter mémoire est une bonne référence de test, pas un store distribué de production.
- `DEC-18` : les niveaux d'assurance devront être référencés à des profils documentés sans faux label de conformité.

### 20.2 Processus d'acceptation d'un ADR

1. Énoncer le problème et les forces en présence.
2. Considérer au moins une alternative viable.
3. Expliquer les conséquences positives et négatives.
4. Lier exigences et scénarios de test.
5. Enregistrer la décision et son statut (`proposed`, `accepted`, `superseded`, etc.).
6. Mettre à jour les documents impactés si elle change.

---

## 21. Fitness functions : comment vérifier l'architecture ?

Une conviction architecturale doit avoir une **preuve objective** lorsqu'elle peut être vérifiée.

### 21.1 Tests structurels

| Test | Règle visée | Preuve attendue |
|---|---|---|
| Import sans Django/FastAPI | PRN-02, PRN-03 | Test d'installation et imports |
| Import sans PyIAMKit | PRN-01 | `ACC-014` |
| Domaine sans ORM/SDK provider | PRN-02 | Analyse des dépendances |
| Plugin tiers sans modification du core | PRN-07, PRN-14 | `ACC-011` |
| Résolution méthode déterministe | PRN-07 | `ACC-009`, `ACC-010` |
| Stores substituables selon capacité | PRN-11 | `ACC-012`, futur `ACC-027` |

### 21.2 Tests comportementaux

| Test | Règle visée | Référence `01` |
|---|---|---|
| Password correct / incorrect | Preuve réellement vérifiée | `ACC-002`, `ACC-003` |
| API key valide / invalide | Refus sûr et principal technique | `ACC-004`, `ACC-005` |
| JWT signature invalidée | Confiance explicite | `ACC-007` |
| JWT expiré, issuer ou audience mauvais | Validation de claims et trust | `ACC-008` |
| Exception d'un verifier | Fail closed | `ACC-016` |
| Deux tentatives simultanées | Pas de fuite de contexte | `ACC-015` |
| Logs en debug | Zéro secret brut | `ACC-018` |
| Evénement de refus | Corrélation sans disclosure | `ACC-013` |
| Principal AGENT ou WORKLOAD | Modèle non limité au Web | `ACC-017` |

### 21.3 Tests avancés de design, non MVP

| Test | Condition préalable | Référence |
|---|---|---|
| MFA incomplet ne valide pas l'auth | Flow engine | `ACC-019` |
| Challenge expiré ou rejoué est rejeté | ChallengeStore | `ACC-020`, `ACC-021` |
| ID Token issuer inattendu | OIDC adapter | `ACC-022` |
| `state` / `nonce` erronés | OIDC flow | `ACC-023` |
| Session révoquée non reconnue | SessionStore | `ACC-024` |
| Assurance insuffisante déclenche step-up | Policy + flow | `ACC-025` |
| Token/credential du tenant B sous tenant A | Trusted tenant resolution | `ACC-026` |
| FastAPI et CLI convergent vers même contrat | Adapters de transport | `ACC-028` |
| Agent à token court sans privilège implicite | Agent integration | `ACC-029` |
| Certificat mTLS non approuvé rejeté | mTLS adapter | `ACC-030` |

### 21.4 Mesures non encore chiffrées

L'analyse `01 §8.1` laisse ouvertes les cibles quantitatives. On doit mesurer avant de fixer :

- temps d'authentification par mécanisme ;
- distribution des latences et budgets selon environnements ;
- effets CPU/mémoire des paramètres de hashage ;
- throughput et comportement concurrent ;
- couverture de tests et mutation/security tests si retenus ;
- compatibilité Python et OS ;
- comportement des timeouts et d'une indisponibilité du provider ;
- visibilité des erreurs et taux de redaction.

**Aucune valeur de SLA, de couverture ou de performance n'est inventée dans ce document.**

---

## 22. Matrice de traçabilité transversale

| Dimension architecturale | Source `00` | Exigences `01` | Documents de suite |
|---|---|---|---|
| Vision du produit | §1-4, §37-39 | FR-001, NFR-006 | `03`, `24` |
| Frontière avec IAM | §5-6, §30 | ARC-012, ARC-018, INT-001-002 | `04`, `23` |
| Modèle principal/evidence | §7, §12 | FR-011-016, SEC-019 | `04`, `05`, `06` |
| Kernel, registry et API | §10, §23-25 | FR-001-010, ARC-002-007 | `03`, `08`, `09`, `24` |
| Patterns et agnosticisme | §19-22 | ARC-001-018, NFR-002-008 | `03`, `18` |
| Password / API key / JWT | §8.1, §8.3, §8.5, §34 | FR-022-027, SEC-003-009 | `10`, `20` |
| MFA / Challenge / Assurance | §8.6-11, §10-14 | FR-028-037, FR-057-060 | `11`, `12`, `15`, `17` |
| Sessions & tokens | §15-17 | FR-038-044, ARC-008-010 | `13`, `19` |
| Federation | §9, §18 | FR-045-050 | `14`, `18` |
| Machine / agent / workload | §7.2-7.6, §31-32 | FR-051-056, INT-006-007 | `16`, `23` |
| Multi-tenancy | §28 | FR-016, SEC-022 | `20`, `25` |
| Sécurité | §26 | SEC-001-024 | `07`, `20`, `26` |
| Observabilité | §27 | FR-061-064, INT-010 | `21`, `26` |
| Intégrations | §19-21, §30-32 | INT-001-010 | `22`, `23` |
| Qualité et qualification | §33-36 | NFR-001-022, ACC-001-030 | `26`, `27`, `28` |

---

## 23. Questions à trancher avant de détailler `03`

Ces questions méritent une **réponse enregistrée**, sans interrompre la rédaction d'une architecture candidate.

1. **Quel est le contrat exact entre `AuthenticatorOutcome` et `AuthenticationResult` ?** Faut-il un résultat intermédiaire pour séparer vérification et policy ?
2. **Quelles sont les frontières des modules ?** `domain`, `application`, `ports`, `authenticators`, `infrastructure`, `integrations` ou autre découpage ?
3. **Où se trouve le `CompositionRoot` ?** Bootstrap explicite, factory et configuration applicative ?
4. **Comment résout-on une méthode ?** Clé explicite par défaut, auto-détection optionnelle restreinte ?
5. **Comment représenter un subject vérifié ?** Issuer, subject, principal type, identity origin, tenant scope et assurance ?
6. **Quelles erreurs deviennent des statuts et lesquelles remontent comme exceptions ?**
7. **Quelles sont les garanties du `CredentialReader` et du `VerificationKeyResolver` ?**
8. **Quel est le contrat de timeout, annulation et concurrence des authenticators async ?**
9. **Quel profil de validation JWT et quelle source de confiance sont autorisés au MVP ?**
10. **Quels événements sont obligatoires et avec quel mode d'échec ?**
11. **Comment le core évite-t-il de charger PyIAMKit ou un framework Web ?**
12. **Quel est le minimum pour préparer les flows futurs sans introduire une machine à états prématurée ?**

Ces décisions relèvent du détail architectural ou des domaines dédiés. Le document `03` doit expliciter les hypothèses retenues et signaler les décisions non fermées.

---

## 24. Definition of Ready et Definition of Done architecturales

### 24.1 Definition of Ready pour une capacité

- Besoin et valeur décrits.
- Exigences `FR/SEC/ARC/NFR/INT` associées.
- Menaces principales connues.
- Contrat d'entrée/sortie et frontière de confiance identifiables.
- Responsabilités avec IAM et application explicites.
- Succès, refus, erreur et continuation spécifiés si applicables.
- Scénarios testables disponibles.
- Dépendances et impact de distribution estimés.

### 24.2 Definition of Done pour une implémentation

- Contrats respectés, invariants vérifiés.
- Tests positifs, négatifs et d'erreurs présents.
- Pas de dépendance Web/IAM imposée au noyau.
- Traitement de secrets et logs revus.
- Conditions de confiance documentées.
- Contract tests de plugin/port passés si applicables.
- Tests de concurrence pour tout état partagé.
- Packaging, typage, linters et CI conformes aux politiques du projet.
- Documentation et exemples de l'API mis à jour.
- Décisions d'architecture impactées tracées.

### 24.3 Conditions de refus d'une évolution

Refuser ou redessiner une capacité qui :

- affaiblit un contrôle sans justification de sécurité ;
- rend IAM ou HTTP obligatoire pour une authentification locale ;
- court-circuite la vérification ou accepte des trust inputs non validés ;
- ajoute une condition provider-specific dans le noyau ;
- produit un principal authentifié sans preuve suffisante ;
- expose du matériel sensible dans logs, exceptions ou événements ;
- modifie la sémantique de `AuthenticationResult` sans plan de compatibilité.

---

## 25. Synthèse pour la suite documentaire

### 25.1 Ce qui est confirmé par les sources

- PyAuthKit est un moteur d'authentification **autonome**, pas une solution IAM complète.
- Il vise les humains et les identités techniques, y compris agents et workloads.
- Il doit être indépendant des frameworks Web, providers et stores spécifiques.
- Les authenticators doivent être extensibles et leurs résultats normalisés.
- Le périmètre fonctionnel à terme comprend MFA, sessions, tokens, passkeys, fédération et adaptive authentication.
- Le MVP initial de référence est centré sur **Engine + Registry + Password + API Key + JWT**.
- La sécurité et l'audit sont transverses, non optionnels.

### 25.2 Orientations proposées dans ce document

- **DDD** pour le langage du domaine et sa frontière ;
- **Hexagonal / Ports & Adapters** pour maîtriser les dépendances ;
- **Strategy + Registry + Adapter + Factory** comme patterns principalement justifiés ;
- **SOLID, DRY, KISS, YAGNI, SoC et DIP** utilisés comme critères d'ingénierie observables ;
- **trust profiles explicites**, fail-closed et preuves vérifiées comme invariants ;
- **plugins opt-in**, interfaces étroites et conformité par contract tests ;
- **extension progressive**, sans workflow engine ou IAM monolithique imposé au MVP ;
- **architecture fitness functions** reliées aux critères `ACC-*`.

### 25.3 Livrables attendus de `03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md`

Le document suivant devra définir, sans ambiguïté :

1. les vues de contexte (C4 Level 1 / Level 2 si retenu) ;
2. les composants logiques et leurs interactions ;
3. le graphe de dépendances et les règles d'import ;
4. les flux de traitement MVP et les points d'extension ;
5. les frontières de confiance et la configuration ;
6. les ports/adapters et leur ownership ;
7. la gestion des erreurs, états et effets externes ;
8. les séquences Password, API key, JWT ;
9. les intégrations facultatives et la frontière avec PyIAMKit ;
10. les contraintes de testabilité, déploiement et packaging ;
11. les arbitrages `DEC-*` non tranchés et hypothèses conservées ;
12. la traçabilité jusqu'aux critères d'acceptation P0.

---

## 26. Conclusion

La réussite de PyAuthKit ne se mesurera pas à la présence immédiate de tous les mécanismes d'authentification. Elle dépend de l'existence d'un **noyau de confiance clair, extensible, auditable et rigoureusement séparé de la gouvernance des identités**.

Le projet doit donc privilégier, dans cet ordre :

1. **la justesse sémantique** des concepts d'authentification ;
2. **la sûreté vérifiable** des chemins de preuve ;
3. **la stabilité contractuelle** et la possibilité d'extension ;
4. **l'ergonomie Python** et l'autonomie d'intégration ;
5. **l'élargissement progressif** du catalogue de mécanismes.

> **Principe final :** *A trustworthy authentication engine does not merely accept credentials. It establishes a verified principal under explicit trust assumptions, without granting authority it does not own.*

**Document suivant :** `03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md`.

---

## Annexe A - Référentiel condensé des principes

| ID | Principe | Exigences centrales |
|---|---|---|
| PRN-01 | Authentication bounded responsibility | ARC-012, ARC-018 |
| PRN-02 | Domain first | ARC-001, ARC-005 |
| PRN-03 | Depend on abstractions | ARC-003, ARC-008 |
| PRN-04 | Explicit trust | SEC-006, SEC-022 |
| PRN-05 | Fail closed | SEC-018, FR-005 |
| PRN-06 | Verified evidence before success | SEC-019 |
| PRN-07 | One core, many authenticators | FR-004, FR-010 |
| PRN-08 | Normalized contracts, preserved semantics | FR-006, FR-015 |
| PRN-09 | Separate policies and mechanisms | ARC-013 |
| PRN-10 | Composable progressive flows | ARC-017 |
| PRN-11 | Storage as port | ARC-008 |
| PRN-12 | Async and concurrency safety | FR-002, NFR-011 |
| PRN-13 | Observability without disclosure | FR-064, SEC-001 |
| PRN-14 | Safe extension | FR-010, RSK-014 |
| PRN-15 | Tenant trust boundary | SEC-022 |
| PRN-16 | No assurance by label | FR-015, DEC-18 |
| PRN-17 | Secure defaults | SEC-006, NFR-018 |
| PRN-18 | Contracts include tests and docs | NFR-008, NFR-015 |

## Annexe B - Lexique des approches

| Terme | Définition courte | Application concrète |
|---|---|---|
| `SOLID` | Cinq principes de conception objet | Responsabilités et substitution des authenticators |
| `DDD` | Conception autour du domaine et de son langage | Authentication Bounded Context |
| `Hexagonal` | Dépendances dirigées vers le core via ports | Separation de Web, stores et providers |
| `Strategy` | Variation d'algorithme derrière un contrat | Password/API Key/JWT authenticators |
| `Adapter` | Traduction d'une interface extérieure | Framework, credential store, federation |
| `Registry` | Résolution contrôlée d'implémentations | Selection d'authenticator |
| `Factory` | Assemblage et construction contrôlée | Bootstrap des composants |
| `Pipeline` | Séquence explicite d'opérations | Parcours auth et challenges futurs |
| `State` | Comportement dépendant d'un état | Challenges/sessions futurs |
| `Observer` | Notification de faits | Audit/events |
| `Facade` | Interface simplifiée sur un sous-système | `AuthenticationEngine.authenticate` |
| `Repository` | Accès à des objets/agrégats du domaine | Seulement si modèle persistant justifié |
| `CQRS` | Séparation des écritures et des lectures | Éventuel pour gestion future de credentials/sessions |
| `Fail-closed` | Refuser quand la preuve ou la confiance n'est pas établie | JWT invalide, provider indisponible |
| `Trust profile` | Règles explicites qui rendent une preuve recevable | Clés, issuer, audience, usage et tenant |
| `Fitness function` | Test mesurable d'un objectif architectural | Import sans Django, plugin, tests JWT |

## Annexe C - Historique documentaire

| Date | Version | Évolution |
|---|---|---|
| 2026-10-27 | 0.1.0-draft | Première rédaction : vision, responsabilités, principes, SOLID/DDD/Hexagonal, patterns, sécurité, extensibilité, MVP, ADR candidats, vérifications et traçabilité |
