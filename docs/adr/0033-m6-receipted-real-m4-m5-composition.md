# ADR-0033 - M6 receipted gateway for actual M4 and M5 verification

Date: 2026-11-06
Status: PROPOSED / EXPERIMENTAL / NO INDEPENDENT SECURITY APPROVAL

## Context

ADR-0032 introduced an experimental M2 receipt gateway using a synthetic
password verifier. A synthetic M2 success cannot qualify API key possession
or JWT signature checking. The two existing M6 composition paths must retain
their own trust requirements while sharing one receipt-before-return boundary.

## Candidate decision

Add two narrow application compositions without a generic user-supplied
authenticator list. `compose_receipted_api_key_gateway` calls the existing
async M4 HMAC composer, including the complete scoped `SecretRef` preflight,
credential owner, attempt guard, final M2 policy and per-attempt key
resolution. `compose_receipted_jwt_gateway` calls the existing v2 M5 RS256
verifier, including exact audience/issuer, static keyset or pinned HTTPS JWKS
egress grants, trusted scope and final policy. Each uses the existing M2
runtime with no additional event sink, then returns only a
`ReceiptedDecisionGateway` as the documented integration surface.

These candidates admit exactly one method per host binding (API_KEY for
M4 or JWT for M5), explicitly deny mixed-method snapshots, refuse any
non-exact `SqliteRequiredAuditCommitter` and preserve generation-floor
checks. The gateway never returns `Authenticated` until its referenced
committer returns a matching local transaction receipt.

## Security and operational boundaries

1. The public `audit_delivery=required` mode is still **REJECTED**.
2. `ReceiptedDecisionGateway` has a private `_base` reference to the
   real M2 runtime. In-process Python access restrictions are conventions,
   not isolation. A host or framework can create or expose a different M2
   runtime and bypass mandatory audit. Claiming an exclusive entrypoint
   would therefore be inaccurate until host/framework integration enforces
   it and is independently qualified.
3. Local SQLite remains neither cryptographically authenticated, remotely
   independent, nor proven durable across host power loss. The test-only
   persistent receipt does not establish an exactly-once external outcome.
4. M4 uses a synthetic secret resolver and M5 uses synthetic RSA/JWK
   material in these tests. Live AWS IAM/KMS, production JWT HTTPS egress,
   real crash/restart and independent cluster fencing remain open.
5. When the SQLite file disappears, authentication that might otherwise
   have been positive is converted to technical dependency failure at the
   gateway; the existing direct M2 API remains best-effort.
6. Cancellation after a SQLite thread starts may still commit but cannot
   lead the cancelled coroutine to return `Authenticated`. Attempt-ID
   replay is intentionally denied, including across M4 and M5 routes that
   share the same store.

## Evidence and next review

`tests/integration/test_m6_receipted_real_m4_m5.py` exercises both
real verification consumers through the experimental gateway with
positive, negative, replay, outage and post-bootstrap revocation scenarios.

Future required audit needs explicit host route-only ingress, no direct
M2 positive path, authoritative audited storage and genuine crash/partition
tests. ADR-0033 is proposed, not ratified. GATE27-07 stays NO-GO.
