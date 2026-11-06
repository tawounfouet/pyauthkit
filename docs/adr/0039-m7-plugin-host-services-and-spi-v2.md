# ADR 0039 - Explicit Host-Service Injection for Admitted Authenticator Plugins

Status: PROPOSED / SECURITY REVIEW REQUIRED
Date: 2026-11-07
Owner decision pending: issue #87, PR #84, GATE27-08

## Problem

The v1 zero-argument authenticator factory cannot receive an operator-approved resolver, attempt guard, key provider or hashing interface without ad-hoc global settings, direct environment access or plugin-defined credential routing. Those alternatives hide trust and make review difficult. The M2 registry resolves by `EvidenceMethod`, not by tenant or profile.

## Decision candidate

1. Keep v1 unchanged: `pyauthkit.authenticators.v1`, `SPI_MAJOR=1`, zero-argument factory, no service injection or fallback.
2. Add a distinct opt-in `pyauthkit.authenticators.v2`, `SPI_MAJOR=2` and `create(services: PluginHostServices)` factory. The group and SPI major must agree in `PluginGrant`.
3. Build the `PluginHostServices` bundle from an operator-owned M6 snapshot and exact host route, with one method approved on its binding. It includes only a frozen mapping of specific ports with structural contracts (`resolve`, `admit`, `verify`, `now`, `emit`).
4. Associate each bundle with one exact v2 `PluginGrant` in `service_bindings`. The managed loader preflights **all grants and bindings before import** and refuses unbound v2 factories or extraneous mappings. The legacy sync loader stays non-owning and refuses v2.
5. Wrap every admitted v2 authenticator in an immutable-scope behavioral guard. A request bound to another tenant, trust profile, method or correlation fails with a technical error without invoking the external verifier.
6. Use the existing M2 engine, final policy and `issue_verified_outcome` only after actual method-specific verification. There is no new `Authenticated` constructor, policy gate or authorization grant.

## Boundaries

- The bundle is not an unforgeable capability, package attestation, security sandbox or proof that the plugin is honest. Authorized Python code runs with the host process permissions.
- Host ports, including ones that encapsulate secrets, must enforce their own scope/tenant admission, freshness/revocation and lifecycle. The plugin receives a port reference, never raw secrets in a grant or metadata.
- M2 registry remains indexed by method. A v2 instance is bound to **one** host scope/profile. Sharing it across tenants is rejected instead of silently using another tenant's port. A future multi-tenant resolver requires a separate ADR and gate.
- The new plugin example uses public synthetic HMAC fixture material. Its passing test shows verification routing and revocation behavior, not production cryptographic assurance.

## Alternatives rejected

- Add optional `services` to the v1 factory and auto-fallback between call signatures: ambiguous version and unsafe downgrade.
- Derive services, key source or scope from caller claims: untrusted inputs cannot select operator authority.
- Send secret bytes in plugin grant or metadata: secret leakage and uncontrolled lifecycle.
- Introduce a new authentication engine or bypass policy to accommodate extensions: violates M2 invariants.

## Verification / gate

Tests must demonstrate: discovery without import, no service -> no load, group and major mismatch, immutable/redacted bindings, method mismatch, invalid/revoked evidence, foreign tenant blocked before plugin call, positive internal outcome but final policy deny, reverse async cleanup, independent wheel smoke. Keep GATE27-08 **NO-GO SECURITY** pending independent review and evidence provenance.
