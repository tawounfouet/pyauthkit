"""Password credential read ports; owner and storage remain host-controlled."""

from typing import Protocol

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.password.records import PasswordRecordLookup, PasswordVerifierRecord


class PasswordCredentialResolver(Protocol):
    """Every lookup MUST be restricted at the source to an approved scope."""

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
    ) -> PasswordRecordLookup: ...

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        """Re-read authoritative version/status under the record's scope.

        A deployment claiming strict revocation must independently qualify its
        store's freshness/consistency. A local snapshot is not such evidence.
        """
        ...
