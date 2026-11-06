# PyAuthKit - Handoff conditionnel M3 vers M4

- Date: 2026-11-05
- M3 implémentation: développée et éprouvée sur un banc de référence.
- M3 gate: **GATE27-04 #74 OPEN / NO-GO FORMEL**.
- PR M3: [#75](https://github.com/tawounfouet/pyauthkit/pull/75), **READY FOR SECURITY REVIEW**, pas fusionnée.
- Référence code testée: `2c6ea7173b44ce314c61f680b436d493c994de3c`, CI [42031794016](https://github.com/tawounfouet/pyauthkit/actions/runs/42031794016), 7/7 (160 source + 9 host).
- Référence documentaire vérifiée: `08eecce6913a7a12cd928cf5be0e8ae89ccc818c`, CI [42032506665](https://github.com/tawounfouet/pyauthkit/actions/runs/42032506665), 7/7.

## Pourquoi cet handoff est conditionnel

La préparation de conception M4 peut commencer dans une branche séparée sans revendiquer la clôture de M3. La fusion sur `main` et la finalisation officielle de M3 restent **bloquées** par les approbations de sécurité, le signoff des ADR-0010..0015, l'acceptation des risques par leurs owners et GATE27-04. Ne pas utiliser la CI comme substitut à ces décisions.

## Contrats M3 que M4 pourra réutiliser

1. `AuthenticationEngine` M2 et `AuthenticationPolicyGate` final et obligatoire.
2. `Authenticator` SPI et `AuthenticatorRegistry` explicite.
3. `PasswordCredentialResolver` scopé, projection sans secret dans le repr, `is_current` et données status/version/expiry.
4. `PasswordHashVerifier` Argon2id strict, `PasswordAttemptGuard` obligatoire et `KDFWorkerPool` fini.
5. Rejet/erreur typés, audit redigé best-effort (pas de garantie de livraison durable).

## Prochain jalon M4 après autorisation

- **Lifecycle Password** : enrollment, reset, changement, rotation, politiques de commit et éventuelle rehash via ports write dédiés. M3 n'implémente aucune écriture.
- **MFA et Step-up** : modes / transitions de facteurs, défis et politique d'élévation sans bypass de la gate.
- **Sessions** : création, expiration, rotation, révocation et frontières des secrets.
- **Conditions de sécurité** : isolation tenant, protection réplay, anti-énumération, audit fiable et tests de courses sur les nouveaux chemins.
- **Gouvernance** : nouvelle branche/M4 PR, ADR et modèles de domaine, tests RED puis implémentation. Aucun merge automatique ni PyPI.

## Checklist GO M3 avant implémentation M4 dépendante

- [ ] Relecteur indépendant et éligible approuve PR #75 et ADR 0010..0015.
- [ ] Risques et restrictions host acceptés ou corrigés par des owners nommés.
- [ ] G4-01..G4-16 et les 40 oracles ont une décision signée.
- [ ] GATE27-04 #74 formellement GO après observation des SHA.
- [ ] PR #75 fusionnée sous règles de protection et CI `main` 7/7 observée.
- [ ] Issues M3 WP et milestone clôturées avec preuves, sans prétendre à la première release.

**Statut actuel : PRÊT POUR REVUE, PAS PRÊT POUR FUSION OU PUBLICATION.**
