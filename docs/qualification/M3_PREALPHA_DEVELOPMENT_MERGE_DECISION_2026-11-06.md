# M3 - pre-alpha development integration decision (2026-11-06)

Status: **OWNER-AUTHORIZED DEVELOPMENT MERGE ONLY**.

The repository maintainer explicitly requested full technical integration
of M3-M6 into main, with green CI. This authorizes combining M3's test and
cryptographic implementation with the already merged M4, M5 and M6 code
**under the existing protected-branch checks**.

This is not a security review, not GATE27-04 GO, not acceptance of all
M3-T01..T40, not ratification of ADR-0010..0015, and not release or
production authorization. PR #75 / issue #74 security blockers remain open.

The source branch was diverged from main after M4, M5 and M6 landed. The
integration merge retains main's existing CI, M4/M5/M6 adapters and M4
wheel smoke, then adds M3-specific files, Password and qualification
extras, an M3 PostgreSQL/Redis/HTTP CI job and isolated Argon2 wheel smoke.

An exact-head PR CI pass and post-merge main CI must be observed; failures
must not be bypassed. Risk items include deployment TLS/proxy, distributed
abuse budgets, time/identity leaks, backend consistency and independent
security review. Formal gate remains **NO-GO** until these are resolved
and signed by a qualified reviewer.
