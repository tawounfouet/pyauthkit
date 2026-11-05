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

The protected `main` branch contains the **M0-M2 engine/domain baseline**,
including host-approved entry catalog, authenticator SPI and final policy.
M3 Password Authentication PR #75 and M4 API Key Authentication PR #76
remain separate unmerged changes; their independent gates are not GO.
A syntactically valid scope or locally successful verifier does not prove
production identity, authorization or secret-management guarantees.
There is **no supported production-ready authentication deployment**.
