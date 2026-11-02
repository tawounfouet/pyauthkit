# PR-05 Execution - M2 Authentication Engine & Ports

- Status: IMPLEMENTATION CANDIDATE / REVIEW PENDING
- Pull Request: https://github.com/tawounfouet/pyauthkit/pull/71
- Baseline: main `8b2f2df35aecfe8e85cf0300606a2ce482514c1f`
- Gate: https://github.com/tawounfouet/pyauthkit/issues/70
- Maturity: NO PRODUCTION VERIFIER, NO AUTHENTICATION RELEASE

## Completed in candidate branch

- [x] ADR-0006..0009 and documented independent adversarial oracles.
- [x] `Authenticator` + `AuthenticatorLookup` async-first ports.
- [x] Explicit `AuthenticatorRegistryBuilder` with one-way freeze, exact resolution.
- [x] Attempt-bound outcome provenance and immutable verification context.
- [x] Explicit `AuthenticationPolicyGate.final_decision` default deny.
- [x] `AuthenticationEngine.authenticate` with preflight, registry, verification,
      coherence validation, final policy and redacted result.
- [x] Timeouts, cancellation propagation, mapped technical failures.
- [x] Best-effort sanitized event port; no guarantee of durable recording.
- [x] Synthetic fake verifier only under tests/ and wheel exclusion check.
- [x] Design Learning Card and initial PR #71.

## Required before PR-05 GO

- [ ] Ruff lint and format pass on the latest PR SHA.
- [ ] Strict mypy, pytest (including negative/property tests) pass.
- [ ] Architecture fitness, five wheel/sdist matrix jobs and secrets scanning pass.
- [ ] All M2-T01..24 cases tagged PASS, N/A with rationale, or explicitly blocked.
- [ ] Adversarial security review with no unresolved P0.
- [ ] Explicit merge under protected ruleset, without admin bypass.
- [ ] 7/7 protected main CI checks pass after merging.
- [ ] GATE27-03 formal decision with proof links and residual risks.

## Non-goals

No M3 password hashing/KDF, M4 API Key verifier, M5 JWT/JOSE validation,
WebAuthn, MFA, sessions, OAuth issuer, OIDC, SAML, IAM permissions or PyPI
release. No runtime fake registered by default. Python-level object markers
are not a sandbox.

## Tracked work packages

- WP27-013: async engine sequencing.
- WP27-014: authenticator protocol with test fake.
- WP27-015: immutable registry and controlled bootstrap.
- WP27-016: mandatory final policy after PR-04 preflight.
- WP27-018: timeout, cancellation, exceptions.

**Do not close GATE27-03 on a passing PR run alone. Post-merge CI is required.**
