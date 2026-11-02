# ADR-0001: Licensing and security governance

- **Status:** OPEN / PROPOSED
- **Related work:** WP27-001 (M0); PR-01
- **Decision owner:** repository maintainer
- **Source:** roadmap 27 §13, §70; bootstrap 28 ADR28-002

## Context

The repository is public but public visibility does not grant a license for
redistribution or commercial use. This draft PR does not silently grant one.
A security-sensitive Python library needs a documented disclosure channel and
support scope before release.

## Alternatives

1. Apache-2.0 with explicit patent grant and required notices.
2. MIT with short permissive terms.
3. Another explicit owner-approved license.

## Proposed decision

Keep this ADR open until the maintainer selects the SPDX license and approves
the copyright/notice text. Add the complete LICENSE file and project metadata
**before merging a release candidate**. Do not upload a package to PyPI while
this decision is open.

SECURITY.md currently directs to a private advisory channel only if enabled.
The maintainer must confirm secure reporting availability and a reviewed
private contact fallback; response SLAs are not yet promised.

## Evidence required for acceptance

- Selected license with rationale, complete LICENSE file and SPDX metadata.
- SECURITY.md reporting channel confirmed privately by maintainer.
- README and package metadata consistent with the license.
