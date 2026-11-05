"""Real PostgreSQL/Redis source isolation, CAS and post-proof revocation."""

import asyncio

import httpx
import pytest
from redis.asyncio import Redis

from pyauthkit.adapters.api_key import HostCallbackApiKeyResolver
from pyauthkit.adapters.api_key_authenticator import ApiKeyAuthenticator
from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.api_key import (
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordLookup,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from qualification.m4_host.app import FixtureProtectionKeySource, compose_app
from qualification.m4_host.guard import HOST_PEER, RedisApiKeyAttemptGuard
from qualification.m4_host.storage import (
    PostgresApiKeyCredentialResolver,
    revoke_cas,
    rotate_cas,
)

from .conftest import (
    BUCKET_KEY,
    REFERENCE_KEY,
    SECRET,
    SELECTOR,
    Infrastructure,
    encode,
    wire,
)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m4_source_scoped_sql_same_selector_tenants(infra: Infrastructure) -> None:
    await infra.seed()
    await infra.seed(scope="tenant-beta", secret=bytes(range(1, 33)), subject="service-beta")
    resolver = PostgresApiKeyCredentialResolver(infra.pool)
    selector = encode(SELECTOR).decode("ascii")
    first = await resolver.resolve(scope_ref=TrustedScopeRef("tenant-alpha"), key_id=selector)
    second = await resolver.resolve(scope_ref=TrustedScopeRef("tenant-beta"), key_id=selector)
    missing = await resolver.resolve(scope_ref=TrustedScopeRef("tenant-gamma"), key_id=selector)
    assert isinstance(first, ApiKeyFound)
    assert isinstance(second, ApiKeyFound)
    assert isinstance(missing, ApiKeyMissing)
    assert first.record.subject_ref.subject_id == "service-alpha"
    assert second.record.subject_ref.subject_id == "service-beta"
    assert first.record.verifier_digest != second.record.verifier_digest


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_pg_cas_revocation_is_single_winner(infra: Infrastructure) -> None:
    await infra.seed()
    resolver = PostgresApiKeyCredentialResolver(infra.pool)
    scope = TrustedScopeRef("tenant-alpha")
    selector = encode(SELECTOR).decode("ascii")
    first = await resolver.resolve(scope_ref=scope, key_id=selector)
    assert isinstance(first, ApiKeyFound)
    decisions = await asyncio.gather(
        *(
            revoke_cas(infra.pool, scope=scope.value, selector=selector, expected_version=1)
            for _ in range(12)
        )
    )
    assert decisions.count(True) == 1
    assert decisions.count(False) == 11
    assert not await resolver.is_current(record=first.record)


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_pg_versioned_rotation_invalidates_stale_proof(infra: Infrastructure) -> None:
    await infra.seed()
    resolver = PostgresApiKeyCredentialResolver(infra.pool)
    scope = TrustedScopeRef("tenant-alpha")
    selector = encode(SELECTOR).decode("ascii")
    first = await resolver.resolve(scope_ref=scope, key_id=selector)
    assert isinstance(first, ApiKeyFound)
    assert await rotate_cas(
        infra.pool,
        scope=scope.value,
        selector=selector,
        expected_version=1,
        digest=bytes([0x42]) * 32,
        protection_ref="key-v2",
    )
    assert not await rotate_cas(
        infra.pool,
        scope=scope.value,
        selector=selector,
        expected_version=1,
        digest=bytes([0x43]) * 32,
        protection_ref="key-v2",
    )
    assert not await resolver.is_current(record=first.record)


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_revocation_between_hmac_and_pg_recheck_denies(infra: Infrastructure) -> None:
    await infra.seed()
    scope = TrustedScopeRef("tenant-alpha")
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "alpha",
                scope,
                TrustProfileRef("reference", "v1", scope),
                frozenset({EvidenceMethod.API_KEY}),
            )
        ]
    )
    start_revoke = asyncio.Event()
    proceed = asyncio.Event()
    key_source = FixtureProtectionKeySource(
        REFERENCE_KEY, approved_scopes=frozenset({"tenant-alpha"})
    )
    proof = HmacApiKeyVerifier(key_source=key_source, approved_refs={scope: frozenset({"key-v1"})})

    class PausedProof:
        async def verify(self, *, scope_ref: TrustedScopeRef, presented, record) -> bool:
            matched = await proof.verify(scope_ref=scope_ref, presented=presented, record=record)
            start_revoke.set()
            await proceed.wait()
            return matched

    guard = RedisApiKeyAttemptGuard(redis=infra.redis, identifier_key=BUCKET_KEY, peer_limit=20)
    authenticator = ApiKeyAuthenticator(
        resolver=PostgresApiKeyCredentialResolver(infra.pool),
        proof_verifier=PausedProof(),
        attempt_guard=guard,
    )
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
        registry=AuthenticatorRegistry({EvidenceMethod.API_KEY: authenticator}),
    )
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, wire(secret=SECRET).encode("ascii")),
        CorrelationId("m4-pg-revoke"),
    )
    peer_token = HOST_PEER.set("192.0.2.100")
    try:
        pending = asyncio.create_task(
            engine.authenticate(request, entry=catalog.resolve_for_host_route("alpha"))
        )
        await asyncio.wait_for(start_revoke.wait(), 3)
        assert await revoke_cas(
            infra.pool,
            scope=scope.value,
            selector=encode(SELECTOR).decode("ascii"),
            expected_version=1,
        )
        proceed.set()
        result = await asyncio.wait_for(pending, 3)
    finally:
        HOST_PEER.reset(peer_token)
        proceed.set()
    assert isinstance(result, Rejected)
    assert not hasattr(result, "principal")


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_redis_atomic_guard_shared_between_instances(infra: Infrastructure) -> None:
    scope = TrustedScopeRef("tenant-alpha")
    first = RedisApiKeyAttemptGuard(
        redis=infra.redis,
        identifier_key=BUCKET_KEY,
        scope_limit=100,
        peer_limit=7,
        selector_limit=100,
    )
    second = RedisApiKeyAttemptGuard(
        redis=infra.redis,
        identifier_key=BUCKET_KEY,
        scope_limit=100,
        peer_limit=7,
        selector_limit=100,
    )

    async def attempt(index: int) -> bool:
        token = HOST_PEER.set("198.51.100.1")
        try:
            guard = first if index % 2 else second
            return await guard.admit(
                scope_ref=scope,
                correlation_id=CorrelationId(f"race-{index}"),
                key_id=encode(SELECTOR).decode("ascii"),
            )
        finally:
            HOST_PEER.reset(token)

    decisions = await asyncio.gather(*(attempt(i) for i in range(64)))
    assert decisions.count(True) == 7
    assert decisions.count(False) == 57

    token = HOST_PEER.set("198.51.100.1")
    try:
        assert await first.admit(
            scope_ref=TrustedScopeRef("tenant-beta"),
            correlation_id=CorrelationId("beta-admission"),
            key_id=encode(SELECTOR).decode("ascii"),
        )
    finally:
        HOST_PEER.reset(token)


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_guard_fails_closed_without_trusted_peer(infra: Infrastructure) -> None:
    guard = RedisApiKeyAttemptGuard(redis=infra.redis, identifier_key=BUCKET_KEY)
    token = HOST_PEER.set(None)
    try:
        assert not await guard.admit(
            scope_ref=TrustedScopeRef("tenant-alpha"),
            correlation_id=CorrelationId("missing-peer"),
            key_id=encode(SELECTOR).decode("ascii"),
        )
    finally:
        HOST_PEER.reset(token)


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_closed_postgresql_owner_yields_503_not_success(
    infra: Infrastructure,
) -> None:
    await infra.seed()
    app = infra.app()
    await infra.pool.close()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://reference"
    ) as client:
        result = await client.post(
            "/alpha/authenticate", headers={"Authorization": "ApiKey " + wire()}
        )
    assert result.status_code == 503
    assert result.json() == {"error": "temporarily_unavailable"}
    assert "service-alpha" not in result.text


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_unreachable_redis_quota_yields_503_not_success(
    infra: Infrastructure,
) -> None:
    await infra.seed()
    unavailable = Redis.from_url(
        "redis://127.0.0.1:1/15", socket_connect_timeout=0.2, socket_timeout=0.2
    )
    try:
        app = compose_app(
            pool=infra.pool,
            redis=unavailable,
            verifier_key=REFERENCE_KEY,
            bucket_key=BUCKET_KEY,
            routes={"alpha": "tenant-alpha"},
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://reference"
        ) as client:
            result = await client.post(
                "/alpha/authenticate", headers={"Authorization": "ApiKey " + wire()}
            )
        assert result.status_code == 503
        assert result.json() == {"error": "temporarily_unavailable"}
    finally:
        await unavailable.aclose()


@pytest.mark.asyncio
@pytest.mark.contract
async def test_m4_two_resolvers_share_source_scope_and_freshness_contract(
    infra: Infrastructure,
) -> None:
    """M4-T37: host callback and PostgreSQL adapter have matching outcomes."""
    await infra.seed()
    await infra.seed(scope="tenant-beta", secret=bytes(range(1, 33)))
    direct = PostgresApiKeyCredentialResolver(infra.pool)

    async def lookup(scope: TrustedScopeRef, key_id: str) -> ApiKeyRecordLookup:
        return await direct.resolve(scope_ref=scope, key_id=key_id)

    async def freshness(record: ApiKeyVerifierRecord) -> bool:
        return await direct.is_current(record=record)

    callback = HostCallbackApiKeyResolver(lookup=lookup, freshness=freshness)
    selector = encode(SELECTOR).decode("ascii")
    for name in ("tenant-alpha", "tenant-beta", "tenant-gamma"):
        scope = TrustedScopeRef(name)
        a = await direct.resolve(scope_ref=scope, key_id=selector)
        b = await callback.resolve(scope_ref=scope, key_id=selector)
        assert type(a) is type(b)
        if isinstance(a, ApiKeyFound):
            assert isinstance(b, ApiKeyFound)
            assert a.record.subject_ref == b.record.subject_ref
            assert a.record.verifier_digest == b.record.verifier_digest
            assert await direct.is_current(record=a.record)
            assert await callback.is_current(record=b.record)
        else:
            assert isinstance(a, ApiKeyMissing)
    known = await direct.resolve(scope_ref=TrustedScopeRef("tenant-alpha"), key_id=selector)
    assert isinstance(known, ApiKeyFound)
    assert await revoke_cas(infra.pool, scope="tenant-alpha", selector=selector, expected_version=1)
    assert not await direct.is_current(record=known.record)
    assert not await callback.is_current(record=known.record)


@pytest.mark.asyncio
@pytest.mark.security
async def test_m4_128_concurrent_attempts_bounded_on_slow_postgresql(
    infra: Infrastructure,
) -> None:
    """M4-T32 lab: 128 simultaneous bad keys, slow source, bounded access."""
    await infra.seed()
    source = PostgresApiKeyCredentialResolver(infra.pool)

    class BoundedSlowResolver:
        def __init__(self) -> None:
            self.semaphore = asyncio.Semaphore(8)
            self.active = 0
            self.peak = 0

        async def resolve(self, *, scope_ref: TrustedScopeRef, key_id: str) -> ApiKeyRecordLookup:
            async with self.semaphore:
                self.active += 1
                self.peak = max(self.peak, self.active)
                try:
                    await asyncio.sleep(0.03)
                    return await source.resolve(scope_ref=scope_ref, key_id=key_id)
                finally:
                    self.active -= 1

        async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
            return await source.is_current(record=record)

    slow = BoundedSlowResolver()
    scope = TrustedScopeRef("tenant-alpha")
    catalog = HostTrustCatalog(
        [
            HostBinding(
                "alpha",
                scope,
                TrustProfileRef("reference", "v1", scope),
                frozenset({EvidenceMethod.API_KEY}),
            )
        ]
    )
    verifier = HmacApiKeyVerifier(
        key_source=FixtureProtectionKeySource(
            REFERENCE_KEY, approved_scopes=frozenset({"tenant-alpha"})
        ),
        approved_refs={scope: frozenset({"key-v1"})},
    )
    guard = RedisApiKeyAttemptGuard(
        redis=infra.redis,
        identifier_key=BUCKET_KEY,
        scope_limit=256,
        peer_limit=256,
        selector_limit=256,
    )
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _sub, _entry: True),
        registry=AuthenticatorRegistry(
            {
                EvidenceMethod.API_KEY: ApiKeyAuthenticator(
                    resolver=slow, proof_verifier=verifier, attempt_guard=guard
                )
            }
        ),
        timeout_seconds=5.0,
    )
    entry = catalog.resolve_for_host_route("alpha")
    peer = HOST_PEER.set("198.51.100.44")
    try:
        decisions = await asyncio.gather(
            *(
                engine.authenticate(
                    AuthenticationRequest(
                        PresentedEvidence(
                            EvidenceMethod.API_KEY, wire(secret=bytes(range(1, 33))).encode()
                        ),
                        CorrelationId(f"load-{index}"),
                    ),
                    entry=entry,
                )
                for index in range(128)
            )
        )
    finally:
        HOST_PEER.reset(peer)
    assert len(decisions) == 128
    assert all(isinstance(result, (Rejected, AuthError)) for result in decisions)
    assert any(isinstance(result, Rejected) for result in decisions)
    assert 1 <= slow.peak <= 8
    assert slow.active == 0
