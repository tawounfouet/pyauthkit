# ADR-0011: Argon2id PHC validation and optional dependency

- Date: 2026-11-02
- Status: PROPOSED
- Scope: M3 / PR-06B / WP27-020

## Problem
The KDF library accepts multiple Argon2 formats, including potentially attacker-chosen high cost verifiers. A valid library API call is not enough to enforce a trust profile.

## Decision
Use the maintained `argon2-cffi` via an opt-in `pyauthkit[password]` extra. Verify ONLY canonical `argon2id` PHC version 19, bounded salt/tag lengths and reviewed cost envelopes before native computation. Default floor: 19 MiB, t=2, p=1. Max acceptance and worker memory budget must be reviewed per host.

## Rejected
Generic SHA-256/bare hash; silent fallbacks; automatically accepting Argon2i/d; inferring KDF cost from caller input; rehash writes during login without store ownership.

## Limits
This policy is not a claim of NIST/FIPS compliance. OWASP's minimum is a design input, not a certificate. Version and platform compatibility must be established by CI, dependency audit and benchmark evidence.

## Tests
Real Argon2id correct/incorrect vectors, corrupted PHC, algorithm downgrade and unbounded-cost rejection, optional-extra wheel install.
