# M6 candidate oracle-to-evidence matrix (M6-T01..T40)

Date: 2026-11-05
Version: candidate / NOT INDEPENDENTLY QUALIFIED.
Source: M6 implementation plan dated 2026-11-05 section 21.

The 40 identifiers are candidate *oracles*, not automatically 40 test cases
nor a declared GATE27-07 PASS. COVERED means an executable candidate test
exercises the stated narrow behavior. PARTIAL indicates known scope gaps.
OPEN and PENDING_SHA are not PASS. No independent reviewer has signed G7.

| Oracle | Coverage status | Evidence or gap |
| --- | --- | --- |
| M6-T01 | COVERED | test_m6_t01_valid_host_mapping_bootstraps_one_generation |
| M6-T02 | COVERED | test_m6_t02_untrusted_provenance_is_denied |
| M6-T03 | COVERED | v2 signed JWT issuer/audience cannot select a foreign trust profile |
| M6-T04 | COVERED | test_m6_t04_extra_security_field_is_denied |
| M6-T05 | PARTIAL | duplicate routes/methods rejected; raw JSON duplicate member parsing is out of reader scope |
| M6-T06 | OPEN | single-source reader; multi-source merge scenarios require explicit decision |
| M6-T07 | COVERED | test_m6_t07_env_override_is_not_a_source |
| M6-T08 | COVERED | test_m6_t08_unknown_route_has_no_fallback |
| M6-T09 | COVERED | v2 route/JWT profile exact coverage plus M2 catalog scope matching |
| M6-T10 | COVERED | test_m6_t10_unregistered_authenticator_prevents_activation |
| M6-T11 | COVERED | v2 parser rejects missing issuer/audience, alg none, invalid JWT constraints |
| M6-T12 | PARTIAL | v2 rejects private IP/HTTP/unauthorized URI and requires separate exact egress grant; live network policy unqualified |
| M6-T13 | COVERED | test_m6_t13_snapshot_does_not_share_mutable_host_input |
| M6-T14 | COVERED | test_m6_t14_snapshot_and_nested_bindings_immutable |
| M6-T15 | COVERED | test_m6_restart_to_new_key_does_not_mix_generations |
| M6-T16 | COVERED | test_m6_t16_cross_scope_secret_denied_without_provider_call and M4 integration |
| M6-T17 | COVERED | test_m6_t17_malformed_reference_and_purpose_denied |
| M6-T18 | COVERED | test_m6_unavailable_secret_blocks_activation |
| M6-T19 | COVERED | test_m6_t19_revoked_secret_has_no_fallback and post-startup revocation |
| M6-T20 | PARTIAL | cross-scope binding denied; separate simultaneous same key ID scenario not explicit |
| M6-T21 | COVERED | test_m6_t21_references_and_snapshot_never_dump_material |
| M6-T22 | COVERED | test_m6_t22_provider_exception_cannot_leak_canary |
| M6-T23 | COVERED | test_m6_t23_audit_contains_only_correlation_method_result_duration |
| M6-T24 | COVERED | test_m6_t24_rejected_and_error_events_never_echo_evidence |
| M6-T25 | PARTIAL | JWT/API Key canaries, no dedicated password canary scenario |
| M6-T26 | OPEN | no metrics label exporter in the current M6 runtime |
| M6-T27 | COVERED | test_m6_t27_best_effort_sink_failure_does_not_change_authn |
| M6-T28 | COVERED | test_m6_t28_audit_submission_timeout_is_not_success_receipt |
| M6-T29 | COVERED | test_m6_t29_audit_cancellation_propagates |
| M6-T30 | COVERED | test_m6_t30_required_audit_policy_rejected_at_bootstrap |
| M6-T31 | COVERED | test_m6_t31_required_audit_cannot_be_enabled_by_a_fake_sink |
| M6-T32 | COVERED | test_m6_t32_in_memory_sink_is_explicitly_non_durable |
| M6-T33 | COVERED | test_m6_t33_memory_sink_does_not_claim_idempotent_delivery |
| M6-T34 | COVERED | test_m6_restart_to_new_key_does_not_mix_generations |
| M6-T35 | PARTIAL | test_m6_t35_invalid_restart_never_returns_a_runtime; host routing not modeled |
| M6-T36 | PARTIAL | stale generation rejected if trusted external floor injected; no durable ledger provided |
| M6-T37 | COVERED | test_m6_restart_to_new_key_does_not_mix_generations |
| M6-T38 | COVERED | test_m6_t22_provider_exception_cannot_leak_canary and post-bootstrap fault |
| M6-T39 | PENDING_SHA | wheel/sdist smoke jobs required at final head SHA |
| M6-T40 | PENDING_SHA | M2/M4/M5 regressions and complete CI required at final head SHA |

## Known security and governance gaps

- M6 now parses and composes a bounded M5 JWT trust profile with issuer,
  audience and pinned JWKS controls under configuration schema v2. Real
  host network egress and reviewer sign-off are still unqualified.
- No source-merging policy is admitted by the current reader. It cannot detect
  duplicate raw JSON keys after another parser has already built a Mapping.
- No metrics exporter exists. Audit events must not be treated as metric labels.
- Memory audit is best-effort only. No exactly-once, idempotence or persisted
  receipt is asserted; `required` is rejected.
- The source adapter only supports synthetic-provider tests here. Any real
  Vault/KMS/DB/HTTP integration needs additional threat, access and fault tests.
- G1/G2 recovery is pinned by host-supplied floor, not a durable authenticated
  ledger. This project cannot prove crash-safe anti-rollback without one.
- M3/M4/M5 upstream security gates have unresolved independent qualification.
- G7-01..G7-16 remain unadjudicated; this document does not ratify their status.

## Exact evidence record to update on final head SHA

- Pull request: https://github.com/tawounfouet/pyauthkit/pull/82
- Baseline: `edeef0288ed9560324bac6f065a4d06057d5faeb`
- Previous developer evidence: `46d8915b69f235256715465f6c49416f5bbbd9d3` -
  365 tests PASS, Ruff, mypy strict 52 modules, architecture fitness.
- Final JWT v2 CI: PENDING at time of this iteration's authoring.
- Reviewer: NOT ASSIGNED.
- GATE27-07: NO-GO / NOT INDEPENDENTLY QUALIFIED.
