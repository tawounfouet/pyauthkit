# M6 Design Learning Card - Trusted Bootstrap and Secret Consumer

Date: 2026-11-05
Status: IMPLEMENTED + TESTED in a defined synthetic M4 integration scope;
not independently qualified, not accepted as a stable public contract.

## Problem first

A valid configuration dictionary may name an unapproved provider, method,
tenant or JWT trust profile. A secret reference in such a dictionary is not
evidence that a consumer is authorized to receive the secret. A provider
might revoke a key between application startup and authentication.

## Trust boundary and invariant

Only host-approved provenance, route bindings, secret grants and consumer
bindings are admitted. `SecretRef` carries no secret. The M4 HMAC verifier
receives material through a narrow `ApiKeyProtectionKeySource` only after
exact scope, key reference, version and purpose checks. If a dependency
fails, no verifier may return a positive authentication outcome.

## Design reasoning

- Use immutable Value Objects for source identity, generation and SecretRef,
  and explicit composition for the single engine generation.
- Use Ports & Adapters only where a real dependency varies: M6 SecretResolver
  to M4 ApiKeyProtectionKeySource. Avoid a global ServiceLocator.
- Reuse M2's AuthenticationPolicyGate for final AuthN. The adapter does not
  introduce a second authorization or JWT verification decision.
- Reject generic bootstraps with unconsumed secret refs, rather than claiming
  that the presence of a SecretResolver grants trust.
- Build a new runtime for rotation; do not mutate the old engine during a
  request. Concurrent G1/G2 runtimes require host-controlled routing.
- `best_effort` audit is not durable and does not own a transaction; required
  audit is rejected at bootstrap until a durable committer exists.

## Alternatives rejected

Raw secrets in TOML/env substitution; implicit default provider; an unbounded
global key cache; best-effort audit mislabeled durable; a mutable registry;
hot reload without a generation pin; plugin discovery as automatic admission.

## Evidence and falsifiability

The test suite exercises the M4 HMAC reference vector, wrong API keys, wrong
namespace and capability, missing/revoked key, provider canary in exceptions,
concurrent G1/G2 and stale-restart denial. See
`tests/integration/test_m6_secret_backed_api_key.py`.

Security limits: only synthetic provider and credentials, Python memory cannot
guarantee secret zeroization, an in-process Python package is not a sandbox,
and an external durable generation ledger plus independent review is needed
for a stronger anti-rollback/release claim.
