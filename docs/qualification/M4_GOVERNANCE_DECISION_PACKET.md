> **ATTENTION - ARCHIVE HISTORIQUE SUPERSEDEE.** La signification des identifiants
> M4-T01..T40 / G5-01..16 dans ce fichier n'est pas alignée avec le
> plan détaillé M4 du 05/11/2026. **NE PAS UTILISER POUR UNE DECISION.**
> Matrice fidèle à la source : `docs/qualification/M4_2026_11_05_SOURCE_MATRIX.md`.
> Catalogue réconcilié : `docs/qualification/M4_CANDIDATE_ORACLE_CATALOG_V2.md`.
> Les anciens chiffres/états ci-dessous décrivent uniquement les étapes historiques.
>
# M4 - Paquet de decision de gouvernance et revue independante

> **Statut : DRAFT / DEMANDE DE DECISION. Ce fichier n'autorise ni merge ni release.**
> Date : 2026-11-05 | PR : https://github.com/tawounfouet/pyauthkit/pull/76 | Qualification : https://github.com/tawounfouet/pyauthkit/issues/77

## 1. Les deux decisions distinctes

**Decision A : ratifier ou corriger le catalogue M4 v1.0.** L'owner des exigences doit accepter, amender ou refuser la subdivision des 40 oracles et 16 criteres G5. Les specifications 27 et 28 n'en fournissent pas de numerotation normative. La proposition est `M4_CANDIDATE_ORACLE_CATALOG_V1.md`. Ne pas traiter son nombre de lignes comme un contrat signe.

**Decision B : qualifier le systeme dans un profil d'hote defini.** Un examinateur securite/crypto independant doit suivre `M4_SECURITY_REVIEW_CHECKLIST.md` et `M4_SECURITY_RISK_REGISTER.md`, accepter/refuser les ADR-0016/0017/0018, verifier les 40 scenarios contre des preuves et arbitrer G5-01..16. La qualification ne peut pas preceder une decision A explicite.

## 2. Dossier a remettre aux reviseurs

- Plan source : `docs/specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md` §17/§56 et `docs/specs/28_PYAUTHKIT_IMPLEMENTATION_BOOTSTRAP_PLAN.md` §49.
- Rapprochement qualitatif : `M4_CANONICAL_REQUIREMENTS_CROSSWALK.md`; catalogue propose : `M4_CANDIDATE_ORACLE_CATALOG_V1.md`.
- Registre des tests et donnees : `M4_EVIDENCE_MANIFEST.json`; dossier de qualification : `M4_SECURITY_QUALIFICATION_DOSSIER.md`.
- Risques et limites : `M4_SECURITY_RISK_REGISTER.md`; modele de decision : `M4_SECURITY_REVIEW_CHECKLIST.md`.
- Dernier checkpoint **technique** avant cette proposition : SHA `86ab6ce20f882aa86060cc0e0c9ae2e5143a7f0a`, run `42069178325`, 209 tests Python + 13 host, 8/8 jobs CI.
- Les nouveaux commits documentaires devront etre verifies a nouveau sur leur SHA avant toute prise de decision.

## 3. Questions bloquantes qui appellent une vraie autorite

1. **Domaine:** quelles exigences sont P0/P1 pour M4, en evitant la numerotation arbitraire ? Qui en est proprietaire ?
2. **Crypto:** le protocole `ak1`, le format digest/HMAC, les allowlists et la politique de reissue/rotation sont-ils acceptes ? Quid du KMS reel ?
3. **Revocation:** quelle garantie est exigee apres `is_current` et quelle fenetre TOCTOU residuelle est acceptable ?
4. **Perimetre hote:** quel deploiement avec TLS/proxy, stockage, Redis, logs et SIEM est **effectivement** vise ?
5. **Rejeu et fuite:** quelles mesures de mitigation bearer et de redaction seront verifiees dans cet environnement ?
6. **Preuve:** quels journaux CI et artefacts avec empreintes sont archives, qui en garantit la conservation ?
7. **Securite:** un relecteur independant du code est-il designe et habilite a conclure ?
8. **Dependance:** quel traitement du GATE27-04 / PR #75 M3 avant la fusion du PR #76 ?

## 4. Formulaire de decision texte, a remplir dans une issue GitHub

- Decision A : `ADOPT / AMEND / REJECT / PENDING` : **PENDING**.
- Owner exigences, identifiant, role, date : **NON RENSEIGNE**.
- Version catalogue/commit adopte : **NON RENSEIGNE**.
- Ecarts et commentaires : **NON RENSEIGNE**.
- Decision B : `GO / NO-GO / REPORT` : **NO-GO, non adjudique**.
- Responsable securite independant : **NON RENSEIGNE**.
- Perimetre teste et profil de confiance : **NON RENSEIGNE**.
- Risques residuels acceptes et echeance : **NON RENSEIGNE**.
- SHA exact et reference preuves/approbation : **NON RENSEIGNE**.
- Autorisation de merge : **NON DONNEE** ; release : **NON DONNEE**.

## 5. Regles de separation des devoirs

- Ne jamais inferer qu'un auteur de test est un relecteur independant.
- Ne pas demander une review GitHub au titulaire du depot au titre d'une independance fictive.
- Une issue de decision sans approbation conserve un statut ouvert.
- Le passage Draft -> Ready, le merge vers `main`, le tag ou le publish PyPI sont hors du present mandat de revue.
- GATE27-05 reste **NO-GO** tant qu'une vraie decision, rattachee a un SHA, n'a pas ete enregistree.
