"""M3-T21: a timed-out engine must not release an active native worker."""

import asyncio
from threading import Event

from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import (
    PasswordRecordFound,
    PasswordRecordStatus,
    PasswordVerifierRecord,
)


class PermitFixtureGuard:
    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        identifier_kind: str | None,
        identifier_value: str | None,
    ) -> bool:
        return True


class FixedFixtureResolver:
    def __init__(self, scope: TrustedScopeRef) -> None:
        self.record = PasswordVerifierRecord(
            scope_ref=scope,
            subject_ref=ScopedSubjectRef("fixture-subject", "fixture-issuer", scope),
            encoded_hash="test-only-verifier-material",
            status=PasswordRecordStatus.ACTIVE,
            version=1,
        )

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
    ) -> PasswordRecordFound:
        return PasswordRecordFound(self.record)

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        return True


class BlockingFixtureKDF:
    """Intentionally fake: only native-worker lifetime is being qualified."""

    max_memory_cost_kib = 19456

    def __init__(self, entered: Event, release: Event) -> None:
        self.entered = entered
        self.release = release

    def validate_hash(self, encoded_hash: str) -> None:
        if not encoded_hash:
            raise ValueError("missing fixture hash")

    def verify(self, *, password: bytes, encoded_hash: str) -> bool:
        self.entered.set()
        return self.release.wait(4)

    def needs_rehash(self, *, encoded_hash: str) -> bool:
        return False


def test_m3_t21_timeout_never_grants_late_success_or_releases_busy_worker() -> None:
    scope = TrustedScopeRef("capacity-scope")
    entered, release = Event(), Event()
    workers = KDFWorkerPool(
        max_workers=1,
        max_inflight=1,
        max_memory_cost_kib=19456,
        memory_budget_kib=19456,
    )
    verifier = PasswordAuthenticator(
        resolver=FixedFixtureResolver(scope),
        attempt_guard=PermitFixtureGuard(),
        hash_verifier=BlockingFixtureKDF(entered, release),
        workers=workers,
        dummy_hash="fixture-dummy-verifier",
    )
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "route", scope, TrustProfileRef("p", "v1", scope),
                frozenset({EvidenceMethod.PASSWORD}),
            )
        ]
    )
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _subject, _entry: True),
        registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: verifier}),
        timeout_seconds=0.05,
    )

    async def scenario() -> None:
        entry = catalog.resolve_for_host_route("route")

        def request(trace: str) -> AuthenticationRequest:
            return AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.PASSWORD, b"fixture-input"),
                CorrelationId(trace),
                ClaimedIdentity("username", "fixture-user"),
            )

        first = asyncio.create_task(engine.authenticate(request("first"), entry=entry))
        assert await asyncio.to_thread(entered.wait, 2)
        timed_out = await first
        assert isinstance(timed_out, AuthError)
        assert timed_out.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        second = await engine.authenticate(request("second"), entry=entry)
        assert isinstance(second, AuthError)
        assert second.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        release.set()
        await asyncio.to_thread(workers.close)
        assert isinstance(timed_out, AuthError)

    try:
        asyncio.run(scenario())
    finally:
        release.set()
        workers.close()
