# ADR 0042 - Metadata recheck and unresolved Python plugin import provenance

Date: 2026-11-07
Status: PROPOSED / INDEPENDENT SECURITY REVIEW REQUIRED
Gate: GATE27-08, PR #84, issue #89

## Context

An approved Python package entry point contains descriptive distribution and target metadata. `EntryPoint.load()` executes whatever module the current Python importer resolves. Distribution name/version alone neither attest bytes nor prevent `sys.path` shadowing.

## Decision candidate

- Re-read and compare entry point metadata **immediately before** loading each preflighted plugin.
- Refuse on drift, with a sanitized error message before import.
- Keep the full batch preflight to reject unapproved grants before any third-party code.
- Record a separate reproducible source-shadowing threat test that demonstrates what metadata validation **does not** protect.
- Do not claim code provenance attestation, signature validation or process isolation.
- Block production adoption pending a trusted artifact / import-origin policy and independent review.

## Alternatives considered

Using `find_spec` as a universal pre-import origin check is unsound without examining parent-package import side effects, zip loaders, namespace packages and races. Pinning a wheel digest is useful only when coupled to a trusted deployment and import policy. Treating `PluginGrant` as a secure object capability would overstate what it enforces.

## Tests and evidence

- `test_entry_point_changed_after_batch_preflight_never_imports` : boundary improvement.
- `test_distribution_metadata_alone_does_not_attest_import_origin` : explicit counterexample.
- Security gate: NO-GO, with source evidence at exact SHA to be recorded after CI.

## Exactitude des tests et preuve source (2026-11-07)

La dérive post-preflight est reproduite par une modification de la version de `METADATA` sur disque, **pas** par mutation de `EntryPoint` (qui est immuable). Le test de shadowing inspecte une origine via `importlib.util.find_spec` sans exécuter de module. Les cas ont passé la CI sur `28e0d7ff4ae6b4c59d0080e73c0950a9be7a557a` (https://github.com/tawounfouet/pyauthkit/actions/runs/42327812346). L'ADR 0043 propose séparément un digest de wheel approuvé hors bande, sans attestation de l'import. NO-GO maintenu.
