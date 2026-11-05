# PR-09 - M6 Configuration, Secrets and Minimal Audit

Status: IN PROGRESS / DEVELOPMENT BRANCH, not qualified.
Date: 2026-11-05.
Base commit: `edeef0288ed9560324bac6f065a4d06057d5faeb`.
Branch: `feat/m6-config-secrets-audit-pr09`.

## Scope delivered as development code

- WP27-033: explicit host mapping with host-owned provenance allowlist. No environment
  discovery, no merge of security-critical fields, unknown keys always rejected.
- WP27-034: typed, deeply immutable snapshot (tuple/frozenset constituents),
  generation and source admission; explicit composition with M2 catalog, M2 gate,
  M2 engine and frozen authenticator registry. Missing authenticator means no start.
- WP27-035: `SecretRef`, purpose-and-namespace-granted asynchronous resolver,
  sanitized failure, synthetic-only in-memory adapter. Material does not enter
  `ConfigurationSnapshot`. A configured reference **blocks engine composition**
  until an approved consumer integration is actually built and verified.
- WP27-036/037: preserve M2 `AuthenticationEvent` and `AuthenticationEventSink`,
  add bounded best-effort adapter and non-durable memory sink. `required` mode
  is **rejected**, not simulated. Cancellation propagates.
- WP27-038: explicit generation floor at bootstrap. A durable, authenticated
  external generation ledger is the responsibility of the host. Without it,
  crash-safe anti-rollback across restarts is NOT guaranteed.

## Security and API limits

This is an internal, provisional composition API. No stable public SDK exports,
no Vault/KMS adapter, no durable audit, no hot reload, no cryptographic
qualification, and no deployment approval are claimed. The synthetic verifier in
tests does **not** perform real JWT verification. The existing M5 verifiers remain
the responsibility of the M5 security gate.

## Verification checklist

- [ ] CI at exact PR head SHA
- [ ] Ruff
- [ ] mypy strict
- [ ] M6 source, snapshot, secret, audit and rotation negative tests
- [ ] M2/M4/M5 regression
- [ ] packaging smoke and architecture fitness
- [ ] GATE27-07 independent review
- [ ] M5 GATE27-06 remains NO-GO
- [ ] Release/publication remain unauthorized

## Design learning

Problem: external operational inputs can widen trust or leak secret material.
Trust boundary: the Python host asserts source and scope authority, NOT the
source file nor the caller's JWT/header. Pattern: simple typed values, a strict
reader and ports only where an actual adapter varies. Alternatives rejected:
automatic discovery, dict union for trust blocks, secret string interpolation,
undocumented durable-audit claim, and a mutable engine registry.

## 2026-11-05 development iteration 2 - M4 secret consumer integration

- New `ScopedApiKeySecretSource` bridges approved M6 references to M4's
  `ApiKeyProtectionKeySource`, keyed by exact trusted scope and M4 key ref.
  Provider/namespace/purpose/version are explicit; secrets are fetched per use,
  never placed in snapshots or memoized by this adapter.
- `compose_secret_backed_api_key_runtime` is a specialized async composition
  route. It validates complete secret binding coverage, preflights key
  availability and material length, then builds the existing M4 HMAC verifier,
  API Key authenticator and M2 policy-gated engine.
- The generic `compose_authentication_engine` still rejects snapshots
  containing secret references. This remains intentional fail-closed behavior.
- Key rotation is implemented as new configuration generation + new engine
  instance, not hot reload. A provider revocation after successful bootstrap
  triggers a fail-closed dependency error during subsequent verification.
- Host-owned `minimum_generation` remains an injected trust input. This
  package does NOT supply a durable cross-restart ledger.
- Synthetic-only positive and negative integration checks exercise a genuine
  M4 HMAC and the normal M2 final-policy path, not a JWT cryptographic fake.

**Evidence, first post-change CI quality run**: SHA
`46d8915b69f235256715465f6c49416f5bbbd9d3`,
https://github.com/tawounfouet/pyauthkit/actions/runs/42105908829 -
Ruff lint/format PASS, mypy strict 52 source files PASS, 365 pytest PASS,
architecture fitness PASS. These are developer tests, not independent G7 sign-off.

Further verification: dedicated M6 boundary CI job, expanded audit event tests,
candidate oracle evidence register and controlled restart runbook.

## 2026-11-05 development iteration 3 - versioned M5 JWT policy from M6

- Add `schema_version=2` and exactly populated `jwt_profiles` for enabled
  JWT routes. Version 1 remains legacy and has no automatic JWT trust policy.
- Require exact host-bound scope/profile/version, HTTPS issuer, non-empty
  audience, RS256 only, access-token `typ`, explicit size/skew controls,
  and exactly one static public keyset or pinned HTTPS JWKS source.
- Do not let a JWT, its `iss`, `aud`, `jku`, `x5u` or `kid` choose a new
  trust profile. The JWT may only select a kid within the existing profile.
- `compose_trusted_jwt_runtime` performs exact out-of-band static public JWK
  admission or requires independently host-approved source-id/URI/IP egress.
  It composes M5 `JWTAuthenticator` with M2's original policy gate, not a
  second authentication engine or an OAuth/OIDC provider.
- The generic v2 composer denies JWT configurations without this dedicated
  consumer. Mixed v2 secret-backed M4 + JWT composition is **not** admitted
  by the present dedicated paths, preventing unqualified implicit wiring.
- Local tests cover signed JWT success, negative claims, malformed trust
  config, unknown or private JWK, prohibited SSRF URLs/private IP addresses
  and missing or mismatched host egress grants. The M5 HTTPS transport
  handles TLS/DNS/rebinding, but M6 tests do not prove live deployment egress.

Final exact-head CI result: PENDING at time of writing. GATE27-07 remains NO-GO.

## 2026-11-05 development iteration 4 - canonical JSON ambiguity guard

- Add explicit `load_approved_json_configuration(bytes, provenance, policy,
  generation)` as a JSON-only adapter into the existing strict M6 mapping
  loader; this is not file discovery or environment reading.
- Enforce allowlisted source before parsing; reject raw duplicate member names
  at any depth (including JWT `issuer`), nonfinite numbers, oversized documents,
  deep structures and malformed encoding. Mapping-only ingestion still cannot
  retroactively recover JSON duplicate names discarded by the caller's parser.
- Harden schema v2 issuer URI validation against missing hostname, userinfo,
  query/fragment and wildcard authority.
- Add exact negative oracles to the M6 CI job and security tests.

Evidence and GATE27-07: pending exact SHA CI review; no independent sign-off.

## 2026-11-05 development iteration 5 - exact source precedence and metrics privacy

- Introduced `SourceLayerPolicy` and `load_layered_configuration`:
  authority is exactly one host-approved complete mapping, operational layers
  are an exact host-approved low-to-high precedence chain. Only
  `timeout_seconds` can vary. Any attempt to change JWT issuer, tenant,
  routes, secret refs, audit mode, algorithm policy or schema fails before
  activation. No trust-bearing field is deep-merged, and no layer is silently
  skipped. The immutable snapshot records the ordered operational provenance.
- Added optional `BestEffortTelemetrySink` to split minimal audit delivery
  from identity-free metrics. An `AuthenticationMetricsSample` contains only
  method enum, outcome enum and duration seconds. Its only labels are
  `method` and `outcome`, with fixed enumerated values.
- Each telemetry destination has an independent timeout and error handling
  policy; audit failure does not hide a metrics attempt, nor does metrics
  failure mutate an AuthN decision. Async cancellation still propagates.
  In-memory metrics are bounded synthetic test adapters, not production
  exporters, audit receipts or outbox storage.
- Expanded dedicated M6 CI with source precedence and label privacy tests.
  New ADRs and learning cards remain **PROPOSED**, not security approvals.

Final developer CI SHA: PENDING validation. GATE27-07 remains NO-GO.

## 2026-11-05 development iteration 6 - persistent single-host generation floor

- Added a host-controlled `GenerationFloorLedger` port, explicit one-time
  `provision_sqlite_generation_ledger`, and a SQLite reference CAS adapter.
  Normal reading uses `mode=rw`, never automatic create/default G1.
  Invalid schema/state, stale generation, wrong journal mode and unavailable
  database fail closed.
- Added `prepare_with_generation_ledger` and async variant: read trusted
  floor, prepare and validate one M6Runtime candidate, atomically advance
  floor, then return the runtime. Failed dependency composition cannot advance
  the floor. Concurrent candidate commits with the same expected generation
  floor cannot both succeed.
- This only strengthens single-file local persistence. A privileged host
  process can rewrite/reset the ledger; filesystems, process crash durability,
  multi-replica fencing, attacker-driven tampering, external config authenticity
  and promotion to active serving remain host/deployment responsibilities.
- Negative tests cover stale restart, absent/corrupt ledger, provisioning
  collision, invalid floors, concurrent CAS, failed preflight, same-generation
  restart, and re-opened database persistence.
- The source code and tests are DEVELOPMENT CANDIDATE only. Exact-HEAD CI
  and independent GATE27-07 acceptance remain mandatory.

## 2026-11-05 development iteration 7 - AWS Secrets Manager adapter candidate

- Added optional `AwsSecretsManagerResolver` implementing the existing M6
  `SecretResolver` port. The host passes a preconstructed AWS Secrets
  Manager SDK client and an immutable allowlist mapping M6 `SecretRef` to a
  complete AWS secret ARN, with exact partition, region and account pinning.
- The adapter accepts only `purpose=verify`, a concrete AWS VersionId
  (32-64 characters) and the exact resource ARN. Every lookup requests
  `VersionId` AND `VersionStage=AWSCURRENT`; no fallback to default or
  `AWSPREVIOUS`. The returned ARN, version, stage and binary payload must
  match the request or the adapter returns a sanitized failure.
- M4 API Key HMAC consumes this provider through the existing
  `ScopedApiKeySecretSource`; no second authentication engine was created.
- Added SDK-level `botocore.stub.Stubber` tests and security-fault tests for
  cross-scope alias, unexpected version, provider errors, revoked staging
  label and no plaintext in repr.
- AWS SDK is optional under `pyauthkit[aws]`; development tests install
  the SDK explicitly. No AWS credentials, endpoints or fallback secrets are
  obtained by PyAuthKit.
- **Limitations:** Live IAM/KMS/TLS/CloudTrail, egress controls, cross-account
  assumptions and provider rotation/revocation are NOT independently
  qualified. Async execution uses a worker thread around a synchronous AWS
  client, so cancellation of a coroutine does not cancel an AWS network
  request already running. The host must bound SDK connect/read timeouts,
  retries and concurrency. Secret bytes cannot be reliably zeroized in
  standard Python. No production deployment is authorized.

Final exact-head CI: PENDING at authoring. GATE27-07 stays NO-GO.

## 2026-11-05 development iteration 8 - AWS SDK admission and manual live-read harness

- Added `admit_aws_client_profile` and `build_admitted_aws_resolver` as
  an explicit preflight path for host-created boto3/botocore clients. It
  rejects wrong service, region, noncanonical endpoint, HTTP/custom URL,
  unbounded connect/read timeouts, unsigned/unknown signature policies,
  nonstandard retry mode, too many retry attempts or explicit SDK proxies.
- The low-level `AwsSecretsManagerResolver` remains available for isolated
  SDK-shaped fakes, but the documented real-host path now goes through
  `build_admitted_aws_resolver`. Neither path authenticates a cloud IAM
  principal or validates a VPC endpoint policy by itself.
- Added `qualification/m6_aws_live/run_live.py` and its README with an
  explicit environmental approval gate, exact expected STS assumed-role
  identity, isolated account/resource/VersionId and no plaintext logging.
  **No live AWS read was performed** in this ChatGPT session or in PR CI.
- Added offline tests for hostile client endpoints, wrong regions/services,
  excessive timeouts/retries, unsigned signature, missing admission, and
  missing explicit live approval. Integrated tests into M6 CI.
- Remaining AWS qualification: separately approved test account and role,
  IAM/KMS/VPC policies, real endpoint/timeout/throttle/revocation tests and
  independent reviewer sign-off. GATE27-07 remains NO-GO.

Exact-head CI result: PENDING for this iteration until verified.

## 2026-11-05 development iteration 9 - local pseudonymized SQLite audit

- Added `provision_sqlite_audit_store` and
  `SqliteAuthenticationAuditSink` as an optional, explicitly provisioned,
  **local** reference for persisted M2 AuthenticationEvent values. Normal
  opening refuses missing files; the API never silently replaces/recreates a
  store. File provisioning refuses collisions and uses private local mode.
- Each audit event is validated for bounded method, outcome and duration.
  Correlation identifiers are pseudonymized using a host-provided 32-byte
  HMAC key, with explicit key version tags and no raw correlation identifier,
  subject, token or credential columns. Events have distinct random IDs and
  bounded record capacity; a full store fails rather than auto-pruning
  security evidence. Rotation changes the correlation tag for future records
  without rewriting historical records.
- Synchronous SQLite transactions commit before a normal `emit` return,
  while an async `to_thread` execution preserves M2's nonblocking API.
  The adapter validates local rollback journal mode and attempts synchronous
  EXTRA before writes. This is NOT file tamper-resistance, a cluster-wide
  log, or a power-loss guarantee on arbitrary host storage.
- **Critical:** M2's `AuthenticationEngine._emit_event` still suppresses
  audit sink exceptions. Therefore a successful AuthN result can be returned
  even when the local SQLite sink fails. This is intentional backward
  compatibility; the M6 configuration still refuses `audit_delivery=required`.
  A separately designed commit-before-positive-response protocol with a
  durable receipt/denial contract is necessary to enable required audit.
- Tests cover local persistence across process-style reopen, corruption,
  deletion, capacity refusal, concurrent inserts, key rotation, no
  credential/raw-correlation leakage, M2 positive authentication and
  best-effort audit outage. The reference does not simulate a power cut,
  privileged DB modification or a live managed audit store.

**CI and G7:** pending exact-head qualification. GATE27-07 remains NO-GO.
