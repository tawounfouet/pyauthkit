# PyAuthKit - Index des spécifications

> Baseline documentaire initiale : **29 spécifications numérotées (00 à 28) + 1 convention transversale = 30 documents**.

> **Statut :** documentation de conception. Les modèles, APIs et garanties décrits sont proposés ou spécifiés, mais ne sont pas nécessairement implémentés, testés ou qualifiés dans le dépôt.

## Convention transversale

- [Software Design & Learning Convention](PYAUTHKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md) - *Problem First, Trust First, Pattern Second, Evidence Before Claim*.

## Parcours de lecture recommandé

1. Cadrage et architecture : `00` à `03`.
2. Domaine et invariants : `04` à `08`.
3. Moteur et méthodes : `09` à `17` (capacités avancées majoritairement post-MVP).
4. Infrastructure et contrôles : `18` à `21`.
5. Intégrations et qualification : `22` à `26`.
6. Mise en œuvre : `27` et `28`.

## Catalogue des documents

### 01 - Cadrage, vision et architecture

| Document | Sujet |
| --- | --- |
| [`00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md`](00_PYAUTHKIT_EXPRESSION_DU_BESOIN.md) | Expression du besoin |
| [`01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md`](01_PYAUTHKIT_REQUIREMENTS_ANALYSIS.md) | Analyse des exigences |
| [`02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md`](02_PYAUTHKIT_PRODUCT_VISION_AND_ARCHITECTURE_PRINCIPLES.md) | Vision produit et principes d'architecture |
| [`03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md`](03_PYAUTHKIT_SYSTEM_ARCHITECTURE.md) | Architecture système |

### 02 - Domaine et cas d'usage

| Document | Sujet |
| --- | --- |
| [`04_PYAUTHKIT_DOMAIN_OBJECTS.md`](04_PYAUTHKIT_DOMAIN_OBJECTS.md) | Objets du domaine |
| [`05_PYAUTHKIT_ENTITIES_AND_VALUE_OBJECTS.md`](05_PYAUTHKIT_ENTITIES_AND_VALUE_OBJECTS.md) | Entities et Value Objects |
| [`06_PYAUTHKIT_DOMAIN_RELATIONSHIPS_AND_ERD.md`](06_PYAUTHKIT_DOMAIN_RELATIONSHIPS_AND_ERD.md) | Relations du domaine et ERD |
| [`07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md`](07_PYAUTHKIT_DOMAIN_INVARIANTS_AND_BUSINESS_RULES.md) | Invariants et règles métier |
| [`08_PYAUTHKIT_COMMANDS_QUERIES_AND_USE_CASES.md`](08_PYAUTHKIT_COMMANDS_QUERIES_AND_USE_CASES.md) | Commands, Queries et Use Cases |

### 03 - Mécanismes d'authentification

| Document | Sujet |
| --- | --- |
| [`09_PYAUTHKIT_AUTHENTICATION_ENGINE_MODEL.md`](09_PYAUTHKIT_AUTHENTICATION_ENGINE_MODEL.md) | Moteur d'authentification |
| [`10_PYAUTHKIT_AUTHENTICATOR_AND_CREDENTIAL_MODEL.md`](10_PYAUTHKIT_AUTHENTICATOR_AND_CREDENTIAL_MODEL.md) | Authenticators et credentials |
| [`11_PYAUTHKIT_AUTHENTICATION_FLOW_AND_CHALLENGE_MODEL.md`](11_PYAUTHKIT_AUTHENTICATION_FLOW_AND_CHALLENGE_MODEL.md) | Flows et challenges |
| [`12_PYAUTHKIT_MFA_AND_ASSURANCE_MODEL.md`](12_PYAUTHKIT_MFA_AND_ASSURANCE_MODEL.md) | MFA et assurance |
| [`13_PYAUTHKIT_SESSION_AND_TOKEN_MODEL.md`](13_PYAUTHKIT_SESSION_AND_TOKEN_MODEL.md) | Sessions et tokens |
| [`14_PYAUTHKIT_FEDERATION_OIDC_OAUTH_SAML_MODEL.md`](14_PYAUTHKIT_FEDERATION_OIDC_OAUTH_SAML_MODEL.md) | Fédération OIDC, OAuth et SAML |
| [`15_PYAUTHKIT_WEBAUTHN_PASSKEY_AND_PASSWORDLESS_MODEL.md`](15_PYAUTHKIT_WEBAUTHN_PASSKEY_AND_PASSWORDLESS_MODEL.md) | WebAuthn, passkeys et passwordless |
| [`16_PYAUTHKIT_MACHINE_WORKLOAD_AND_AGENT_AUTH_MODEL.md`](16_PYAUTHKIT_MACHINE_WORKLOAD_AND_AGENT_AUTH_MODEL.md) | Machines, workloads et agents |
| [`17_PYAUTHKIT_ADAPTIVE_AUTH_AND_RISK_MODEL.md`](17_PYAUTHKIT_ADAPTIVE_AUTH_AND_RISK_MODEL.md) | Authentification adaptative et risque |

### 04 - Infrastructure et sécurité

| Document | Sujet |
| --- | --- |
| [`18_PYAUTHKIT_PORTS_ADAPTERS_AND_PLUGIN_ARCHITECTURE.md`](18_PYAUTHKIT_PORTS_ADAPTERS_AND_PLUGIN_ARCHITECTURE.md) | Ports, adapters et plugins |
| [`19_PYAUTHKIT_STORAGE_AND_PERSISTENCE_ARCHITECTURE.md`](19_PYAUTHKIT_STORAGE_AND_PERSISTENCE_ARCHITECTURE.md) | Stockage et persistance |
| [`20_PYAUTHKIT_SECURITY_THREAT_MODEL.md`](20_PYAUTHKIT_SECURITY_THREAT_MODEL.md) | Modèle de menaces |
| [`21_PYAUTHKIT_AUDIT_EVENTS_AND_OBSERVABILITY.md`](21_PYAUTHKIT_AUDIT_EVENTS_AND_OBSERVABILITY.md) | Audit et observabilité |

### 05 - Intégrations, SDK et qualification

| Document | Sujet |
| --- | --- |
| [`22_PYAUTHKIT_FRAMEWORK_INTEGRATIONS.md`](22_PYAUTHKIT_FRAMEWORK_INTEGRATIONS.md) | Intégrations des frameworks Python |
| [`23_PYAUTHKIT_PYIAMKIT_INTEGRATION_CONTRACT.md`](23_PYAUTHKIT_PYIAMKIT_INTEGRATION_CONTRACT.md) | Contrat d'intégration PyIAMKit |
| [`24_PYAUTHKIT_PUBLIC_API_AND_SDK_DESIGN.md`](24_PYAUTHKIT_PUBLIC_API_AND_SDK_DESIGN.md) | API publique et SDK |
| [`25_PYAUTHKIT_CONFIGURATION_MODEL.md`](25_PYAUTHKIT_CONFIGURATION_MODEL.md) | Configuration |
| [`26_PYAUTHKIT_TESTING_AND_QUALIFICATION_STRATEGY.md`](26_PYAUTHKIT_TESTING_AND_QUALIFICATION_STRATEGY.md) | Tests et qualification |

### 06 - Exécution et bootstrap

| Document | Sujet |
| --- | --- |
| [`27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md`](27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md) | Roadmap d'implémentation |
| [`28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md`](28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md) | Plan de bootstrap |

## Gouvernance documentaire

- Les spécifications initiales restent dans `docs/specs/` et sont versionnées avec le code.
- Les décisions réellement adoptées sont consignées séparément dans `docs/adr/`.
- Le suivi opérationnel des milestones et des PR peut vivre dans `docs/roadmap/`, sans recopier les fichiers `27` et `28`.
- La progression d'une capacité se vérifie dans le code, les tests et les résultats CI. `DOCUMENTED` n'implique pas `IMPLEMENTED` ou `QUALIFIED`.
- Toute divergence entre documents doit être traitée explicitement (revue et ADR), sans réécriture silencieuse de la source de référence.

[Retour au README du dépôt](../../README.md)
