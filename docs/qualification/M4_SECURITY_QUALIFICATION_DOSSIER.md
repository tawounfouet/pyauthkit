# PyAuthKit - M4 API Key : dossier de qualification securite v2

> **Statut : TECHNICAL CANDIDATE / GATE27-05 NO-GO**
> Mise a jour : 2026-11-05. Ce document remplace l'ancien dossier qui
> utilisait une correspondance M4-T/G5 erronee.
> **Decision humaine independante : NON RECUE.** Ce n'est pas une certification.

## 1. Source et priorites

La source de verite des noms M4 est le plan detaille fourni au projet,
`2026-11-05_PYAUTHKIT_M4_API_KEY_AUTHENTICATION_IMPLEMENTATION_PLAN.md`,
sections 20 (40 oracles) et 22 (16 G5). Le fichier
`M4_2026_11_05_SOURCE_MATRIX.md` est sa transcription de reference.
`M4_CANDIDATE_ORACLE_CATALOG_V2.md` lie les preuves au plan;
les versions V1 sont des archives SUPERSEDED et ne sont plus utilisables
pour rendre un verdict. Les priorites du plan sont **39 P0 + 1 P1 T28**.

## 2. Baseline technique verifiee, pas un GO

- Reference code avant cette mise a jour documentaire :
  `f96690a7663a7b63ddd50dec58bb09c1d80bae16`.
- [Workflow 42076715449](https://github.com/tawounfouet/pyauthkit/actions/runs/42076715449) :
  **8/8 jobs SUCCESS**, dont quality, security, PostgreSQL/Redis HTTP et
  les cinq variants packaging Ubuntu 3.12/3.13/3.14, macOS 3.12, Windows 3.12.
- Quality : **218 tests passed**, strict mypy, Ruff et fitness architecture.
- Host : **20 tests passed** avec PostgreSQL/Redis reels, HTTP loopback et
  deux processus Uvicorn distincts. Le wheel M4 exerce un HMAC positif et
  un secret modifie depuis un venv isole, sans extras Web/DB.
- Timing observation : **50 mauvaises preuves et 50 selectors absents**,
  p50/p95/p99 par classe et intervalle exploratoire des medianes.
  Ce n'est pas une demonstration d'equivalence statistique.
- Le statut de preuve demeure limite aux environnements CI;
  ce dossier documentaire a un nouveau SHA et doit lui-meme repasser CI.

## 3. Etat des 40 oracles (verification de traçabilite)

| Statut d'evidence candidate | Nombre | Signification |
| --- | ---: | --- |
| `EVIDENCE_REFERENCED` | 29 | Noeuds de tests et preuve CI identifiables, non revus independamment |
| `PARTIAL` | 10 | La preuve ne satisfait pas encore l'ensemble des conditions du plan |
| `MISSING` | 1 | Aucun test/couverture suffisante pour ce choix, P1 T28 |
| **`APPROVED`** | **0** | Aucune adjudication de reviewer valide |

Les limites prioritaires demeurent :
- T25, T35 : temps maximal de propagation des revocations et caches dans
  l'environnement cible non contracte.
- T27/T28 : rotation NO_OVERLAP testee dans le banc, mais le choix owner
  et l'exemption P1 T28 ne sont pas signes.
- T29 : test de non-fuite sur objets/evenements et refus HTTP, mais
  pas sur toutes les traces proxy/SIEM de deploiement reel.
- T31 : statistiques exploratoires en CI loopback, pas de test host
  TLS/proxy avec seuil d'acceptation prealablement defini.
- T32/T33 : charge et cancellations testees en laboratoire, pas de SLO
  ou de nettoyage distribue garanti en exploitation.
- T38 : M1/M2 passes sur base M2, tandis que M3 PR #75 demeure non fusionnee;
  l'owner doit trancher la strategie G5-01.
- T39/T40 : wheel smoke M4 et CI multi-OS ont passe sur le SHA de reference,
  mais l'approbation doit porter sur l'exact HEAD final.

## 4. Frontieres de securite

```text
Client opaque bearer
  -> route hote approuvee (pas de tenant client)
  -> M2 preflight + guard (Redis, tenant/peer/selector)
  -> SELECT PostgreSQL scope_id ET key_id (lookup)
  -> HMAC secret complet sous key_ref allowliste
  -> is_current record/version/status apres HMAC
  -> VerifiedOutcome interne, jamais permission IAM
  -> M2 AuthenticationPolicyGate.final_decision
```

Un bearer peut etre rejoue s'il est expose. Aucun membre de la chaine ne
garantit par lui-meme la non-enumeration par timing, la linearizabilite
apres derniere relecture DB, TLS/proxy, gestion de KMS reel ni audit durable.
Le banc `qualification/m4_host` n'est **pas** une implementation de production.

## 5. Dossier pour les reviewers

- Source normative : `M4_2026_11_05_SOURCE_MATRIX.md`.
- Catalogue et preuves : `M4_CANDIDATE_ORACLE_CATALOG_V2.md`,
  `M4_EVIDENCE_MANIFEST.json` et `scripts/check_m4_evidence.py`.
- Matrice gate : `GATE27-05_M4_API_KEY_DECISION.md`.
- Protocole : `M4_SECURITY_REVIEW_CHECKLIST.md` (v2).
- Gouvernance : `M4_GOVERNANCE_DECISION_PACKET.md` (v2),
  [issue #78](https://github.com/tawounfouet/pyauthkit/issues/78) et
  [issue #79](https://github.com/tawounfouet/pyauthkit/issues/79).
- Risques : `M4_SECURITY_RISK_REGISTER.md`,
  ADR-0016/0017/0018 et ADR-0019 PROPOSED.
- Preuves machine historiques : GitHub Actions liens et job IDs du
  manifeste. Elles sont soumises a retention, pas un depot immuable
  d'artefacts d'audit.

## 6. Autorisation et ordre des operations

Sans ADR approuvees, proprietaire du risque, reviewer independant et
G5-01..16 signes, le statut est **GATE27-05 NO-GO**. La Ruleset GitHub
impose 7 jobs mais configure **zero reviewer obligatoire**; l'absence
de blocage technique au merge ne represente pas un accord de securite.

Le merge PR #76 ne peut etre effectue qu'apres un GO formel.
Une fois merge, inspecter le nouveau SHA de main et sa CI.
La publication PyPI, M8/M9 et tout host production ont des decisions
supplementaires distinctes.

**Verdict : NON FUSIONNABLE EN L'ETAT SELON LE GATE M4.**
