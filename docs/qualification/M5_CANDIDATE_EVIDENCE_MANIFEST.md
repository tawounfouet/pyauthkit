# M5 - Candidate security oracle and GATE27-06 manifest

> Status: DRAFT / NOT ADJUDICATED. Current verdict: **NO-GO**.
> Scope: PR-08 development branch; no merge or release authorized.
> This ledger is NOT a signed qualification report. Links are candidate test
> nodes, not proof of an APPROVED oracle or of independent cryptographic review.

## Candidate security oracles (M5-T01..T40)

| ID | Expected property / scenario | Candidate evidence path | Review status |
| --- | --- | --- | --- |
| M5-T01 | Host profile + signed JWT + final allow | tests/integration/test_m5_jwt_authentication.py::test_valid_signed_access_jwt_passes_final_m2_policy | NOT_ADJUDICATED |
| M5-T02 | Signed JWT + final deny | tests/integration/test_m5_jwt_authentication.py::test_valid_signature_does_not_bypass_final_policy | NOT_ADJUDICATED |
| M5-T03 | alg none / empty signature | tests/integration/test_m5_jwt_authentication.py::test_non_compact_oversized_and_unsigned_rejected | NOT_ADJUDICATED |
| M5-T04 | HS-RS confusion | tests/integration/test_m5_jwt_authentication.py::test_rsa_hmac_algorithm_confusion_rejected | NOT_ADJUDICATED |
| M5-T05 | Unknown algorithm | tests/qualification/test_m5_openssl_vectors.py::test_openssl_signed_wrong_purpose_algorithm_or_key_rejected | NOT_ADJUDICATED |
| M5-T06 | Key type/use/key_ops compatibility | tests/integration/test_m5_jwt_authentication.py::test_unapproved_jwk_algorithm_key_use_and_type_rejected_at_bootstrap | NOT_ADJUDICATED |
| M5-T07 | Bit-flipped signature | tests/integration/test_m5_jwt_authentication.py::test_mutated_signature_is_rejected | NOT_ADJUDICATED |
| M5-T08 | Modified header/payload without resigning | tests/qualification/test_m5_openssl_vectors.py::test_openssl_signed_token_tampering_rejected | NOT_ADJUDICATED |
| M5-T09 | Incorrect JWS segment count | tests/integration/test_m5_jwt_authentication.py::test_non_compact_oversized_and_unsigned_rejected | NOT_ADJUDICATED |
| M5-T10 | Noncanonical encoding / malformed JSON | tests/integration/test_m5_jwt_authentication.py::test_jws_excessive_json_depth_and_noncanonical_base64url_rejected | NOT_ADJUDICATED |
| M5-T11 | Duplicate header or claims keys | tests/integration/test_m5_jwt_authentication.py::test_duplicate_untrusted_jose_properties_rejected | NOT_ADJUDICATED |
| M5-T12 | Unknown crit / b64=false | tests/integration/test_m5_jwt_authentication.py::test_explicit_unencoded_payload_header_rejected | NOT_ADJUDICATED |
| M5-T13 | Embedded JWK / jku / x5u injection | tests/integration/test_m5_jwt_authentication.py::test_untrusted_key_discovery_headers_rejected | NOT_ADJUDICATED |
| M5-T14 | Untrusted issuer not authorized | tests/qualification/test_m5_openssl_vectors.py::test_openssl_valid_signature_wrong_claims_rejected | NOT_ADJUDICATED |
| M5-T15 | Valid signature under wrong issuer profile | tests/integration/test_m5_jwt_authentication.py::test_profile_scoping_prevents_key_reuse_from_another_tenant | NOT_ADJUDICATED |
| M5-T16 | Audience strict match | tests/integration/test_m5_jwt_authentication.py::test_signed_claims_invalidities_fail_closed | NOT_ADJUDICATED |
| M5-T17 | ID/access typ confusion | tests/integration/test_m5_jwt_authentication.py::test_wrong_typ_cannot_substitute_id_token | NOT_ADJUDICATED |
| M5-T18 | exp missing/expired/bool/boundary | tests/integration/test_m5_jwt_authentication.py::test_signed_claims_invalidities_fail_closed | NOT_ADJUDICATED |
| M5-T19 | nbf future / skew | tests/integration/test_m5_jwt_authentication.py::test_signed_claims_invalidities_fail_closed | NOT_ADJUDICATED |
| M5-T20 | iat future/age/bad numeric | tests/integration/test_m5_jwt_authentication.py::test_age_bound_requires_iat | NOT_ADJUDICATED |
| M5-T21 | Subject required and typed | tests/integration/test_m5_jwt_authentication.py::test_signed_claims_invalidities_fail_closed | NOT_ADJUDICATED |
| M5-T22 | Issuer+subject+scope namespace | tests/integration/test_m5_jwt_authentication.py::test_valid_signed_access_jwt_passes_final_m2_policy | NOT_ADJUDICATED |
| M5-T23 | Client tenant hint vs host scope | tests/integration/test_m5_jwt_authentication.py::test_client_supplied_tenant_is_not_a_trust_profile_selector | NOT_ADJUDICATED |
| M5-T24 | role=admin never grants IAM | tests/integration/test_m5_jwt_authentication.py::test_signed_roles_do_not_override_m2_denial | NOT_ADJUDICATED |
| M5-T25 | Unknown kid cannot cause unbounded requests | tests/security/test_m5_jwks_cache.py::test_100_unknown_kids_coalesce_into_single_fetch_per_profile | NOT_ADJUDICATED |
| M5-T26 | Same kid across profiles isolated | tests/security/test_m5_jwks_cache.py::test_same_kid_isolated_by_tenant_profile_and_source | NOT_ADJUDICATED |
| M5-T27 | Duplicate kid ambiguous | tests/integration/test_m5_jwt_authentication.py::test_duplicate_kids_rejected_at_bootstrap | NOT_ADJUDICATED |
| M5-T28 | JWKS jku SSRF probe | tests/security/test_m5_jwks_https.py::test_ssrf_invalid_dns_and_mixed_records_never_connect | NOT_ADJUDICATED |
| M5-T29 | Redirect/DNS rebinding/private target | tests/security/test_m5_jwks_https.py::test_rebinding_to_private_address_after_first_approved_fetch; tests/qualification/test_m5_jwks_tls_host.py::test_real_tls_certificate_hostname_sni_and_body_are_verified [SIMULATED EGRESS ONLY] | NOT_ADJUDICATED |
| M5-T30 | Malformed/oversized JWKS | tests/security/test_m5_jwks_cache.py::test_ambiguous_jwks_and_corrupted_json_fail_closed | NOT_ADJUDICATED |
| M5-T31 | Network unavailable / timeout | tests/security/test_m5_jwks_cache.py::test_rotation_expiration_invalidation_and_no_stale_error_fallback | NOT_ADJUDICATED |
| M5-T32 | Key rotation and stale cache | tests/security/test_m5_jwks_cache.py::test_rotation_expiration_invalidation_and_no_stale_error_fallback | NOT_ADJUDICATED |
| M5-T33 | Profile revision snapshot during verification | tests/integration/test_m5_jwt_authentication.py::test_profile_revision_cannot_fallback_to_another_versions_keys | NOT_ADJUDICATED |
| M5-T34 | Single-flight concurrency | tests/security/test_m5_jwks_cache.py::test_100_unknown_kids_coalesce_into_single_fetch_per_profile | NOT_ADJUDICATED |
| M5-T35 | Cancellation / no late success | tests/security/test_m5_jwks_cache.py::test_cancelled_resolution_propagates_without_caching | NOT_ADJUDICATED |
| M5-T36 | Oversized token / JSON depth | tests/integration/test_m5_jwt_authentication.py::test_jws_excessive_json_depth_and_noncanonical_base64url_rejected | NOT_ADJUDICATED |
| M5-T37 | No token leakage in repr/log/events | tests/integration/test_m5_jwt_authentication.py::test_no_token_secrets_in_representation | NOT_ADJUDICATED |
| M5-T38 | No registry fallback | tests/integration/test_m5_jwt_authentication.py::test_jwt_registry_has_no_other_authenticator_fallback | NOT_ADJUDICATED |
| M5-T39 | Minimal and JWT-extra wheel smoke | .github/workflows/ci.yml::m5_jwt | NOT_ADJUDICATED |
| M5-T40 | Full M5 CI and regression | .github/workflows/ci.yml::quality,compatibility,security,m4_host,m5_jwt | NOT_ADJUDICATED |

## Proposed G6 acceptance criteria (NOT ratified)

| ID | Condition | Status |
| --- | --- | --- |
| G6-01 | Baseline and dependency isolation | PENDING / NO-GO |
| G6-02 | Host-selected trust profiles | PENDING / NO-GO |
| G6-03 | Strict bounded JOSE parsing | PENDING / NO-GO |
| G6-04 | Approved algorithms and key types | PENDING / NO-GO |
| G6-05 | Independent cryptographic vectors | PENDING / NO-GO |
| G6-06 | Issuer and audience matching | PENDING / NO-GO |
| G6-07 | Mutually exclusive token purpose | PENDING / NO-GO |
| G6-08 | Temporal and scoped subject binding | PENDING / NO-GO |
| G6-09 | Real-host anti-SSRF | PENDING / NO-GO |
| G6-10 | JWKS keyset and cache isolation | PENDING / NO-GO |
| G6-11 | Fail-closed dependency errors | PENDING / NO-GO |
| G6-12 | No evidence leak or IAM grants | PENDING / NO-GO |
| G6-13 | Substitutability and bounded concurrency | PENDING / NO-GO |
| G6-14 | Exact-SHA CI, wheels and supply chain | PENDING / NO-GO |
| G6-15 | Accepted ADR and signed risk decisions | PENDING / NO-GO |
| G6-16 | Gate signoff, post-merge SHA/CI | PENDING / NO-GO |


## Evidence handling

An oracle becomes PASS only when its test node, input vectors, assertions,
source SHA, CI job and real result are independently reviewed. In particular:

- Offline tests do not establish actual TLS, DNS rebinding or egress safety.
- The host-provided JWKS fetch port is a dependency contract, not a network
  proof. M5-T28/29 remain blocked pending a real adversarial host.
- The RSA positive vector is generated by the same PyJWT ecosystem used for
  validation; an independent OpenSSL/vector test is still required.
- TTL caching is not token revocation or multi-process consistency.
- The M2/M4 regression suite can pass while M4 independent GATE27-05 remains NO-GO.
- G6-16 must include a real security reviewer / owner verdict, date, tested SHA,
  CI URLs, exceptions, and a separately authorized merge/post-merge SHA.

## Evidence packets added on this branch

- `tests/security/test_m5_jwks_https.py`: DNS/SSRF/redirect/HTTP budget simulations.
- `tests/qualification/test_m5_jwks_tls_host.py`: ephemeral actual local TLS with synthetic public egress routing, real certificate verification.
- `tests/qualification/test_m5_openssl_vectors.py`: OpenSSL CLI-created signatures, PyJWT verifier cross-check.
- `docs/qualification/M5_G6_TECHNICAL_REVIEW_2026-11-05.md`: preliminary 40-oracle evidence review and G6 decision register, without independent signoff.
- `M5-T29` remains PARTIAL despite linked tests: the route to the local TLS server is intentionally mocked. Production DNS, network policy and proxy egress require a separate environment-based gate.

## Open blockers

1. Independent JOSE, key-size and canonicalization review.
2. Actual HTTPS JWKS transport with egress policy, DNS/IP revalidation,
   redirects disabled, response budget, TLS and server-hostile tests.
3. Secure host integration and tests for key compromise and rotation incidents.
4. Candidate 40-oracle adoption, complete coverage and G6 signoff.
5. CI exact SHA plus source, wheel, supply-chain and package compatibility
   evidence; no production or release approval.

