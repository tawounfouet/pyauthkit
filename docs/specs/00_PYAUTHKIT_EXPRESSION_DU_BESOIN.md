# 00_PYAUTHKIT_EXPRESSION_DU_BESOIN

## PyAuthKit — Expression du besoin

**Statut :** Document de cadrage initial  
**Type :** Expression du besoin  
**Produit :** PyAuthKit  
**Langage cible :** Python  
**Positionnement :** Moteur générique, modulaire et agnostique d’authentification  
**Écosystème :** Py**Kit / PyIAMKit / PyAgentsKit / applications et services Python

---

# 1. Contexte

L’authentification constitue une primitive transversale de la majorité des systèmes logiciels modernes.

Une application peut devoir authentifier :

- un utilisateur humain ;
- un collaborateur interne ;
- un client externe ;
- un administrateur ;
- une application ;
- un service backend ;
- un workload ;
- un device ;
- un agent logiciel ou agent IA ;
- une identité provenant d’un fournisseur externe.

Les mécanismes d’authentification eux-mêmes se sont fortement diversifiés :

- identifiant / mot de passe ;
- PIN ;
- API Key ;
- token bearer ;
- JWT ;
- OAuth 2.0 ;
- OpenID Connect ;
- SAML ;
- authentification sociale ;
- MFA ;
- OTP / TOTP ;
- magic links ;
- WebAuthn ;
- passkeys ;
- certificats ;
- mTLS ;
- client credentials ;
- assertions signées ;
- authentification adaptative ;
- authentification basée sur le risque ;
- step-up authentication.

Dans de nombreux projets, ces mécanismes sont implémentés directement dans les applications, ou dépendent étroitement d’un framework Web, d’un fournisseur d’identité ou d’une bibliothèque spécifique.

Cette approche entraîne fréquemment :

- une duplication de logique ;
- un fort couplage avec les frameworks ;
- une difficulté à changer de fournisseur ;
- une multiplication des implémentations de sécurité ;
- des modèles de sessions et de tokens incohérents ;
- des difficultés à ajouter de nouvelles méthodes d’authentification ;
- une confusion entre authentification, identité et autorisation ;
- une faible réutilisabilité pour les services, agents et workloads non humains.

Le besoin apparaît donc de disposer d’un **moteur Python d’authentification générique, extensible et indépendant des frameworks et fournisseurs**.

Ce moteur est nommé **PyAuthKit**.

---

# 2. Problème à résoudre

Les applications ont généralement besoin de répondre à une question fondamentale :

> **Comment prouver de manière fiable l’identité du principal qui tente d’accéder au système ?**

Cette question est différente de :

> Qui est cette identité dans l’organisation ?

ou :

> À quelles ressources cette identité peut-elle accéder ?

Ces dernières questions relèvent davantage de l’Identity & Access Management et de l’autorisation.

PyAuthKit doit donc isoler le problème de **l’Authentication** du reste du domaine IAM.

Le produit doit fournir une abstraction homogène permettant de traiter différents moyens d’authentification sans que l’application métier ait à connaître les détails propres à chaque protocole ou fournisseur.

---

# 3. Vision

PyAuthKit doit devenir :

> **Un moteur Python d’authentification provider-agnostic, framework-agnostic et extensible pour les humains, applications, services, workloads, devices et agents.**

Le moteur doit permettre à une application d’exprimer :

```python
result = await auth.authenticate(request)
```

sans dépendre directement du mécanisme utilisé :

```text
Password
Google
GitHub
Microsoft
Passkey
WebAuthn
TOTP
API Key
JWT
Certificate
mTLS
OIDC
SAML
Client Credentials
...
```

Le résultat doit être normalisé sous une abstraction commune.

---

# 4. Objectif principal

L’objectif de PyAuthKit est de fournir un **noyau d’authentification générique** capable :

1. de recevoir une demande d’authentification ;
2. de déterminer la stratégie appropriée ;
3. de valider les credentials ou preuves présentées ;
4. d’exécuter éventuellement plusieurs facteurs ou challenges ;
5. d’appliquer des politiques d’authentification ;
6. d’évaluer le contexte et le niveau d’assurance ;
7. de produire un principal authentifié ;
8. de gérer les artefacts nécessaires à l’authentification :
   - sessions ;
   - tokens ;
   - challenges ;
   - credentials ;
   - facteurs ;
9. de déléguer ensuite la gestion d’identité et l’autorisation à d’autres composants, notamment PyIAMKit.

---

# 5. Positionnement fonctionnel

PyAuthKit se concentre sur :

```text
AUTHENTICATION
     │
     ├── Credentials
     ├── Authenticators
     ├── Authentication Flows
     ├── Challenges
     ├── Factors
     ├── Sessions
     ├── Tokens
     ├── Federation
     ├── Passwordless
     ├── Social Login
     ├── Machine Authentication
     ├── Adaptive Authentication
     └── Authentication Policies
```

PyAuthKit ne doit pas devenir un monolithe IAM complet.

---

# 6. Différence entre PyAuthKit et PyIAMKit

## 6.1 PyAuthKit

PyAuthKit répond principalement à :

> **Peux-tu prouver qui tu es ?**

Il couvre :

- les credentials ;
- les mécanismes d’authentification ;
- les protocoles d’authentification ;
- les facteurs ;
- les challenges ;
- les sessions ;
- les tokens ;
- la fédération ;
- les passkeys ;
- le MFA ;
- l’authentification sociale ;
- l’authentification machine-to-machine ;
- l’évaluation de confiance ;
- l’authentification adaptative.

---

## 6.2 PyIAMKit

PyIAMKit répond principalement à :

> **Qui es-tu dans le système, à quelle organisation appartiens-tu et que peux-tu faire ?**

Il peut couvrir notamment :

- utilisateurs ;
- comptes ;
- identités ;
- groupes ;
- organisations ;
- tenants ;
- rôles ;
- permissions ;
- politiques d’accès ;
- provisioning ;
- deprovisioning ;
- gouvernance des identités ;
- access reviews ;
- gestion du cycle de vie ;
- audit IAM.

---

## 6.3 Relation entre les deux

La relation cible est :

```text
Credentials / Authentication Evidence
                │
                ▼
        ┌──────────────────┐
        │    PyAuthKit     │
        │ Authentication   │
        └────────┬─────────┘
                 │
                 ▼
        Authenticated Principal
                 │
                 ▼
        ┌──────────────────┐
        │     PyIAMKit     │
        │ Identity + IAM   │
        └────────┬─────────┘
                 │
                 ▼
        Roles / Permissions
                 │
                 ▼
          Protected Resource
```

PyAuthKit doit pouvoir fonctionner **sans PyIAMKit**.

PyIAMKit peut en revanche utiliser PyAuthKit comme moteur d’authentification.

---

# 7. Principaux acteurs

PyAuthKit doit supporter plusieurs catégories de principals.

## 7.1 Humain

Exemples :

- utilisateur final ;
- collaborateur ;
- administrateur ;
- partenaire ;
- client.

Méthodes possibles :

- password ;
- passkey ;
- MFA ;
- social login ;
- SSO ;
- magic link.

---

## 7.2 Service

Exemples :

- API backend ;
- microservice ;
- daemon ;
- worker.

Méthodes possibles :

- API key ;
- bearer token ;
- OAuth client credentials ;
- JWT assertion ;
- certificat ;
- mTLS.

---

## 7.3 Application

Une application cliente peut s’authentifier indépendamment de l’utilisateur qu’elle représente.

---

## 7.4 Agent logiciel ou agent IA

Les architectures agentiques nécessitent également une identité authentifiable.

Exemples :

```text
GeneralAgent
FinanceManagerAgent
SalesAgent
HRManagerAgent
AutomationAgent
```

Les agents peuvent utiliser :

- workload identity ;
- delegated credentials ;
- signed tokens ;
- API keys ;
- client credentials ;
- short-lived tokens ;
- certificates.

---

## 7.5 Device

Exemples :

- poste de travail ;
- mobile ;
- serveur ;
- device IoT.

---

## 7.6 Workload

Exemples :

- container ;
- VM ;
- Kubernetes workload ;
- serverless function ;
- CI/CD job.

---

## 7.7 Identité externe

Une identité peut provenir d’un Identity Provider externe :

- Google ;
- Microsoft ;
- GitHub ;
- Apple ;
- entreprise partenaire ;
- fournisseur OIDC ;
- fournisseur SAML.

---

# 8. Méthodes d’authentification à supporter

PyAuthKit doit être conçu de manière à permettre l’ajout progressif de nouvelles stratégies.

## 8.1 Password Authentication

Support attendu :

- password verification ;
- hashing sécurisé ;
- salage ;
- politique de mot de passe ;
- rotation éventuelle ;
- password reset ;
- invalidation de credential.

Le noyau ne doit pas imposer un algorithme unique.

---

## 8.2 PIN Authentication

Pour certains environnements ou devices.

---

## 8.3 API Key Authentication

Support :

- génération ;
- stockage sécurisé ;
- hashing ;
- rotation ;
- expiration ;
- scopes éventuels ;
- révocation.

---

## 8.4 Bearer Token

Validation générique de token bearer.

---

## 8.5 JWT

Support :

- signature validation ;
- claims validation ;
- issuer ;
- audience ;
- expiration ;
- not-before ;
- key rotation ;
- JWKS.

---

## 8.6 OTP

Support potentiel :

- email OTP ;
- SMS OTP ;
- custom OTP provider.

---

## 8.7 TOTP

Compatibilité avec les applications d’authentification standards.

---

## 8.8 MFA

Le MFA ne doit pas être modélisé comme un authenticator unique mais comme une composition de facteurs.

Exemple :

```text
Password
   +
TOTP
   +
Risk Policy
```

---

## 8.9 WebAuthn

Support de l’authentification cryptographique WebAuthn.

---

## 8.10 Passkeys

Support passwordless moderne fondé sur WebAuthn/FIDO.

---

## 8.11 Magic Link

Authentification par lien à durée de vie limitée.

---

## 8.12 OpenID Connect

OIDC doit permettre l’authentification fédérée et sociale.

Exemples :

- Google ;
- Microsoft ;
- GitHub lorsque pertinent ;
- fournisseurs OIDC personnalisés.

---

## 8.13 OAuth 2.0

OAuth 2.0 doit être supporté lorsque nécessaire aux flux d’autorisation ou de machine authentication.

Il convient toutefois de maintenir une distinction conceptuelle claire :

> **OAuth 2.0 est principalement un protocole d’autorisation déléguée et non, à lui seul, un protocole d’authentification utilisateur.**

Pour l’authentification fédérée moderne, PyAuthKit utilisera généralement OpenID Connect au-dessus d’OAuth 2.0.

---

## 8.14 SAML

Support de l’authentification fédérée entreprise.

---

## 8.15 Certificates

Validation d’identités fondées sur certificats.

---

## 8.16 mTLS

Support pour les systèmes machine-to-machine nécessitant une authentification mutuelle forte.

---

## 8.17 Client Credentials

Support des applications et services utilisant OAuth 2.0 Client Credentials.

---

## 8.18 Signed Assertions

Support futur :

- JWT bearer assertions ;
- custom signed assertions ;
- workload identity assertions.

---

# 9. Social Authentication

PyAuthKit doit permettre l’authentification via des providers externes.

Exemples :

```text
Google
Microsoft
GitHub
Apple
LinkedIn
Custom OIDC Provider
```

L’intégration doit reposer sur une abstraction provider-agnostic.

Exemple conceptuel :

```python
auth.register(
    GoogleOIDCAuthenticator(...)
)

auth.register(
    MicrosoftOIDCAuthenticator(...)
)

auth.register(
    GitHubAuthenticator(...)
)
```

Les providers doivent être des adapters et non des concepts structurants du domaine.

---

# 10. Authentication Pipeline

PyAuthKit doit permettre d’exprimer l’authentification comme un pipeline.

Exemple :

```text
Authentication Request
        │
        ▼
Credential Extraction
        │
        ▼
Authenticator Resolution
        │
        ▼
Credential Validation
        │
        ▼
Challenge
        │
        ▼
Additional Factor
        │
        ▼
Context Evaluation
        │
        ▼
Authentication Policy
        │
        ▼
Principal Resolution
        │
        ▼
Session / Token Issuance
        │
        ▼
Authentication Result
```

Le pipeline doit être composable.

---

# 11. Authentication Flows

Le moteur doit supporter des flows simples et complexes.

## Exemple 1 — Password

```text
Username + Password
        │
        ▼
Password verification
        │
        ▼
Authenticated Principal
```

## Exemple 2 — Password + MFA

```text
Password
   │
   ▼
Primary authentication
   │
   ▼
TOTP challenge
   │
   ▼
MFA validation
   │
   ▼
Authenticated Principal
```

## Exemple 3 — Passkey

```text
Authentication Request
        │
        ▼
WebAuthn Challenge
        │
        ▼
Signed Assertion
        │
        ▼
Cryptographic Verification
        │
        ▼
Authenticated Principal
```

## Exemple 4 — Social Login

```text
Application
   │
   ▼
OIDC Provider
   │
   ▼
Authorization Code Flow
   │
   ▼
ID Token
   │
   ▼
Claims Validation
   │
   ▼
Authenticated External Principal
```

## Exemple 5 — Machine-to-Machine

```text
Service
  │
  ▼
Client Credentials
  │
  ▼
Credential Validation
  │
  ▼
Service Principal
```

---

# 12. Modèle conceptuel initial

Le domaine devra probablement introduire les abstractions suivantes.

## Principal

Entité logique cherchant à s’authentifier.

Types potentiels :

```text
HUMAN
SERVICE
APPLICATION
AGENT
DEVICE
WORKLOAD
EXTERNAL
```

---

## Identity

Représentation d’une identité connue ou affirmée.

---

## Credential

Preuve ou secret permettant de participer à une authentification.

Exemples :

```text
PasswordCredential
ApiKeyCredential
TokenCredential
CertificateCredential
PasskeyCredential
AssertionCredential
```

---

## Authenticator

Composant capable de valider un type donné de preuve d’authentification.

---

## AuthenticationRequest

Demande normalisée d’authentification.

---

## AuthenticationAttempt

Tentative d’authentification identifiable et traçable.

---

## AuthenticationFactor

Facteur utilisé dans une authentification.

Catégories classiques :

```text
Knowledge
Possession
Inherence
Federated
Contextual
```

---

## AuthenticationChallenge

Challenge nécessaire pour poursuivre un flow.

---

## AuthenticationSession

État permettant de maintenir un flow d’authentification ou une session authentifiée.

---

## AuthenticationResult

Résultat normalisé de l’authentification.

Exemple conceptuel :

```python
AuthenticationResult(
    authenticated=True,
    principal=principal,
    identity=identity,
    factors=[...],
    assurance_level="AAL2",
    session=session,
)
```

---

## AuthenticationContext

Informations contextuelles exploitables pendant l’authentification.

Exemples :

- IP ;
- device ;
- user agent ;
- geography abstraite ;
- application cliente ;
- channel ;
- tenant ;
- risk signals.

---

## Assurance Level

Niveau de confiance associé à l’authentification réalisée.

Le modèle doit pouvoir représenter des niveaux d’assurance sans enfermer le moteur dans un standard unique.

---

# 13. Authentification adaptative

PyAuthKit doit pouvoir évoluer vers une authentification conditionnelle.

Exemple :

```text
Login Request
     │
     ▼
Password valid
     │
     ▼
Risk Evaluation
     │
     ├── Low Risk ─────► Login accepted
     │
     └── High Risk ────► Step-up MFA
```

Les signaux de risque peuvent inclure :

- nouvel appareil ;
- nouvelle localisation ;
- adresse IP inhabituelle ;
- vélocité impossible ;
- comportement suspect ;
- ressource sensible ;
- authentification précédente ancienne ;
- niveau de confiance insuffisant.

Le moteur ne doit pas nécessairement calculer tous ces signaux lui-même.

Il doit pouvoir recevoir des évaluateurs externes.

---

# 14. Step-Up Authentication

Une application doit pouvoir demander un niveau d’authentification supérieur pour une opération sensible.

Exemple :

```text
Utilisateur authentifié par password
               │
               ▼
Consultation standard
               │
               └── autorisée

Virement sensible
               │
               ▼
Required Assurance Level > Current Level
               │
               ▼
Passkey / MFA Challenge
               │
               ▼
Elevated Authentication Context
```

---

# 15. Sessions

PyAuthKit doit fournir une abstraction de gestion des sessions.

Le moteur doit pouvoir fonctionner avec différents stores :

- memory ;
- Redis ;
- SQL ;
- custom backend.

Les sessions doivent pouvoir supporter :

- création ;
- expiration ;
- renouvellement ;
- révocation ;
- invalidation globale ;
- metadata ;
- authentication context ;
- assurance level ;
- session rotation.

---

# 16. Tokens

PyAuthKit doit fournir ou intégrer un modèle cohérent pour :

- access tokens ;
- refresh tokens ;
- ID tokens ;
- session tokens ;
- one-time tokens ;
- temporary challenge tokens.

Le moteur doit séparer :

```text
Authentication
```

de :

```text
Token Format
```

Un token JWT ne doit donc pas devenir une hypothèse structurelle du système.

---

# 17. Credentials Management

PyAuthKit doit permettre la gestion sécurisée des credentials.

Fonctions envisagées :

- création ;
- vérification ;
- rotation ;
- révocation ;
- expiration ;
- compromise handling ;
- metadata ;
- last-used timestamp ;
- credential status.

Le stockage réel doit rester interchangeable.

---

# 18. Federation

Le moteur doit supporter l’authentification déléguée à des Identity Providers externes.

Architecture cible :

```text
PyAuthKit
   │
   ├── OIDC Adapter
   │      ├── Google
   │      ├── Microsoft
   │      └── Custom IdP
   │
   └── SAML Adapter
          ├── Enterprise IdP
          └── Partner IdP
```

La fédération doit rester un sous-domaine de l’authentification et non le cœur du modèle.

---

# 19. Framework Agnosticism

PyAuthKit ne doit pas dépendre structurellement de :

- Django ;
- FastAPI ;
- Flask ;
- Starlette ;
- Litestar ;
- autre framework Web.

Le cœur doit pouvoir être utilisé depuis :

```text
CLI
API
Worker
Web application
Background service
Agent runtime
Desktop application
Tests
```

Les frameworks devront être supportés via des intégrations.

Exemple :

```text
pyauthkit.integrations.fastapi
pyauthkit.integrations.django
pyauthkit.integrations.flask
pyauthkit.integrations.starlette
```

---

# 20. Provider Agnosticism

PyAuthKit ne doit pas imposer :

- Auth0 ;
- Keycloak ;
- Microsoft Entra ID ;
- Google Identity ;
- Okta ;
- Cognito ;
- Clerk ;
- Supabase Auth ;
- Firebase Auth.

Ces solutions pourront éventuellement être connectées via adapters.

---

# 21. Storage Agnosticism

Le moteur ne doit pas imposer une base de données.

Backends envisageables :

```text
Memory
PostgreSQL
SQLite
Redis
MongoDB
Custom implementation
```

Les contrats doivent être définis sous forme de ports / protocols.

---

# 22. Principes d’architecture

Le produit doit privilégier les principes suivants.

## Separation of Concerns

Séparer clairement :

- authentication ;
- identity management ;
- authorization ;
- persistence ;
- provider integration ;
- transport ;
- framework integration.

---

## Dependency Inversion

Le domaine ne doit pas dépendre des fournisseurs ou frameworks externes.

---

## Open/Closed Principle

L’ajout d’une nouvelle méthode d’authentification ne doit pas nécessiter la modification du moteur central.

---

## Strategy Pattern

Chaque mécanisme d’authentification peut être modélisé comme une stratégie.

---

## Adapter Pattern

Les fournisseurs externes sont encapsulés derrière des adapters.

---

## Factory / Registry

Le moteur doit pouvoir résoudre dynamiquement l’authenticator adapté.

---

## Pipeline / Chain of Responsibility

Les flows multi-étapes peuvent être modélisés comme des pipelines de traitements ou challenges.

---

## Hexagonal Architecture

Les dépendances externes doivent rester derrière des ports.

---

## Domain-Driven Design

Le vocabulaire du produit doit être explicitement défini et cohérent.

---

# 23. Architecture conceptuelle

```text
                         PyAuthKit
                            │
                    Authentication API
                            │
                            ▼
                 Authentication Engine
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
          ▼                 ▼                  ▼
    Authenticator       Flow Engine       Policy Engine
      Registry
          │                 │                  │
          ▼                 ▼                  ▼
   Authenticators      Challenges          Risk /
                                         Assurance
          │
          ▼
 ┌──────────────────────────────────────────────────┐
 │ Password │ TOTP │ WebAuthn │ OIDC │ APIKey │ ...│
 └──────────────────────────────────────────────────┘
          │
          ▼
       Principal
          │
          ▼
 Session / Token / AuthenticationResult
```

---

# 24. API conceptuelle

L’objectif est de tendre vers une API simple.

```python
engine = AuthenticationEngine()

engine.register(PasswordAuthenticator(...))
engine.register(TOTPAuthenticator(...))
engine.register(GoogleOIDCAuthenticator(...))
engine.register(WebAuthnAuthenticator(...))
```

Puis :

```python
result = await engine.authenticate(
    AuthenticationRequest(
        method="password",
        credentials=credentials,
        context=context,
    )
)
```

ou :

```python
result = await engine.authenticate(request)
```

avec résolution automatique de la stratégie.

---

# 25. Extensibilité

Une nouvelle méthode doit pouvoir être ajoutée de manière indépendante.

Exemple :

```python
class MyAuthenticator(Authenticator):
    async def authenticate(self, request):
        ...
```

Puis :

```python
engine.register(MyAuthenticator(...))
```

Le moteur ne doit pas contenir de condition centrale de type :

```python
if provider == "google":
    ...
elif provider == "github":
    ...
elif provider == "microsoft":
    ...
```

---

# 26. Sécurité

La sécurité constitue une exigence fondamentale.

Le produit devra notamment considérer :

- secure defaults ;
- secret handling ;
- constant-time comparisons ;
- strong password hashing ;
- replay protection ;
- nonce validation ;
- state validation ;
- CSRF protections pour les flows concernés ;
- PKCE ;
- token expiration ;
- token rotation ;
- session fixation protection ;
- session invalidation ;
- credential compromise ;
- brute-force protection ;
- lockout policies ;
- rate limiting hooks ;
- auditability ;
- key rotation ;
- cryptographic agility.

Les détails seront approfondis dans une spécification dédiée.

---

# 27. Observabilité et audit

Chaque tentative d’authentification doit pouvoir produire des événements exploitables.

Exemples :

```text
AuthenticationStarted
CredentialValidated
CredentialRejected
ChallengeCreated
ChallengeSucceeded
ChallengeFailed
AuthenticationSucceeded
AuthenticationFailed
SessionCreated
SessionRevoked
TokenIssued
TokenRevoked
CredentialRotated
```

Ces événements doivent pouvoir être consommés par :

- logs ;
- SIEM ;
- audit trail ;
- monitoring ;
- analytics ;
- sécurité ;
- workflows externes.

Aucune information sensible ne doit être exposée dans les événements.

---

# 28. Multi-Tenant

PyAuthKit doit être compatible avec des architectures multi-tenant.

Le contexte d’authentification peut contenir :

```text
tenant_id
organization_id
realm
authentication_policy
identity_provider
```

Toutefois, le moteur ne doit pas imposer un modèle organisationnel spécifique.

Celui-ci peut être géré par PyIAMKit ou l’application.

---

# 29. Cas d’usage représentatifs

## UC-01 — Login classique

Un utilisateur s’authentifie avec email et mot de passe.

---

## UC-02 — MFA

Après validation du mot de passe, un challenge TOTP est requis.

---

## UC-03 — Social Login

Un utilisateur se connecte via Google.

PyAuthKit valide l’authentification OIDC et retourne un principal externe authentifié.

---

## UC-04 — Enterprise SSO

Un collaborateur se connecte via l’IdP de son entreprise.

---

## UC-05 — Passkey

Un utilisateur s’authentifie sans mot de passe via WebAuthn.

---

## UC-06 — API Key

Une application cliente appelle une API protégée avec une API key.

---

## UC-07 — Machine-to-Machine

Un service backend utilise Client Credentials.

---

## UC-08 — mTLS

Deux services s’authentifient mutuellement à l’aide de certificats.

---

## UC-09 — Agent Authentication

Un agent IA obtient une identité authentifiée avant d’exécuter une action.

---

## UC-10 — Step-Up Authentication

Une opération sensible nécessite un second facteur malgré une session déjà valide.

---

## UC-11 — Provider Custom

Une organisation ajoute son propre authenticator sans modifier le core de PyAuthKit.

---

# 30. Intégration avec PyIAMKit

Une séquence typique sera :

```text
1. AuthenticationRequest
          │
          ▼
2. PyAuthKit
          │
          ▼
3. AuthenticatedPrincipal
          │
          ▼
4. PyIAMKit
          │
          ├── Identity Resolution
          ├── Account
          ├── Organization
          ├── Groups
          ├── Roles
          └── Permissions
          │
          ▼
5. Authorization Decision
```

Le contrat entre PyAuthKit et PyIAMKit doit rester explicite et minimal.

---

# 31. Intégration avec PyAgentsKit

Les agents pourront être considérés comme des principals.

Exemple :

```python
Principal(
    type=PrincipalType.AGENT,
    subject="finance-manager-agent",
)
```

PyAuthKit pourra authentifier cet agent.

PyIAMKit pourra ensuite déterminer ses permissions.

PyAgentsKit pourra utiliser l’identité authentifiée dans son runtime.

---

# 32. Intégration potentielle avec Synqentra

Dans Synqentra, les acteurs peuvent être :

```text
Human User
General Agent
Manager Agent
Specialized Agent
External Service
Internal Service
Integration
```

PyAuthKit peut devenir la couche commune permettant de prouver l’identité de chacun de ces acteurs avant toute interaction avec les ressources de la plateforme.

---

# 33. Hors périmètre initial

La première version ne devra pas chercher à résoudre immédiatement :

- un serveur IAM complet ;
- un annuaire LDAP ;
- un produit concurrent complet de Keycloak ;
- un moteur complet d’autorisation ;
- une interface utilisateur de gestion des comptes ;
- une solution de gouvernance IAM ;
- un moteur de détection de fraude ;
- un SIEM ;
- un Password Manager ;
- un PKI complet ;
- tous les providers sociaux existants.

Le core doit d’abord établir les abstractions fondamentales.

---

# 34. MVP envisagé

Un premier MVP pourrait couvrir :

```text
Authentication Engine
        │
        ├── Principal
        ├── Credential
        ├── AuthenticationRequest
        ├── AuthenticationResult
        ├── Authenticator Protocol
        ├── Authenticator Registry
        ├── Authentication Context
        │
        ├── Password Authenticator
        ├── API Key Authenticator
        └── JWT Authenticator
```

Puis :

```text
MFA / Challenges
Sessions
Tokens
OIDC
Social Login
WebAuthn / Passkeys
Machine Auth
Federation
Adaptive Auth
```

---

# 35. Trajectoire fonctionnelle possible

```text
0.x
 │
 ├── Authentication Core
 ├── Credentials
 ├── Password
 ├── API Keys
 └── JWT
      │
      ▼
MFA & Challenges
      │
      ▼
Sessions & Tokens
      │
      ▼
OIDC / Social
      │
      ▼
WebAuthn / Passkeys
      │
      ▼
Machine Authentication
      │
      ▼
Federation / SAML
      │
      ▼
Adaptive / Risk-Based Authentication
```

Cette trajectoire n’est pas encore une roadmap de release définitive.

Elle exprime uniquement une progression fonctionnelle logique.

---

# 36. Critères de réussite

PyAuthKit pourra être considéré comme répondant au besoin lorsque :

1. une application Python peut intégrer le moteur sans dépendre d’un framework Web précis ;
2. plusieurs stratégies d’authentification peuvent coexister ;
3. un nouvel authenticator peut être ajouté sans modifier le core ;
4. le moteur fonctionne pour humains et machines ;
5. les flows multi-facteurs sont composables ;
6. les résultats sont normalisés ;
7. le stockage peut être remplacé ;
8. les fournisseurs externes restent derrière des adapters ;
9. PyIAMKit peut consommer le résultat sans dépendre de l’implémentation de l’authentification ;
10. les primitives de sécurité sont explicites et testables ;
11. les événements d’authentification sont auditables ;
12. le design permet l’évolution vers passkeys, fédération et adaptive authentication.

---

# 37. Résumé

PyAuthKit doit être un **Authentication Engine Python autonome**, clairement séparé de PyIAMKit.

La frontière conceptuelle est :

```text
PyAuthKit
    │
    └── « Prouve qui tu es »

PyIAMKit
    │
    └── « Qui es-tu dans le système et que peux-tu faire ? »
```

Le produit doit fournir une couche uniforme pour :

```text
Human Authentication
Machine Authentication
Agent Authentication
Password Authentication
Passwordless Authentication
MFA
Social Login
Federation
Sessions
Tokens
Credentials
Adaptive Authentication
```

tout en restant :

```text
Framework-Agnostic
Provider-Agnostic
Storage-Agnostic
Extensible
Composable
Secure by Design
```

L’ambition n’est donc pas de créer simplement une bibliothèque de login.

L’ambition est de créer une **primitive d’infrastructure d’authentification réutilisable dans l’ensemble de l’écosystème Python et Py**Kit**.

---

# 38. Formulation courte du produit

> **PyAuthKit is a framework-agnostic, provider-agnostic Python authentication engine for human, machine, workload, device and agent identities.**

---

# 39. Positionnement dans l’écosystème

```text
                         SECURITY & IDENTITY
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
             PyAuthKit                     PyIAMKit
                 │                             │
          Authentication                 Identity & Access
                 │                             │
     ┌───────────┼────────────┐      ┌────────┼────────────┐
     │           │            │      │        │            │
 Credentials    MFA      Federation Users    Roles      Policies
 Sessions      Passkeys   Social     Groups   Perms      Governance
 Tokens        Machine    OIDC/SAML  Orgs     Access     Lifecycle
                 │                             │
                 └──────────────┬──────────────┘
                                │
                         Applications
                         Services
                         Agents
                         Synqentra
```

---

**Document suivant recommandé :**

`01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md`
