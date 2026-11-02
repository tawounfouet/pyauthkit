"""Explicit in-memory password resolver for tests and local demonstrations.

SECURITY: This snapshot is NOT durable, distributed, or proof of instant revocation.
"""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.password.records import (
    PasswordRecordAmbiguous,
    PasswordRecordFound,
    PasswordRecordLookup,
    PasswordRecordMissing,
    PasswordRecordUnavailable,
    PasswordRecordStatus,
    PasswordVerifierRecord,
    is_scoped_human_record,
)


type LookupKey = tuple[str, str, str]


class InMemoryPasswordCredentialResolver:
    """Immutable host-provisioned scoped mapping, with collision detection."""

    __slots__ = ("_records",)

    def __init__(self, records: Mapping[LookupKey, Sequence[PasswordVerifierRecord]]) -> None:
        checked: dict[LookupKey, tuple[PasswordVerifierRecord, ...]] = {}
        for key, values in records.items():
            if (
                not isinstance(key, tuple)
                or len(key) != 3
                or not all(isinstance(part, str) and part for part in key)
            ):
                raise ValueError("invalid scoped password lookup key")
            record_values = tuple(values)
            if not all(isinstance(record, PasswordVerifierRecord) for record in record_values):
                raise ValueError("invalid password record")
            checked[key] = record_values
        object.__setattr__(self, "_records", MappingProxyType(checked))

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("password resolver snapshot cannot be mutated")

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
    ) -> PasswordRecordLookup:
        if not isinstance(scope_ref, TrustedScopeRef):
            return PasswordRecordUnavailable()
        matches = self._records.get((scope_ref.value, identifier_kind, identifier_value), ())
        if len(matches) > 1:
            return PasswordRecordAmbiguous()
        if not matches:
            return PasswordRecordMissing()
        record = matches[0]
        if not is_scoped_human_record(record, scope_ref):
            return PasswordRecordUnavailable()
        return PasswordRecordFound(record)

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        """Snapshot-only check, without external revocation freshness guarantee."""
        if not isinstance(record, PasswordVerifierRecord):
            return False
        if record.status is not PasswordRecordStatus.ACTIVE:
            return False
        return any(
            other is record and other.version == record.version
            for key, records in self._records.items()
            if key[0] == record.scope_ref.value
            for other in records
        )
