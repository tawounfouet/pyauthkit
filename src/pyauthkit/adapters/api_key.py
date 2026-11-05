"""Host-injected API-key resolver adapter for PR-07A.

An integration callback MUST query by (host-approved scope, key_id) at source.
Rejecting a foreign result here is defense-in-depth, not proof of SQL isolation.
This adapter never cryptographically verifies a key or issues AuthenticationResult.
"""

from collections.abc import Awaitable, Callable
from typing import Never

from pyauthkit.domain.api_key import (
    ApiKeyAmbiguous,
    ApiKeyCredentialRef,
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordLookup,
    ApiKeyUnavailable,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.scope import TrustedScopeRef

LookupCallback = Callable[[TrustedScopeRef, str], Awaitable[ApiKeyRecordLookup]]
FreshnessCallback = Callable[[ApiKeyVerifierRecord], Awaitable[bool]]


class HostCallbackApiKeyResolver:
    """Explicit callback composition. No default store, global search or cache."""

    __slots__ = ("_lookup", "_freshness")

    _lookup: LookupCallback
    _freshness: FreshnessCallback

    def __init__(self, *, lookup: LookupCallback, freshness: FreshnessCallback) -> None:
        if not callable(lookup) or not callable(freshness):
            raise ValueError("both authoritative resolver callbacks are required")
        object.__setattr__(self, "_lookup", lookup)
        object.__setattr__(self, "_freshness", freshness)

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("resolver composition is immutable")

    def __repr__(self) -> str:
        return "HostCallbackApiKeyResolver(<host-owned callbacks>)"

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, key_id: str
    ) -> ApiKeyRecordLookup:
        if not isinstance(scope_ref, TrustedScopeRef):
            raise ValueError("invalid approved scope")
        ApiKeyCredentialRef(key_id)
        outcome = await self._lookup(scope_ref, key_id)
        if isinstance(outcome, ApiKeyFound):
            record = outcome.record
            if record.scope_ref != scope_ref or record.subject_ref.scope_ref != scope_ref:
                return ApiKeyUnavailable()
            if record.key_id != key_id:
                return ApiKeyUnavailable()
            return outcome
        if isinstance(outcome, (ApiKeyMissing, ApiKeyAmbiguous, ApiKeyUnavailable)):
            return outcome
        return ApiKeyUnavailable()

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        if not isinstance(record, ApiKeyVerifierRecord):
            raise ValueError("invalid verifier record")
        # Only a real bool True is accepted; an unexpected value cannot grant trust.
        return (await self._freshness(record)) is True
