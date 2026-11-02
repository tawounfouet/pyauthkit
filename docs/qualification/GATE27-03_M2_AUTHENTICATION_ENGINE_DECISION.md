# PyAuthKit - GATE27-03 - M2 Authentication Engine & Ports

> Qualification recommendation: **GO FOR M2 ENGINE AND PORTS ONLY**.
> PR-04, PR-05 and the PR-72 qualification delta are merged and their CI is green.
> Final authoritative sign-off is recorded on GitHub issue #70; a successful
> engineering gate does not grant production authentication or release approval.
>
> Date: 2026-11-02. Qualified code baseline: main at
> c6122ca17a23abd299fc4098aa29a8797ca3923a.
> **Not a release, not a password/JWT/API-key implementation and not a
> cryptographic or production authentication certification.**

## 1. Evidence and provenance

| Evidence | Value |
|---|---|
| PR-04 host context, preflight | https://github.com/tawounfouet/pyauthkit/pull/69 |
| PR-04 reviewed head | 1b87ee1596af21744928bb69123d9043fde0c5b7 |
| PR-04 merge SHA | 8b2f2df35aecfe8e85cf0300606a2ce482514c1f |
| PR-04 PR CI | https://github.com/tawounfouet/pyauthkit/actions/runs/41440351266 (7/7 PASS) |
| PR-04 main CI | https://github.com/tawounfouet/pyauthkit/actions/runs/41449081791 (7/7 PASS) |
| PR-05 Engine + Ports | https://github.com/tawounfouet/pyauthkit/pull/71 |
| PR-05 reviewed head | 1eb1f277a99e65f7b01a2b2c3c6986766c26dace |
| PR-05 merge SHA | 2992c359d29f992c822e595ef9ef3babaed1d856 |
| PR-05 PR CI | https://github.com/tawounfouet/pyauthkit/actions/runs/41452347496 (7/7 required PASS, GitGuardian PASS) |
| PR-05 main CI | https://github.com/tawounfouet/pyauthkit/actions/runs/41452679229 (7/7 PASS) |
| PR-05 tested scope | 102 pytest PASS on PR head; Ruff lint/format, mypy strict 23 files, architecture, dependency and secret scans |
| Packaging | wheel/sdist and fresh-venv smoke on Ubuntu Py3.12/3.13/3.14, macOS Py3.12 and Windows Py3.12 |
| Security review | PR #69 and PR #71 COMMENT reviews; engineering review, not external independent assessment |
| Gate tracking | https://github.com/tawounfouet/pyauthkit/issues/70 |
| PR-72 qualification | https://github.com/tawounfouet/pyauthkit/pull/72 (7/7 required + GitGuardian pass) |
| Qualified main baseline | `c6122ca17a23abd299fc4098aa29a8797ca3923a` |
| Main CI after PR-72 | https://github.com/tawounfouet/pyauthkit/actions/runs/41453376670 (7/7 required jobs PASS) |
| Final integrated pytest | 104 passed in 3.35s (Ubuntu Python 3.12.15); mypy strict 23 source files PASS |
| Closure delta | PR-72 #72: M2-T06 empty-registry and M2-T16 audit-cancellation tests passed in main CI; merged SHA `c6122ca17a23abd299fc4098aa29a8797ca3923a`. |

## 2. Requirement-to-test matrix

Every row refers to an independent test or build guard. Verification status
means the assertion was executed on the qualified code PR/head, except the
two explicit closure-delta tests which require closure CI before final GO.

| ID | Source of proof | Qualified observation |
|---|---|---|
| M2-T01 | test_m2_t01_untrusted_request_payload_limits, domain kernel | Bounded evidence rejects malformed inputs |
| M2-T02 | test_client_tenant_claim_cannot_select_another_profile; tenant property tests | Host scope not selected from claimed tenant |
| M2-T03 | test_unknown_route_fails_without_a_default_scope | No unknown-route fallback |
| M2-T04 | test_scope_profile_mismatch_rejected_at_bootstrap | Binding mismatch rejects bootstrap |
| M2-T05 | test_disabled_method_fails_closed_even_under_valid_host_context | No verifier invoked |
| M2-T06 | test_m2_t06_t07_t08_registry_freeze_and_no_fallback + closure empty-registry test | Unknown method and empty catalog refuse |
| M2-T07 | test_m2_t06_t07_t08_registry_freeze_and_no_fallback; SPI contracts | Duplicate registration refuses |
| M2-T08 | test_m2_t08_t23_host_catalog_registry_engine_and_policy_are_not_mutable | Frozen composition rejects ordinary mutation |
| M2-T09 | test_m2_t09_t10_t14_negative_fault_paths; contract tests | Negative outcome remains REJECTED, no principal |
| M2-T10 | test_m2_t09_t10_t14_negative_fault_paths; contract tests | Technical outcome remains ERROR, no principal |
| M2-T11 | test_m2_t11_foreign_positive_outcomes_fail_before_final_gate | Foreign attempt/profile/method refuses before gate |
| M2-T12 | test_m2_t12_positive_fake_with_final_denial_never_yields_principal | Final denial overrides synthetic positive |
| M2-T13 | test_m2_t13_only_host_bound_fake_plus_final_allow_succeeds | Positive only in controlled test harness |
| M2-T14 | test_m2_t09_t10_t14_negative_fault_paths | Verifier exceptions sanitized |
| M2-T15 | test_m2_t15_timeout_cannot_late_authenticate | Timeout yields technical failure |
| M2-T16 | test_m2_t16_cancellation_is_propagated_not_normalized_to_success + closure async audit test | Cancellation propagated, never returned as success |
| M2-T17 | test_m2_t17_concurrent_tenants_are_cryptographically_unclaimed_but_scope_isolated | Parallel tenants kept scoped |
| M2-T18 | test_m2_t18_t21_event_redaction_and_documented_best_effort | Optional event sink failure does not lie about audit durability |
| M2-T19 | scripts/smoke_wheel.py, all 5 packaging jobs | Fake under tests/ absent from published wheel |
| M2-T20 | architecture fitness and packaging/import checks | No implicit plugin loading in core |
| M2-T21 | event and request redaction tests | No raw secrets in repr/audit |
| M2-T22 | fresh-venv wheel smoke and architecture check | No mandatory Web, IAM or DB dependency |
| M2-T23 | immutable-snapshot tests + method-drift adversarial test | Registry/host snapshot stable, drift refuses |
| M2-T24 | test_m2_t24_verifier_cannot_return_final_authenticated_itself | Direct success bypass rejected |

Qualification notes: Tests use an in-memory test-only fake. A successful
test does not prove Password/Argon2, API-key revocation or JWT/JOSE security.
No M2 tests assert a standards certification or cryptographic identity.

## 3. G3-01..G3-14 decision

| Criterion | Decision evidence |
|---|---|
| G3-01 | PR-04 reviewed, normally merged, post-merge main CI 7/7 |
| G3-02 | PR-05 reviewed, normally merged, post-merge main CI 7/7 |
| G3-03 | Engine explicit pipeline, preflight and mandatory final gate |
| G3-04 | Authenticator returns internal outcome only; bypass test negative |
| G3-05 | Synthetic success verifier only under tests/, wheel excludes it |
| G3-06 | Non-success result variants cannot carry final principal |
| G3-07 | Foreign/ambiguous host, unknown method/profile refuse |
| G3-08 | Registry duplicate/freeze/drift + wheel/provenance controls |
| G3-09 | Timeout, cancellation, exception injection tested |
| G3-10 | Unit, contract, property, concurrent, architecture CI successful |
| G3-11 | 7 required jobs + GitGuardian on PR, 7/7 main jobs |
| G3-12 | ADR-0006..0009, learning cards, this risk ownership and WP record |
| G3-13 | Pure Python core with no required framework, IAM, DB, runtime fake |
| G3-14 | Pending signed issue #70 decision after closure PR CI and merge |

All criteria except the final administrative sign-off are supported by the
implementation evidence above. The additional closure tests passed on the PR-72 candidate and protected main.
Final sign-off is the separate issue #70 gate decision, not this report alone.

## 4. Residual risks owned explicitly

| Risk | Owner | Treatment |
|---|---|---|
| Real ASGI/WSGI reverse-proxy route provenance | Framework adapter maintainer and relying-party integrator | Require authenticated server-side route selection before any production integration; no raw user headers as trust |
| Privileged in-process extension code | PyAuthKit maintainer and package integrator | Only pre-approved dependencies; Python privacy is not sandboxing |
| Production password/API key/JWT verification absent | M3/M4/M5 work packages | Qualify each real cryptographic method separately |
| Durable mandatory audit not provided | Deployment integrator and future audit implementation | M2 audit is best-effort, no delivery guarantee |
| Independent security review and reproducible release provenance | Repository maintainer, existing issues #64/#63 | Must remain release blockers; not resolved by M2 GO |

## 5. Decision and scope of the next gate

**GO is limited to M2 async Engine, trusted host preflight, explicit SPI and
registry, mandatory final policy, cancellation/timeout and synthetic contract
qualification.** It authorizes starting M3 PR-06 after issue #70 sign-off.
It does **not** authorize a PyPI release, live credential verification,
session/token issuance, IAM authorization, a claim of NIST AAL or SOC 2
compliance, or execution of arbitrary untrusted plugins.

M3 must select a mature password KDF implementation (e.g. Argon2id), use
a scoped credential resolver, conceal account existence and test revoked/
missing records, invalid inputs, cross-tenant lookup, time/memory limits and
hash migration, then obtain its independent GATE27-04 evidence.

## 6. Final administrative sequence

1. Merge this closure/tests PR with all required checks green.
2. Verify 7/7 mandatory jobs on the resulting main SHA.
3. Record the final signed GO on issue #70 with the closure main SHA.
4. Close WP27-013..018 and issue #70 only if all P0 remain successful.
5. Close M2 milestone and initiate M3.

## 7. Post-merge closure verification (2026-11-02)

- **PR-72**: merged on `main`, merge commit `c6122ca17a23abd299fc4098aa29a8797ca3923a`.
- **PR verification**: run [41453150814](https://github.com/tawounfouet/pyauthkit/actions/runs/41453150814), seven mandatory jobs successful. GitGuardian is a separate scan; it does not increase the required job count.
- **Protected main**: run [41453376670](https://github.com/tawounfouet/pyauthkit/actions/runs/41453376670), seven of seven required jobs successful, verified by checking individual job conclusions.
- **Integrated test logs**: exactly `104 passed in 3.35s` with pytest 9.2.0 on Python 3.12.15; strict mypy reports `Success: no issues found in 23 source files`. Ruff, architecture, packaging and security scans green.
- **Engineering determination**: all 24 M2-T01..24 cases have traceable assertions, and the 14 G3 criteria have satisfied technical evidence except the separate gate-issue administrative sign-off. The formal decision belongs in [GATE27-03 issue #70](https://github.com/tawounfouet/pyauthkit/issues/70).
- **Scope restriction**: the qualified host trust model is an explicit trusted catalog and preflight. A production framework/reverse-proxy adapter with independently verified route provenance is NOT part of this M2 GO. Real password authentication, sessions, IAM, production readiness, release, independent audit and reproducibility certification are NOT asserted. Issues #63 and #64 stay open.
- **Work package closure**: WP27-013..018 may be marked completed only for bounded M2 responsibilities after gate sign-off. GitHub milestone closure is a separate administrative operation and must not be inferred from issue closures.
