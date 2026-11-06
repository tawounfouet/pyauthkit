# M5 - Decision de fusion de developpement pre-alpha (PR-08)

> Date: 2026-11-05
> Projet: PyAuthKit / PR #80
> Statut: DEVELOPMENT MERGE AUTHORIZED BY REPOSITORY OWNER; SECURITY GATE STILL NO-GO
> Portee: main, integration pre-alpha uniquement; aucun deploiement, aucune release
> Contrat: docs/qualification/M5_G6_TECHNICAL_REVIEW_2026-11-05.md
> Gate: GATE27-06 = NO-GO, issue de suivi #81

## 1. Autorite, decision et separation des gates

Le mainteneur du depot a explicitement demande le 5 novembre 2026 de
qualifier les travaux realisables et d'integrer M5 sur main. La decision
operationnelle est d'autoriser une fusion **de developpement pre-alpha**
sous conditions CI, en conservant distinctement les exigences de securite
non qualifiees. Il ne s'agit ni d'une attestation d'audit externe, ni
d'une derogation silencieuse, ni d'une autorisation de production.

La qualification GATE27-06 reste NO-GO car aucun humain independant
n'a formellement accepte les 40 oracles, les 16 criteres G6, les ADR
candidats ni le banc de validation de reseau d'exploitation. Aucune
revue tierce n'est inventee. Le suivi demeure ouvert dans #81.

Les gates anterieurs sont conserves: M4 GATE27-05 NO-GO, M3 #75
distinct. La future etape de developpement (notamment M6) peut etre
preparee sans aucune implication que M5 est apte a la production.

## 2. Perimetre code effectivement livre

- M5 JWT strict: profil de confiance approuve par l'hote, compaction
  JWS bornee, typ=at+jwt, RS256, verification cryptographique PyJWT,
  issuer/audience/exp/nbf/iat/sub valides, aucune attribution IAM.
- M2 obligatoire: enregistrement explicite dans le registry et passage
  final dans AuthenticationPolicyGate avant Authenticated.
- JWK: catalogues immuables host-approved, cles RSA publiques,
  isolation par reference de profil et version, pas de repli de kid.
- JWKS: cache avec TTL, single-flight, echec ferme et invalidation
  par generation contre resurrection pendant un refresh.
- Transport HTTPS optionnel explicite: ApprovedJwksSource, liste d'IP
  publiques precises autorisees, controle de toutes les reponses DNS,
  connexion sur l'IP approuvee, verification du nom DNS et certificat
  par TLS, refus des redirects, limite de taille, de temps et de headers.
- Verification independante de l'emission PyJWT: JWS synthetiques
  signes avec l'outil OpenSSL CLI puis verifies avec PyJWT.
- Banc TLS local: vraie negotiation TLS avec CA et SNI, routage IP
  externe/observations du pair intentionnellement simules.

## 3. Preuves techniques de reference avant fusion

| Preuve | SHA | Run/job | Resultat |
| --- | --- | --- | --- |
| Workflow complet | 70186f44bec800da6046e4b2407bd9fbe2dd4d2b | Actions #42095829528 | 9/9 PASS |
| M5 JWT/JWKS/OpenSSL/TLS | meme SHA | Job 127485478753 | 109 PASS |
| Tests qualite et architecture | meme SHA | Job 127485478803 | 328 PASS; mypy 40 fichiers; Ruff PASS |
| Tests M4 regression host | meme SHA | Job 127485478833 | 20 PASS |
| Security/dependency/secret scans | meme SHA | Job 127485478717 | PASS |
| Packaging matrice Python/OS | meme SHA | Workflow #42095829528 | PASS |

Source: https://github.com/tawounfouet/pyauthkit/actions/runs/42095829528

**Note SHA:** ce document, ajoute apres la verification precedente,
declenche un NOUVEAU SHA. La fusion exige donc de verifier les
controles CI exacts sur le HEAD final de la PR, pas seulement sur
70186f44. Une fusion effective exige ensuite SHA/main et checks propres.

## 4. Verification des protections de main

Ruleset actif PYAUTHKIT_PROTECT_MAIN (#26350656), verifie via GitHub
le 2026-11-05:
- pull request requise, resolution des threads de review requise;
- mise a jour en fast-forward seule et suppression de main refusee;
- sept checks obligatoires: quality, security et cinq jobs wheel/sdist;
- validation stricte sur branche a jour;
- zero approbation imposee par le ruleset; aucun bypass declare.
- Le job M5 additionnel n'est pas dans les sept checks de ruleset;
  cette decision de merge exige volontairement qu'il soit egalement vert.

L'API de branch protection classique renvoie 403 depuis le connecteur
GitHub App; le ruleset actif est la preuve de controle accessible.
Un check vert est une propriete technique et non un audit de securite.

## 5. Conditions explicites du merge

- [ ] PR #80 head final identifiable.
- [ ] Tous les neuf jobs Actions PASS sur le SHA exact du head final.
- [ ] PR mergeable, base main a jour, branche protegee respectee.
- [ ] Aucun review thread non resolu ni nouveau blocage P0 dans la PR.
- [ ] Fusion via API PR standard, sans direct push, sans bypass.
- [ ] Verification du SHA main apres fusion et des checks post-merge.

## 6. Limites et obligations apres fusion

GATE27-06 **NO-GO** tant que ne sont pas obtenus:
1. la qualification DNS/egress/proxy/firewall avec un vrai hote deployable,
   un provider JWKS reel et la politique exacte d'IP approuvees;
2. la revue cryptographique et du code par une personne independante;
3. la revue et signature des M5-T01..T40, G6-01..G6-16 et ADR-0020/0021;
4. la politique de rotation/revocation et tests entre plusieurs processus;
5. le GO formel du proprietaire securite avec SHA et exceptions datees.

Ces controles ne sont ni declares PASS ni transformes en N/A pour
faciliter une fusion. La publication PyPI, l'exposition publique, le
deploiement et l'usage d'authentification en production restent interdits.

## 7. Learning card

- Probleme: dev integration != assurance operationnelle.
- Invariant: les preuves du code ne modifient pas l'autorite du gate.
- Pattern: separation quality gate / security qualification gate.
- Anti-pattern: appeler une CI verte une homologation de production.
- Test: SHA et run exacts du branch + main post-merge.
- Risque residuel: egress reel, CDN/IP rotation, audit independant.

