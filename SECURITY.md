# Security Policy

## Supported versions

No production-supported release or authentication mechanism exists during
PR-01 bootstrap. There is no production security assurance or support SLA.

## Reporting a vulnerability

Prefer GitHub's private vulnerability reporting / security-advisory channel
if and when the maintainer enables it for this repository. If unavailable,
a reviewed private reporting contact must be established by the maintainer.
**Do not disclose vulnerabilities, credentials, tokens or private keys in
public GitHub Issues or Pull Requests.**

## Triage

The maintainer evaluates impact, affected versions, mitigation, and release
status. No response-time commitment is made until a governance policy is
explicitly approved. See `docs/adr/0001-licensing-and-governance.md`.

## PR-01 limitation

Scope reference syntax validation is not an authentication or authorization
control. Never treat `TrustedScopeRef` as evidence of an approved tenant.
