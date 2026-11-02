# M2 PR-05 - Independent security oracles before implementing the positive path

- Date: 2026-11-02
- Status: SPECIFIED / NOT YET EXECUTED
- Baseline: PR-04 #69 merged into main `8b2f2df35aecfe8e85cf0300606a2ce482514c1f`
- Scope: WP27-013..016, WP27-018; gate #70
- Basis: `09` engine steps, `07` invariants, `20` threat model, M2 plan §9

## Threat -> oracle -> independent assertion

| Case | Adversarial input | Independent oracle | P0 |
|---|---|---|---|
| M2-T11 | Positive internal outcome with foreign tenant/profile, method or attempt marker | Engine returns ERROR; final gate not called; no principal | yes |
| M2-T12 | Valid test-only positive outcome plus final policy denies | Result is REJECTED; no principal; final gate called exactly once | yes |
| M2-T13 | Correct host-bound test-only verification plus explicit policy allow | AUTHENTICATED only in harness; selected verifier called once; final gate called exactly once | yes |
| M2-T24 | Verifier returns a public Authenticated or attempts to bypass policy | Invalid outcome becomes ERROR; no direct success; policy spy confirms no skipped gate | yes |
| M2-T02/03/05 | Forged tenant / unknown route / forbidden method | Refusal before invoking any verifier; effective catalog unchanged | yes |
| M2-T06/07/08 | Unknown method / duplicate / post-freeze mutation | No fallback; bootstrap rejects or resolution refuses | yes |
| M2-T15/16 | verifier blocks and deadline/cancellation fires | No principal; timeout error or cancellation propagation | yes |
| M2-T18/21 | audit raises / secret-shaped bytes supplied | Best-effort is documented; event has no raw evidence or sensitive repr | conditional |
| M2-T19/20/22 | built wheel imports test fakes, plugins or Web/IAM | Independent wheel contents and import inspections fail the test | yes |

## Test design (RED first)
1. Define a spy gate and fake authenticators in `tests/`, never packaged.
2. Assert gate ordering using a recording spy independent of the `AuthenticationEngine` implementation.
3. Construct a foreign positive outcome with a distinct marker and assert no principal.
4. For M2-T12 explicitly return a denial from the final gate and verify `REJECTED` despite positive proof.
5. For M2-T13 require a verifier selected by immutable registry and an allow from the final policy, with a unique marker.
6. M2-T24 uses a malicious adapter returning `Authenticated` as an invalid SPI outcome.

## Evidence gate
A marked oracle is not a passed test. Record the actual pytest node ID, commit SHA, GitHub Actions run and observed result for each P0. A GO needs all required tests green, PR reviews, accepted ADRs and post-merge main CI. Existing M1 success constructors remain restricted until a qualified engine owns the transition. No fake verifier proves Password/API Key/JWT cryptography.
