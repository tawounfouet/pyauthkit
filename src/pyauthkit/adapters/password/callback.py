"""Host-defined scoped resolver callbacks with defensive postvalidation."""

from collections.abc import Awaitable, Callable

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.password.records import (
    PasswordRecordFound,
    PasswordRecordLookup,
    PasswordRecordUnavailable,
    PasswordVerifierRecord,
    is_scoped_human_record,
)

type ResolveCallback = Callable[[TrustedScopeRef, str, str], Awaitable[PasswordRecordLookup]]
type CurrentCallback = Callable[[PasswordVerifierRecord], Awaitable[bool]]


class CallbackPasswordCredentialResolver:
    """Callbacks must enforce source-side scope, not merely filter results.

    The postcondition catches obvious cross-scope adapter failures, but cannot
    prove the host backend query was securely scoped.
    """

    __slots__ = ("_resolve_callback", "_current_callback")

    def __init__(
        self, *, resolve_callback: ResolveCallback, current_callback: CurrentCallback
    ) -> None:
        if not callable(resolve_callback) or not callable(current_callback):
            raise ValueError("password resolver callbacks are required")
        self._resolve_callback = resolve_callback
        self._current_callback = current_callback

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
    ) -> PasswordRecordLookup:
        result = await self._resolve_callback(scope_ref, identifier_kind, identifier_value)
        if isinstance(result, PasswordRecordFound):
            if not is_scoped_human_record(result.record, scope_ref):
                return PasswordRecordUnavailable()
            return result
        from pyauthkit.password.records import (
            PasswordRecordAmbiguous,
            PasswordRecordMissing,
        )

        if isinstance(result, (PasswordRecordMissing, PasswordRecordAmbiguous, PasswordRecordUnavailable)):
            return result
        return PasswordRecordUnavailable()

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        return await self._current_callback(record) is True
