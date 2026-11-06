"""Real cryptography and deterministic trust-boundary assertions for M3."""

import asyncio
from datetime import UTC, datetime

from argon2 import PasswordHasher
from argon2.low_level import Type

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.adapters.password.memory import InMemoryPasswordCredentialResolver
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import (
    PasswordRecordFound,
    PasswordRecordStatus,
    PasswordVerifierRecord,
)


class PermitFixture:
    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        identifier_kind: str | None,
        identifier_value: str | None,
    ) -> bool:
        return True


class FrozenClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def make_record(encoded: str, *, expiration: ObservedAt | None = None) -> PasswordVerifierRecord:
    scope = TrustedScopeRef("real-qual-scope")
    return PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("stable-subject", "host-owned", scope),
        encoded_hash=encoded,
        status=PasswordRecordStatus.ACTIVE,
        expires_at=expiration,
        version=7,
    )


def make_engine(
    record: PasswordVerifierRecord, resolver: object, *, clock: FrozenClock | None = None
) -> tuple[AuthenticationEngine, HostTrustCatalog, KDFWorkerPool]:
    scope = record.scope_ref
    pool = KDFWorkerPool(max_workers=1, max_inflight=2, memory_budget_kib=65536)
    dummy = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"synthetic-dummy-phrase"
    )
    verifier = PasswordAuthenticator(
        resolver=resolver,  # type: ignore[arg-type]
        attempt_guard=PermitFixture(),
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=pool,
        dummy_hash=dummy,
        clock=clock,
    )
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "r",
                scope,
                TrustProfileRef("p", "v1", scope),
                frozenset({EvidenceMethod.PASSWORD}),
            )
        ]
    )
    return (
        AuthenticationEngine(
            policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
            registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: verifier}),
        ),
        catalog,
        pool,
    )


def submit(phrase: bytes) -> AuthenticationRequest:
    return AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.PASSWORD, phrase),
        CorrelationId("real-qualification"),
        ClaimedIdentity("username", "alice"),
    )


def test_m3_t07_expiration_exact_utc_instant_is_rejected() -> None:
    exact = datetime(2026, 11, 3, 8, 0, tzinfo=UTC)
    h = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"valid-phrase"
    )
    record = make_record(h, expiration=ObservedAt(exact))
    resolver = InMemoryPasswordCredentialResolver(
        {(record.scope_ref.value, "username", "alice"): (record,)}
    )
    engine, catalog, workers = make_engine(record, resolver, clock=FrozenClock(exact))
    try:
        result = asyncio.run(
            engine.authenticate(submit(b"valid-phrase"), entry=catalog.resolve_for_host_route("r"))
        )
        assert isinstance(result, Rejected)
    finally:
        workers.close()


def test_m3_t35_unicode_bytes_are_not_normalized_or_truncated() -> None:
    composed = "café-éléphant".encode()
    decomposed = "cafe\u0301-éléphant".encode()
    assert composed != decomposed
    h = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(composed)
    record = make_record(h)
    resolver = InMemoryPasswordCredentialResolver(
        {(record.scope_ref.value, "username", "alice"): (record,)}
    )
    engine, catalog, workers = make_engine(record, resolver)
    try:

        async def check() -> tuple[object, object]:
            entry = catalog.resolve_for_host_route("r")
            correct = await engine.authenticate(submit(composed), entry=entry)
            different = await engine.authenticate(submit(decomposed), entry=entry)
            return correct, different

        correct, different = asyncio.run(check())
        assert isinstance(correct, Authenticated)
        assert isinstance(different, Rejected)
    finally:
        workers.close()


def test_m3_t33_revocation_during_post_kdf_freshness_check_is_rejected() -> None:
    h = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"valid-phrase"
    )
    record = make_record(h)

    class ConcurrentResolver:
        def __init__(self) -> None:
            self.entered = asyncio.Event()
            self.release = asyncio.Event()
            self.current = True

        async def resolve(
            self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
        ) -> PasswordRecordFound:
            return PasswordRecordFound(record)

        async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
            self.entered.set()
            await self.release.wait()
            return self.current

    resolver = ConcurrentResolver()
    engine, catalog, workers = make_engine(record, resolver)

    async def scenario() -> None:
        task = asyncio.create_task(
            engine.authenticate(
                submit(b"valid-phrase"),
                entry=catalog.resolve_for_host_route("r"),
            )
        )
        await asyncio.wait_for(resolver.entered.wait(), timeout=2)
        resolver.current = False
        resolver.release.set()
        result = await task
        assert isinstance(result, Rejected)
        assert not hasattr(result, "principal")

    try:
        asyncio.run(scenario())
    finally:
        workers.close()


def test_m3_t40_legacy_tag_size_needs_rehash_but_authn_is_read_only() -> None:
    legacy = PasswordHasher(
        memory_cost=19456, time_cost=2, parallelism=1, hash_len=16, type=Type.ID
    ).hash(b"fixture-old-tag")
    crypto = Argon2idPasswordHashVerifier(Argon2idPolicy())
    assert crypto.needs_rehash(encoded_hash=legacy)
    record = make_record(legacy)
    original_hash = record.encoded_hash
    resolver = InMemoryPasswordCredentialResolver(
        {(record.scope_ref.value, "username", "alice"): (record,)}
    )
    engine, catalog, workers = make_engine(record, resolver)
    try:
        result = asyncio.run(
            engine.authenticate(
                submit(b"fixture-old-tag"), entry=catalog.resolve_for_host_route("r")
            )
        )
        assert isinstance(result, Authenticated)
        assert record.encoded_hash == original_hash
        assert record.version == 7
    finally:
        workers.close()
