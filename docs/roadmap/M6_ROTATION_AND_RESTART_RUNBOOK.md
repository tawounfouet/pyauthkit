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

## SQLite reference ledger drill (M6 iteration 6)

The optional adapter in `pyauthkit.adapters.generation_sqlite` is a
**single trusted local-host reference** for a persisted monotonic floor.
It is not distributed consensus, a tamper-resistant HSM, a managed secrets
store, or a replacement for protected deployment control planes.

1. An authorized host administrator explicitly provisions the ledger **once**
   in a protected, already-existing local directory, with a documented
   `initial_floor`. Do not create a replacement ledger on startup if one is
   missing or corrupt. Treat such an event as a security incident.
2. The host retrieves the authentic configuration snapshot and calls
   `prepare_with_generation_ledger` (or the async variant) with an approved
   `SqliteGenerationFloorLedger` and a trusted builder. The builder **must**
   pass the supplied floor as `minimum_generation` to M2/M4/M5 composition.
3. The helper reads the floor, checks candidate freshness, prepares the
   engine and its dependencies, validates snapshot identity and then commits
   the candidate floor by atomic SQLite compare-and-advance. A conflicting
   commit refuses activation; no partially composed engine is returned.
4. The host activates routing **only after** a runtime is returned. The
   host still owns drain, fence, rollback authorization and replica routing.
   The SQLite adapter does not switch traffic or revoke old credentials.
5. A crash after the generation CAS but before traffic switch may advance the
   floor without activating the service. Restart with the same generation
   and valid dependencies; do not silently revert to an older generation.
6. A missing file, altered schema, unsafe journal mode, incomplete transaction
   or stale floor must result in operator intervention, **not** automatic reset.
7. Never put the SQLite database on a shared NFS volume or assert multi-node
   anti-rollback. Read-only host permissions alone do not prevent a process
   with file or directory write permission from substituting the database.

### Example (trusted host-side Python; synthetic verifier omitted)

```python
from pathlib import Path

from pyauthkit.adapters.generation_sqlite import SqliteGenerationFloorLedger
from pyauthkit.configuration.generation import prepare_with_generation_ledger

ledger = SqliteGenerationFloorLedger(path=Path("/protected/host/state/m6-generation.db"))
runtime = prepare_with_generation_ledger(
    snapshot,
    ledger=ledger,
    build=lambda floor: compose_authentication_engine(
        snapshot,
        authenticators=trusted_authenticators,
        minimum_generation=floor,
    ),
)
# The host may route to runtime only after this function returns.
```

The example assumes the administrator provisioned the database previously.
It does not authorize using a synthetic verifier or treating SQLite as
a remote multi-replica coordinator.

## AWS Secrets Manager reference consumer (M6 iteration 7)

1. The host creates a Secrets Manager SDK client with explicit region,
   IAM identity/role, bounded connect/read timeouts, bounded retries and no
   custom unreviewed endpoint. No account credentials are embedded in config.
2. The host config defines `SecretRef(provider="aws-secrets-manager", ...)`
   and separately maps that complete logical reference to the exact full ARN.
   `SecretRef.version` must be the AWS VersionId (not a mutable alias).
3. AWS IAM permits `secretsmanager:GetSecretValue` on only the intended
   resources. When a customer-managed KMS key protects a secret, `kms:Decrypt`
   must be restricted to that key and use. Do not grant secret-write/rotation
   privileges to the verification process.
4. The adapter requests exact VersionId with AWSCURRENT. The response must
   confirm the same ARN/version and contain `SecretBinary`. The M4 HMAC
   consumer requires exactly 32 bytes and obtains them for each verification.
5. The host rotates by installing the new AWS secret VersionId, applying a
   new approved M6 snapshot/generation, preflighting, and switching traffic
   only after readiness. Do not silently reuse AWSPREVIOUS after revocation.
6. At an incident, deny a failed lookup (resource missing, stage moved,
   response mismatch, IAM/KMS error, timeout). SDK exception text and raw
   material should never be written to application logs.
7. Live qualification requires a dedicated test account, IAM least
   privilege, a customer-managed KMS key if used, CloudTrail/event review,
   network policy checks, simulated throttling and mid-flight rotation.

**SDK risk:** The adapter runs the synchronous `get_secret_value` call
through an async worker thread. Cancelling/expiring the calling coroutine
does not stop an SDK call already executing. Bound AWS SDK I/O and retry
settings and worker concurrency in the host. No real account was used in
the candidate tests.
