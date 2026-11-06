# M4 - Autorisation de fusion du mainteneur unique (developpement uniquement)

- Date de la decision : 2026-11-05
- Depot : `tawounfouet/pyauthkit`
- Auteur de la demande : utilisateur se presentant comme l'unique developpeur
  et mainteneur, ayant donne l'instruction explicite en conversation :
  « Pythos, je suis le seul dev et mainteneur et je valide tout,
  faire donc le necessaire pour tout fusionner sur la main ».
- Nature de la trace : **consentement utilisateur recueilli dans la conversation**
  et retranscrit par l'assistant. Cette trace ne remplace pas une signature
  cryptographique, une review GitHub independante ou une preuve d'identite externe.
- Cible : [PR #76, M4 API Key Authentication](https://github.com/tawounfouet/pyauthkit/pull/76).
- Perimetre : **INTEGRATION SUR MAIN POUR DEVELOPPEMENT/PREALPHA UNIQUEMENT**.
- Baseline de revue technique :
  `e9a3613666be685482a7ab141b4bbcf7ce797eaa`,
  [CI 42077293032](https://github.com/tawounfouet/pyauthkit/actions/runs/42077293032),
  **8/8 SUCCESS, 218 pytest, 20 tests hote de reference PostgreSQL/Redis/HTTP**.
- L'implementation de production, la publication de package et la
  certification de securite ne sont **pas** autorisees par cette decision.

## 1. Decisions attribuees au mainteneur unique

1. **Accepter le merge de PR #76 sur `main`**, sous reserve des required
   checks GitHub verts sur le SHA final, du non-contournement de la Ruleset et
   de la verification post-merge.
2. **Adopter pour la tracabilite de developpement** la transcription de
   l'implementation plan M4 du 05/11/2026 : 40 oracles, dont 39 P0 et
   `M4-T28` P1, et 16 G5. Cela ne signe aucun des 40 verdicts de securite.
3. **Retenir `NO_OVERLAP` pour le banc M4** : une rotation atomique de
   verificateur invalide l'ancienne preuve apres commit. L'option
   `BOUNDED_OVERLAP` n'est pas retenue pour ce prototype.
   `M4-T28` est **NOT_APPLICABLE au profil de laboratoire NO_OVERLAP**,
   pas un test `BOUNDED_OVERLAP` passe ni une politique production approuvee.
4. **Permettre M4 sur la base M2** sans attendre la qualification de
   [M3 PR #75](https://github.com/tawounfouet/pyauthkit/pull/75).
   M3 conserve sa propre PR et son gate; aucune fusion de M3 n'est
   induite par cette autorisation M4.
5. **Accepter explicitement pour ce merge de developpement** le risque
   transitoire de travail avec une seule personne et des preuves partielles.
   Le mainteneur et l'assistant ne se presentent jamais comme un reviewer
   independant. La derogation de revue solo deja tracee dans
   [issue #64](https://github.com/tawounfouet/pyauthkit/issues/64)
   est invoquee pour cet objectif limite, sans supprimer les exigences
   strictes de revue avant release.
6. Les decisions techniques proposees dans ADR-0016..0019 sont
   **admises comme options d'implementation experimentale** pour developper
   sur `main`, mais leur **approbation de securite externe reste PENDING**.

## 2. Limites expressement non levees

- **GATE27-05 SECURITY / INDEPENDENT QUALIFICATION = NO-GO**.
  Cette derogation autorise une **fusion de code prealpha**, pas la
  constatation que 39 P0 et 16 G5 ont ete independamment approuves.
- A la revue precedente, le manifeste presentait
  **29 EVIDENCE_REFERENCED, 10 PARTIAL, 1 MISSING P1** et
  **0/40 approbations independantes, 0/16 signatures G5**.
  Ces valeurs ne sont pas reconverties artificiellement en `PASS`.
- Il reste notamment les garanties de securite en environnement reel :
  TLS/proxy peer, KMS, logs et audit durable, risque de rejeu bearer,
  propagation de revocation apres le dernier `is_current`, anti-enumeration
  reseau, SLO/charge, gestion des incidents.
- Aucun nom de reviewer, audit externe ou signature ne peut etre invente.
- Pas de publication PyPI, production, tag de release securisee,
  migration M8/M9 en statut GO ou promesse de conformite.

## 3. Exception de processus et conditions de validite

**Reference :** exception solo mainteneur pour M0-M7 dans issue #64,
**limitee a un depot de developpement prealpha**, maintenue ici sur
decision explicite de l'utilisateur proprietaire du chantier.

La derogation expire **avant GATE27-09 (M8), avant toute publication
PyPI ou avant tout deploiement de production, selon le premier evenement**.
Elle est revoquee plus tot si un defaut de securite critique invalide les
hypotheses de cette decision. L'issue #79 de revue independante
demeure **OPEN**, pas cloturee par une approbation presumee.

Aucune protection `main` ne doit etre desactivee ou contournee;
la regle de PR et les sept checks requis restent applicables.

## 4. Protocole d'integration et controle post-merge

- [ ] Conserver cette trace dans le HEAD de PR #76.
- [ ] Rejouer les 8 jobs CI sur le SHA documentaire final.
- [ ] Passer PR #76 de Draft a Ready uniquement pour permettre le merge
  explicitement autorise par le mainteneur.
- [ ] Fusionner par GitHub avec `expected_head_sha` (sans bypass).
- [ ] Relever le SHA reel de `main`, le statut `merged` et la CI de `main`.
- [ ] Reporter le merge dans l'issue #77 et conserver #79 pour la
  qualification independante plus tard.

**Decision operationnelle : GO POUR MERGE DEV UNIQUEMENT.**
**Decision de securite independante : NO-GO.**
**Release et production : NO-GO.**

Les cases restent historiques tant que leurs actions ne sont pas
effectivement observees. Les preuves d'execution finales sont
publiees dans la conversation et dans les issues GitHub.
