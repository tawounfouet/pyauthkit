# Security Policy

## Supported versions

PyAuthKit is in pre-alpha bootstrap. No version is supported for production
authentication, and no production security assurance or response-time SLA is
offered yet.

## Reporting a vulnerability

**GitHub Private Vulnerability Reporting is enabled for this repository.**
The maintainer enabled it with authenticated GitHub CLI on 2026-11-02 and
verified the API returned `enabled: true`. See the M0 governance record
(`docs/roadmap/M0_GH_CLI_GOVERNANCE.md`).

To report a security issue, use the repository's **Security and quality**
page, open **Advisories**, and select **Report a vulnerability**. This starts a
private report rather than a public GitHub Issue.

Do **not** open a public Issue or Pull Request containing exploitable
vulnerability details, passwords, API keys, tokens, private keys or personal
information. Never paste raw credentials in public CI logs.

## Triage

The maintainer reviews affected versions, impact, reproduction information,
severity and mitigations privately. No disclosure timetable or response-time
guarantee is committed until a separate policy is accepted. A private report
does not imply a fix or a supported production release.

For the licensing/disclosure decision, see
`docs/adr/0001-licensing-and-governance.md`.

## Current implementation limitations

The protected `main` branch includes the **M0-M2 engine/domain baseline**
and, after PR #76 has been merged, the **M4 API Key experimental
implementation** (strict parser, scoped verification, reference-only
PostgreSQL/Redis/HTTP qualification fixtures). PR #75 / M3 Password
Authentication remains a separate workstream; its formal gate is not GO.

M4 was authorized by its sole maintainer for **development integration
only**, documented in
`docs/qualification/M4_SOLO_MAINTAINER_DEV_MERGE_AUTHORIZATION_2026-11-05.md`.
**GATE27-05 independent security qualification remains NO-GO.**
A syntactically valid scope or locally successful verifier does not prove
production identity, authorization, real KMS/TLS/proxy controls, audit
durability or revocation consistency after the final freshness check.
The reference host under `qualification/m4_host` is **NOT deployable
as a production authentication service**.

There is **no supported production-ready authentication deployment**,
and no permission to publish or deploy M4 follows from merging to `main`.
