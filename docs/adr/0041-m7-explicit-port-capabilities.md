# ADR 0041 - Explicit host-granted port capabilities for SPI v2

Date: 2026-11-07
Status: PROPOSED / GATE27-08 SECURITY REVIEW REQUIRED
Scope: M7 / PR #84 / T19 and T25

## Context and risk

The original SPI v2 bundle checked only a role name and the existence of a callable such as `verify` or `resolve`. It did not require a per-plugin declaration of exactly which role references the operator intended to provide. A mistakenly broad host mapping could therefore supply an unneeded sensitive port to an otherwise admitted plugin. This is an unintended increase in the host/plugin trust surface.

## Proposed decision

1. Extend host-owned `PluginGrant` with a new immutable `port_roles: frozenset[str]`.
2. For v1, require no roles. For v2, require a nonempty role set with names allowed for the grant's `EvidenceMethod`.
3. `PluginHostServices` independently rejects roles incompatible with its bound method.
4. Before `EntryPoint.load()`, compare the **exact** set of the grant's roles against the injected bundle's mapping keys; reject missing and extra roles, with sanitized errors.
5. Keep the existing host method/scope/profile binding, per-request wrapper and engine final policy unchanged. No new issuer of final `Authenticated` outcomes.
6. Execute a selected reviewed Markdown example in the isolated wheel CI environment as one concrete T25 evidence. The rest of the guide remains illustrative until separately covered.

## Candidate method-role policy

- `PASSWORD`, `API_KEY`: `record_resolver`, `attempt_guard`, `hash_verifier`, `clock`, `event_sink`.
- `JWT`: `record_resolver`, `attempt_guard`, `key_resolver`, `clock`, `event_sink`.

These are explicit **candidate constraints**, not a completed domain capability taxonomy. Changing allowed roles or grant semantics requires further review and versioning policy.

## Alternatives considered

- Trust all ports with callable methods: overly broad authority for host misconfiguration.
- Derive roles from installed plugin metadata or claims: reverses the trusted-host decision boundary.
- Auto-inject all known port types: violates least privilege.
- Rewrite M2 registry or final policy: unnecessary for this contract.

## Consequences and boundaries

A `frozenset` limits **which names the host injects**. It does not constrain the behavior of a Python plugin after import; it is not OS process isolation, an unforgeable permission, cryptographic attestation or certificate of a real verifier. Ports can contain mutable state and secrets. The host remains responsible for review and permissions of each concrete port.

## Evidence and qualification

- Negative tests in `tests/security/test_m7_plugin_services.py` verify unknown/incompatible role and exact role mismatch before plugin import.
- Independent wheel test retains a host-owned synthetic HMAC verifier; its public fixture key is not a production secret.
- `docs/guides/m7-capability-contract.md` is executed via `scripts/check_m7_doc_examples.py` in CI using the isolated installed PyAuthKit wheel.
- Both T19 and T25 remain PARTIAL (CI), GATE27-08 NO-GO until independent review, complete executable SDK docs and trustworthy plugin/supply-chain proof.
