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
