# M4 - Paquet d'arbitrage du gate (v2, alignement plan detaille)

> **Etat : PREPARED FOR HUMAN DECISION / NO-GO.**
> PR #76, issues #77 (qualification), #78 (ratification), #79 (review).
> Source precise : `M4_2026_11_05_SOURCE_MATRIX.md` et plan M4 05/11 §20/§22.

## Decision A - Propriete et priorite des exigences

Confirmer la transcription fidele des **40 oracles, 39 P0 + 1 P1**, et
des **16 criteres G5** du plan M4. Les anciens catalogues V1 sont
SUPERSEDED, et non une source normative concurrente.
- Decision : **ADOPT / AMEND / REJECT**, actuellement **PENDING**.
- Owner, version, SHA, objections et date : **NON RENSEIGNE**.
- Issue a traiter : #78.

## Decision B - Evaluation independante et risques

Le reviewer doit conduire les controles de `M4_SECURITY_REVIEW_CHECKLIST.md`,
rendre un verdict par oracle et gate, verifier ADR-0016/17/18 et
nouvel ADR-0019 sur le guard, evaluer R-M4-01..10 et F-M4-01, decider
la portee host et l'exemption eventuelle du P1 T28.

Le choix M4 sur base M2 doit etre arbitre en tenant compte de M3 PR #75.
Le resultat ne peut pas etre inferé des checks GitHub (7 requis / 8 jobs
Actions) ni d'une configuration ruleset 0 approbations.

- Reviewer independant, autorite, conflits d'interets : **NON RENSEIGNE**.
- Profil TLS/proxy, KMS, logs, limites revoke-to-deny : **NON RENSEIGNE**.
- Statuts par G5, risques et decision ADR : **NON RENSEIGNE**.
- Verdict actuel : **NO-GO**.
- Issue a traiter : #79.

## Decision C - Fusion conditionnelle et revalidation

Seulement en cas de GO signe :
1. Figer SHA de PR #76, CI exact-HEAD, exiger les reviews legitimement
   approuvees et ruleset confirme.
2. Lever Draft si les conditions de review sont reunies.
3. Merger sans bypass; verifier nouveau SHA de `main` et ses checks.
4. Mettre a jour le gate avec preuves de l'integration reelle et
   fermer seulement les issues veritablement resolues.
5. La release/production reste independante du merge.

- Autorisation de merge : **NON DONNEE**.
- Owner/date/SHA : **NON RENSEIGNE**.

Un GO ne doit pas etre declare a partir d'une acceptation supposee
ou d'un reviewer fictif. **GATE27-05 reste NO-GO.**
