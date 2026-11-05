"""Mandatory host-managed online API key attempt admission port.

[SECURITY: Anti-Automation] [ARCH: Dependency Inversion]
The host owns quotas and trusted client-network provenance. A permissive
test fake is not production protection or a globally coordinated rate limit.
"""

from typing import Protocol

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId


class ApiKeyAttemptGuard(Protocol):
    """Admit a bounded attempt before any key lookup or secret computation."""

    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        key_id: str | None,
    ) -> bool:
        """Return only true for an explicitly admitted attempt.

        Never trust client-supplied IP, tenant or budget headers. A store outage
        should raise a safe exception and become a technical failure.
        """
        ...
