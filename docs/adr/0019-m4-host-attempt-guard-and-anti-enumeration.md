# ADR-0019 - M4 Host Attempt Guard, quotas et anti-enumeration

- Statut : **PROPOSED / NOT ACCEPTED** (2026-11-05)
- Source : plan M4 detaille §20 (T05, T29..T35) et §22 (G5-08, 09, 11, 12).
- Perimetre : host-owned guard, pas d'adaptation automatique d'un SDK public.

## Probleme
Les selectors peuvent etre enumeres; les erreurs de lookup et de HMAC peuvent avoir des latences differentes. L'adresse reseau ou le tenant fournis par l'appelant ne sont pas une source d'autorite. Le guard doit limiter les abus multi-processus sans jamais devenir permissif si Redis est indisponible.

## Decision candidate
1. [DIP] L'authenticator M4 requiert un port `ApiKeyAttemptGuard` injecte par le host; un bool strictement `True` permet de poursuivre. Une exception ou un refus interdit la promotion.
2. [Security] Seul `TrustedScopeRef` du contexte M2 preapprouve choisit le scope; ni `X-Tenant` ni le selector ne choisissent un tenant.
3. [Abuse control] Le **banc de reference** emploie Redis Lua avec compteurs atomiques scope, pair de socket et selector, noms de buckets pseudonymises par HMAC et expiration explicite.
4. [Peer authority] Le pair utilise est le pair socket pour Uvicorn **sans proxy**. Un host avec TLS/proxy doit adopter une politique explicite de hops de confiance et la tester sous requetes adversariales.
5. [Fail Closed] Si Redis est unavailable, AuthError/HTTP 503. Aucun fallback in-memory ou autre scope.
6. [HTTP] Refus ordinaires 401 avec corps/en-tetes uniformes testables. Les en-tetes Authorization dupliques sont rejetes avec guard. La temporisation de refus est une mesure du banc uniquement.
7. [Timing] Les p50/p95/p99 et l'intervalle descriptif de difference de medianes en loopback ne prouvent **pas** un temps constant ni l'absence d'enumeration en production.
8. [Governance] Le host owner doit approuver seuils, taux, source d'identite peer, logs, incidents, disponibilite et politique anti-rejeu.

## Options rejetees / non prouvees
- Guard absent ou fail-open : refuse.
- Limiteur uniquement par selector : peut permettre l'epuisement cible.
- Source peer via en-tete client non valide : refuse.
- Garantie de timing end-to-end deduite de `hmac.compare_digest` : invalide.
- Faible latence en CI = preuve de SLO production : invalide.

## Revue / gate
- Evidence candidate : `qualification/m4_host/guard.py`, `test_m4_http.py`, `test_m4_pg_redis.py`.
- Reste non qualifie : vrai TLS/proxy, KMS, SIEM durable, budgets production, etude reseau et incident response.
- Owner de l'ADR : **NON RENSEIGNE**.
- Security reviewer independant : **NON RENSEIGNE**.
- Decision, date et SHA : **PENDING**.
- **GATE27-05 NO-GO** ; aucune publication ni autorisation de merge.
