# PyAuthKit - Software Design & Learning Convention

> **Document** : `PYAUTHKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md`  
> **Projet** : PyAuthKit  
> **Domaine** : Authentication Engine / Application Security / Software Design  
> **Type** : Convention de conception, d'apprentissage, de documentation et de qualification  
> **Version documentaire** : `1.0.0` (proposition initiale)  
> **Date** : 28 octobre 2026  
> **Statut** : **PROPOSED - convention à adopter explicitement**  
> **Langue** : français ; noms de contrats, idiomes Python et patterns en anglais  
> **Portée** : spécifications, ADR, domain model, code, docstrings, commentaires, tests, PR, documentation, releases et supports pédagogiques  
> **Référentiel produit** : `00` à `03` de PyAuthKit (architecture cible, non preuve de code opérationnel)  
> **Inspirations méthodologiques** : conventions PySRMKit et PyAccountingKit v2.0 fournies comme références

> **Principe directeur** : **La frontière de confiance et la preuve exigée précèdent l'API ; le problème précède le pattern ; l'invariant précède l'implémentation ; le code et les tests précèdent toute affirmation de qualification.**

> **Avertissement fondamental** : Ce document décrit **comment concevoir et apprendre** pendant le développement de PyAuthKit. Les classes, signatures et pipelines présentés sont des **illustrations de design** et non l'inventaire d'une codebase auditée, une API publique stabilisée ou une certification de conformité. Les protections cryptographiques doivent être confiées à des bibliothèques reconnues, configurées et testées ; aucun exemple pédagogique ne vaut implémentation de sécurité prête pour la production.

---

## Guide de lecture

| Parcours | Sections | Usage principal |
|---|---|---|
| Vision & gouvernance | 0-7 | Raison d'être, sources, état de preuve, méthode |
| Abstractions & frontières | 8-15 | Deux cartes, taxonomie, trust, DDD, ontologie |
| Conception | 16-24 | Principes, GoF, architectural patterns, Python, algorithmes |
| Cas PyAuthKit | 25-47 | Design Learning Cards, MVP et extensions |
| Qualité & sécurité | 48-56 | Menaces, invariants, tests, observabilité, patterns interdits |
| Conventions d'équipe | 57-73 | Docs, code, ADR, PR, DoD, releases et roadmap |
| Synthèse & références | 74-80, annexes | Exemples de transfert, manifeste, gabarits et lexique |

**Lecture courte** : `0 → 4 → 8 → 10 → 14 → 17 → 25 → 27 → 35 → 48 → 61 → 69 → 78`.

---

## 0. Résumé exécutif

PyAuthKit doit être simultanément :

1. un **framework Python d'authentification exploitable**, modulaire et indépendant des frameworks Web, fournisseurs d'identité et technologies de persistance ;
2. un **terrain d'apprentissage délibéré** de la modélisation de domaine, des principes SOLID et voisins, des patterns de conception, de l'architecture logicielle, de l'algorithmique, des idiomes Python, du runtime et de la sécurité.

La pédagogie n'autorise **jamais** une réduction de la sécurité du produit, ni l'ajout d'abstractions sans besoin. Les fonctions et objets doivent porter des **noms naturels du domaine Authentication**. Les patterns sont identifiés dans les documents lorsque leurs propriétés sont réellement observables.

**La question d'ingénierie centrale est :**

> Comment transformer une preuve d'authentification non fiable en un sujet authentifié, sous un contexte de confiance établi et une politique explicite, tout en préservant le refus, la traçabilité, la provenance et la séparation avec l'autorisation ?

**La question pédagogique centrale est :**

> Comment reconnaître, justifier, coder, tester et finalement intérioriser les choix de conception rencontrés pour résoudre ce problème - y compris le choix de ne pas utiliser de pattern ?

### 0.1 Références et responsabilité documentaire

| Référence | Autorité documentaire | N'apporte pas à elle seule |
|---|---|---|
| `00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md` | WHY : contexte, périmètre, vision, cas d'usage | Critères de qualification du code |
| `01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md` | WHAT : FR, NFR, SEC, ARC, INT, ACC, DEC | API stable ou conformité de réalisation |
| `02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md` | HOW/WHY architectural : PRN-01..PRN-18, alternatives candidates | ADR nécessairement acceptés |
| `03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md` | WHERE/HOW cible : composants, trust boundaries, ports, séquences, FIT | Architecture physiquement déployée ou auditée |
| Convention présente | HOW TO REASON/LEARN : classification, pédagogie, conventions | Catalogue canonique de toutes les entités |
| `04` à `28` (documents cibles) | Contrats détaillés à produire | Preuve de leur implémentation |
| Dépôt, tests, CI, artefacts | État effectivement implémenté et qualifié, **après vérification** | Exactitude du raisonnement sans revue |

La convention **ne modifie pas silencieusement** les références `FR-*`, `SEC-*`, `ARC-*`, `INT-*`, `PRN-*`, `TB-*`, `FIT-*`, `DEC-*` ou `ADRC-*`. Elle les cite et peut proposer des compléments à traiter par le document propriétaire ou par ADR.

### 0.2 Vocabulaire des statuts

| Statut | Signification | Preuve exigée |
|---|---|---|
| `CONCEPTUAL` | Idée ou possibilité documentée | Texte, aucune preuve de code |
| `PROPOSED` | Design candidat, en attente de décision | Proposition tracée |
| `SPECIFIED` | Contrat et critères définis | Spec datée, versionnée |
| `ACCEPTED` | Décision formelle adoptée | ADR/revue consignée |
| `IMPLEMENTED` | Code réellement présent | Commit/diff identifié |
| `TESTED` | Comportements testés | Suite, environnement et résultat |
| `QUALIFIED` | Critères pertinents couverts, échecs inclus | Rapport de qualification et preuves |
| `RELEASED` | Artefact publié | Version, build, provenance, checksums si utiles |

`DOCUMENTED != IMPLEMENTED`; `TESTED != SECURE`; `RELEASED != CERTIFIED`.

---

## 1. Mission de la convention

La convention poursuit cinq objectifs : concevoir correctement PyAuthKit ; apprendre par des cas réels ; construire un langage partagé ; documenter les décisions et leurs coûts ; transférer les connaissances vers les autres frameworks Python.

Sa règle est :

```text
REAL AUTHENTICATION PROBLEM
    -> CLAIM / EVIDENCE / TRUST BOUNDARY
    -> DOMAIN CONCEPT + INVARIANT
    -> DESIGN PRESSURE
    -> SIMPLEST CORRECT DESIGN
    -> PRINCIPLE / ALGORITHM / PATTERN (if genuinely applicable)
    -> PYTHON CONTRACT + IMPLEMENTATION
    -> NEGATIVE TESTS + SECURITY EVIDENCE
    -> DESIGN REVIEW / REFACTORING
    -> REUSABLE ENGINEERING INTUITION
```

## 2. Ce que signifie « laboratoire pédagogique de production »

Une *learning card* ne doit pas rendre la codebase moins maintenable. Les exemples « sans pattern » et « avec pattern » restent dans `docs/learning/`, les tests ou des tutoriels, sauf si la variante enrichie répond à un besoin réel de production.

Une abstraction est admise si elle répond à une variation observée, une frontière de confiance, un invariant, un contrat de substitution, une exigence d'intégration ou un risque de sécurité ; **jamais uniquement pour illustrer Strategy ou Factory**.

## 3. Deux objectifs indépendants à vérifier

**Produit :** comportement correct, fail-closed, sûr, documenté, extensible sans fragiliser le noyau.

**Apprentissage :** capacité à expliquer **le problème**, **le modèle**, **le principe**, **le mécanisme Python**, **l'alternative refusée** et **la preuve de test**.

Une PR peut réussir les tests mais manquer d'explication sur une frontière structurante ; une explication pédagogique élégante ne rend pas la PR sûre sans tests.

## 4. North Star : Problem First, Trust First, Pattern Second

```text
BAD: "Let us add Chain of Responsibility to learn it."

GOOD:
"The authentication flow now requires multiple independently
validated steps and explicit continuation state. A composition
model may become useful. Is a state machine enough?"
```

**Sécurité d'abord** ne veut pas dire complexité d'abord : la première solution correcte peut être un vérificateur unique avec un port minimal, quelques valeurs immuables et des erreurs explicites.

## 5. Gouvernance de la source de vérité

1. Les **faits** de l'authentification appartiennent au *Authentication bounded context* et aux sources d'évidence authentifiées, chacun selon son périmètre.
2. L'identité organisationnelle, le provisioning et les permissions relèvent de **PyIAMKit** ou de l'application hôte.
3. Les relations avec les providers externes sont des **contrats de confiance et d'intégration**, non une cession générale de l'autorité du domaine.
4. Les modes d'authentification ne sont **pas** interchangeables en garanties de sécurité simplement parce qu'ils retournent le même type.
5. Un niveau d'assurance est une **conclusion sous conditions établies**, pas un label inféré de `method='mfa'`.

## 6. Contrat pédagogique de chaque décision significative

Répondre, si applicable, à :

1. Quel comportement est attendu et par qui ?
2. Quelle frontière de confiance est franchie ?
3. Quelles données sont non fiables, lesquelles deviennent vérifiées, et quand ?
4. Quel est le propriétaire de la règle, du credential, du token ou de la session ?
5. Quels invariants, cas d'échec et contraintes temporelles s'appliquent ?
6. Quelle pression actuelle impose une abstraction ?
7. Quel algorithme et quelles structures de données sont nécessaires ?
8. Quels principes et quels patterns sont réellement observables ?
9. Quelle implémentation Python minimale respecte le contrat ?
10. Quelles alternatives, complexités et vulnérabilités sont introduites ?
11. Quels tests positifs, négatifs, de propriétés et de frontières protègent la décision ?
12. Quelle preuve autorise à qualifier l'état comme implémenté ou testé ?

## 7. Classification obligatoire des concepts

Ne pas mélanger :

| Niveau | Question | Exemple authentification |
|---|---|---|
| Domaine | De quoi parle-t-on ? | `Credential`, `Challenge`, `AuthenticatedPrincipal` |
| DDD | Quel rôle porte le modèle ? | Value Object de preuve, service de domaine, aggregate de session si pertinent |
| Principe | Quelle qualité doit tenir le design ? | DIP, fail-closed, SoC |
| Design pattern | Comment organisons-nous une variation locale ? | Strategy entre authenticators, Adapter vers provider |
| Architectural pattern | Comment sont organisées les frontières globales ? | Hexagonal / Ports & Adapters |
| Algorithme | Comment calcule-t-on / vérifie-t-on ? | validation de claims, résolution de clés sous profil fiable |
| Python | Avec quelle primitive ? | `Protocol`, `dataclass(frozen=True)`, `Enum`, `async` |
| Runtime | Quelles garanties à l'exécution ? | concurrence, timeout, atomicité, annulation |
| Infrastructure | Avec quel système ? | crypto lib, PostgreSQL, Redis, HTTP client |
| Qualification | Quelle preuve établit la propriété ? | test de substitution, tests d'attaque, contrôle CI |

---

## 8. Carte A : de l'authentification au matériel

```text
1  DOMAINE DE SÉCURITÉ / BESOIN D'AUTHENTIFICATION
   -> parties, preuves, limites de confiance, objectifs d'assurance
2  MODÉLISATION DE DOMAINE (DDD)
   -> Principal, Evidence, Credential, TrustProfile, Result
3  CONCEPTION LOGICIELLE
   -> SOLID, SoC, Strategy, Adapter, Hexagonal si justifiés
4  ALGORITHMIQUE ET STRUCTURES DE DONNÉES
   -> parsing borné, lookup, comparaison, validation, machine à états
5  PROGRAMMATION PYTHON
   -> classes, fonctions, Protocol, dataclass, asyncio, exceptions
6  RUNTIME
   -> pile, event loop, scheduling, mémoire, cancellation, timing
7  SYSTÈME D'EXPLOITATION
   -> processus, permissions, sockets, génération d'aléa, isolation
8  ARCHITECTURE MACHINE / ISA
   -> instructions, mémoire, primitives cryptographiques accélérées
9  LOGIQUE NUMÉRIQUE
   -> circuits, calcul et manipulation d'états binaires
10 PHYSIQUE
   -> transistors, électronique, phénomènes matériels
```

Cette carte explique **où** une décision finit par s'exécuter. PyAuthKit ne construit pas le système d'exploitation ni un algorithme cryptographique maison. L'architecture logicielle et l'algorithmique sont deux dimensions de conception, pas nécessairement des phases strictement successives.

## 9. Carte B : responsabilités du domaine Authentication

```text
UNTRUSTED REQUEST / CLAIM / EVIDENCE
    |
    v
TRUSTED HOST CONTEXT / SCOPE RESOLUTION
    |
    v
AUTHENTICATOR SELECTION (allowed method + policy)
    |
    v
TRUST PROFILE (approved issuer / audience / key sources / scope)
    |
    v
EVIDENCE VERIFICATION (method-specific)
    |
    +--> INVALID / AMBIGUOUS / UNAVAILABLE => FAIL CLOSED
    |
    v
VERIFIED SUBJECT + PROVENANCE
    |
    v
AUTHENTICATION POLICY / RESULT NORMALIZATION
    |
    +--> DENIED / CHALLENGE REQUIRED / FAILURE
    |
    v
AUTHENTICATED PRINCIPAL / RESULT
    |
    +--> OPTIONAL SESSION / TOKEN (separate responsibility, future)
    |
    v
PYIAMKIT OR HOST APP: IDENTITY RESOLUTION + AUTHORIZATION
```

Cette carte est une **carte de responsabilités et transitions de confiance**. Elle ne prétend pas que tout authenticator suit exactement ce flux séquentiel ; WebAuthn, OIDC, mTLS ou MFA comportent des cérémonies et ordres propres. Elle n'impose pas un répertoire Python par boîte.

## 10. Bounded Contexts et frontières d'autorité

### 10.1 Authentication

PyAuthKit possède les contrats et la vérification des preuves, les tentatives, la composition de facteurs, le résultat, ainsi que les mécanismes de sessions et tokens lorsqu'ils sont dans son périmètre contractuel.

### 10.2 Identity & Access Management

PyIAMKit possède ou coordonne les comptes, groupes, tenants, rôles, permissions, affiliations organisationnelles, provisioning et gouvernance. PyAuthKit **peut fonctionner seul**.

### 10.3 Providers d'identité et autorités externes

Un provider OIDC/SAML, un fournisseur de clés ou un store possède des faits dans son propre périmètre. PyAuthKit consomme des preuves **sous configuration de confiance explicite**, en préservant provenance, audience, scope et limites.

### 10.4 Application hôte

L'hôte possède son routage fiable, son opération demandée et la décision d'autorisation finale. Une signature vérifiée n'est pas une décision d'accès à une ressource.

### 10.5 Context map

```text
External Credential / Identity Systems
                |
          adapters + explicit trust
                v
     +-------------------------+
     |  PyAuthKit              |
     |  Authentication BC      |
     |  VerifiedSubject        |
     +------------+------------+
                  | published contract (provenance + scope)
                  v
      +------------------------+
      |  PyIAMKit (optional)   |
      |  Identity + Access     |
      +------------+-----------+
                   |
            authorization inputs
                   v
          Host application / protected resource
```

## 11. Ubiquitous Language : distinctions essentielles

| Terme | Définition de travail | Ne pas confondre avec |
|---|---|---|
| `ClaimedIdentity` | identité affirmée avant vérification | `VerifiedSubject` |
| `Evidence` | élément présenté pour prouver | preuve déjà validée |
| `Credential` | secret/artefact associé à un moyen d'authentification | identité organisationnelle |
| `Authenticator` | comportement de vérification d'un mécanisme | Identity Provider global |
| `AuthenticatorOutcome` | verdict interne d'une vérification | `AuthenticationResult` public |
| `VerifiedSubject` | sujet établi sous contexte de confiance | user IAM |
| `AuthenticatedPrincipal` | représentation normalisée d'un sujet authentifié | permission/access grant |
| `AuthenticationContext` | informations liées à la tentative ; provenance à typer | `TrustedScope` automatiquement établi |
| `TrustedScope` | partition de confiance issue d'une résolution autorisée | `tenant_hint` déclaratif |
| `TrustProfile` | règles de confiance sur mécanisme, issuer, audience, clés et scope | contenu libre du token |
| `AuthenticationPolicy` | exigences d'une cérémonie d'authentification | RBAC/ABAC d'une ressource |
| `Factor` | type/mécanisme réellement vérifié | canal de notification ou signal de risque |
| `Challenge` | étape/cérémonie à résoudre sous état borné | succès partiel devenu accès |
| `Session` | état de continuité, expiration et révocation | identité fondamentale |
| `Token` | artefact de représentation/transport d'informations | preuve automatiquement recevable |
| `OAuth 2.0` | cadre d'autorisation déléguée | authentification utilisateur autonome |
| `OpenID Connect` | couche d'identité/authentification bâtie sur OAuth 2.0 | token bearer générique |
| `WebAuthn` | protocole de preuve cryptographique via authenticator | tout mécanisme « passwordless » |
| `Passkey` | credential/expérience fondés sur WebAuthn | garantie universelle d'un niveau AAL donné |
| `RiskSignal` | indice contextuel non nécessairement vérifié | facteur de possession/connaissance |
| `AssuranceLevel` | assertion justifiée sous référentiel/conditions | simple enum arbitraire |

**Règle** : ne pas appeler une valeur `verified` si elle n'a pas traversé les vérifications requises ; ne pas appeler une décision `authorized` lorsque seule l'authentification a réussi.

## 12. Stratégic DDD : découpage conceptuel, pas explosion de services

Sous-domaines candidats :

- Authentication Orchestration ;
- Credential Verification ;
- Trust and Policy ;
- Challenges and Factors ;
- Session and Token Lifecycle ;
- Federation ;
- Audit and Security Events.

Ces sous-domaines **ne sont pas** automatiquement sept bounded contexts autonomes, équipes, packages, bases ou microservices. L'ownership métier, les invariants et la nécessité d'évolution indépendante doivent justifier chaque frontière.

## 13. Tactical DDD : catégoriser sans dogme

| Objet candidat | Classification plausible | Question à résoudre dans `04-07` |
|---|---|---|
| `AuthenticationAttempt` | Entity | Identité stable, transition et audit de la tentative ? |
| `CredentialRecord` | Entity | Rotation/révocation/expiration sous quel ownership ? |
| `AuthenticationChallenge` | Entity ou member d'aggregate | Unicité, TTL, consommation unique, concurrence ? |
| `AuthenticationSession` | Aggregate candidat | Cohérence de renouvellement/révocation, identité d'instance ? |
| `AuthenticationRequest` | Command/DTO d'entrée | Quels champs sont non fiables et quels invariants locaux ? |
| `AuthenticationResult` | Value/Result Object | Exhaustivité des issues et impossibilité des succès incohérents ? |
| `VerifiedSubject` | Value Object candidat | Provenance, assurance, émetteur, partition et preuve réellement vérifiée ? |
| `TrustProfile` | Configuration immutable et validée | Qui l'autorise et la versionne ? |
| `Authenticator` | Port / comportement substituable | Contrat, preuves supportées, erreurs et policy ? |
| `AuthenticationEngine` | Application Service / orchestrator | Orchestration sans vérifier lui-même toute crypto ? |
| `AuthenticationPolicy` | Domain Policy ou Application Policy selon responsabilité | Contrôle de preuve vs exigence métier d'accès ? |
| `CredentialStore` | Port de persistance | Lookup scoped, garanties de cohérence et révocation ? |

Une entité n'est pas automatiquement un Aggregate Root. Un objet immuable n'est pas nécessairement un Value Object ; une interface n'est pas un bounded context ; un nom `Service` n'est pas une preuve de Domain Service.

## 14. Trust Ownership, provenance et qualification

Trois formes de « vérité » à distinguer :

```text
PRESENTED CLAIM     : ce que déclare l'appelant (non fiable)
VERIFIED EVIDENCE   : ce que le mécanisme établit sous profil approuvé
AUTHENTICATED RESULT: ce que le moteur publie après contrôles transverses
```

Aucune de ces formes ne se substitue à la vérité **IAM** relative à l'affiliation, aux comptes ou aux autorisations.

Un résultat peut conserver `verification_method`, `issuer`, `subject`, `trusted_scope`, `verified_at`, `assurance_evidence`, versions de policy et références corrélables, **sans stocker la preuve brute**. Le schéma final est à spécifier ; la conservation doit respecter la minimisation des données.

## 15. Temporalité et concurrence comme dimensions de sécurité

À documenter pour chaque opération sensible : `issued_at`, `not_before`, `expires_at`, `verified_at`, `revoked_at`, `consumed_at`, timestamp de politique, tolérance de dérive justifiée, source d'horloge, modèle de concurrence, invalidation, ordre des événements.

**Règles candidates** :

- un credential révoqué ne doit pas redevenir valide par lecture stale non maîtrisée ;
- un challenge one-time doit être consommé atomiquement dans le scope prévu ;
- un résultat de vérification ne doit pas réutiliser une configuration de confiance implicitement modifiée en cours de contrôle ;
- la validation temporelle s'appuie sur une source d'horloge contrôlée et des règles explicites ;
- timeout et cancellation ne doivent jamais créer un succès ;
- le même principal revendiqué depuis deux tenants ne signifie pas même identité vérifiée.

Le choix exact de garantie de cohérence dépend du mécanisme et du backend ; un store mémoire et Redis ne sont pas interchangeables sans tests contractuels propres à ces garanties.

---

## 16. Principes de conception appliqués

| Principe | Pression PyAuthKit | Preuve observée |
|---|---|---|
| SRP | L'engine ne doit pas gérer aussi stockage, crypto et IAM | responsabilités et imports isolés |
| OCP | Ajout d'authenticator sans modifier le noyau | test plugin tiers |
| LSP | Un authenticator respectant le port tient les mêmes postconditions | contract tests partagés |
| ISP | Pas de `GiantIdentityProvider` pour tous les mécanismes | ports fins par capacité |
| DIP | Le core ne dépend pas d'un SDK ou backend donné | tests d'architecture/imports |
| DRY | Pas de logique divergente de validation de confiance | règle canonique et tests multi-canaux |
| KISS | Pas de workflow distribué pour une vérification stateless | solution minimale explicite |
| YAGNI | Ne pas implémenter passkeys/SAML au MVP par anticipation | découpage des versions |
| SoC | Authn, IAM, authz, crypto, transport et observabilité séparés | flux et ownership explicités |
| Information Hiding | Secret, record et clés derrière capacités contrôlées | aucune fuite par API, logs, repr |
| High Cohesion | Un module par responsabilité stable | dépendances locales et tests focalisés |
| Low Coupling | Framework et provider remplaçables | alternate adapters compatibles |
| Composition over Inheritance | Configurer des behaviors plutôt que sous-classer l'engine | wiring explicite |
| Fail Closed | Indisponibilité ou ambiguïté donne refus/erreur, jamais réussite | tests négatifs et de fault injection |
| Secure by Default | Configuration dangereuse impossible par omission | tests de configuration invalide |
| Least Privilege | Port et plugin n'ont que les capacités nécessaires | revue de permissions et dépendances |
| Explicit Trust | La sélection de clé et politique vient d'une source approuvée | tests de confusion de tenant / issuer |
| Auditability | Décisions traçables sans données secrètes | schéma allowlist et tests de confidentialité |

**Attention** : `Fail Closed`, `Least Privilege` et `Secure by Default` sont des **principes de sécurité** et non des patterns GoF.

## 17. Design Patterns : catalogue de référence, pas checklist

### 17.1 GoF - Creational

`Factory Method`, `Abstract Factory`, `Builder`, `Prototype`, `Singleton`.

### 17.2 GoF - Structural

`Adapter`, `Bridge`, `Composite`, `Decorator`, `Facade`, `Flyweight`, `Proxy`.

### 17.3 GoF - Behavioral

`Strategy`, `Observer`, `Command`, `State`, `Iterator`, `Mediator`, `Chain of Responsibility`, `Template Method`, `Visitor`, `Memento`, `Interpreter`.

### 17.4 Statut et pertinence **candidats** pour PyAuthKit

| Concept | Cas naturel | Niveau | Statut pédagogique |
|---|---|---|---|
| Strategy | comportements de vérification interchangeables | Design Pattern | fortement pertinent |
| Adapter | fournisseur OIDC, Django/FastAPI, store | Design Pattern | fortement pertinent |
| Facade | API `authenticate(request)` | Design Pattern | probable |
| Factory / Registry | construction/wiring des authenticators | Factory/Registry idiom | si plusieurs compositions nécessaires |
| Repository | persistance de credential/session/challenge | DDD/Enterprise Pattern | lorsque persistance réelle |
| Chain of Responsibility | traitement séquentiel compositionnel | GoF | différé, pas automatique |
| State | comportement polymorphe selon état | GoF | conditionnel ; enum + guards d'abord |
| Observer | subscribers de notification locale | GoF | possible, pas synonyme de domain event |
| Decorator | préoccupations transverses explicites | GoF | si composition non confuse |
| Builder | configuration réellement complexe | GoF | différé |
| Unit of Work | atomicité de plusieurs mutations | Enterprise Pattern | si transaction nécessaire |
| CQRS | read/write nettement distincts | Architectural Pattern | non requis au MVP |
| Event Sourcing | historique comme source d'état | Architectural Pattern | non requis |
| Singleton | état partagé global | GoF | éviter par défaut |
| Abstract Factory | familles de composants liés | GoF | non requis actuellement |
| Visitor / Flyweight / Prototype | aucun besoin fort identifié | GoF | ne pas imposer |

### 17.5 Evidence du pattern Strategy

Le pattern n'est présent que si : plusieurs comportements sont substituables, le consommateur reste stable, ils respectent le même contrat, et la sélection ne dépend pas d'un grand conditionnel au sein du core.

Une seule implémentation derrière un `Protocol` peut être utile pour le test ou une frontière externe, **sans être suffisante pour affirmer que Strategy a été exercé en production**.

## 18. Architectural Patterns : échelle et responsabilités

- **Layered Architecture** : séparer domain/application/adapters ;
- **Hexagonal / Ports & Adapters** : orienter les dépendances vers les abstractions ;
- **Clean Architecture** : préserver la règle de dépendance ;
- **Modular Monolith / in-process library** : découper sans déployer chaque module comme service ;
- **Event-Driven Design** : produire des faits et notifications à la bonne frontière ;
- **CQRS (sélectif)** : seulement si lecture/écriture divergent réellement ;
- **Microkernel / Plugin architecture** : si le registry et la politique de chargement forment un besoin démontré ;
- **Pipes & Filters** : si des transformations indépendantes apportent valeur sans diluer les frontières de confiance ;
- **Microservices** : non nécessaires pour un moteur bibliothèque ;
- **Event Sourcing** : non requis pour tracer des événements d'audit.

`AuthenticationEngine` **n'est pas** un service réseau autonome par défaut. `Registry` **n'est pas** automatiquement du Microkernel. `AuthenticationEvent` **n'est pas** automatiquement de l'Event Sourcing.

## 19. Différences conceptuelles à protéger

```text
State Machine           != GoF State Pattern
Authentication Command  != GoF Command Pattern
Domain Event            != GoF Observer Pattern
Dependency Injection    != Dependency Inversion Principle
Repository              != generic CRUD wrapper
OAuth 2.0               != authentication protocol by itself
JWT format              != proof of authentication
JWT signature verified  != resource access authorized
Identity Provider       != Authenticator instance
TrustedScope            != tenant hint from client
RiskSignal              != AuthenticationFactor
MFA enabled             != MFA successfully completed
Credential present      != Credential verified
Passwordless            != guaranteed phishing resistance
Plugin satisfies port   != plugin code is trusted
Audit event produced    != durable audit event persisted
Test passing            != security certification
```

## 20. Algorithmique et structures de données : ne pas tout appeler « pattern »

| Besoin | Algorithme / structure | Attention de sécurité |
|---|---|---|
| Résoudre un authenticator | mapping/registry par méthode et scope | méthode autorisée par trusted policy |
| Trouver credential | recherche indexée scoped | absence de fuite cross-tenant |
| Comparer secret | vérification cryptographique/compare en temps sûr | ne jamais faire `==` sur secret brut sensible lorsque comparaison protégée requise |
| Vérifier JWT | parsing borné + vérification signature et claims | pas de clé/alg choisi librement par le token |
| Vérifier OTP | calcul standard + fenêtre temporelle bornée | anti-replay, limitation des essais |
| Rechercher facteurs | ensemble des facteurs vérifiés, exigences | vérifier indépendance et provenance |
| Consommer challenge | transition atomique/compare-and-swap | race et replay |
| Vérifier expiration | comparaison sur horloge contrôlée | tolérance dérive explicite |
| Révoquer session | index de session/référence, transition atomique | cohérence distribuée |
| Détecter doublons | set / contrainte d'unicité | collisons/clé de scope |
| Collecter événement | construction allowlist / sérialisation | minimisation, redact secrets |
| Appliquer rate limit | compteur borné et horodaté, stockage partagé | stratégie définie par hôte/adapters |

La complexité temporelle, l'utilisation mémoire et les volumes attendus sont documentés lorsqu'ils influencent le risque, la latence ou la scalabilité. Ne pas réinventer password hashing, signature validation ou génération de clés pour illustrer un algorithme.

## 21. Pythonic Software Design

Primitives pertinentes : `typing.Protocol`, fonctions simples, `dataclasses`, `Enum`, `Mapping`, `Literal` si approprié, type unions, exceptions typées, `async def`, `await`, context managers, composition, immutable value objects, standard `secrets` pour les opérations adaptées à ce module, clients de bibliothèques crypto éprouvées.

**Règle d'ordre** : fonction pure → objet de valeur → petit service/port → composition. Ne créer une hiérarchie profonde ou un framework de plugins qu'après une pression de conception identifiée.

### 21.1 Example : port minimal (pseudocode pédagogique)

```python
from typing import Protocol

class Authenticator(Protocol):
    async def verify(self, request: "AuthenticationRequest", context: "TrustedAuthContext") -> "AuthenticatorOutcome":
        """Verify evidence under an already established trusted context."""
        ...
```

Cette signature **n'est pas** l'API publique figée. Le `TrustedAuthContext` doit être construit par une source autorisée ; il ne doit pas contenir de `trust_profile` sélectionné directement par une valeur de token non vérifiée.

### 21.2 Example : composition (pseudocode)

```python
# Design sketch: names and constructors are illustrative.
engine = AuthenticationEngine(
    authenticators=approved_authenticators,
    trust_resolver=trusted_resolver,
    result_policy=authentication_policy,
)
result = await engine.authenticate(request)
```

Dans le code effectif, ne pas accepter une liste arbitraire de plugins chargés automatiquement ; la composition est une décision explicite de l'application et doit respecter les contrôles de sécurité.

## 22. Runtime et infrastructure

- `asyncio` : annulation et timeout doivent être définis pour les appels réseau/providers ;
- concurrence : aucun `engine.current_user` ni `engine.current_tenant` partagé entre appels ;
- processus multiples : un store mémoire local n'assure pas une révocation globale ;
- gestion mémoire : pas de garantie d'effacement physique des secrets offerte par un objet Python ;
- horloges : la dérive et les conversions UTC doivent être contrôlées ;
- disponibilité : les dépendances externes tombent en panne ; l'état de panne ne doit pas être confondu avec l'authentification ;
- logs/traces : redaction et propagation de corrélation sans exposer les preuves ;
- deployment : librairie utilisable par application, CLI, worker, API, agent ou service.

## 23. Trust boundaries : la carte précède le code

| Frontière | Source risquée | Question à poser | Test nécessaire |
|---|---|---|---|
| Client → hôte | identifiants, headers, token | Extraction ≠ validation ? | valeurs forgées et surdimensionnées |
| Hôte → PyAuthKit | application/tenant hints | Qui a établi le scope ? | tenant spoofing |
| Core → Credential Store | identifiant/credential | Lookup sous bon scope et bon statut ? | cross-tenant |
| Core → KeyResolver | `iss`, `kid`, `jku` | Sources et algs approuvés ? | injection de JWK URL et algorithm confusion |
| Authenticator → Result | verdict partiel | Qui peut produire `VerifiedSubject` ? | success fabriqué |
| Core → Telemetry | données d'essai | Secrets et PII exclus ? | inspection des événements |
| Core → IAM | subject + provenance | Résolution IAM explicite ? | scope mismatch |
| IAM → Authorization | permissions/scopes | Authn ≠ authz ? | permission denied malgré authn OK |
| Composition → Plugins | code tiers | Politique d'activation explicite ? | plugin inconnu refusé |

**Un `kid` peut désigner une clé parmi les clés autorisées d'un profil donné ; il ne peut pas devenir à lui seul l'autorité choisissant la source distante de confiance.**

## 24. Modèle minimal des invariants (à confirmer dans `07`)

| ID pédagogique | Invariant candidat | Cas de test négatif |
|---|---|---|
| `AUTH-LINV-01` | Aucune réussite sans preuve vérifiée et policy satisfaite | accepted on unverified claim |
| `AUTH-LINV-02` | Tout résultat authentifié appartient à un scope de confiance établi | spoofed tenant accepted |
| `AUTH-LINV-03` | Toute sélection de clés/alg est bornée par config trusted | alg confusion |
| `AUTH-LINV-04` | Une preuve expirée ou révoquée est refusée sous les règles applicables | expired credential |
| `AUTH-LINV-05` | Un challenge non consommable ne peut pas réussir | OTP replay |
| `AUTH-LINV-06` | Le flux n'élève pas implicitement le niveau d'assurance | unverified MFA claim |
| `AUTH-LINV-07` | Une erreur infrastructure ne se convertit jamais en réussite | KeyResolver unavailable |
| `AUTH-LINV-08` | Un résultat n'implique aucune permission de ressource | role missing |
| `AUTH-LINV-09` | Les événements ne contiennent pas de secret brut | token in log |
| `AUTH-LINV-10` | L'ajout d'un plugin n'élargit pas silencieusement les mécanismes acceptés | unapproved plugin |
| `AUTH-LINV-11` | Les opérations one-time sont atomiques dans leur scope | concurrent consume |
| `AUTH-LINV-12` | Changer de configuration ne valide pas rétroactivement une preuve passée | stale trust profile reuse |

**Ces identifiants `AUTH-LINV-*` sont locaux à la convention et illustratifs.** Ils ne remplacent pas les exigences `SEC-*` de `01`, ni les invariants définitifs du futur document `07`.

---

## 25. Design Learning Card : `AuthenticationEngine`

**Business/Security Problem.** Les applications ne devraient pas dupliquer la sélection et l'orchestration de chaque mécanisme d'authentification.

**Domain Role.** Orchestrateur d'authentification ; il **ne possède** ni toutes les validations cryptographiques ni les règles d'autorisation métier.

**Design Pressure.** Plusieurs mécanismes coexistent et nécessitent une sortie stable. Leur preuve et leurs échecs restent spécialisés.

**Principles.** SRP, OCP, DIP, SoC, Explicit Trust, Fail Closed.

**Patterns.** Façade publique possible ; Strategy utilisée par les authenticators lorsqu'ils sont réellement substituables ; orchestration en Application Layer.

**Python.** `async def`, construction par injection explicite, ports `Protocol`, immutable request context.

**Alternative plus simple.** Une fonction `authenticate_password(...)` peut suffire pour un programme ne supportant qu'un mécanisme. Le moteur devient utile lorsqu'il faut unifier plusieurs parcours.

**Anti-pattern.** `GodAuthenticationManager` associant SQL, HTTP, Google, crypto, permissions, audit et UI dans un seul objet.

**Evidence.** Tests d'enregistrement, résolution explicite, résultat normalisé, refus des méthodes inconnues, isolation des tentatives concurrentes ; architecture import rules.

**Statut.** `SPECIFIED` dans la cible `00-03` ; pas de preuve d'implémentation ici.

## 26. Design Learning Card : `Authenticator`

**Problème.** Password, API key et JWT nécessitent des vérifications différentes, tout en étant appelés par un moteur commun.

**Domain Role.** Port de vérification d'evidence par mécanisme.

**Variation.** Mécanisme et dépendances crypto/storage ; pas la règle d'accès à une ressource.

**Principles.** OCP, DIP, LSP, Interface Segregation, Composition.

**Pattern.** Strategy **si** comportements substituables par un contrat unique et résolution indépendante ; Adapter pour déporter API/provider tiers.

**Contrat.** Un authenticator ne produit un outcome positif que s'il a effectivement vérifié la preuve sous un `TrustProfile` autorisé et si son contrat le permet. Il ne choisit pas un autre trust profile en se fondant sur une valeur non fiable.

**Alternatives.** Des fonctions spécialisées peuvent constituer un MVP suffisant ; le registre s'impose lorsque la sélection est un besoin avéré.

**Mécanisme Python.** `Protocol` structurel + fonctions ou classes concrètes injectées ; contrats de cancellation et erreurs.

**Tests.** Toute implémentation passe une suite commune : invalid evidence, unsupported method, scope mismatch, cancellation, dependency failure, no unverified positive outcome.

**Pattern evidence.** Ajouter une nouvelle implémentation agréée ne requiert pas de modifier la fonction centrale d'authentification.

## 27. Design Learning Card : `TrustProfile` et `TrustProfileResolver`

**Problème.** Un JWT peut contenir `iss`, `aud`, `alg`, `kid` ou des métadonnées suggérant une source de clé ; aucune de ces valeurs ne doit définir librement l'autorité à laquelle faire confiance.

**Domain Role.** `TrustProfile` est une configuration de confiance approuvée ; le resolver associe le contexte issu du **routage fiable** aux contraintes et clés autorisées.

**Frontière.** `UntrustedTokenHeader/Claims -> constrained lookup within approved profile -> verified evidence`.

**Distinction.** `ClaimedIssuer != ApprovedIssuer`; `key hint != trusted key source`.

**Principles.** Fail Closed, Least Privilege, explicit trust, Information Hiding, Secure Defaults.

**Pattern.** Resolver est un nom de responsabilité, **pas un pattern GoF**. Un port peut isoler la configuration ; pas de `Strategy` nécessaire si une simple fonction sûre suffit.

**Algorithme.** Résolution scoped, sélection d'un ensemble de profils autorisés, rejet des ambiguïtés, validation des contraintes cryptographiques et de politique.

**Alternatives rejetées.** Télécharger une JWKS URI contenue directement dans le token ; chercher globalement la première clé avec ce `kid` ; accepter librement `alg=none`.

**Preuves.** Tests de confusion de clés/algorithmes, issuer inconnu, mauvais audience, cross-tenant, spoofing de scope, `kid` ambigu, clé absente, timeout réseau.

**Statut.** Candidat majeur décrit dans `03 §9-10/14-16`, à spécifier et qualifier.

## 28. Design Learning Card : `PasswordAuthenticator`

**Problème.** Authentifier un humain sans stocker ni exposer son secret brut et sans introduire de vérification cryptographique improvisée.

**Domain Role.** Vérification de password sous policy et credential record valide.

**Principles.** SoC entre extraction, lookup, password hash verification, policy et résultat ; least privilege.

**Pattern.** Adapter pour le hasher/credential store. Le pattern Strategy ne découle **pas** du mot « Password » mais de l'interchangeabilité au niveau du moteur.

**Python.** Ports typés et fonction de vérification invoquant une bibliothèque éprouvée ; pas de chiffrement/algorithme bricolé.

**Pseudo-séquence.**

```text
claimed identifier
 -> trusted credential namespace
 -> credential record (valid, scoped)
 -> verified password using approved password-hashing library
 -> verified subject
 -> authentication policy
 -> result
```

**Fail cases.** Credential absent/révoqué, secret erroné, hasher configuration invalid, policy unmet, store unavailable. Les réponses publiques et la temporalité sont conçues contre l'énumération de comptes ; ne pas prétendre éliminer tous les canaux temporels.

**Tests.** Wrong password, disabled credential, malformed record, no raw secret in repr/logs, replay/guessing protections dans l'hôte, authenticator substituable.

**Anti-pattern.** `hash(password) == saved_hash` en Python natif, MD5/SHA brut en remplacement d'un password-hashing adapté, journaliser le password.

## 29. Design Learning Card : `APIKeyAuthenticator`

**Problème.** Authentifier un client/service avec une clé révocable et correctement scindée par tenant/application.

**Domain Role.** Vérification de possession d'un secret API valide dans le namespace prévu.

**Lifecycle.** Génération sécurisée, stockage sous forme protégée, rotation, expiration, révocation, éventuellement scopes **à traiter comme restrictions de credential**, pas autorisation métier universelle.

**Principles.** Least Privilege, scoped lookup, information hiding, fail-closed.

**Design.** `ApiKeyCredential` pour l'artefact ; `CredentialRecord` pour métadonnées/cycle de vie ; `CredentialStore` comme port ; authenticator vérifie.

**Algorithmic Concern.** Lookup sous scope, hash/verification adapté à la nature et entropie de la clé, vérification de statut et temporelle ; ne pas faire dépendre un accès d'un simple préfixe public.

**Trade-off.** Clés opaques + hash en base vs jetons autoportés ; révocation et opérations différeront. Ne pas les rendre interchangeables sans contrat.

**Tests.** Clé inconnue, expirée, révoquée, tenant différent, mauvaise intégration, rotation, fuite via exceptions/logs, accès concurrent lors de révocation.

**Anti-pattern.** Enregistrer la clé brute ; clé globale accessible dans plusieurs tenants sans politique de lien explicite ; traiter API key comme une permission RBAC.

## 30. Design Learning Card : `JWTAuthenticator`

**Problème.** Vérifier un token signé sans accepter des claims non vérifiés comme preuve de sujet ou comme configuration de confiance.

**Distinction.** `JWT` est un format ; le fait qu'un token soit syntaxiquement valide ne prouve rien. Un JWT peut porter différents types de jetons dont l'usage est déterminé par le protocole et le profil de validation.

**Domain Role.** Authenticator/validator d'une preuve JWT **sous un TrustProfile donné**.

**Principles.** Explicit Trust, Fail Closed, Segregation of Concerns, Secure Defaults.

**Verifications candidates.** Type/usage attendu, signature, algorithme autorisé lié à la clé, issuer, audience, validité temporelle, conditions de `nbf/exp`, claims nécessaires, profils d'application, protection contre confusion entre types de JWT.

**Algorithme (conceptuel).**

```text
Host trusted context
  -> allowed token profile(s)
  -> bounded parse (untrusted)
  -> approved key selection within profile
  -> cryptographic verification via maintained library
  -> mandatory claims + audience/issuer/time validation
  -> verified subject -> normalized result
```

**Architectural Pattern.** Adapter vers bibliothèque JWT/JWK et key store ; pas de parser JWT maison.

**Alternatives rejetées.** `decode(..., verify=False)` ; construire une URL JWKS à partir de `jku` non autorisé ; considérer que `sub` suffit ; audience non contrôlée.

**Tests.** Signature falsifiée, algorithme inattendu, issuer/audience incohérents, expiré, absent, `kid` arbitraire, cross-JWT confusion, key rotation, clock skew explicite, failure of key resolver.

## 31. Design Learning Card : `AuthenticatorRegistry`

**Problème.** Ajouter une nouvelle méthode sans écrire une chaîne centrale `if provider == ...`.

**Domain Role.** Registre d'instances activées et sélection de capacités autorisées par configuration.

**Principles.** OCP, DIP, explicit configuration, least privilege.

**Pattern.** Registry idiom ; Factory **si** le registre crée des instances ; Strategy par délégation aux authenticators. Ne pas multiplier les patterns sans besoin.

**Algorithme.** Mapping `(method, scope/profile) -> authenticator` ou équivalent ; définir collisions, précédence, override et gel de configuration.

**Risques.** Plugin malveillant ou non qualifié ; auto-discovery non maîtrisée ; sélection dépendant de headers/claims non fiables ; mutable registry en cours de tentative.

**Tests.** Double registration rejected or explicitly resolved, unknown method rejected, approved-only providers, concurrent reads consistent, plugin added without core edit.

## 32. Design Learning Card : `AuthenticationPolicy`

**Problème.** Une méthode peut prouver un sujet, mais ne pas satisfaire l'assurance demandée pour **l'authentification en cours**.

**Responsabilité.** Définir les contraintes de cérémonie et d'acceptation de la preuve ; la décision d'accès à une ressource demeure extérieure.

**Domain Role.** Domain Policy ou Application Policy selon si elle exprime une règle intrinsèque à l'authentification ou une exigence de l'hôte.

**Examples.** `requires_verified_factor`, `requires_fresh_authentication`, `challenge_required`, `accepted_methods` - sans en déduire un RBAC interne.

**Patterns.** Policy Object ; Strategy si plusieurs politiques interchangeables le justifient ; Specification uniquement si composition logique utile.

**Trade-off.** Un simple ensemble de règles explicites peut être préférable à un langage de policy générique.

**Security Tests.** Preuve valide mais assurance insuffisante ; policy absente ; mismatch between profile and outcome ; step-up demandé mais non accompli.

**Anti-pattern.** `AuthenticationPolicy.can_edit_invoice(user)` : cette question est celle de l'autorisation métier.

## 33. Design Learning Card : `AuthenticationResult`

**Problème.** `True/False` est insuffisant pour représenter refus, challenge, provenance ou indisponibilité ; un booléen ne protège pas des états incohérents.

**Domain Role.** Résultat public sémantiquement normalisé.

**Candidate variants.** `Authenticated`, `Denied`, `ChallengeRequired`, `OperationalFailure` selon taxonomie à accepter dans `08/24`.

**Principles.** Explicit Modeling, type safety, information hiding.

**Pattern.** Result Object / discriminated union, pas GoF. Une `dataclass(frozen=True)` ou des types distincts peuvent rendre des états impossibles à construire.

**Invariant.** Un résultat `Authenticated` contient un subject vérifié et une policy satisfaite ; un refus ne contient pas par accident un principal utilisable ; une erreur infrastructure n'est pas un succès.

**Python.** `dataclass(frozen=True)`, `Enum` ou unions typées ; constructors/factories restreints si nécessaire.

**Tests.** Matrice exhaustive de combinaisons d'états ; `None principal` en refus ; aucune fuite de secret dans repr/serialization ; error categories stable.

## 34. Design Learning Card : `VerifiedSubject` et `AuthenticatedPrincipal`

**Problème.** Le code a besoin d'un objet « sujet authentifié » sans confondre une chaîne `user_id`, un sujet externe vérifié et un compte interne IAM.

**Domain Role.** Valeur vérifiée sous un mécanisme, un scope et une provenance. L'objet public peut ajouter le contexte normalisé de l'authentification.

**Truth Boundary.** Le principal ne devient fiable **qu'à la sortie du mécanisme et des contrôles transverses**.

**Concepts.** Explicit state transition, Value Object candidat, anti-corruption boundary avec IAM.

**Python.** Types distincts pour claimed/verified ; champs immuables ; factories internes contrôlées si nécessaires ; éviter un constructeur public autorisant `verified=True` sur demande.

**Tests.** Impossible de construire un succès public depuis une simple claim via API normale ; provenance conservée ; two tenants remain distinct ; IAM absent ne bloque pas l'authentification.

**Anti-pattern.** `Principal(subject=request.headers["X-User"], authenticated=True)`.

## 35. Design Learning Card : `AuthenticationAttempt`

**Problème.** Relier les événements d'une tentative sans stocker les preuves brutes et gérer des issue multiples.

**Domain Role.** Entity **candidate** identifiée par `attempt_id`, selon besoins effectifs d'état et d'audit.

**Considerations.** `started_at`, `method`, sanitized failure reason, trusted scope, status, correlation ID ; conservation limitée à l'utile.

**Pattern.** Pas automatiquement Aggregate Root ni Event Sourcing. Un simple identifiant de corrélation avec événements structurés peut suffire au MVP.

**Alternatives.** Agrégat persisté vs traces structurées ; arbitrer selon audit, concurrence, observabilité et obligations de minimisation.

**Tests.** Plusieurs tentatives parallèles, aucun secret dans événements, pas de confusion entre tentative et session, délais et retentions.

## 36. Design Learning Card : `AuthenticationChallenge` et MFA

**Problème.** Une authentification peut nécessiter plusieurs interactions ; les étapes doivent être liées à la même tentative et protégées contre le replay.

**Domain Role.** Challenge / continuation avec statut, TTL, scope, tentative, facteurs vérifiés.

**Patterns.** State machine de base ; GoF State **uniquement** si comportements polymorphes deviennent nécessaires ; Workflow/Pipeline optionnel ; State != état stocké.

**Invariant.** Challenge expiré, déjà consommé ou lié au mauvais sujet/tenant => refus. Les facteurs doivent être **réellement vérifiés** ; un risque élevé n'est pas un facteur supplémentaire.

**Algorithmic Concern.** Transition atomique, essais bornés, données aléatoires cryptographiquement adaptées, fenêtres temporelles et protection anti-replay.

**Security Caveat.** Un code OTP reçu par email/SMS n'est pas automatiquement équivalent à un authenticator cryptographique fort ni à une résistance au phishing.

**Tests.** Two simultaneous consumes, invalid code, expired challenge, unknown attempt, different tenant/device, replay, step-up absent, cancellation.

**Scope.** Post-MVP selon `01 §13.3` ; ce document ne prétend pas une implémentation actuelle.

## 37. Design Learning Card : `AuthenticationSession`

**Problème.** Maintenir une continuité d'authentification tout en permettant expiration, renouvellement, révocation et rotation.

**Domain Role.** Aggregate **candidat** lorsqu'il faut protéger des invariants de cycle de vie ; sinon simple état dans un store adapté.

**Distinctions.** Session de navigateur ≠ token bearer ; session établie ≠ autorisation immuable ; session state ≠ GoF State Pattern.

**Policy.** Durées de vie, inactivity timeout, absolute timeout, revoke-all, binding éventuel au client, policy update, step-up recency.

**Runtime.** Concurrence entre refresh et revoke, rotation atomique, stockage partagé, gestion cohérente de l'expiration.

**Tests.** Session fixation, stolen token handling, refresh after revoke, concurrent refresh, expire at boundary, cross-tenant lookup, missing store.

**Pattern.** Repository/Store port si persistance requise ; UoW ou CAS si plusieurs mutations atomiques ; aucun Event Sourcing nécessaire.

## 38. Design Learning Card : `TokenManager`

**Problème.** Émettre, stocker, valider, renouveler et révoquer des artefacts sans considérer que tout token est un JWT.

**Domaine.** Token issuance/validation peut être une capacité distincte de la vérification initiale d'evidence.

**Distinctions.** JWT = format ; access token, ID token, refresh token, challenge token = rôles différents. Un ID token OIDC **n'est pas** automatiquement un access token destiné à n'importe quelle API.

**Policies.** Audience, purpose, lifetime, scope, revocation, signature, token binding si besoin, key rotation.

**Security.** Vérification adaptée à chaque type, interdiction de confusion entre usages, pas de token brut en audit, secret-handling.

**Tests.** Wrong token type/audience, refresh replay, revocation, expiration, key rotation, signing failure, distinct trust context.

**Phase.** Modèle avancé ; le MVP peut seulement **valider** des JWT sous profil sûr sans fournir un serveur complet d'émission.

## 39. Design Learning Card : fédération OIDC et Social Login

**Problème.** Déléguer une authentification à un IdP externe tout en gardant le contrôle de la validation et de l'association d'identité.

**Rôle.** Adapter OIDC/provider, validation du protocole, production d'un `VerifiedSubject` portant le contexte de fédération.

**Distinctions.** `OAuth authorization grant != user authentication` ; social login est une expérience fournisseur, pas un modèle de domaine autonome.

**Protocol expectations.** Contrôle de `state`, `nonce` quand requis, `PKCE` pour les flows concernés, redirect URI approuvées, issuer, audience, signature, claim semantics et association explicite du sujet externe.

**Patterns.** Adapter / Anti-Corruption Layer ; facade côté hôte ; pas de `GoogleUser` comme superclasse canonique de `Principal`.

**Tests.** Login CSRF, replay, mauvais nonce/state, issuer/audience inattendus, subject collision entre providers, IdP unavailable, metadata poisoning, host callback mismatch.

**Phase.** Post-MVP, pas une prétention de conformité OIDC.

## 40. Design Learning Card : WebAuthn / passkeys

**Problème.** Authentifier par preuve cryptographique liée à un authenticator, un challenge et au contexte du relying party.

**Domain Role.** Authenticator WebAuthn utilisant une bibliothèque/protocole spécialisés, credential record lié à un sujet, challenge store sécurisé.

**Boundary.** Browser/client fournit une assertion ; le serveur valide challenge, origin, RP ID, signature, credential/public key et autres contraintes requises par la cérémonie.

**Patterns.** Adapter vers bibliothèque WebAuthn, challenge state machine si besoin ; pas d'algorithme cryptographique maison.

**Claims not allowed.** « passkey disponible » ≠ « toutes les exigences d'un niveau d'assurance donné sont atteintes » ; l'assurance dépend du contexte/cérémonie et du référentiel invoqué.

**Tests.** Wrong RP ID/origin, challenge replay, credential mismatch, expired challenge, clone/signal anomalies selon modèle, two-tenant credential confusion.

**Phase.** Post-MVP.

## 41. Design Learning Card : `Machine / Workload / Agent Authentication`

**Problème.** Un service, container ou agent doit prouver sa propre identité sans se faire passer automatiquement pour un utilisateur humain.

**Distinctions.** Service identity, workload identity, agent identity, delegated user authority. Un agent IA n'acquiert pas de permissions parce qu'il est « autonome ».

**Domain Role.** Principals non humains sous des preuves adaptées : certificats, mTLS, workload assertions, API keys, OAuth client credentials ou jetons bornés.

**Trust.** Durée de vie courte lorsque possible, provenance du workload, audience, scope, key rotation, révocation et frontières de délégation.

**Patterns.** Adapters des systèmes de workloads ; policy d'authentification ; délégation explicitement modélisée par PyIAMKit ou l'hôte.

**Tests.** Agent impersonating user, wrong audience, stolen credential, expired assertion, namespace mismatch, step-up non applicable, revoked delegation.

**Integration.** PyAgentsKit peut utiliser le subject vérifié ; PyIAMKit décide ce que cet agent est autorisé à faire.

## 42. Design Learning Card : `Tenant / Realm / TrustedScope`

**Problème.** Deux tenants peuvent avoir même `subject`, `kid`, email, nom de clé ou issuer affiché sans partager la même autorité de confiance.

**Domain Role.** `TrustedScope` définit la partition d'authentification établie par l'hôte et sa configuration.

**Pattern.** Value/Context Object candidat, scoped resolver ; ni Strategy ni Aggregate obligatoires.

**Principles.** Fail Closed, Explicit Trust, Secure Defaults, Isolation.

**Algorithm.** Résoudre un scope depuis un routage fiable ; sélectionner seulement ses profils/credential namespaces ; rejeter 0 ou N profils lorsqu'un profil unique est obligatoire.

**Tests.** Forged tenant header, cross-tenant `kid` collision, credential present in tenant A and requested in B, cross-tenant fallback when provider fails.

**Do not do.** `trusted_tenant = request.body["tenant_id"]`.

## 43. Design Learning Card : `AuthenticationEvent` / Audit

**Problème.** Retracer les succès, refus et erreurs sans exposer passwords, API keys, bearer tokens, PII inutile ou détails facilitant l'attaque.

**Domain Role.** Événement factuel et minimal ; un `AuthenticationFailed` ne signifie pas nécessairement un événement métier persistant de longue durée.

**Patterns.** Domain/Event Notification ; Observer *possible* pour l'abonnement ; transport Kafka et broker ne définissent pas le modèle d'événement.

**Important.** Événement produit != événement livré durablement. Si la durabilité est une exigence, traiter explicitement retry, outbox, idempotence et erreurs.

**Privacy.** Champs allowlist, payload spécifique par type, redaction, rétention, permissions d'accès, correlation IDs.

**Tests.** Log capture, event schema, secrets and claims filtering, handling of sink outage, sequence consistency, success not dependent on unsafe logging.

## 44. Design Learning Card : `Plugin / Adapter` et supply chain

**Problème.** Un fournisseur custom doit être intégrable sans modifier le core, mais exécuter un plugin Python revient à exécuter du code potentiellement privilégié dans le processus hôte.

**Domain Role.** Extension sous contrat et activation explicite ; la confiance dans le plugin est une décision d'exploitation.

**Principles.** Open/Closed, DIP, explicit dependencies, least privilege, supply-chain security.

**Patterns.** Adapter/Strategy pour la fonctionnalité ; microkernel seulement si les exigences du système de plugins le justifient.

**Threats.** Automatic entry point discovery, malicious dependency, API token exfiltration, global state mutation, bypassing result normalization.

**Controls.** Liste d'extensions approuvées, pinning et revue des dépendances, contracts + security tests, version compatibility, isolation lorsque pertinente. `Protocol` assure au mieux une propriété de forme ; il **ne sandboxe pas** du code Python.

**Tests.** Unknown plugin rejected, registration collision, denied privileges, no leaked secrets, mismatch of declared capabilities, incompatible version.

---

## 45. Trois parcours MVP complets : méthode de revue

Les parcours suivants sont des **références de raisonnement**, non des tests actuellement passés. Chaque ligne doit pouvoir être reliée aux specs, au code et à un cas de test réel lors de l'implémentation.

### 45.1 Password

```text
PROBLÈME        : prouver un sujet humain par password
TRUST BOUNDARY  : input -> credential store scoped -> verifier
INVARIANTS     : record valide, preuve vérifiée, aucune fuite
DESIGN         : PasswordAuthenticator + CredentialStore port
PATTERN        : Strategy au niveau engine si autres methods
PYTHON         : async contract + hasher adapter
TESTS          : wrong/valid/revoked/unknown/store down/log sanitization
RESULT         : VerifiedSubject or typed non-success
```

### 45.2 API key

```text
PROBLÈME        : prouver client/service par secret révocable
TRUST BOUNDARY  : opaque key -> scoped record verification
INVARIANTS     : tenant scope, expiration, rotation, revocation
DESIGN         : APIKeyAuthenticator + record lifecycle
PATTERN        : Adapter/Repository if storage justified
PYTHON         : Protocol + guarded lookup + immutable outcome
TESTS          : wrong key, other tenant, revoked, expired, outage
RESULT         : non-human verified subject or typed non-success
```

### 45.3 JWT

```text
PROBLÈME        : accepter une assertion signée attendue
TRUST BOUNDARY  : untrusted token -> trusted profile -> crypto
INVARIANTS     : expected issuer, audience, alg, claims, time
DESIGN         : TrustProfileResolver + JWTAuthenticator
PATTERN        : Adapter for crypto/key-source; resolver is a role
PYTHON         : typed profile + maintained JWT library
TESTS          : signature, alg, kid, jku, iss, aud, exp, nbf, outage
RESULT         : proven subject preserving accepted scope
```

### 45.4 Retrospective obligatoire après chaque parcours

- Le design sait-il expliquer **comment** une preuve devient vérifiée ?
- La surface d'attaque a-t-elle grandi avec l'abstraction ?
- Un test de refus peut-il contourner l'engine ou l'adapter ?
- Le mode de panne d'un store et celui d'une mauvaise preuve sont-ils différenciés sans fuite au client ?
- Le résultat est-il stable sans effacer les différences de garantie ?
- L'exemple est-il en Python pur, sans import de framework Web ?

## 46. Parcours post-MVP : documenter avant de construire

| Capacité | Nouveau problème | Nouveau concept | Qualification particulière |
|---|---|---|---|
| TOTP/MFA | plusieurs preuves, assurance | challenge + factors | anti-replay, independence, assurance |
| Sessions | continuité et révocation | session lifecycle | fixation, rotate, concurrent revoke |
| Token issuance | artefacts différents | token purpose/policy | type confusion, audience, rotation |
| OIDC | IdP externe + redirect flow | federation + ACL | state, nonce, PKCE, issuer, callback |
| SAML | assertion fédérée entreprise | federation adapter | signature, audience, recipient, replay |
| WebAuthn | preuve asymétrique sur challenge | passkey credential + challenge | RP ID, origin, challenge binding |
| mTLS | preuve au transport | certificate trust binding | certificate path, client identity |
| Adaptive auth | risque et step-up | risk evaluator + policy | no silent assurance elevation |
| Agent delegation | sujet agissant pour un autre | delegation context | no implicit user permission |
| Advanced multi-tenant | plusieurs authorities | realm/trust scope | isolation and key confusion |

Aucun de ces parcours n'autorise à élargir le MVP sans décision formalisée et mise à jour de la roadmap.

## 47. Exemple comparatif : simple fonction vs Strategy

### 47.1 Solution simple

```python
# Illustration conceptuelle. La vérification effective est déléguée
# à une implémentation sûre, non fournie par cet extrait.
async def authenticate_password(request, verifier):
    return await verifier.verify(request)
```

Pour un script ne gérant qu'un mécanisme, cette solution peut être optimale.

### 47.2 Pression de conception réelle

Une application exige Password, API Key et JWT, chacun avec des dépendances et politiques spécifiques, et l'utilisateur du moteur souhaite **un contrat stable**.

### 47.3 Solution par composition

```python
# Pseudocode : la résolution de méthode doit être bornée par le
# trusted context et une configuration de mécanismes approuvés.
class AuthenticationEngine:
    def __init__(self, registry):
        self._registry = registry

    async def authenticate(self, request, trusted_context):
        authenticator = self._registry.resolve(
            method=request.method,
            trusted_context=trusted_context,
        )
        return await authenticator.verify(request, trusted_context)
```

**Avertissement** : ce squelette démontre la *substitution*, pas une implémentation sécurisée complète. Le vrai moteur doit encore vérifier les preconditions de confiance, appliquer la policy, normaliser le résultat et traiter les erreurs avec des postconditions fail-closed. Ne pas copier ce code comme authenticator de production.

### 47.4 Leçon

`OCP + DIP` peuvent rendre pertinent un comportement substituable ; `Strategy` est nommé **après** avoir démontré cette variation. Le coût introduit : registre, contrats, indirection, tests de conformité et revue de sécurité des extensions.

---

## 48. Testing : chaque propriété de design a une preuve

| Objectif | Test recommandé | Exemple PyAuthKit |
|---|---|---|
| Invariant local | Unit / negative test | pas de sujet en cas de preuve invalide |
| Substitution | Contract test | tous les authenticators respectent outcome semantics |
| Frontière de confiance | Security / adversarial test | `tenant_hint` ne modifie pas trusted scope |
| Sémantique temporelle | Boundary test | `expires_at` atteint / `nbf` futur |
| Atomicité | Concurrency test | two challengers consume same OTP |
| Propriété globale | Property-based test | aucun input arbitraire ne construit un success non vérifié |
| Adapter | Integration test | store down, wrong schema, errors mapped |
| Architecture | Dependency/import test | core n'importe pas FastAPI/SQLAlchemy |
| Protocole | Conformance test | JWT/OIDC/WebAuthn selon profil exact |
| Observabilité | Privacy test | aucune chaîne de secret/token dans events |
| Performance | Benchmark | volume de vérifications sous profil mesuré |
| Déploiement | Smoke/packaging test | package fonctionne en Python pur |
| Release | Evidence audit | commit, CI, build, tests, artefacts cohérents |

Une validation « happy path » **ne suffit jamais** pour une surface de sécurité.

## 49. Tests d'invariants : syntaxe standard

Pour chaque invariant : `ID`, `meaning`, `trusted inputs`, `untrusted inputs`, `preconditions`, `scope`, `positive case`, `negative case`, `boundary case`, `concurrency case if applicable`, `failure semantics`, `test references`.

**Exemple : `AUTH-LINV-03` - JWT trust selection**

```text
Premise    : TrustedScope is established independently of JWT contents.
Positive   : expected issuer + audience + allowed signing key -> verified.
Negative   : token-provided key URL is not followed as trust authority.
Boundary   : absent key / unexpected algorithm / ambiguous kid -> no success.
Failure    : key source unavailable -> operational failure, not authentication.
Evidence   : security test IDs + tested library version + CI run.
```

Tous ces cas demeurent des **tests à écrire** tant qu'aucune exécution du dépôt n'est vérifiée.

## 50. Property-Based Testing : génération sous contraintes

Propriétés candidates :

1. Une chaîne de bytes arbitraire n'est jamais une réussite JWT sans validation de signature et claims appropriés.
2. Aucun `tenant_hint` arbitraire ne permet un lookup hors `TrustedScope`.
3. Pour toute preuve expirée selon les règles d'horloge applicables, le résultat n'est pas authentifié.
4. Pour deux tentatives concurrentes consommant le même challenge one-time, au plus une peut réussir si le contrat l'exige.
5. Toute erreur de dépendance produit un état non authentifié.
6. Pour tout credential révoqué selon la source autoritative attendue, aucune nouvelle authentification acceptée ne peut être obtenue.
7. La sérialisation d'un événement n'inclut jamais les classes de secrets bannies.
8. Un résultat de type `Authenticated` a toujours un sujet vérifié et une provenance minimale conforme au contrat.

**Important** : les hypothèses sont explicites. Un test de propriétés ne démontre ni l'absence universelle de vulnérabilités ni la conformité à un standard entier. Utiliser des données de test non sensibles, borner volumes et temps.

## 51. Security Regression Suites

Groupes recommandés :

```text
security/
  test_input_validation.py
  test_claims_and_trust_profile.py
  test_jwt_algorithm_and_key_confusion.py
  test_scope_and_cross_tenant.py
  test_password_secret_handling.py
  test_api_key_lifecycle.py
  test_error_fail_closed.py
  test_plugin_registration_policy.py
  test_audit_secret_redaction.py
  # post-MVP:
  test_challenge_replay_and_atomicity.py
  test_session_fixation_and_revocation.py
  test_oidc_state_nonce_pkce.py
  test_webauthn_origin_rp_challenge.py
```

Ce squelette est une **organisation pédagogique**, pas un inventaire de fichiers existants. Les méthodes sensibles nécessitent également des revues spécialisées, une veille de dépendances et des mises à jour de sécurité.

## 52. Architecture Fitness Functions

**Règles candidates** :

```text
DOMAIN -> cannot import -> FastAPI / Django / Flask / SQLAlchemy / Redis / HTTP SDKs
APPLICATION -> can depend on -> DOMAIN and abstract PORTS
ADAPTERS -> can depend on -> PORTS / APPLICATION contracts
COMPOSITION ROOT -> can depend on -> concrete ADAPTERS

CORE -> cannot import -> PyIAMKit
CORE -> cannot import -> PyAgentsKit

AUTHENTICATION RESULT -> cannot imply -> authorization granted

ALL APPROVED AUTHENTICATORS -> must pass -> common contract suite
ALL AUDIT EVENTS -> must pass -> secret-redaction schema checks
```

Ces règles peuvent être vérifiées par analyse statique de dépendances, lint, imports, tests de contrats et smoke tests de packaging. L'outil précis (par ex. import graph checker) est secondaire : **la règle est première**.

## 53. Failure semantics : système sûr ≠ succès/échec booléen

| Situation | Résultat architectural candidat | Attention |
|---|---|---|
| Preuve fausse | `DENIED` | minimiser l'information publique |
| Méthode interdite | `DENIED` ou erreur de configuration contrôlée | ne pas déclencher autre authenticator |
| Challenge manquant | `CHALLENGE_REQUIRED` si flow autorisé | jamais créer `AuthenticatedPrincipal` utilisable |
| Provider indisponible | `DEPENDENCY_UNAVAILABLE` | aucun fallback permissif |
| TrustProfile introuvable | `CONFIGURATION_ERROR` ou `DENIED` selon contrat | jamais profil par défaut risqué |
| Plusieurs profils critiques admissibles | `AMBIGUOUS` / configuration invalide | pas de `first()` |
| Token expiré | `DENIED` | validation du temps explicite |
| Credential révoqué | `DENIED` | gestion stale caches/consistency |
| Bug inattendu | `INTERNAL_ERROR` | pas de secret dans l'erreur, pas de succès |
| Cancellation/timeout | opération non réussie | nettoyer état et éventuelle continuation |

La taxonomie définitive relève du document `08` et de l'API `24`. Les contrôles du transport (HTTP 401/403/5xx) se font **dans l'intégration**, non dans le core. `401` et `403` ne doivent pas être confondus avec des exceptions Python du domaine.

## 54. Gestion des secrets, PII et observabilité

Les valeurs suivantes ne sont pas journalisées en clair : passwords, API keys, bearer/refresh/ID tokens, assertions, codes OTP, secrets TOTP, clés privées, seed, cookies de session, headers d'authentification, credential records contenant des secrets.

**Préférer :** IDs opaques de tentative, codes d'événement, méthode générique, scope déjà établi (quand autorisé), durée, statut, identifiant de configuration/version, erreur catégorisée, métadonnées minimisées.

La minimisation de PII et la rétention sont régies par le contexte légal et organisationnel. Le journal d'audit n'est pas une justification pour stocker la preuve elle-même.

## 55. API publique : sémantique avant signature

Chaque méthode publique doit définir :

- préconditions : nature fiable/non fiable des paramètres ;
- postconditions : garanties vérifiables et degré de confiance ;
- erreurs : refus de preuve vs panne opérationnelle ;
- effets de bord : accès au store, événements, transitions ;
- async / cancellation ;
- exigences de concurrence ;
- versioning et compatibilité ;
- données sensibles interdites en logs/repr ;
- exemple de référence en Python pur.

Une signature apparemment simple comme `authenticate(request)` n'est pas complète si la source du trusted context et le profil de policy sont indéfinis.

## 56. Interopérabilité sans dépendances cachées

Les integrations peuvent utiliser FastAPI, Django, Flask, CLI, services, workloads, agents ou SDK spécifiques. L'**application hôte** construit un contexte d'entrée, choisit une configuration approuvée, traite la sortie et décide de l'autorisation en aval.

```text
FastAPI/Django/CLI/Agent host
    -> adapter extracts request
    -> host establishes trusted scope
    -> PyAuthKit authenticates evidence
    -> result: verified principal or non-success
    -> PyIAMKit optionally maps identity and permissions
    -> host enforces authorization separately
```

PyAuthKit ne doit pas dépendre de `request.user`, d'un modèle Django, d'une session Web ou d'une table SQL spécifique.

---

## 57. Convention de nommage : les noms parlent Authentication

**Préférer :**

```text
AuthenticationEngine
AuthenticationRequest
AuthenticationResult
Authenticator
PasswordAuthenticator
APIKeyAuthenticator
JWTAuthenticator
AuthenticatorRegistry
TrustProfile
TrustedScope
CredentialStore
CredentialRecord
AuthenticationPolicy
AuthenticationChallenge
AuthenticationSession
VerifiedSubject
AuthenticatedPrincipal
AuthenticationEvent
```

**Éviter :**

```text
StrategyPatternAuthenticator
AbstractFactoryPattern
GenericAuthenticationManager
AuthenticationGodService
RepositoryImpl
ObserverPatternHandler
MyStatePattern
UniversalSecurityContext
```

`Factory` et `Adapter` peuvent apparaître dans un nom lorsqu'ils décrivent réellement une responsabilité de construction ou de traduction (`OidcProviderAdapter`, `AuthenticatorFactory`), pas seulement pour faire entrer un pattern dans le code.

## 58. Convention docstrings

Les docstrings de contrats structurants peuvent contenir `Responsibility`, `Trust boundary`, `Preconditions`, `Postconditions`, `Failure semantics`, `Design concepts`, `Rationale`, en restant concises.

```python
class Authenticator(Protocol):
    """Verify presented evidence under an established trusted context.

    Contract:
        Never report success on unverified evidence or dependency failure.
        Never choose a new trust authority from untrusted token claims.

    Design:
        Replaceable behavior (Strategy when multiple implementations apply).
        Dependency Inversion through an application-facing port.
    """
    ...
```

Ce bloc n'implique pas que la simple annotation `Protocol` rende l'implémentation sûre. Les postconditions doivent être imposées dans le code et les tests.

## 59. Convention commentaires

Les commentaires expliquent les **raisons** et les **frontières de sécurité**, non ce que la ligne de code décrit déjà.

Mauvais :

```python
# Read the key id.
kid = header["kid"]
```

Meilleur :

```python
# The JWT header is untrusted; a key ID may only select among
# keys already approved by the active trust profile.
```

Un commentaire ne doit pas être une excuse pour laisser une condition de sécurité non testée.

## 60. Convention Learning Tags

Tags facultatifs, utiles dans specs, deep dives, ADR et revues pédagogiques :

```text
[DOMAIN: Credential Verification]
[DDD: Domain Policy]
[PRINCIPLE: Dependency Inversion]
[SECURITY: Explicit Trust / Fail Closed]
[PATTERN: Strategy]
[ARCH: Ports and Adapters]
[ALGORITHM: Scoped Resolution]
[PYTHON: Protocol]
[TEST: Contract + Adversarial]
```

Éviter de les placer sur chaque classe, fonction ou ligne de production. Ils nomment une propriété constatée ou un choix proposé, et **jamais** un badge de conformité automatique.

## 61. Template officiel - Design Learning Card

````markdown
# <Natural Authentication Concept>

## Problem & actor
Qui subit le problème, quelle preuve est attendue ?

## Bounded Context / Authority
Qui possède la règle ou la donnée et quel est le contrat publié ?

## Trust Boundary
Quelles données sont déclarées, lesquelles sont établies ?

## Domain Role / Invariants
Entity, Value Object, Policy, Service, Port, Event, etc.

## Temporal / Concurrency Dimension
Expiration, rotation, révocation, replay, état concurrent, horloge.

## Design Pressure
Quelle variation/contrainte observée justifie ce design ?

## Principles
SOLID, SoC, explicit trust, fail-closed, etc.

## Algorithm / Data Structure
Parsing, lookup, comparison, transition, indexation, etc.

## Pattern(s), if genuinely applicable
Quel problème résout le pattern, preuve de sa présence ?

## Natural Python Contract
Protocol, dataclass, fonctions, enums, exceptions, async.

## Simplest Alternative & Rejected Options
Pourquoi une solution plus simple suffit ou ne suffit plus ?

## Failure Semantics & Security
Que se passe-t-il pour INVALID / UNAVAILABLE / AMBIGUOUS ?

## Tests & Evidence
Cas positifs, négatifs, frontières, propriétés, liens CI/commit.

## Explainability & Provenance
Quelles raisons et références conserver sans divulguer la preuve ?

## Implementation Status
CONCEPTUAL | PROPOSED | SPECIFIED | ACCEPTED | IMPLEMENTED | TESTED | QUALIFIED | RELEASED
Indiquer la preuve correspondante.
````

**Règle** : une fiche complète est recommandée pour les concepts architecturaux **structurants**, pas pour chaque `Enum`, helper ou fonction simple.

## 62. Template officiel - Pattern Usage Record

````markdown
# Pattern: <Name>

## Intent
## Instances in PyAuthKit
## Real design pressure
## Evidence the pattern is actually present
## Alternatives and trade-offs
## Where not to use it
## Python idioms
## Related tests
## Related ADR / spec
## Status and proof
````

Un catalogue de patterns doit distinguer `PLANNED`, `IN USE`, `REMOVED`, `NOT NECESSARY`. Ne pas marquer `Strategy` comme implémenté sur la seule base d'un diagramme.

## 63. Template officiel - ADR pédagogique et sécurité

````markdown
# ADR-AUTH-XXX - <Decision in natural domain terms>

## Status
Proposed | Accepted | Rejected | Superseded

## Context / Security Problem
## Bounded Context / Responsibility Owner
## Trust Boundary and Threat Assumptions
## Invariants and Failure Semantics
## Temporal / Versioning / Concurrency Constraints
## Design Forces
## Alternatives (including simpler solution)
## Decision
## Principles, Algorithms, Patterns (if applicable)
## Python / Ports / Adapters Impact
## Risk Assessment and Trade-offs
## Tests and Verification Evidence
## Backward Compatibility and Migration
## Documentation and Learning Notes
## Reviewers / Date
````

**Règle** : ADR décide ; spec contractualise ; learning card enseigne ; tests vérifient ; security review évalue. Une seule de ces pièces ne remplace pas les autres.

## 64. Quand rédiger un ADR ?

Un ADR est attendu lorsqu'une proposition :

- change une frontière PyAuthKit/PyIAMKit ;
- introduit une nouvelle source de confiance ;
- sélectionne un modèle de JWT validation / key rotation ;
- modifie des garanties de révocation ou d'atomicité ;
- change une taxonomie de résultats ou d'erreurs publique ;
- introduit un plugin loader ou des capacités dangereuses ;
- transforme un flow stateless en flow stateful ;
- modifie la règle de dépendance ou l'API publique ;
- engage une compatibilité de protocole ou d'assurance revendiquée.

Un changement de nom de variable ne nécessite pas d'ADR.

## 65. Règle `Problem → Evidence → Principle → Pattern`

```text
1. OBSERVED PROBLEM
2. TRUST/SECURITY CONSEQUENCE
3. CURRENT SIMPLE SOLUTION
4. DESIGN PRESSURE
5. ALTERNATIVES
6. PRINCIPLE(S)
7. PATTERN ONLY IF IT FITS
8. IMPLEMENTATION
9. SECURITY + CONTRACT TESTS
10. REVIEW, EVOLVE OR REMOVE
```

**Interdit** : imposer une `AbstractFactory` pour configurer un authenticator simple, ou un `Event Sourcing` uniquement parce que des événements d'audit existent.

## 66. Code review : questions obligatoires pour changements structurants

1. Qui possède le domaine et la responsabilité ?
2. Quelles valeurs viennent du client et lesquelles de la configuration fiable ?
3. Quelle preuve concrète permet le succès ?
4. Quelles règles d'issuer, audience, scope, algorithme, credential status s'appliquent ?
5. Le code peut-il retourner un succès lors d'une panne/ambiguïté ?
6. Quel invariant et quelle frontière de confiance sont touchés ?
7. Le core importe-t-il directement une dépendance framework/provider ?
8. Le pattern proposé correspond-il à une variation réelle ?
9. Une fonction ou une composition plus simple serait-elle meilleure ?
10. Le résultat protège-t-il son état et sa provenance ?
11. Le comportement est-il correct en présence d'expiration, révocation, retry et concurrence ?
12. L'API ou les logs exposent-ils une donnée sensible ?
13. Les tests négatifs et de substitution sont-ils suffisants ?
14. Le statut de qualification est-il étayé par une preuve accessible ?
15. Faut-il modifier une spec, un ADR, une learning card ou un threat model ?

## 67. Anti-patterns PyAuthKit

| Smell / Anti-pattern | Risque | Meilleure orientation |
|---|---|---|
| `GodAuthenticationEngine` | responsabilités et vulnérabilités mêlées | engine orchestrator + ports spécialisés |
| Giant `if/elif` providers | fermeture à l'extension | registry sous configuration explicite |
| Framework Leakage | core dépendant d'une technologie | adapters d'entrée |
| Provider model leakage | types externes dans domaine | anti-corruption adapter |
| `authenticated=True` user supplied | bypass | verified-only result construction |
| Untrusted JWT selects JWK URL | SSRF/issuer confusion | approved trust profile |
| Algorithm confusion | acceptation de signature inadéquate | allowlist alg/key binding |
| Cross-tenant fallback | fuite d'identité | scope boundary et refus |
| Credential in logs | exposition de secrets | event schema allowlist |
| Implicit MFA success | assurance fictive | verified factor record |
| Risk signal as factor | niveau fictif | distinguer observation et preuve |
| Session as authorization | droits périmés ou contournés | authorization decision distincte |
| Auto plugin discovery | code non approuvé exécuté | activation explicite |
| Universal `IdentityProvider` port | ISP violé | petits ports par capability |
| Always-on State Pattern | overengineering | enum + transitions explicites |
| Repository for every object | cérémonie inutile | persistance justifiée par invariants |
| Magic `latest()` policy | résultat non déterministe | version/autorité/context explicites |
| Silent fallback on outage | bypass | fail closed avec erreur typée |
| Homegrown crypto | erreurs cryptographiques | bibliothèques maintenues |
| Boolean explosion | états incohérents | résultat discriminé / state machine |

**Anti-pattern = signal à examiner**, pas interdiction absolue de tout conditionnel ni preuve d'une vulnérabilité sans contexte.

## 68. Convention de traçabilité

Chaîne minimale :

```text
BUSINESS / SECURITY NEED (`00`)
    ↔ REQUIREMENT (`01`: FR/SEC/ARC/NFR/INT)
    ↔ ARCHITECTURE PRINCIPLE (`02`: PRN-*)
    ↔ COMPONENT / TRUST BOUNDARY (`03`: CMP/TB/FIT)
    ↔ DOMAIN OBJECT & INVARIANT (`04-07`)
    ↔ USE CASE / API (`08`, `24`)
    ↔ DESIGN DECISION / ADR / LEARNING CARD
    ↔ TEST ID + CI EVIDENCE
    ↔ RELEASE ARTIFACT (if published)
```

Ne pas inventer un ID `FR-*` ou `SEC-*` pour compléter artificiellement cette chaîne. Ajouter une exigence implique un changement explicite à `01`.

---

## 69. Definition of Ready - concept structurant

Un nouveau composant significatif est **ready** lorsque :

- [ ] son problème d'authentification et ses acteurs sont explicités ;
- [ ] le document source `FR/SEC/ARC` pertinent est identifié ;
- [ ] son bounded context / responsabilité / propriétaire de confiance sont définis ;
- [ ] claimed inputs et trusted inputs sont distingués ;
- [ ] les invariants et états d'échec sont énoncés ;
- [ ] la sémantique des expirations, versions et retries est définie si nécessaire ;
- [ ] une solution minimale et ses alternatives sont examinées ;
- [ ] le port/API est conceptualisé sans dépendance framework inutile ;
- [ ] tests de succès, refus, erreur et limites sont esquissés ;
- [ ] les risques de sécurité résiduels sont nommés ;
- [ ] le statut de décision est `ACCEPTED` ou explicitement `PROPOSED` pour exploration ;
- [ ] le milestone est défini sans prétention de livraison.

## 70. Definition of Done - fonctionnalité d'authentification

- [ ] Contrat et invariants respectés.
- [ ] Aucun succès possible sans preuve vérifiée selon la policy.
- [ ] Scopes, issuer, audience, algorithmes et autorités vérifiés lorsque applicables.
- [ ] Les mauvais inputs, ambiguïtés et indisponibilités donnent un état **non authentifié**.
- [ ] Tests positifs, négatifs, frontières temporelles et fault injection pertinents exécutés.
- [ ] Concurrence/replay/atomicité qualifiés quand l'état est mutable ou consommable.
- [ ] Le core reste indépendant de l'ORM, du framework Web et de PyIAMKit.
- [ ] La nouvelle implémentation respecte les contract tests du port.
- [ ] Les logs, events, exceptions et repr n'exposent pas de preuve brute.
- [ ] Les dépendances cryptographiques sont identifiées, maintenues et adaptées au protocole.
- [ ] Les alternatives et trade-offs sont documentés si l'abstraction est structurante.
- [ ] La documentation publique mentionne les garanties et limites, sans label de conformité abusif.
- [ ] `Implementation status` s'appuie sur commit, tests, CI et périmètre exact.
- [ ] Threat model et ADR mis à jour si la frontière de confiance change.

**Règle d'arrêt** : une capacité de sécurité qui manque un invariant essentiel n'est pas qualifiée, même si 100 % des tests existants passent.

## 71. Definitions of Done spécialisées

### 71.1 Nouvel Authenticator

- [ ] mécanisme et type d'evidence explicités ;
- [ ] `TrustProfile` et sélection de clés établis indépendamment des inputs non fiables ;
- [ ] comportement positif/négatif et erreurs documentés ;
- [ ] contract tests communs + tests spécifiques de protocole ;
- [ ] aucun contournement de policy/normalisation ;
- [ ] plugin non approuvé impossible à activer implicitement.

### 71.2 Nouveau Credential Store

- [ ] lookup scindé par scope ;
- [ ] stockage, statut, révocation et expiration testés ;
- [ ] atomicité/consistency adaptées au contrat ;
- [ ] secrets protégés et permissions minimisées ;
- [ ] panne traduite en résultat/exception typé sans succès ;
- [ ] tests de concurrence et de multi-processus si nécessaire.

### 71.3 Nouveau Challenge ou flow MFA

- [ ] tentative, sujet, tenant/scope et durée de vie liés ;
- [ ] preuve/second facteur réellement vérifié ;
- [ ] consommation et replay traités ;
- [ ] résultats partiels incapables d'accorder un accès ;
- [ ] timeouts/retry/cancellation et reprise définis ;
- [ ] assurance revendiquée justifiée par critères explicites.

### 71.4 Nouvel Adapter IdP

- [ ] protocole et version annoncés ;
- [ ] state/nonce/PKCE et autres protections pertinentes au flow ;
- [ ] issuer, audience, metadata, clés et redirections approuvés ;
- [ ] provenance externe vers `VerifiedSubject` conservée ;
- [ ] cross-provider subject collision et replay testés ;
- [ ] modèle du provider ne contamine pas le domaine.

### 71.5 Nouvelle API publique

- [ ] préconditions, postconditions et types d'erreurs définis ;
- [ ] imports depuis Python pur et documentation d'exemples ;
- [ ] aucune permission IAM implicite ;
- [ ] compatibilité et migration précisées ;
- [ ] charge de maintenance et surface d'attaque évaluées.

## 72. Conventions de release et de preuves

Ne pas utiliser comme qualificatif acquis : « secure », « production-ready », « compliant », « phishing-resistant », « AAL2 », « certified », « stable », sans périmètre et preuve correspondante. Les expressions peuvent être utilisées en **objectif cible** si identifiées comme telles.

**Release note de conception** (gabarit) :

```text
<version> - <capability>
Status: TARGET | IMPLEMENTED | TESTED | QUALIFIED | RELEASED
Code reference: <commit SHA>
Public contracts: <API / spec revision>
Security boundaries covered: <list>
Positive and negative scenarios: <test IDs>
Execution evidence: <CI run + environment>
Dependency versions: <versions>
Residual risks: <list>
Learning outcomes: <principles/patterns really used>
Artifact provenance: <wheel/sdist hashes when published>
```

Une documentation théorique ne certifie ni une release ni un audit externe.

## 73. Carte d'application dans la suite documentaire PyAuthKit

| Document cible | Sujet de conception à enseigner | Frontière/risque à expliciter |
|---|---|---|
| `04_PYAUTHKIT_DOMAIN_OBJECTS.md` | vocabulaire et rôles DDD | claim vs evidence vs verified subject |
| `05_PYAUTHKIT_ENTITIES_AND_VALUE_OBJECTS.md` | identity, VO, entities, aggregates | immutabilité et trusted construction |
| `06_PYAUTHKIT_DOMAIN_RELATIONSHIPS_AND_ERD.md` | cardinalités, ownership | scope et persistance non universelle |
| `07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md` | design by contract, policy | fail-closed, preuve, temporalité |
| `08_PYAUTHKIT_COMMANDS_QUERIES_AND_USE_CASES.md` | application service, command/query | authn sans authz |
| `09_PYAUTHKIT_AUTHENTICATION_ENGINE_MODEL.md` | façade, Strategy, registry | passage fiable de la preuve au résultat |
| `10_PYAUTHKIT_AUTHENTICATOR_AND_CREDENTIAL_MODEL.md` | verifier, credential, store ports | secrets, rotation, révocation |
| `11_PYAUTHKIT_AUTHENTICATION_FLOW_AND_CHALLENGE_MODEL.md` | state machine vs State | replay et transition atomique |
| `12_PYAUTHKIT_MFA_AND_ASSURANCE_MODEL.md` | policy, factor composition | assurance non fictive |
| `13_PYAUTHKIT_SESSION_AND_TOKEN_MODEL.md` | lifecycle, concurrency, identity | fixation, type confusion, révocation |
| `14_PYAUTHKIT_FEDERATION_OIDC_OAUTH_SAML_MODEL.md` | Adapter / ACL / protocol | state, nonce, issuer, audience |
| `15_PYAUTHKIT_WEBAUTHN_PASSKEY_AND_PASSWORDLESS_MODEL.md` | crypto adapter / challenge | origin, RP ID, replay |
| `16_PYAUTHKIT_MACHINE_WORKLOAD_AND_AGENT_AUTH_MODEL.md` | principal et délégation | human != service != agent |
| `17_PYAUTHKIT_ADAPTIVE_AUTH_AND_RISK_MODEL.md` | policy + signal evaluation | signal != factor |
| `18_PYAUTHKIT_PORTS_ADAPTERS_AND_PLUGIN_ARCHITECTURE.md` | ports, DIP, OCP, registry | plugin trust / supply chain |
| `19_PYAUTHKIT_STORAGE_AND_PERSISTENCE_ARCHITECTURE.md` | Repository, UoW/CAS si besoin | scoped stores, atomicité |
| `20_PYAUTHKIT_SECURITY_THREAT_MODEL.md` | threat modeling | adversarial cases, trust boundaries |
| `21_PYAUTHKIT_AUDIT_EVENTS_AND_OBSERVABILITY.md` | domain/integration events | secret redaction, delivery |
| `22_PYAUTHKIT_FRAMEWORK_INTEGRATIONS.md` | driving adapters | trusted host context |
| `23_PYAUTHKIT_PYIAMKIT_INTEGRATION_CONTRACT.md` | bounded-context collaboration | authn ≠ authz, provenance |
| `24_PYAUTHKIT_PUBLIC_API_AND_SDK_DESIGN.md` | façade publique, errors | preconditions et security contracts |
| `25_PYAUTHKIT_CONFIGURATION_MODEL.md` | explicit configuration, composition root | security defaults |
| `26_PYAUTHKIT_TESTING_AND_QUALIFICATION_STRATEGY.md` | tests properties, contracts, fitness | proof/attacks/conformance |
| `27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md` | release boundaries / architectural evolution | MVP vs future specs |
| `28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md` | Python packaging / CI / tests | secure baseline |

Cette table est une **proposition de mapping documentaire** fondée sur la suite prévue dans le projet. Elle ne préjuge pas l'existence de ces fichiers dans le dépôt.

---

## 74. Catalogue pédagogique vivant

Arborescence **possible**, à valider lors du bootstrap :

```text
docs/
  architecture/
  adr/
  domain/
  security/
  learning/
    cards/
    patterns/
    without-vs-with-pattern/
    lessons-learned/
  requirements/
  testing/
```

Pour chaque concept, les liens doivent connecter la fiche de domaine, le cas de test, la décision et le code. Éviter un second référentiel d'objets canoniques en parallèle des specs `04-07`.

## 75. Boucle de pratique délibérée

```text
I DISCOVER
  A signature mismatch under an unexpected issuer.
     |
     v
I EXPLAIN THE THREAT
  The token was able to influence key selection.
     |
     v
I NAME THE DESIGN PRESSURE
  Trust selection must be explicit and scoped.
     |
     v
I CHOOSE THE SIMPLEST VALID MODEL
  Approved trust profile + bounded key lookup.
     |
     v
I IDENTIFY CONCEPTS
  Explicit Trust, Fail Closed, SoC; Adapter if appropriate.
     |
     v
I IMPLEMENT AND TEST
  Wrong issuer, algorithm confusion, key source outage.
     |
     v
I REVIEW THE TRADE-OFFS
  Extra config vs safety and auditability.
     |
     v
I TRANSFER THE LEARNING
  API key tenant isolation, OIDC federation, mTLS scope.
```

**L'apprentissage est achevé lorsqu'on reconnaît la frontière, pas lorsqu'on mémorise le nom de l'interface.**

## 76. Transfert inter-projets

| PyAuthKit | Structure conceptuelle | Autre contexte possible |
|---|---|---|
| `Authenticator` | comportement remplaçable sous contrat | `QualificationPolicy` PySRMKit |
| `CredentialStore` | port de persistance scoped | repository SRM / comptable |
| `TrustProfileResolver` | sélection sûre sous autorité | `AccountRoleResolver` PyAccountingKit *(analogie de résolution seulement)* |
| `AuthenticationPolicy` | policy sous contexte | `PostingPolicy` PyAccountingKit *(règles différentes)* |
| `AuthenticationResult` | résultat discriminé | `ResolutionResult` PyAccountingKit |
| `AuthenticationEvent` | fait/notification | `SupplierQualified`, `JournalEntryPosted` *(sémantiques différentes)* |
| `Challenge` | cycle de vie et gardes | workflow transitions |
| `TrustedScope` | partition de sécurité | bounded context/tenant scope *(à distinguer)* |

**Ne pas copier les classes entre domaines.** La similarité d'une structure de design ne signifie pas équivalence de règles, d'autorité, de gravité des échecs ou de garanties de sécurité.

## 77. Roadmap pédagogique sans roadmap produit fictive

Une progression d'apprentissage **possible**, distincte des versions officielles :

| Étape | Exercice concret | Concepts à observer | Preuve |
|---|---|---|---|
| E0 | langage, demandes et résultats | DDD, VO/DTO, invariants | unit + naming review |
| E1 | kernel + registry | Strategy/OCP/DIP ou alternatives simples | contract suite |
| E2 | Password/API key/JWT | adapter, trust, algorithms | negative security matrix |
| E3 | credential stores | repository/ports, consistency | storage contract tests |
| E4 | sessions + challenges | state machine, temporalité | replay/concurrency tests |
| E5 | OIDC/WebAuthn | federation adapters, protocols | conformance/security tests |
| E6 | agents/tenants/policies | identity boundaries, principal, scope | isolation tests |
| E7 | production integration | observability, CI/release evidence | quality gate review |

Ne pas annoncer des numéros de versions `0.1`, `0.2` ou `v1.0` tant que `27` et les décisions effectives du dépôt ne les ont pas fixés.

## 78. Manifeste PyAuthKit - Design & Learning

1. **Authentication is not authorization.**
2. **Evidence is untrusted until verified.**
3. **A claim never chooses its own authority.**
4. **Trust boundaries before implementation details.**
5. **Explicit trusted scope before credential lookup.**
6. **No success on ambiguous or failed verification.**
7. **A verified subject is not an IAM account.**
8. **Provider names are adapters, not domain foundations.**
9. **Factor observed is not factor verified.**
10. **Assurance is justified, not inferred from a label.**
11. **JWT is a format, not a universal authentication proof.**
12. **OAuth delegated authorization is not OIDC authentication.**
13. **State machine is not GoF State Pattern.**
14. **Domain event is not automatically Observer or Event Sourcing.**
15. **Authentication policies are not RBAC policies.**
16. **Problem first, pattern second.**
17. **Domain names first, design vocabulary in documentation.**
18. **SOLID, KISS and YAGNI must reinforce one another.**
19. **Composition over unnecessary inheritance.**
20. **Ports are valuable when they protect a real boundary.**
21. **Plugins are code, not automatically trusted extensions.**
22. **Never write cryptography merely to teach an algorithm.**
23. **Failures, timeouts and cancellations never authenticate.**
24. **Sessions, tokens and credentials have different lifecycles.**
25. **Time, rotation, revocation and concurrency are first-class.**
26. **Audit without disclosure; privacy without blind spots.**
27. **Security tests must include adversarial inputs.**
28. **Architecture must be enforceable, not only illustrated.**
29. **Documented is not implemented; tested is not certified.**
30. **Understand the problem, prove the behavior, reuse the insight.**

## 79. North Star opérationnelle

> **PyAuthKit sert à établir l'authentification sous des frontières de confiance explicites, et cette responsabilité fournit le terrain d'apprentissage des bons choix logiciels.** Les abstractions sont retenues lorsqu'elles rendent une preuve, un invariant ou une évolution plus sûre, compréhensible et testable. Les patterns sont reconnus après l'analyse du problème. Les contrats sont démontrés par des tests et des preuves, sans transformer une intention documentaire en garantie opérationnelle.

En termes pédagogiques :

```text
DON'T MEMORIZE THE PATTERN.
RECOGNIZE THE TRUST BOUNDARY.
DEFINE THE INVARIANT.
CHOOSE THE SMALLEST SECURE DESIGN.
NAME THE CONCEPT.
TEST THE FAILURE MODES.
REPEAT UNTIL IT BECOMES ENGINEERING JUDGMENT.
```

## 80. Conclusion et décision de gouvernance

Cette convention reprend de PySRMKit l'approche *Problem First, Pattern Second*, le refus du *pattern cargo cult*, le nommage naturel et la répétition par problèmes réels. Elle reprend de PyAccountingKit v2.0 la distinction entre **WHAT/HOW/EVIDENCE**, les deux cartes d'abstraction, le DDD stratégique et tactique, les invariants, l'algorithmique, les trade-offs, la qualification et les preuves.

Elle ajoute des exigences pédagogiques **propres au domaine Authentication** :

- le passage de **claimed evidence** à **verified subject** ;
- la distinction entre configuration de confiance, claims et autorisation ;
- le contrôle de **tenant/scope/issuer/audience/key** ;
- le modèle de refus et de panne **fail-closed** ;
- la confidentialité et l'audit des preuves ;
- le traitement des cycles de vie, du replay et de la concurrence ;
- l'obligation de distinguer **capacité implémentée**, **assurance validée** et **certification revendiquée**.

**Décision à prendre** : accepter cette convention comme référence pédagogique et documentaire pour les travaux `04` à `28`, avec révision continue lorsqu'une spec, un ADR ou les preuves du dépôt montrent un besoin de modification.

---

# Annexe A - Exemple de matrice exigences -> design -> tests

| Besoin / principe documenté | Concept d'architecture cible | Leçon de design | Tests candidats |
|---|---|---|---|
| Authentication core indépendant (`00`, `01`, `02 PRN-02`) | Domain + Application + Ports | SoC, Hexagonal, DIP | imports and pure Python smoke |
| Plusieurs authenticators (`01 §5`, `02 PRN-07`) | Registry + Authenticators | Strategy conditionnelle | contract suite, unknown method |
| Refus sans preuve (`02 PRN-05/06`) | VerifiedSubject / Result | Fail Closed, result object | invalid evidence never succeeds |
| Trust explicite (`02 PRN-04/17`) | TrustedScope + TrustProfile | trust boundary | issuer/alg/key/tenant confusion |
| Observabilité sûre (`02 PRN-13`) | safe AuthenticationEvent | event vs Observer | redact/no raw secret |
| Plugins contrôlés (`02 PRN-14`) | approved registry | OCP vs supply chain | unapproved plugin rejected |
| Multi-tenant sûr (`02 PRN-15`) | scoped stores + trusted resolver | context ownership | cross-tenant isolation |
| Séparation IAM (`00 §6`, `02 PRN-01`) | published principal contract | bounded contexts | authn success + authz denial |

Les numéros exacts de tests et les liens de dépôt ne doivent être renseignés qu'après leur création. Cette matrice n'invente aucune conformité déjà acquise.

# Annexe B - Taxonomie de concepts de référence

```text
AUTHENTICATION DOMAIN
  Claims and Evidence
  Credentials and Records
  Authenticator Verification
  Verified Subject / Principal
  Attempt / Result
  Authentication Policy
  TrustProfile / TrustedScope
  Session and Token lifecycle
  Factor / Challenge / Flow
  Federation
  Authentication Events

STRATEGIC / TACTICAL DDD
  Bounded Context / Context Map / Published Language
  Entity / Value Object / Aggregate / Aggregate Root
  Domain Service / Domain Policy / Domain Event
  Repository / Anti-Corruption Layer

PRINCIPLES
  SOLID / DRY / KISS / YAGNI
  SoC / Information Hiding / Explicit Dependencies
  Low Coupling / High Cohesion / Composition
  Fail Closed / Least Privilege / Secure Defaults / Explicit Trust

DESIGN PATTERNS (WHEN JUSTIFIED)
  Strategy / Adapter / Facade / Factory / Registry idiom
  State / Observer / Decorator / Builder

ARCHITECTURE
  Layered / Hexagonal / Clean
  In-Process Library / Plugins
  CQRS optional / Event Driven optional

ALGORITHMS
  Parsing / Validation / Comparison / Lookup
  Time-window / Indexing / CAS / State Transition
  Key Selection within approved trust set

PYTHON
  Protocol / dataclass / Enum / Callable
  Functions / Composition / async / Exceptions

TESTING
  Invariant / Contract / Adversarial / Property-based
  Temporal / Concurrency / Integration / Architecture / Packaging
```

# Annexe C - Références internes utilisées

1. `00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md` - vision, acteurs, méthodes, pipeline, frontières et MVP.
2. `01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md` - exigences, risques, statuts, critères d'acceptation et jalons candidats.
3. `02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md` - PRN-01..PRN-18, DDD, SOLID, patterns, sécurité et doctrine architecturale.
4. `03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md` - architecture logique, trust boundaries, ports, séquences Password/API Key/JWT, qualification et arbitrages.
5. `PYSRMKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md` - pédagogie par problème réel, anti-cargo-cult, annotations et transfert.
6. `PYACCOUNTINGKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md` - convention v2.0, double cartographie, DDD stratégique, invariants, learning cards, preuve et gouvernance.

Les références PySRMKit et PyAccountingKit inspirent la **méthode**, non les concepts de sécurité du domaine Authentication. Les exemples de sécurité restent des **propositions de design** de PyAuthKit et nécessiteront revue de specs, vérifications de standards et tests avant toute revendication de conformité.

# Annexe D - Questions ouvertes avant implémentation

| Sujet | Décision attendue | Source d'arbitrage |
|---|---|---|
| `VerifiedSubject` / `AuthenticatedPrincipal` | distinction, champs, constructibilité | `04-08`, `24` |
| Source de `TrustedScope` | qui la produit et comment la valide-t-on ? | `03`, `20`, ADR |
| `TrustProfile` | version, sélection, contraintes, clés | `10`, `20`, `25` |
| Outcome / Result | variantes, codes, erreurs publiques | `08`, `24` |
| Password hashing | lib, alg, paramétrage, migration | `10`, `20` |
| API key lifecycle | hash, prefix, revoke, rotation | `10`, `19` |
| JWT accepted usage | ID token/access token/assertion et profils | `10`, `14`, `20` |
| Registry / plugins | composition, gel, politique d'activation | `09`, `18` |
| Transactional challenge | one-time atomicity, expiry, attempts | `11`, `19` |
| Assurance | référentiel précis, conditions de revendication | `12`, `20` |
| Multi-tenant | namespaces, scope, failure isolation | `03`, `19`, `20`, `25` |
| Async / sync façade | garantie de cancellation, I/O, API | `18`, `24` |
| Audit failure | perte tolérable, durabilité, buffering | `21`, `26` |
| MVP freeze | versions, scope et release gates | `27`, `28` |

**Aucune réponse de cette annexe ne doit être présumée décidée simplement parce qu'une classe illustrative apparaît dans ce document.**

# Annexe E - Historique documentaire

| Version | Date | Évolution | Statut |
|---|---|---|---|
| `1.0.0` | 2026-10-28 | Première convention PyAuthKit, synthèse PySRMKit / PyAccountingKit v2, adaptation aux frontières Authentication et aux docs `00-03` | Proposed |

---

**Formule de clôture** : **Domain first. Trust explicit. Pattern only when justified. Security through verifiable evidence. Learning through deliberate practice.**
