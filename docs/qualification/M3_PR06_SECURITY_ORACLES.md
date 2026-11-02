# M3 PR-06 Security Oracles and Qualification Register

- Date: 2026-11-02
- PR: #75 (draft)
- Gate: #74 GATE27-04 (OPEN / NO GO YET)
- Entry: M2 `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`
- Status: IMPLEMENTATION CANDIDATE / TEST RESULTS PENDING

## Threat -> control -> oracle -> test

| ID | Threat | Security control | Oracle / evidence target | Status |
|---|---|---|---|---|
| M3-T01 | Valid secret not recognized | Real Argon2id | correct secret + ACTIVE + final ALLOW -> Authenticated | NOT_RUN |
| M3-T02 | Wrong secret accepted | KDF mismatch | wrong secret -> Rejected | NOT_RUN |
| M3-T03 | Account enumeration | dummy KDF and host response shaping | missing login -> Rejected, no principal | NOT_RUN |
| M3-T04 | Cross-tenant access | authoritative scoped lookup | foreign record -> no success | NOT_RUN |
| M3-T05 | Credential collision | explicit Ambiguous result | ambiguous -> no success | NOT_RUN |
| M3-T06 | Disabled/revoked record | status checks | no positive result | NOT_RUN |
| M3-T07 | Expired verifier | injected clock, expiry checks | no positive result | NOT_RUN |
| M3-T08 | Argon2 variant downgrade | allowlist algorithm/version | non-id -> rejected BEFORE KDF | NOT_RUN |
| M3-T09 | KDF memory DoS | bounded PHC parser and pool | high m/t/p -> no native execution | NOT_RUN |
| M3-T10 | Async starvation | worker pool | event loop remains responsive | NOT_RUN |
| M3-T11 | Cancellation capacity bypass | release on native completion | canceled caller holds slot | NOT_RUN |
| M3-T12 | Final policy bypass | M2 final gate | valid KDF + policy DENY -> Rejected | NOT_RUN |
| M3-T13 | Secret leakage | redaction; negative outcomes | hash/password absent from repr/results | NOT_RUN |
| M3-T14 | Stale credential accepted | is_current version/status | false -> Rejected | NOT_RUN |
| M3-T15 | Store outage grants access | safe errors | unavailable -> AuthError, no principal | NOT_RUN |
| M3-T16 | Missing claim grants identity | dummy path, generic reject | no principal | NOT_RUN |
| M3-T17..T40 | Full plan qualification scenarios | see uploaded plan §13 | Must map individual tests and CI runs | NOT_RUN |

## Qualification policy

Never replace `NOT_RUN` with `PASS` based on code presence. For a GO, map all 40 scenarios individually, record command, OS/Python, dependency lock, SHA, workflow URLs, reviewer approval and explicit residual risk. The KDF worker pool is local to one process and does not prove network-wide brute-force resistance. Hash migration, password lifecycle and MFA are excluded from M3.
