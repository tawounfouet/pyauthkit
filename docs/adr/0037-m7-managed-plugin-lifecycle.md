# ADR 0037 - Managed lifetime of admitted authenticator plugins

Status: PROPOSED / PR-10 REVIEW
Date: 2026-11-06

## Problem

An exact host grant does not own resources created by third-party factories. If the second plugin fails after the first allocates an async client, the original synchronous loader returns no instances and cannot release resources automatically. An unexpected cancellation can interrupt shutdown.

## Proposed decision

Keep the existing synchronous loader for stateless plugins, and expose an async context manager `activate_approved_authenticators`. The manager performs the same metadata-first preflight, observes each factory instance before structural validation and attempts reverse-order `aclose()` on normal exit, failed bootstrap, and cancellation.

- Optional coroutine `aclose` is the only supported managed closer.
- A synchronous `close` without `aclose` is rejected in this scope.
- A finite timeout in the range (0, 30] seconds bounds a cooperative async closer. This is not a forced kill or hard real-time guarantee.
- Cleanup exceptions are sanitized and remaining closers are attempted.
- Cancellation of the host task does not intentionally cancel the cleanup task.
- The host must drain in-flight verifications before exiting; no automatic drain, process isolation, or rollback of factory side effects is implied.
- The original synchronous loader remains non-owning.

## Alternatives

A mandatory lifecycle method on all authenticators adds needless complexity to stateless verifiers. Synchronous close inside an event loop risks blocking. A global registry does not express ownership. A Python context manager is not a sandbox.

## Evidence

Dedicated M7 lifecycle and cancellation tests, two-tenant plugin scope tests and CI at an exact SHA. Independent review remains required for GATE27-08.
