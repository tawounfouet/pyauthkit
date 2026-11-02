"""Adversarial cross-tenant, stale record, cancellation and result redaction."""

import asyncio

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
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError, Rejected
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


class PermitTestGuard:
    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        identifier_kind: str | None,
        identifier_value: str | None,
    ) -> bool:
        return True


def encoded() -> str:
    return PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"real-secret"
    )


def setup() -> tuple[PasswordAuthenticator, AuthenticationEngine, HostTrustCatalog, KDFWorkerPool]:
    scope = TrustedScopeRef("tenant-1")
    other = TrustedScopeRef("tenant-2")
    foreign = PasswordVerifierRecord(
        scope_ref=other,
        subject_ref=ScopedSubjectRef("foreign", "issuer", other),
        encoded_hash=encoded(),
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )

    class BrokenResolver:
        async def resolve(
            self, *, scope_ref: TrustedScopeRef, identifier_kind: str, identifier_value: str
        ) -> PasswordRecordFound:
            return PasswordRecordFound(foreign)

        async def is_current(self, *, record: PasswordVerifierRecord) -> bool:
            return True

    workers = KDFWorkerPool(max_workers=1, max_inflight=1, memory_budget_kib=65536)
    verifier = PasswordAuthenticator(
        resolver=BrokenResolver(),
        attempt_guard=PermitTestGuard(),
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=workers,
        dummy_hash=encoded(),
    )
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "r1", scope, TrustProfileRef("p", "v1", scope), frozenset({EvidenceMethod.PASSWORD})
            )
        ]
    )
    registry = AuthenticatorRegistry({EvidenceMethod.PASSWORD: verifier})
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
        registry=registry,
    )
    return verifier, engine, catalog, workers


def test_cross_tenant_resolver_cannot_authenticate() -> None:
    _, engine, catalog, workers = setup()
    try:
        req = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.PASSWORD, b"real-secret"),
            CorrelationId("m3-cross"),
            claimed_identity=ClaimedIdentity("username", "victim"),
        )
        result = asyncio.run(engine.authenticate(req, entry=catalog.resolve_for_host_route("r1")))
        assert isinstance(result, AuthError)
        assert not hasattr(result, "principal")
        assert "real-secret" not in repr(result)
    finally:
        workers.close()


def test_mismatched_context_rejected_before_kdf() -> None:
    verifier, _, catalog, workers = setup()
    try:
        scope = TrustedScopeRef("tenant-1")
        context = VerificationContext(
            scope,
            TrustProfileRef("p", "v1", scope),
            EvidenceMethod.JWT,
            CorrelationId("wrong"),
            object(),
        )
        req = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.PASSWORD, b"real-secret"),
            CorrelationId("actual"),
        )
        result = asyncio.run(verifier.verify(req, context))
        assert result.status == "ERROR"
    finally:
        workers.close()


def test_host_preflight_blocks_claimed_foreign_tenant() -> None:
    _, engine, catalog, workers = setup()
    try:
        req = AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.PASSWORD, b"real-secret"),
            CorrelationId("foreign-claim"),
            claimed_identity=ClaimedIdentity("username", "victim", claimed_tenant="tenant-2"),
        )
        result = asyncio.run(engine.authenticate(req, entry=catalog.resolve_for_host_route("r1")))
        assert isinstance(result, Rejected)
    finally:
        workers.close()
