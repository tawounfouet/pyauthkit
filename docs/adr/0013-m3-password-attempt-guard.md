# ADR-0013: Mandatory host-owned password attempt guard

- Date: 2026-11-02
- Status: PROPOSED / SECURITY REVIEW REQUIRED
- Milestone: M3 / WP27-022
- Pull request: #75

## Problem
A correct Argon2id verifier alone does not prevent online guessing. A Python
library cannot inspect all HTTP requests or enforce globally consistent limits
across hosts. Silently omitting a guard would be especially hazardous.

## Decision
Require the operator to inject a `PasswordAttemptGuard` at M3 bootstrap;
failure to supply it blocks construction. The authenticator invokes it before
any credential resolution/KDF. Denied attempts do not enter the KDF path;
an unavailable guard produces a technical failure, not successful authentication.
The port is scoped and accepts correlation + untrusted lookup hint only.
There is deliberately NO permissive production default adapter.

## Limits
The library cannot prove that arbitrary host-supplied implementations enforce
quotas, coordinated distributed counters, per-IP defenses, bot policies or
safe HTTP response shaping. The host must qualify these with real deployment
tests, especially for distributed rate limiting and privacy. A test fake
returning True proves only SPI wiring.

## Tests
Missing guard at bootstrap, guard rejection, guard outage and existing
real-KDF integration with explicitly named test guard.
