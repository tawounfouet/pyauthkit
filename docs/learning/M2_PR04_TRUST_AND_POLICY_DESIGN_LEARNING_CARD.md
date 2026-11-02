# M2 PR-04 - Host Context & Policy Preflight Design Learning Card

- **State:** IMPLEMENTING / GATE27-03 NOT QUALIFIED
- **Work packages:** WP27-016 (partial), WP27-017 (host binding)
- **Design sources:** specs 07, 09, 20, 24, 25; roadmap 27 section 15; bootstrap 28 section 46

## Problem and security boundary

A caller may supply an identifier, tenant hint, token claims, headers or
evidence. None of these may choose a trusted tenant, allowed method or
verification key source. A host-owned bootstrap binding determines the
active scope and trust profile, and the policy gate enforces method and
context consistency before any verification starts.

## Pattern choice

- Immutable **bootstrap catalog**, not a mutable discovery registry.
- Explicit **domain/application service** to enforce a safe decision boundary.
- **Dependency Inversion**: future engine consumes the context contract, not
  HTTP routes, a Django request, a storage engine or PyIAMKit.
- **Result Object** for preflight verdicts. A `VerificationPermitted` does
  not mean `AUTHENTICATED`.
- No Strategy, Chain of Responsibility, provider discovery or framework
  dependency: they add complexity without demonstrating provenance.

## Security contract

- `HostBinding` is accepted only at trusted configuration/bootstrap, with
  exact scope/profile match and a non-empty set of approved evidence methods.
- `HostTrustCatalog` copies bindings into an immutable snapshot; duplicate,
  unknown and empty bindings are rejected without fallback.
- A `TrustedEntryContext` is created from the catalog, whose `owns`
  check compares *object identity*, rejecting a fabricated context or one
  belonging to another catalog.
- `AuthenticationPolicyGate.preflight()` returns only permission to *try*
  verification, `Rejected`, or `AuthError`. There is **no success factory**.
- A caller's claimed tenant may cause a denial if inconsistent; it cannot
  select the effective tenant or approved trust profile.
- **Critical host precondition**: the host route passed to the catalog must
  be established and validated by the application, never sourced directly
  from a client `X-Tenant`, `Forwarded`, JWT `iss`, `kid`, or request
  parameter without authoritative host verification.
- Python-level constructor blocking or object identity is defense in depth
  for normal integrations, **not** an isolation boundary against privileged
  arbitrary Python code.

## Rejected alternatives

A single caller-controlled `TrustedEntryContext(tenant=request.tenant)`
would silently promote an unauthenticated string into authority. A default
trust profile on unknown routes would create cross-tenant fallback. Both
approaches are rejected.

## Test oracle

Negative cases: unknown route, wrong tenant claim, disallowed method,
duplicate route, empty or mismatched bootstrap, fabricated/foreign context,
mutation, and no issued `Authenticated` principal. Property tests may be
added as engine behavior is introduced in PR-05.

## Deferred work

PR-05 adds async AuthenticationEngine, approved Authenticator SPI and immutable
authenticator registry, timeout and cancellation semantics, and final
positive AuthenticationPolicyGate transition *after* verified evidence. A
fake authenticator is test-only; this PR offers no production authentication.
