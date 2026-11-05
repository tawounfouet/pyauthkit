"""Scoped, async read port for externally owned API-key verifier records.

[ARCH: Ports & Adapters] [PRINCIPLE: Dependency Inversion]
The store must scope the query at its authoritative source; a Python port alone
cannot prove an SQL query or upstream service actually enforces isolation.
"""

from typing import Protocol

from pyauthkit.domain.api_key import ApiKeyRecordLookup, ApiKeyVerifierRecord
from pyauthkit.domain.scope import TrustedScopeRef


class ApiKeyCredentialResolver(Protocol):
    """Only host-approved scope + bounded selector, never global key lookup."""

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, key_id: str
    ) -> ApiKeyRecordLookup: ...

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        """Re-read authoritative version/state where owner consistency permits."""
        ...
