# ADR-0008 - Verified-outcome provenance and mandatory final authentication policy

- Status: ACCEPTED FOR M2 DESIGN; NOT an authentication production approval
- Date: 2026-11-02
- Related: ADR27-009, ADR28-014, WP27-016

## Security problem
A positive `AuthenticatorOutcome` is not an authorized `Authenticated` result. If a caller can skip the gate, substitute a verified outcome, mix tenants, or replay a subject from a different attempt, a false identity results.

## Decision
The public runtime entrypoint receives only `AuthenticationRequest` and an already host-issued `TrustedEntryContext`. It *always* runs policy preflight and selects a registered authenticator. It constructs a unique per-attempt in-memory marker and `VerificationContext` bound to the approved `TrustedScopeRef`, versioned `TrustProfileRef`, evidence method and correlation. The selected authenticator returns a discriminated internal outcome; a positive outcome must carry the same attempt marker and profile/method/scope as the verification context. The engine rejects malformed or mismatched positive outcomes before final policy.

Only a positive and coherent outcome passes through `AuthenticationPolicyGate.final_decision`, and only an explicit final allow creates an `Authenticated` value. The engine never accepts a user-supplied `VerifiedOutcome` or `VerificationPermitted` as an input parameter. A private construction utility is permitted for qualified authenticators and test fakes, not exported as a public success API. Python private names and object markers do not protect against privileged malicious in-process code.

M2 demonstrates this path with a fake in `tests/`, never in `src/`; this does not validate real credentials. No AuthN success implies a session, token issuance, IAM account, permission or agent delegation.

## Adversarial independent oracles
- M2-T11: wrong attempt/profile/method/scope -> ERROR, no principal.
- M2-T12: coherent positive outcome plus explicit final denial -> REJECTED, no principal.
- M2-T13: test-only positive verifier plus allow -> AUTHENTICATED with gate called once.
- M2-T24: bypass attempt by verifier directly returning `Authenticated` -> ERROR, no principal.
- Unknown policy / gate exception / invalid final output -> fail closed.

## Limit
Synthetic verification evidence is intentionally not a production cryptographic assertion. The contract admits only intentionally configured adapters and cannot sandbox Python packages. Cryptographic verification and independent security review remain follow-on gates.
