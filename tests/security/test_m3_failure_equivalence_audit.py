"""M3-T09/T25/T27/T28/T29/T34: safe negative result projections."""

import asyncio

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorNotConfigured, AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.outcome import RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import (
    PasswordRecordAmbiguous,
    PasswordRecordFound,
    PasswordRecordMissing,
    PasswordRecordStatus,
    PasswordVerifierRecord,
)
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.ports.events import AuthenticationEvent


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


class CollectEvents:
    def __init__(self) -> None:
        self.events: list[AuthenticationEvent] = []

    async def emit(self, event: AuthenticationEvent) -> None:
        self.events.append(event)


class FixtureResolver:
    def __init__(self, outcome: object, *, outage: bool = False) -> None:
        self.outcome = outcome
        self.outage = outage

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
    ) -> object:
        if self.outage:
            raise RuntimeError("INTERNAL_FAILURE_CANARY_NEVER_PUBLIC")
        return self.outcome

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        return True


def setup(
    resolver: FixtureResolver,
) -> tuple[AuthenticationEngine, HostTrustCatalog, KDFWorkerPool, CollectEvents]:
    scope = TrustedScopeRef("negative-test-scope")
    workers = KDFWorkerPool(max_workers=1, max_inflight=2, memory_budget_kib=65536)
    dummy = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"synthetic-dummy-for-tests"
    )
    verifier = PasswordAuthenticator(
        resolver=resolver,  # type: ignore[arg-type]
        attempt_guard=PermitFixture(),
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=workers,
        dummy_hash=dummy,
    )
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "route",
                scope,
                TrustProfileRef("p", "v1", scope),
                frozenset({EvidenceMethod.PASSWORD}),
            )
        ]
    )
    events = CollectEvents()
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
        registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: verifier}),
        event_sink=events,
    )
    return engine, catalog, workers, events


def request(with_hint: bool = True) -> AuthenticationRequest:
    return AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.PASSWORD, b"synthetic-wrong-input"),
        CorrelationId("safe-trace"),
        ClaimedIdentity("username", "RAW_LOGIN_CANARY_NEVER_PUBLIC") if with_hint else None,
    )


def test_m3_t09_store_outage_is_generic_technical_error_and_audit_is_redacted() -> None:
    engine, catalog, workers, events = setup(FixtureResolver(None, outage=True))
    try:
        result = asyncio.run(
            engine.authenticate(request(), entry=catalog.resolve_for_host_route("route"))
        )
        assert isinstance(result, AuthError)
        assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        assert len(events.events) == 1
        assert events.events[0].result_status == "ERROR"
        combined = repr(result) + repr(events.events[0]) + str(events.events[0].result_status)
        for marker in ("RAW_LOGIN_CANARY", "INTERNAL_FAILURE_CANARY", "synthetic-wrong-input"):
            assert marker not in combined
    finally:
        workers.close()


def test_m3_t25_missing_wrong_revoked_ambiguous_and_no_hint_share_denial() -> None:
    scope = TrustedScopeRef("negative-test-scope")
    h = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"synthetic-correct-input"
    )
    active = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("host-subject", "issuer", scope),
        encoded_hash=h,
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    revoked = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("host-subject", "issuer", scope),
        encoded_hash=h,
        status=PasswordRecordStatus.REVOKED,
        version=2,
    )
    conditions: list[tuple[object, bool]] = [
        (PasswordRecordFound(active), True),
        (PasswordRecordMissing(), True),
        (PasswordRecordFound(revoked), True),
        (PasswordRecordAmbiguous(), True),
        (PasswordRecordMissing(), False),
    ]
    observed: list[tuple[str, object]] = []
    for outcome, with_hint in conditions:
        engine, catalog, workers, _ = setup(FixtureResolver(outcome))
        try:
            result = asyncio.run(
                engine.authenticate(
                    request(with_hint), entry=catalog.resolve_for_host_route("route")
                )
            )
            assert isinstance(result, Rejected)
            assert not hasattr(result, "principal")
            observed.append((result.status, result.reason_code))
        finally:
            workers.close()
    assert len(set(observed)) == 1


def test_m3_t27_t28_audit_event_never_contains_hash_or_login_canary() -> None:
    scope = TrustedScopeRef("negative-test-scope")
    encoded = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"test-audit-phrase"
    )
    record = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("PRIVATE_SUBJECT_CANARY", "issuer", scope),
        encoded_hash=encoded,
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    engine, catalog, workers, events = setup(FixtureResolver(PasswordRecordFound(record)))
    try:
        outcome = asyncio.run(
            engine.authenticate(request(), entry=catalog.resolve_for_host_route("route"))
        )
        assert isinstance(outcome, Rejected)
        assert len(events.events) == 1
        event = events.events[0]
        details = repr(event) + repr(outcome) + repr(record)
        assert encoded not in details
        assert "PRIVATE_SUBJECT_CANARY" not in details
        assert "RAW_LOGIN_CANARY" not in details
        assert event.method is EvidenceMethod.PASSWORD
        assert event.result_status == "REJECTED"
    finally:
        workers.close()


def test_m3_t34_malformed_or_oversized_evidence_rejected_before_kdf() -> None:
    for payload in (b"", b"x" * 65537):
        with pytest.raises(ValueError):
            PresentedEvidence(EvidenceMethod.PASSWORD, payload)
    with pytest.raises(ValueError):
        ClaimedIdentity("username", "control\x00character")
    with pytest.raises(ValueError):
        ClaimedIdentity("username", "x" * 257)


def test_m3_t29_registry_does_not_auto_register_password() -> None:
    class NonPasswordFixture:
        @property
        def method(self) -> EvidenceMethod:
            return EvidenceMethod.JWT

        async def verify(
            self, request: AuthenticationRequest, context: VerificationContext
        ) -> RejectedOutcome:
            return RejectedOutcome()

    registry = AuthenticatorRegistry({EvidenceMethod.JWT: NonPasswordFixture()})
    with pytest.raises(AuthenticatorNotConfigured):
        registry.resolve(EvidenceMethod.PASSWORD)
