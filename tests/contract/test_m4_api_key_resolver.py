"""PR-07A: independent scoped-lookup contract tests. No authentication claim."""

import asyncio
from collections import defaultdict
from datetime import UTC, datetime

import pytest

from pyauthkit.adapters.api_key import HostCallbackApiKeyResolver
from pyauthkit.domain.api_key import (
    ApiKeyAmbiguous,
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordLookup,
    ApiKeyRecordStatus,
    ApiKeyUnavailable,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.ports.api_key import ApiKeyCredentialResolver


def record(scope: str, key_id: str = "collision") -> ApiKeyVerifierRecord:
    scope_ref = TrustedScopeRef(scope)
    return ApiKeyVerifierRecord(
        scope_ref=scope_ref,
        subject_ref=ScopedSubjectRef(
            subject_id="service-1", issuer_ref="trusted-issuer", scope_ref=scope_ref
        ),
        principal_type=PrincipalType.SERVICE,
        key_id=key_id,
        verifier_digest=bytes(range(32)),
        verifier_algorithm="hmac-sha256",
        protection_key_ref="key-version-1",
        status=ApiKeyRecordStatus.ACTIVE,
        version=1,
        not_before=ObservedAt(datetime(2026, 1, 1, tzinfo=UTC)),
    )


class InMemoryApiKeyResolver:
    """Test-only source-scoped fake: no real DB or distributed freshness claim."""

    def __init__(self, records: list[ApiKeyVerifierRecord]) -> None:
        self.records: dict[tuple[TrustedScopeRef, str], list[ApiKeyVerifierRecord]] = defaultdict(
            list
        )
        self.available = True
        for item in records:
            self.records[(item.scope_ref, item.key_id)].append(item)

    async def lookup(self, scope: TrustedScopeRef, key_id: str) -> ApiKeyRecordLookup:
        if not self.available:
            return ApiKeyUnavailable()
        candidates = self.records.get((scope, key_id), [])
        if not candidates:
            return ApiKeyMissing()
        if len(candidates) != 1:
            return ApiKeyAmbiguous()
        return ApiKeyFound(candidates[0])

    async def freshness(self, record_: ApiKeyVerifierRecord) -> bool:
        if not self.available:
            return False
        current = self.records.get((record_.scope_ref, record_.key_id), [])
        return len(current) == 1 and current[0] is record_

    def as_adapter(self) -> ApiKeyCredentialResolver:
        return HostCallbackApiKeyResolver(lookup=self.lookup, freshness=self.freshness)


@pytest.mark.contract
def test_same_selector_in_two_tenants_has_independent_results() -> None:
    first = record("tenant-a")
    second = record("tenant-b")
    adapter = InMemoryApiKeyResolver([first, second]).as_adapter()

    async def run() -> None:
        for scope, expected in (("tenant-a", first), ("tenant-b", second)):
            result = await adapter.resolve(scope_ref=TrustedScopeRef(scope), key_id="collision")
            assert isinstance(result, ApiKeyFound)
            assert result.record is expected
        missing = await adapter.resolve(scope_ref=TrustedScopeRef("tenant-c"), key_id="collision")
        assert isinstance(missing, ApiKeyMissing)

    asyncio.run(run())


@pytest.mark.contract
def test_ambiguity_is_not_silently_resolved() -> None:
    adapter = InMemoryApiKeyResolver([record("tenant-a"), record("tenant-a")]).as_adapter()
    outcome = asyncio.run(
        adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="collision")
    )
    assert isinstance(outcome, ApiKeyAmbiguous)


@pytest.mark.contract
def test_unavailable_has_no_fallback_to_stale_record() -> None:
    memory = InMemoryApiKeyResolver([record("tenant-a")])
    memory.available = False
    adapter = memory.as_adapter()
    outcome = asyncio.run(
        adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="collision")
    )
    assert isinstance(outcome, ApiKeyUnavailable)


@pytest.mark.security
def test_callback_foreign_scope_is_rejected() -> None:
    async def foreign(_scope: TrustedScopeRef, _key_id: str) -> ApiKeyRecordLookup:
        return ApiKeyFound(record("tenant-b"))

    async def current(_record: ApiKeyVerifierRecord) -> bool:
        return True

    adapter = HostCallbackApiKeyResolver(lookup=foreign, freshness=current)
    outcome = asyncio.run(
        adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="collision")
    )
    assert isinstance(outcome, ApiKeyUnavailable)


@pytest.mark.security
def test_callback_wrong_selector_is_rejected() -> None:
    async def mismatch(_scope: TrustedScopeRef, _key_id: str) -> ApiKeyRecordLookup:
        return ApiKeyFound(record("tenant-a", "other-id"))

    async def current(_record: ApiKeyVerifierRecord) -> bool:
        return True

    adapter = HostCallbackApiKeyResolver(lookup=mismatch, freshness=current)
    outcome = asyncio.run(
        adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="collision")
    )
    assert isinstance(outcome, ApiKeyUnavailable)


@pytest.mark.contract
def test_unknown_callback_outcome_fails_closed() -> None:
    async def invalid(_scope: TrustedScopeRef, _key_id: str) -> ApiKeyRecordLookup:
        return None  # type: ignore[return-value]

    async def current(_record: ApiKeyVerifierRecord) -> bool:
        return True

    adapter = HostCallbackApiKeyResolver(lookup=invalid, freshness=current)
    outcome = asyncio.run(
        adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="collision")
    )
    assert isinstance(outcome, ApiKeyUnavailable)


@pytest.mark.contract
def test_bounded_selector_rejected_before_host_callback() -> None:
    calls = []

    async def lookup(_scope: TrustedScopeRef, key_id: str) -> ApiKeyRecordLookup:
        calls.append(key_id)
        return ApiKeyMissing()

    async def current(_record: ApiKeyVerifierRecord) -> bool:
        return False

    adapter = HostCallbackApiKeyResolver(lookup=lookup, freshness=current)
    with pytest.raises(ValueError, match="invalid API key selector"):
        asyncio.run(adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="x" * 129))
    assert not calls


@pytest.mark.contract
def test_freshness_fails_closed_on_false_or_non_bool() -> None:
    async def lookup(_scope: TrustedScopeRef, _key_id: str) -> ApiKeyRecordLookup:
        return ApiKeyMissing()

    async def truthy(_record: ApiKeyVerifierRecord) -> bool:
        return 1  # type: ignore[return-value]

    adapter = HostCallbackApiKeyResolver(lookup=lookup, freshness=truthy)
    assert asyncio.run(adapter.is_current(record=record("tenant-a"))) is False


@pytest.mark.contract
def test_freshness_detects_replacement() -> None:
    first = record("tenant-a")
    memory = InMemoryApiKeyResolver([first])
    adapter = memory.as_adapter()
    assert asyncio.run(adapter.is_current(record=first))
    memory.records[(first.scope_ref, first.key_id)] = [record("tenant-a")]
    assert not asyncio.run(adapter.is_current(record=first))


@pytest.mark.contract
def test_callback_signature_is_explicitly_scoped() -> None:
    seen: list[tuple[TrustedScopeRef, str]] = []

    async def lookup(scope: TrustedScopeRef, key_id: str) -> ApiKeyRecordLookup:
        seen.append((scope, key_id))
        return ApiKeyMissing()

    async def freshness(_record: ApiKeyVerifierRecord) -> bool:
        return False

    adapter = HostCallbackApiKeyResolver(lookup=lookup, freshness=freshness)
    asyncio.run(adapter.resolve(scope_ref=TrustedScopeRef("tenant-a"), key_id="selector-1"))
    assert seen == [(TrustedScopeRef("tenant-a"), "selector-1")]
