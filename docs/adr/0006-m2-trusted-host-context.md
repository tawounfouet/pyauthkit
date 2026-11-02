# ADR-0006 - Host-authoritative authentication context

- Status: ACCEPTED FOR M2 DESIGN (implementation evidence is separate)
- Date: 2026-11-02
- Decision owners: PyAuthKit authentication architecture
- Scope: PR-04 / PR-05, WP27-017, ADR28-012 and configuration snapshot decision

## Problem
An HTTP host, forwarded header, tenant claim, OAuth issuer, credential or user parameter may be attacker-controlled. Authentication cannot let those values choose a trusted scope, issuer, key source or policy.

## Decision
The application composition root binds a validated server-controlled route identifier to one `TrustedScopeRef`, one versioned `TrustProfileRef`, and a nonempty permitted-method set. `HostTrustCatalog` validates and freezes these bindings at startup, rejects unknown/duplicate routes, and issues a `TrustedEntryContext` owned by that catalog. The engine invokes the catalog-bound `AuthenticationPolicyGate.preflight` on each attempt. No profile fallback is permitted.

The host integration must resolve routes using a trusted router, authenticated deployment configuration or validated reverse-proxy topology. Raw `Host`, `Forwarded`, `X-Forwarded-Host`, `X-Tenant`, JWT `iss`/`kid`, or user-provided names MUST NOT be used directly as route authority. A claimed tenant is only a mismatch-rejection hint.

## Limit and threat model
Python object identity and restricted constructors guard against accidental misuse by cooperative adapters. They do not isolate malicious code with the process's privileges. A true ASGI/WSGI proxy/host integration is deferred and must receive its own adversarial tests. One attempt uses the same immutable catalog/profile snapshot throughout.

## Alternatives rejected
1. Caller-supplied `TrustedEntryContext(tenant=...)`: promotes unverified data.
2. Default tenant or profile: opens a cross-tenant fallback.
3. Dynamic auto-discovery of providers at call time: widens trust under concurrency.

## Oracles and consequences
- M2-T02/T03/T04/T05/T17/T23: no untrusted selection, no fallback, bootstrap rejection on mismatch.
- PR-04 #69 implements the host catalog; PR-05 MUST invoke preflight itself rather than accepting an externally furnished `VerificationPermitted`.
- Authority of real proxy hosts remains an integration obligation, not a claim of M2 cryptographic verification.
