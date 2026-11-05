# M4 / PR-07 - API Key Authentication Security Oracle Register

- Date: 2026-11-05
- Version: 0.1 candidate, **not a formally signed qualification record**
- Scope: M4, work packages WP27-023..026 / tasks WP28-045..060
- Baseline: M2 `main` SHA `55c550d292f2a4294d25dc7b710fcbc4d5ff4f92`
- PR: https://github.com/tawounfouet/pyauthkit/pull/76 (DRAFT)
- Latest **technical checkpoint before this document**: SHA `d4a2346de60d7f9ca05409dac4b18a6a65eca5c4`
- CI evidence: https://github.com/tawounfouet/pyauthkit/actions/runs/42052986729 (7/7 SUCCESS, quality 207 passing tests).
- Status: **0/40 independent adjudications**, GATE27-05 **NO GO / NOT ADJUDICATED**.

## Interpret statuses correctly

- `CODE_TEST_PRESENT`: concrete test path exists and was executed as part of the CI.
  This does **not** mean the entire security oracle is fully qualified or
  independently inspected, especially across real infrastructure.
- `CI_EVIDENCE`: automated checks produced logs for the exact checkpoint; not
  a production or release attestation.
- `PENDING_HOST`: test or independent deployment evidence missing.
- `PENDING_REVIEW`: human authorization/review required.
- `QUALIFIED`: intentionally **never** assigned in this register. This
  status requires independent sign-off, recorded preconditions, environment,
  SHA, assertions, artifacts and acceptance of residual risks.

This 40-row index is a **candidate mapping of the M4-T01..T40 names** to the
visible implementation and proposed qualification plan. It is not a verbatim
extraction from the full 2026-11-05 M4 plan or an adopted canonical oracle
register. Confirm mapping against the plan before formal gate review.

## Candidate oracle coverage

| ID | Assertion / threat | Coverage | Current evidence or missing proof |
|---|---|---|---|
| `M4-T01` | M2 method routing selects exactly API_KEY | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_full_secret_hmac_and_explicit_m2_allow_produce_authenticated |
| `M4-T02` | M2 final policy rejects verified proof by default | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_valid_proof_cannot_bypass_final_policy |
| `M4-T03` | Host-selected tenant rejects foreign claim | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_mismatched_tenant_claim_rejected_by_m2_preflight |
| `M4-T04` | Malformed or too-long evidence fails parser | `CODE_TEST_PRESENT` | tests/unit/test_m4_api_key_parser.py::test_noncanonical_truncated_or_modified_input_is_rejected |
| `M4-T05` | Canonical ak1 selector and bearer lengths | `CODE_TEST_PRESENT` | tests/unit/test_m4_api_key_parser.py::test_valid_opaque_key_has_exact_canonical_length |
| `M4-T06` | Base64url spare bits, padding and UTF-8 rejected | `CODE_TEST_PRESENT` | tests/unit/test_m4_api_key_parser.py::test_parser_rejects_noncanonical_unused_base64_bits |
| `M4-T07` | Selector alone cannot authenticate | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_wrong_selector_even_with_correct_secret_fails_before_key_lookup |
| `M4-T08` | Independent 32-byte HMAC proof vector | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_independent_openssl_vector_accepts_full_key_only |
| `M4-T09` | Every changed bearer secret must fail | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_one_byte_secret_mutation_never_matches |
| `M4-T10` | Tampered stored digest rejected | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_digest_tampering_is_rejected |
| `M4-T11` | Same selector in distinct tenants isolated | `CODE_TEST_PRESENT` | tests/contract/test_m4_api_key_resolver.py::test_same_selector_in_two_tenants_has_independent_results |
| `M4-T12` | Foreign scope verifier record rejected | `CODE_TEST_PRESENT` | tests/contract/test_m4_api_key_resolver.py::test_callback_foreign_scope_is_rejected |
| `M4-T13` | Unknown selector is a negative outcome | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_missing_selector_never_reaches_proof |
| `M4-T14` | Multiple records cannot select first | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_ambiguous_records_cannot_pick_first |
| `M4-T15` | Unavailable resolver is an error, not a retry to another scope | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_store_unavailable_is_technical_error |
| `M4-T16` | HMAC key must be approved by scope | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_unknown_hmac_key_reference_fails_closed_without_lookup |
| `M4-T17` | Missing approved HMAC material is a technical error | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_missing_approved_hmac_key_is_technical_failure |
| `M4-T18` | Unapproved hashing algorithm cannot downgrade | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_unsupported_algorithm_has_no_fallback |
| `M4-T19` | Operator key-ref policy is frozen and scoped | `CODE_TEST_PRESENT` | tests/security/test_m4_api_key_hmac.py::test_protection_policy_is_immutable_and_scoped |
| `M4-T20` | Key source exception does not authenticate | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_key_source_outage_is_technical |
| `M4-T21` | Disabled, suspended or revoked credential denied | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_inactive_record_fails_before_cryptography |
| `M4-T22` | not_before from trusted clock | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_missing_expiry_expired_or_not_yet_valid_rejected |
| `M4-T23` | Expiry boundary denies at time >= expiration | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_missing_expiry_expired_or_not_yet_valid_rejected |
| `M4-T24` | Missing expiry fails conservative M4 policy | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_missing_expiry_expired_or_not_yet_valid_rejected |
| `M4-T25` | Revoke after HMAC before freshness denies | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_post_hmac_revocation_version_change_blocks_verified_outcome |
| `M4-T26` | Authoritative record version replacement fails freshness | `CODE_TEST_PRESENT` | tests/contract/test_m4_api_key_resolver.py::test_freshness_detects_replacement |
| `M4-T27` | Client timestamp cannot override trusted clock | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_full_secret_hmac_and_explicit_m2_allow_produce_authenticated |
| `M4-T28` | Only policy gate creates final Authenticated | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_valid_proof_cannot_bypass_final_policy |
| `M4-T29` | Scoped positive may be approved only after full proof | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_full_secret_hmac_and_explicit_m2_allow_produce_authenticated |
| `M4-T30` | Tenant claim never sets trusted scope | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_mismatched_tenant_claim_rejected_by_m2_preflight |
| `M4-T31` | Missing guard cannot bootstrap Authenticator | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_authenticator_cannot_be_constructed_without_guard |
| `M4-T32` | Guard denies before resolver/cryptography | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_guard_requires_exact_bool_true |
| `M4-T33` | Guard outage is not success | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_guard_outage_is_technical_not_permissive |
| `M4-T34` | Bearer replay limitations and transport policy reviewed | `PENDING_HOST` | Host threat review + TLS/proxy/credential exposure assessment |
| `M4-T35` | Distributed revoke/rotate CAS correctness under races | `PENDING_HOST` | Real PostgreSQL transactional test with concurrent principals/processes |
| `M4-T36` | Source-scoped SQL, multi-tenant and cache consistency | `PENDING_HOST` | Real PostgreSQL/Redis host + two OS processes |
| `M4-T37` | HTTP refusals, timing and quota cross-worker effectiveness | `PENDING_HOST` | FastAPI/Uvicorn HTTP sockets + reverse proxy + 2-worker Redis |
| `M4-T38` | Audit never discloses secret, subject or tenant claims | `CODE_TEST_PRESENT` | tests/integration/test_m4_api_key_engine.py::test_redacted_event_has_no_secret_or_id_in_repr |
| `M4-T39` | CI matrix, package smoke and security scans are reproducible | `CI_EVIDENCE` | GitHub Actions job logs on exact PR SHA; baseline 42052986729 |
| `M4-T40` | Independent approval and explicit GATE27-05 GO/NO-GO | `PENDING_REVIEW` | Security reviewer signoff + ADR owner approval + gate decision |

## Gate evidence still required

1. Validate this 40-case mapping against the canonical M4 plan and approve
   exact independent oracle definitions. Distinguish tests executed from
   tests independently adjudicated.
2. Run actual host integration with a **source-scoped** PostgreSQL credential
   owner and Redis distributed quota guard, with two separate OS processes.
   Attach SQL/query review, isolation, CAS/revocation timing and read-back.
3. Qualify network/proxy source-IP provenance, identical HTTP denial surfaces
   across missing/invalid/revoked/throttled credentials, timing analysis and
   rate-limit burst/sustained thresholds. HTTP uniformity is unproven by an
   in-process Python test.
4. Review the HMAC standard library integration, key material boundaries,
   rotation/reissue procedures, KMS failure semantics and the ability to
   revoke within a documented bounded consistency window.
5. Sign ADR-0016, ADR-0017 and ADR-0018 and handle remaining risks. Verify
   M3 gate dependency policy with owner (M3 formal NO-GO remains).
6. Record review identities, test artifacts, precise SHA, deployment profile,
   G5-01..G5-16 individual dispositions and an explicit formal gate verdict.

**No deployment, package release, main merge, or security certification follows
from the automated 207-test checkpoint.**
