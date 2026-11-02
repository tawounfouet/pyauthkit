# Design Learning Card - M1 Domain Kernel (PR-03)

- **Status:** IMPLEMENTING - pending PR CI and GATE27-02 review
- **Milestone:** M1 / WP27-007..012
- **Decision scope:** Non-production domain types; no authentication verifier
- **Sources:** Convention Software Design & Learning, specifications 04-07, 09, 24, 26, 27 §14 and 28 §45

## Problem & actor

An application may accept claimed identifiers and evidence from HTTP, CLI,
agents and framework adapters. Correctly shaped input is not a verified
principal. The domain must preserve this distinction and resist accidental
success construction or leakage of credentials into diagnostics.

## Bounded Context / Authority

- The authentication engine verifies evidence, once its implementation
  becomes available in M2 and later mechanism milestones.
- The host owns effective scope/profile binding (future PR-04).
- The verifier owns cryptographic or credential verification (future PR-05+).
- The authentication policy gate makes the final AuthN decision (future PR-04).
- IAM/PyIAMKit alone owns managed identities, roles and permissions.

## Trust Boundary

| Object | Source | Trust at M1 |
|---|---|---|
| `ClaimedIdentity` | Untrusted caller | No authority |
| `PresentedEvidence` | Untrusted caller | Opaque secret bytes; unverified |
| `AuthenticationRequest` | Transport/application | No scope or policy authority |
| `TrustedScopeRef` | String reference | Well-formed only, never trusted binding |
| `TrustProfileRef` | String/profile reference | Versioned lookup key only |
| `ScopedSubjectRef` | Identity key | Not a verified subject |
| `VerifiedSubject` | Future approved verifier | Reserved constructor, no M1 minting path |
| `Authenticated` | Future final policy gate | Reserved constructor, no M1 minting path |

The words *trusted* and *verified* in a class name never authenticate their
provenance. Python runtime access is not a security sandbox.

## Domain Role / Invariants

- **Value Objects:** `ClaimedIdentity`, `TrustedScopeRef`, `TrustProfileRef`,
  `ScopeProfileRef`, `ScopedSubjectRef`, `CorrelationId`, `ObservedAt`.
- **Sensitive untrusted input:** `PresentedEvidence` is a plain, slotted
  immutable-by-API class. Not a dataclass, because automatic
  `dataclasses.asdict` traversal risks exposing the secret payload.
- **Domain Event:** not introduced. A correlation identifier is sufficient
  for M1; event storage and delivery belong to a later milestone.
- **Outcome vs final result:** `RejectedOutcome` and `ErrorOutcome`
  normalize to `Rejected` and `AuthError`; a positive outcome cannot
  enter a final result without the future policy gate.
- **Discriminated Union:** only `Authenticated` may have a principal field;
  `Rejected`, `AuthError`, `ChallengeRequired` cannot carry one.

Mapping to security requirements: `AUTH-INV-001..010`,
`AUTH-INV-018`, `AUTH-INV-041`, `AUTH-INV-046/047/055/056/061`.
The M1 implementation covers only the structural aspects of these invariants.
Cryptographic claims remain unproven until the relevant later gates.

## Temporal / Concurrency Dimension

- `ObservedAt` accepts aware time and normalizes UTC; `Clock` is injected.
- No implicit `datetime.now()` in domain objects or tests.
- No session TTL, replay lock, revocation or multi-step flow exists in M1.
- `CorrelationId` identifies a trace; it is not a bearer credential.

## Design Pressure

Untrusted input often resembles verified identity fields. A single loose
`Principal(id: str, authenticated: bool)` data container would permit
caller-controlled success without evidence or policy.

## Principles

- **DDD / Explicit Modeling:** separate claims, evidence, identity reference,
  verified subject and final result.
- **SoC and DIP:** domain imports only Python standard library and itself;
  no Web/IAM framework or storage dependency.
- **Fail Closed:** unknown evidence methods, invalid scopes, mismatched
  profile/scope refs and unknown outcome transitions do not default to success.
- **Information Hiding:** dangerous constructor paths are absent and
  representations/serializers exclude sensitive input.
- **KISS / YAGNI:** no universal factory, event store, runtime registry,
  backend adapter or artificial aggregate is introduced in PR-03.

## Algorithm / Data Structure

- Bounded lexical validation for identifiers and trace IDs.
- Frozen dataclasses for immutable, public nonsecret structural values.
- Plain slotted opaque-evidence carrier to avoid generic dataclass dumps.
- Literal-discriminated negative-result variants for safe pattern matching.
- Exact scope-profile consistency check, not a resolver or trust derivation.
- A guarded `normalize_non_success` that fails for unknown and verified outcomes.

## Pattern(s), if genuinely applicable

- **Result Object / Algebraic Data Type** is justified to prevent confusing
  `REJECTED` with `ERROR` and to structurally deny principal on non-success.
  It is not a GoF pattern.
- **Value Object** holds only the immutable identity/time references.
- No Factory/Strategy/State/Observer pattern is claimed for this slice.

## Natural Python Contract

- `ClaimedIdentity` and `ScopedSubjectRef` are deliberately different.
- `PresentedEvidence` rejects empty, oversized and unsupported payloads.
- `AuthenticationRequest` has no effective tenant/profile field.
- Positive `VerifiedSubject`, `VerifiedOutcome`, and `Authenticated`
  cannot be directly constructed through their normal Python constructors
  in M1. M2 needs an approved verification and policy protocol.
- `public_request_summary` and `public_result_summary` are explicit
  serializers. Do not call `dataclasses.asdict` on untrusted request
  graphs for JSON, logging or audit.

## Simplest Alternative & Rejected Options

**Rejected overly complex design:** a single `GenericPrincipal` aggregate
with `authenticated: bool`, inherited Human/Agent classes, a
`UniversalAuthenticationManager`, an event store and a Strategy registry.
It adds hierarchy and mutable authority flags without proving evidence
or the host trust boundary. Using a large graph of factories and Abstract
Factories here would make insecure success paths easy to hide.

**Chosen simpler alternative:** small distinct value objects, exact
negative-result variants and no operational positive constructor yet.
An additional `AuthenticatedPrincipal` class is deferred as suggested
by `05 §7.6` until an observable need arises.

## Failure Semantics & Security

- Rejection: generic public code, no account enumeration or principal.
- Technical error: stable operational code, no raw dependency messages.
- Unavailable dependencies: operational failure, never interpreted as denial
  or authenticated success.
- Evidence: no data in repr, no generic dataclass serialization, no zeroization
  guarantee from immutable Python bytes.
- Status `CHALLENGE_REQUIRED`: reserved without issuing bearer continuations.
- Privileged local Python code can bypass private naming or
  `object.__setattr__`. Those are **not security boundaries**.
  Real authorization must depend on the future host-binding, verifier,
  policy-gate and adapter controls.

## Tests & Evidence

- Unit tests: positive structure, negative validation and boundaries.
- Hypothesis property tests: arbitrary evidence and claims do not become
  authenticated or leak through approved repr/serializers.
- Scope/issuer isolation and deterministic injected time tests.
- Negative constructor tests for the three reserved positive types.
- Architecture and package smoke tests in the existing 7-job M0 CI matrix.
- Evidence URL and SHA will be recorded in `docs/roadmap/PR-03_EXECUTION.md`
  when GitHub CI has actually run.

## Explainability & Provenance

Stable public refusal/technical codes and non-bearer correlation IDs
support triage. No raw identity hints, tokens or credentials are copied
into result objects or public summaries.

## Implementation Status

**IMPLEMENTING** until PR checks, source review and gate evidence have
been independently evaluated. **Not** an implemented authenticator and
**not** production authentication.
