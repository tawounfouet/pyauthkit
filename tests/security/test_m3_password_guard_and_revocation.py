"""M3 guard admission and revocation-between-KDF-and-publication tests."""

import asyncio

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.outcome import ErrorOutcome, RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import (
    PasswordRecordFound,
    PasswordRecordStatus,
    PasswordVerifierRecord,
)
from pyauthkit.ports.authenticator import VerificationContext


def real_hash(secret: bytes) -> str:
    return PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        secret
    )


class Guard:
    def __init__(self, *, allow: bool = True, fail: bool = False) -> None:
        self.allow = allow
        self.fail = fail
        self.calls = 0

    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        identifier_kind: str | None,
        identifier_value: str | None,
    ) -> bool:
        self.calls += 1
        if self.fail:
            raise RuntimeError("internal-host-guard-error")
        return self.allow


class Resolver:
    def __init__(self, record: PasswordVerifierRecord) -> None:
        self.record = record
        self.resolved = 0
        self.checked = 0
        self.current = True

    async def resolve(
        self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
    ) -> PasswordRecordFound:
        self.resolved += 1
        return PasswordRecordFound(self.record)

    async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
        self.checked += 1
        return self.current


def components(
    guard: Guard,
) -> tuple[PasswordAuthenticator, Resolver, KDFWorkerPool, TrustedScopeRef]:
    scope = TrustedScopeRef("guard-scope")
    record = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("subject", "trusted-issuer", scope),
        encoded_hash=real_hash(b"actual-test-password"),
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    resolver = Resolver(record)
    workers = KDFWorkerPool(max_workers=1, max_inflight=1, memory_budget_kib=65536)
    authenticator = PasswordAuthenticator(
        resolver=resolver,
        attempt_guard=guard,
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=workers,
        dummy_hash=real_hash(b"dummy-test-password"),
    )
    return authenticator, resolver, workers, scope


@pytest.mark.parametrize(
    ("allow", "fail", "expected"),
    [
        (False, False, RejectedOutcome),
        (True, True, ErrorOutcome),
    ],
)
def test_guard_denial_or_outage_blocks_resolver_and_kdf(
    allow: bool, fail: bool, expected: type[object]
) -> None:
    guard = Guard(allow=allow, fail=fail)
    authenticator, resolver, workers, scope = components(guard)
    try:
        trace = CorrelationId("guard-test")
        ctx = VerificationContext(
            scope, TrustProfileRef("p", "v1", scope), EvidenceMethod.PASSWORD, trace, object()
        )
        req = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.PASSWORD, b"actual-test-password"),
            trace,
            ClaimedIdentity("username", "alice"),
        )
        result = asyncio.run(authenticator.verify(req, ctx))
        assert isinstance(result, expected)
        assert guard.calls == 1
        assert resolver.resolved == 0
        assert resolver.checked == 0
    finally:
        workers.close()


def test_missing_attempt_guard_rejected_at_bootstrap() -> None:
    guard = Guard()
    authenticator, resolver, workers, _ = components(guard)
    try:
        with pytest.raises(TypeError):
            PasswordAuthenticator(
                resolver=resolver,
                hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
                workers=workers,
                dummy_hash=real_hash(b"dummy-test-password"),
            )
        with pytest.raises(AttributeError):
            authenticator._resolver = resolver  # type: ignore[misc]
    finally:
        workers.close()


def test_revalidated_revocation_refuses_correct_password_before_final_gate() -> None:
    guard = Guard()
    authenticator, resolver, workers, scope = components(guard)
    resolver.current = False
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
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _subject, _entry: True),
        registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: authenticator}),
    )
    try:
        result = asyncio.run(
            engine.authenticate(
                AuthenticationRequest(
                    PresentedEvidence(EvidenceMethod.PASSWORD, b"actual-test-password"),
                    CorrelationId("revocation-race"),
                    ClaimedIdentity("username", "alice"),
                ),
                entry=catalog.resolve_for_host_route("route"),
            )
        )
        assert isinstance(result, Rejected)
        assert resolver.resolved == 1
        assert resolver.checked == 1
        assert not hasattr(result, "principal")
    finally:
        workers.close()
