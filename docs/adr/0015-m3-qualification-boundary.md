# ADR-0015: Evidence and release boundary for M3

- Date: 2026-11-02
- Status: PROPOSED / REVIEW REQUIRED

## Decision
Treat M3 source code, tests, CI and gate approval as separate milestones.
No release claim is made by adding an Argon2 adapter or obtaining a green
single-platform unit test. Qualify against M3-T01..M3-T40, including negative
and adversarial cases, platform wheel imports, resource limits, store freshness,
host rate limits, sanitized telemetry, benchmark p50/p95/p99 and residual risks.

## Consequences
Keep PR #75 DRAFT, GATE27-04 #74 OPEN and main unchanged until the evidence
register is completed and independently reviewed. An upstream M2 GO is an
entry condition, not an implicit M3 GO. No automatic password change/reset,
password migration, MFA, token issuance or IAM permissions are delivered.
