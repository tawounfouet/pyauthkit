# ADR-0014: M3 verifier outcome and mandatory M2 final policy

- Date: 2026-11-02
- Status: PROPOSED / REVIEW REQUIRED

## Decision
Implement `PasswordAuthenticator` as one explicitly composed implementation of
the M2 `Authenticator` SPI. After real Argon2id verification, scoped active
credential checks, current-version confirmation and admission guard, it may
issue only the internal M2 `VerifiedOutcome`. The unmodified M2
`AuthenticationPolicyGate` remains mandatory for public `Authenticated`.

## Why not create a direct login result?
Direct success in an adapter conflates proof verification with the policy
decision and bypasses the M2 trusted-scope and attempt-token controls.

## Limitations and proof
Tests must show a correct password with final policy DENY still rejects; forged
or stale outcomes and foreign scopes cannot be promoted. In-process Python
private helpers are not security isolation against malicious loaded code.
