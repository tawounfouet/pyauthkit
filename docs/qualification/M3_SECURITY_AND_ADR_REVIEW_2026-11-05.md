# PyAuthKit M3 - Revue critique des ADR et frontières de sécurité

**Date :** 2026-11-05  
**Nature :** analyse technique assistée, **PAS une revue indépendante approuvée**  
**Périmètre :** PR #75, ADR-0010..0015, composant M3 et hôte de référence `qualification/host`  
**Critère de décision :** Evidence Before Claim, Trust Before Integration, fail closed.

## 1. Analyse décision par décision

| ADR | Contrat et décision examinés | Preuve automatisée | Évaluation | Approbation |
|---|---|---|---|---|
| ADR-0010 | PasswordCredentialResolver scoped, propriétaire du credential externe | Contrats mémoire/callback, requête PostgreSQL filtrée par `scope_id`, deux tenants de référence | Cohérent avec Ports & Adapters. Attention à la fenêtre entre le dernier `is_current` et la réponse. | PROPOSED, reviewer manquant |
| ADR-0011 | Argon2id-v19 uniquement, PHC canonique, plancher de coût et dépendance optionnelle | Vecteur publié, PHC malveillant, vrai KDF, cinq plateformes wheel | Bon baseline. Les paramètres autorisés peuvent rendre les timings différents entre hashes historiques; benchmark réel nécessaire à chaque profil. | PROPOSED, reviewer manquant |
| ADR-0012 | Pool KDF borné, retenue de permis après annulation | Saturation 120 tentatives, timeout, shutdown, plus tests HTTP | Finite per-process, sans préemption du C natif. Multiplier les instances multiplie le budget total. | PROPOSED, reviewer manquant |
| ADR-0013 | AttemptGuard obligatoire, responsabilités hôte | Redis Lua atomique, HMAC des dimensions, anti-spoofing XFF, panne Redis fail closed, deux replicas | Limites réelles à qualifier : proxy, changement d'IP, CGNAT, source partagée, botnet, multi-région, rotation HMAC. | PROPOSED, reviewer manquant |
| ADR-0014 | Politique finale M2 obligatoire et VerifiedOutcome interne | Tests de policy DENY, faux résultats, scoped login + KDF | Pas de raccourci connu de l'adaptateur vers un résultat public positif. Processus Python pas une sandbox contre code hôte malveillant. | PROPOSED, reviewer manquant |
| ADR-0015 | Séparer code, CI, qualification, GO et release | Matrice 40 oracles, CI, benchmark, hôte de test, issue gate ouverte | Doit rester bloquant tant qu'aucun owner ne signe les risques et les garanties hôtes. | PROPOSED, reviewer manquant |

## 2. Contrats de confiance de l'hôte de référence

Le host de qualification conserve un catalogue de routes explicitement construit. Les scopes effectifs n'arrivent jamais depuis un `X-Tenant` ni depuis le JSON. Les credentials sont interrogés avec `WHERE scope_id=$1` au niveau de la source SQL. La vérification Argon2id et `is_current` sont deux étapes distinctes; des tests modifient la version de l'enregistrement PostgreSQL entre les deux.

Les limites Redis sont deux clés HMAC (scope + adresse source, scope + identifiant) exécutées dans un seul script Lua transactionnel. La clé HMAC doit être identique entre replicas; elle est générée dynamiquement pour chaque session de test. Aucun compte réel ni hash opérationnel n'est utilisé.

La source réseau provient de la connexion ASGI, sans accepter `Forwarded` ou `X-Forwarded-For`. **Cela rend le test sûr face à un en-tête forgé, mais ne constitue PAS un design complet de reverse-proxy de production.**

## 3. Risques résiduels non acceptés

| ID | Risque | Priorité | Owner à désigner | Critère de levée |
|---|---|---|---|---|
| M3-Q-R01 | Métadonnées d'adresse et chaîne reverse-proxy non qualifiées | P0 production | Framework integrator | Valider TLS/proxy de confiance, IP/source, spoofing réel |
| M3-Q-R02 | Timing et équivalence au-delà du loopback | P0 production | Host + sécurité | Essais réseau multi-hôte, en-têtes, quotas, latence, interprétation statistique |
| M3-Q-R03 | Révocation après l'ultime lecture `is_current` | P0 si garantie « immédiate » | Credential owner | Contrat explicite de consistance, garanties limitées ou mécanisme transactionnel |
| M3-Q-R04 | Saturation mémoire/capacité globale sous multi-instance | P1 | SRE / Infra | Budget par processus + cluster, cibles p95/p99/RSS |
| M3-Q-R05 | Quotas Redis fixed-window, rotation HMAC, botnet/spray | P1 | Sécurité + Host | Politique de débit réelle, telemetry, scénarios d'abus |
| M3-Q-R06 | Audit best-effort de M2 | P1 | Ops / Security | Audit durable au point de décision si exigé par le host |
| M3-Q-R07 | Reproductibilité des artefacts et lock transitoires | P1 release | Supply-chain owner | Issue #63, preuves de build pour publication |
| M3-Q-R08 | Approbation humaine indépendante absente | P0 gate | Maintainer + reviewer éligible | Revue GitHub d'une personne distincte et compétente; issue #64 |

**Aucun de ces risques n'a été accepté par une personne habilitée**. On ne peut pas assimiler une proposition d'owner ou un test partiel à une dérogation formelle.

## 4. Périmètre de qualification et décision proposée

- **Composant M3** : les tests de sécurité, cryptographie, concurrence et packaging constituent un bon niveau de preuve de développement.
- **Hôte d'essai** : API FastAPI/PostgreSQL/Redis, test sur un véritable socket TCP Uvicorn et vérification de quotas inter-instances. Le test de deux processus OS indépendants vise à renforcer T24, lorsqu'il aura été exécuté et consigné dans la CI.
- **Production** : aucune preuve sur un vrai proxy, un store métier réel, un déploiement multi-région ou un audit durable n'est fournie. Ne pas faire de claim « production-ready ».
- **Gouvernance** : ADR-0010..0015 restent `PROPOSED`; la PR #75 reste en revue ou brouillon jusqu'à un sign-off éligible; `main` et PyPI ne doivent pas être modifiés par ce rapport.

**Verdict de cette analyse : candidat robuste pour revue indépendante; aucune auto-approbation de GATE27-04.**
