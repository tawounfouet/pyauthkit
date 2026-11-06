"""Host-managed online-attempt guard; no default permit-all implementation."""

from typing import Protocol

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId


class PasswordAttemptGuard(Protocol):
    """Host policy for admitting an online password verification attempt.

    Must be backed by deployment-appropriate quotas and controls. A local-only
    or test-only adapter is not evidence of distributed brute-force resistance.
    """

    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        identifier_kind: str | None,
        identifier_value: str | None,
    ) -> bool:
        """True only when admission is explicitly permitted."""
        ...
