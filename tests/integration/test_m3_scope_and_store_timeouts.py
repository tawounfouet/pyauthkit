"""M3-T09/T15: real per-scope passwords and an unavailable async store."""

import asyncio

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
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import PasswordRecordStatus, PasswordVerifierRecord


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


def encoded(phrase: bytes) -> str:
    return PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        phrase
    )


def make_request(phrase: bytes, trace: str) -> AuthenticationRequest:
    return AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.PASSWORD, phrase),
        CorrelationId(trace),
        ClaimedIdentity("username", "same-username"),
    )


def test_m3_t15_real_two_tenants_same_username_have_independent_proofs() -> None:
    scope_a, scope_b = TrustedScopeRef("realm-a"), TrustedScopeRef("realm-b")
    record_a = PasswordVerifierRecord(
        scope_ref=scope_a,
        subject_ref=ScopedSubjectRef("subject-a", "issuer", scope_a),
        encoded_hash=encoded(b"realm-a-phrase"),
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    record_b = PasswordVerifierRecord(
        scope_ref=scope_b,
        subject_ref=ScopedSubjectRef("subject-b", "issuer", scope_b),
        encoded_hash=encoded(b"realm-b-phrase"),
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    resolver = InMemoryPasswordCredentialResolver(
        {
            ("realm-a", "username", "same-username"): (record_a,),
            ("realm-b", "username", "same-username"): (record_b,),
        }
    )
    workers = KDFWorkerPool(max_workers=2, max_inflight=4, memory_budget_kib=131072)
    verifier = PasswordAuthenticator(
        resolver=resolver,
        attempt_guard=PermitFixture(),
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=workers,
        dummy_hash=encoded(b"missing-record-dummy"),
    )
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "route-a", scope_a, TrustProfileRef("p", "v1", scope_a),
                frozenset({EvidenceMethod.PASSWORD}),
            ),
            HostBinding(
                "route-b", scope_b, TrustProfileRef("p", "v1", scope_b),
                frozenset({EvidenceMethod.PASSWORD}),
            ),
        ]
    )
    engine = AuthenticationEngine(
        registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: verifier}),
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
    )

    async def scenario() -> None:
        a = catalog.resolve_for_host_route("route-a")
        b = catalog.resolve_for_host_route("route-b")
        correct_a = await engine.authenticate(make_request(b"realm-a-phrase", "a-ok"), entry=a)
        correct_b = await engine.authenticate(make_request(b"realm-b-phrase", "b-ok"), entry=b)
        wrong_a = await engine.authenticate(make_request(b"realm-b-phrase", "a-no"), entry=a)
        wrong_b = await engine.authenticate(make_request(b"realm-a-phrase", "b-no"), entry=b)
        assert isinstance(correct_a, Authenticated)
        assert isinstance(correct_b, Authenticated)
        assert correct_a.principal.subject == record_a.subject_ref
        assert correct_b.principal.subject == record_b.subject_ref
        assert isinstance(wrong_a, Rejected)
        assert isinstance(wrong_b, Rejected)

    try:
        asyncio.run(scenario())
    finally:
        workers.close()


def test_m3_t09_delayed_source_is_timed_out_without_fallback_or_success() -> None:
    scope = TrustedScopeRef("timeout-scope")

    class DelayedResolver:
        def __init__(self) -> None:
            self.reached = False

        async def resolve(
            self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
        ) -> object:
            self.reached = True
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

        async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
            raise AssertionError("should never run")

    resolver = DelayedResolver()
    workers = KDFWorkerPool(max_workers=1, max_inflight=1, memory_budget_kib=65536)
    verifier = PasswordAuthenticator(
        resolver=resolver,
        attempt_guard=PermitFixture(),
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=workers,
        dummy_hash=encoded(b"missing-record-dummy"),
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
        registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: verifier}),
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
        timeout_seconds=0.03,
    )
    try:
        result = asyncio.run(
            engine.authenticate(
                make_request(b"fixture-input", "delayed"),
                entry=catalog.resolve_for_host_route("route"),
            )
        )
        assert resolver.reached
        assert isinstance(result, AuthError)
        assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    finally:
        workers.close()
