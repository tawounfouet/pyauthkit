# PyAuthKit PR-02 secret scan triage

- **Status:** PROPOSED - awaiting CODEOWNER/security sign-off
- **Source run:** https://github.com/tawounfouet/pyauthkit/actions/runs/41406066577
- **Tracking issue:** https://github.com/tawounfouet/pyauthkit/issues/59
- **Scope:** four `Secret Keyword` detections in imported `docs/specs` files
- **Not evidence of production readiness, absence of secrets, or security certification.**

## Technical examination

| Source and line | Meaning | Proposed disposition |
|---|---|---|
| `07` line 1607 | Deliberately incorrect password for a negative tenant test, with `.test` example identity | Synthetic illustration, exact-line exception |
| `10` line 1154 | Enumeration member `PASSWORD` containing its non-secret method identifier | Vocabulary, exact-line exception |
| `10` line 1155 | Enumeration member `API_KEY` containing its non-secret method identifier | Vocabulary, exact-line exception |
| `28` line 423 | Counterexample of unsafe hardcoded login logic explicitly marked NO-GO | Anti-pattern quotation, exact-line exception |

Review based on source context and the detector category. No production token,
private credential or external service access is represented by these strings.

## Guardrails

`scripts/check_secret_scan.py` accepts each reviewed demonstration only if
its exact **path, line number, detector and full line SHA-256** match the reviewed
record. An added finding, renamed detector, moved line or edited example fails
the gate. The output prints **no raw values**. No `docs/specs` subtree is
excluded from the scanner. Only generated virtual environments, transient
scanner output and `.git` metadata are outside the scan.

The four SHA-256 digests in the script represent literal source lines. Each digest has a scoped scanner allowlist comment so its checksum is not mistaken for a credential. These annotations are not proof of secret safety by themselves. A reviewer must consider the context.
`GATE27-01` still requires a security review, a main ruleset and a validated
license/disclosure decision.

## Reassessment checklist

- [ ] Maintainer accepts or rejects the four narrowly scoped exceptions.
- [ ] Security scan passes with no **unreviewed** findings.
- [ ] Negative tests demonstrate new or edited findings cause CI failure.
- [ ] CI run, commit SHA, tools and tested artifact checksums recorded.
