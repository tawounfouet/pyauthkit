"""Real end-to-end Argon2id through M2 preflight, registry and final policy."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.adapters.password.memory import InMemoryPasswordCredentialResolver
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import PasswordRecordStatus, PasswordVerifierRecord


def hash_secret(secret: bytes) -> str:
    return PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(secret)


def request(secret: bytes, login: str = "alice") -> AuthenticationRequest:
    return AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.PASSWORD, secret),
        CorrelationId("m3-integration"),
        claimed_identity=ClaimedIdentity("username", login),
    )


def configured(
    password_hash: str,
    *,
    status: PasswordRecordStatus = PasswordRecordStatus.ACTIVE,
    expires_at: ObservedAt | None = None,
    allow: bool = True,
) -> tuple[AuthenticationEngine, HostTrustCatalog, KDFWorkerPool]:
    scope = TrustedScopeRef("tenant-a")
    record = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("alice-id", "host-owned", scope),
        encoded_hash=password_hash,
        status=status,
        version=1,
        expires_at=expires_at,
    )
    resolver = InMemoryPasswordCredentialResolver({("tenant-a", "username", "alice"): (record,)})
    workers = KDFWorkerPool(max_workers=1, max_inflight=2, memory_budget_kib=65536)
    password_authenticator = PasswordAuthenticator(
        resolver=resolver,
        hash_verifier=Argon2idPasswordHashVerifier(Argon2idPolicy()),
        workers=workers,
        dummy_hash=hash_secret(b"unknown-user-mitigation-secret"),
    )
    builder = AuthenticatorRegistryBuilder()
    builder.register(password_authenticator)
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "login",
                scope,
                TrustProfileRef("password-auth", "v1", scope),
                frozenset({EvidenceMethod.PASSWORD}),
            )
        ]
    )
    return (
        AuthenticationEngine(
            policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: allow),
            registry=builder.freeze(),
            timeout_seconds=3,
        ),
        catalog,
        workers,
    )


@pytest.mark.parametrize(
    ("secret", "login", "allow", "expected"),
    [
        (b"real-long-password-for-M3", "alice", True, Authenticated),
        (b"wrong-password", "alice", True, Rejected),
        (b"real-long-password-for-M3", "missing", True, Rejected),
        (b"real-long-password-for-M3", "alice", False, Rejected),
    ],
)
def test_real_m3_engine_flow_and_final_policy(
    secret: bytes, login: str, allow: bool, expected: type[object]
) -> None:
    engine, catalog, workers = configured(hash_secret(b"real-long-password-for-M3"), allow=allow)
    try:
        outcome = asyncio.run(
            engine.authenticate(
                request(secret, login), entry=catalog.resolve_for_host_route("login")
            )
        )
        assert isinstance(outcome, expected)
        assert hasattr(outcome, "principal") is (expected is Authenticated)
    finally:
        workers.close()


@pytest.mark.parametrize(
    "status",
    [
        PasswordRecordStatus.REVOKED,
        PasswordRecordStatus.DISABLED,
        PasswordRecordStatus.SUSPENDED,
        PasswordRecordStatus.EXPIRED,
    ],
)
def test_inadmissible_credential_rejected_even_with_right_password(
    status: PasswordRecordStatus,
) -> None:
    engine, catalog, workers = configured(hash_secret(b"real-long-password-for-M3"), status=status)
    try:
        result = asyncio.run(
            engine.authenticate(
                request(b"real-long-password-for-M3"),
                entry=catalog.resolve_for_host_route("login"),
            )
        )
        assert isinstance(result, Rejected)
        assert not hasattr(result, "principal")
    finally:
        workers.close()


def test_expired_record_rejected() -> None:
    engine, catalog, workers = configured(
        hash_secret(b"real-long-password-for-M3"),
        expires_at=ObservedAt(datetime.now(UTC) - timedelta(seconds=2)),
    )
    try:
        result = asyncio.run(
            engine.authenticate(
                request(b"real-long-password-for-M3"),
                entry=catalog.resolve_for_host_route("login"),
            )
        )
        assert isinstance(result, Rejected)
    finally:
        workers.close()


def test_unapproved_phc_hash_is_error_never_success() -> None:
    engine, catalog, workers = configured("$argon2id$v=19$m=9999999,t=2,p=1$bad$bad")
    try:
        result = asyncio.run(
            engine.authenticate(
                request(b"real-long-password-for-M3"),
                entry=catalog.resolve_for_host_route("login"),
            )
        )
        assert isinstance(result, AuthError)
    finally:
        workers.close()
