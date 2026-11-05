# M6 runbook - Trusted key rotation by managed restart

Date: 2026-11-05
Status: candidate operations guidance, not a claim of production readiness.

## Preparation (host-owned)

1. Identify the exact deployed generation G1 and its approved scope/profile
   references, credential-owner state, protected M4 key refs and audit mode.
2. Obtain G2 from a host-controlled source with allowed provenance, explicit
   generation increment, and newly versioned SecretRefs.
3. Install new material in the approved provider. Keep the exact scope and
   purpose rights minimal; do not reuse old references as an implicit alias.
4. Prepare the credential-owner migration. Existing records signed under G1
   require an explicit overlap policy or a planned invalidation; PyAuthKit
   does NOT silently re-HMAC records or guarantee zero downtime.

## Candidate pre-activation checks

1. Parse G2 through `load_approved_configuration` with host-owned
   `SourcePolicy` and `SourceProvenance`.
2. Obtain `minimum_generation` from a **durable authoritative host ledger**,
   when anti-rollback across crashes matters. The library only compares it;
   it does not maintain or attest that ledger.
3. Build a fresh M4/M6 composition with
   `compose_secret_backed_api_key_runtime`, exact scoped bindings, an
   approved SecretResolver and existing M4 credential owner/attempt guard.
4. Run synthetic or environment-scoped readiness checks; reject partial
   failures, missing keys, duplicates, incorrect material length and
   unexpected methods or profiles. There is no permissive fallback.
5. Refuse `required` audit unless the separate durable contract is implemented
   and independently qualified; this build admits `best_effort` only.

## Activation and retirement

1. The host starts a new process or otherwise routes **new requests** to G2
   only after the candidate composition is ready. There is no hot-reload API.
2. Do not change the old G1 engine or its catalog in place. Existing in-flight
   requests may finish on G1 under a separately approved drain strategy.
3. Update the host-ledger generation floor only using an atomic, durable
   mechanism appropriate to the deployment. A raw in-memory integer is not
   sufficient for crash-safe anti-rollback.
4. Revoke/retire G1 references and credentials under an explicitly chosen
   overlap period. Verify provider revocation and credential owner consistency.
5. On G2 failure, do not restart an older generation unless a separate,
   explicitly authorized recovery policy approves it. No silent rollback.
6. Retain minimal audit/provenance evidence without secret material.

## Failure drills and proofs

- G2 missing key or key length != 32 bytes: no G2 runtime returned.
- G1 key revoked after startup: AuthN becomes ERROR, not AUTHENTICATED.
- G1 bootstrap replay with floor G2: stale generation rejected.
- Wrong tenant or purpose: no key fetched.
- G1/G2 simultaneous requests: each engine keeps its own profile generation.
- Audit sink outage: `best_effort` result unchanged; no durable receipt claimed.
- Loss of durable external ledger: anti-rollback guarantee unavailable. Operators
  must not assert it as qualified.

Rollback/incident owners, incident run IDs, start/end time and the exact SHA
should be recorded by the deployment host, not inferred from documentation.
