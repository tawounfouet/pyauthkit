# M6 Design Learning Card - Composing audited M4 and M5 without rewriting verification

Date: 2026-11-06
Status: EXPERIMENTAL IMPLEMENTATION CANDIDATE

## Why composition rather than a new verifier?

M4 already binds API-key ownership to a scoped HMAC secret reference, and
M5 already binds RS256 JWT proof to explicit issuer/audience/key sources.
Reimplementing either verification rule inside an audit adapter would create
a divergent trust boundary. Instead, compose the same M2 runtime, wrap the
result and allow the decision to escape only after the receipt is validated.

## Learning patterns

- [DIP / Ports & Adapters] `RequiredAuditCommitter` remains the persistence
  port; M4 and M5 depend on their existing provider-specific ports.
- [Application Service] Each explicit factory owns one allowed mechanism
  and its own trust preflight, then composes a shared decision gateway.
- [Fail Closed] No generic "authenticator" array is accepted in the
  receipted M4/M5 factories. Wrong generation, fake committer and mixed
  method snapshot are rejected.
- [Security Invariant] An M4 HMAC match or M5 cryptographic JWT proof is not
  sufficient for a positive response while the required-audit candidate
  database is unavailable.
- [Separation of Concerns] Host route exclusivity and tamper-resistant
  audit commit guarantees are NOT solved by private Python attributes.

## Verification strategy

Execute synthetic HMAC and RS256 signatures through their real adapters.
Test valid and invalid proof, issued/stale generation, denied secret resolver
and missing audit store. For a shared ledger, the same opaque attempt ID must
not produce two successes across M4 and M5. Never store credentials or
identifiers in the SQLite audit table.

## What is not production-qualified?

The public `required` config stays disabled; real HTTP framework ingress
could bypass this wrapper, and SQLite is not a managed immutable ledger.
No true deployment, AWS IAM/KMS, remote JWKS fault injection, multi-replica
fencing or independent security acceptance has been completed.
