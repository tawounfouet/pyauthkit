"""M5 JWKS cache tests with an operator-controlled transport test double.

No live network test here; DNS rebinding and proxy/TLS policy remain blockers.
"""

import asyncio
import base64
import json

import pytest

from pyauthkit.adapters.jwks_cache import CachedApprovedJwksKeyResolver
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.trust import TrustProfileRef


def _jwk(kid: str, change: int = 0) -> dict[str, object]:
    modulus = bytes([change + 1]) + bytes(range(1, 255)) + b"\x07"
    n = base64.urlsafe_b64encode(modulus).rstrip(b"=").decode()
    return {"kty": "RSA", "kid": kid, "use": "sig", "alg": "RS256", "n": n, "e": "AQAB"}


class Mono:
    value = 100.0

    def now(self) -> float:
        return self.value


class FakeApprovedTransport:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.down = False
        self.invalid = False
        self.wait = False
        self.keys: dict[str, list[dict[str, object]]] = {
            "a": [_jwk("shared", 0)],
            "b": [_jwk("shared", 1)],
        }

    async def fetch(self, *, source: ApprovedJwksSource) -> bytes:
        self.calls.append(source.source_id)
        await asyncio.sleep(0)
        if self.wait:
            await asyncio.sleep(3600)
        if self.down:
            raise RuntimeError("sensitive connection error")
        if self.invalid:
            return b'{"keys":[{"kid":"a","kid":"a"}]}'
        return json.dumps({"keys": self.keys[source.source_id]}).encode()


def _profile(scope: str) -> tuple[TrustedJwtVerificationProfile, ApprovedJwksSource]:
    scope_ref = TrustedScopeRef(scope)
    ref = TrustProfileRef("jwt-api", "rev-1", scope_ref)
    return (
        TrustedJwtVerificationProfile(ref.scope_ref, ref, "https://iss.example.com", "orders"),
        ApprovedJwksSource(ref, scope, f"https://jwks-{scope}.example.com/keys", ttl_seconds=30),
    )


@pytest.mark.security
@pytest.mark.parametrize(
    "uri",
    [
        "http://keys.example.com/keys",
        "https://127.0.0.1/keys",
        "https://169.254.169.254/metadata",
        "https://localhost/keys",
        "https://bad.local/keys",
        "https://" + "user" + ":" + "pw" + "@keys.example.com/keys",
        "https://keys.example.com:8080/keys",
        "https://keys.example.com/keys?user=token",
        "https://[::1]/keys",
    ],
)
def test_unapproved_network_source_is_refused_at_bootstrap(uri: str) -> None:
    profile, source = _profile("a")
    del source
    with pytest.raises(ValueError):
        ApprovedJwksSource(profile.profile_ref, "bad", uri)


@pytest.mark.security
def test_100_unknown_kids_coalesce_into_single_fetch_per_profile() -> None:
    profile, source = _profile("a")
    network = FakeApprovedTransport()
    clock = Mono()
    resolver = CachedApprovedJwksKeyResolver(
        sources={profile.profile_ref: source}, fetcher=network, monotonic=clock.now
    )

    async def run():
        candidates = [
            resolver.resolve_key(profile=profile, kid_hint=f"unknown-{i}", algorithm_hint="RS256")
            for i in range(100)
        ]
        return await asyncio.gather(*candidates)

    assert asyncio.run(run()) == [None] * 100
    assert network.calls == ["a"]


@pytest.mark.security
def test_same_kid_isolated_by_tenant_profile_and_source() -> None:
    a, source_a = _profile("a")
    b, source_b = _profile("b")
    network = FakeApprovedTransport()
    resolver = CachedApprovedJwksKeyResolver(
        sources={a.profile_ref: source_a, b.profile_ref: source_b},
        fetcher=network,
    )

    async def run():
        return await asyncio.gather(
            resolver.resolve_key(profile=a, kid_hint="shared", algorithm_hint="RS256"),
            resolver.resolve_key(profile=b, kid_hint="shared", algorithm_hint="RS256"),
        )

    first, second = asyncio.run(run())
    assert first is not None and second is not None and first != second
    assert sorted(network.calls) == ["a", "b"]


@pytest.mark.security
def test_rotation_expiration_invalidation_and_no_stale_error_fallback() -> None:
    profile, source = _profile("a")
    network = FakeApprovedTransport()
    clock = Mono()
    resolver = CachedApprovedJwksKeyResolver(
        sources={profile.profile_ref: source}, fetcher=network, monotonic=clock.now
    )

    async def lookup(kid: str):
        return await resolver.resolve_key(profile=profile, kid_hint=kid, algorithm_hint="RS256")

    assert asyncio.run(lookup("shared")) is not None
    network.keys["a"] = [_jwk("rotated")]
    assert asyncio.run(lookup("shared")) is not None
    clock.value += 31
    assert asyncio.run(lookup("shared")) is None
    assert asyncio.run(lookup("rotated")) is not None
    resolver.invalidate(profile.profile_ref)
    network.down = True
    with pytest.raises(DomainTechnicalError) as error:
        asyncio.run(lookup("rotated"))
    assert error.value.code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert network.calls == ["a", "a", "a"]


@pytest.mark.security
def test_ambiguous_jwks_and_corrupted_json_fail_closed() -> None:
    profile, source = _profile("a")
    network = FakeApprovedTransport()
    network.keys["a"] = [_jwk("shared"), _jwk("shared")]
    resolver = CachedApprovedJwksKeyResolver(sources={profile.profile_ref: source}, fetcher=network)
    with pytest.raises(DomainTechnicalError) as error:
        asyncio.run(
            resolver.resolve_key(profile=profile, kid_hint="shared", algorithm_hint="RS256")
        )
    assert error.value.code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION

    network.keys["a"] = [_jwk("shared")]
    network.invalid = True
    with pytest.raises(DomainTechnicalError):
        asyncio.run(
            resolver.resolve_key(profile=profile, kid_hint="shared", algorithm_hint="RS256")
        )


@pytest.mark.security
def test_cancelled_resolution_propagates_without_caching() -> None:
    profile, source = _profile("a")
    network = FakeApprovedTransport()
    network.wait = True
    resolver = CachedApprovedJwksKeyResolver(sources={profile.profile_ref: source}, fetcher=network)

    async def cancel():
        task = asyncio.create_task(
            resolver.resolve_key(profile=profile, kid_hint="shared", algorithm_hint="RS256")
        )
        await asyncio.sleep(0.02)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    network.wait = False
    assert (
        asyncio.run(
            resolver.resolve_key(profile=profile, kid_hint="shared", algorithm_hint="RS256")
        )
        is not None
    )
    assert len(network.calls) == 2


@pytest.mark.security
def test_invalidate_during_fetch_never_resurrects_revoked_keyset() -> None:
    profile, source = _profile("a")

    class DeferredTransport(FakeApprovedTransport):
        def __init__(self) -> None:
            super().__init__()
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def fetch(self, *, source: ApprovedJwksSource) -> bytes:
            self.calls.append(source.source_id)
            self.started.set()
            await self.release.wait()
            return json.dumps({"keys": self.keys[source.source_id]}).encode()

    network = DeferredTransport()
    resolver = CachedApprovedJwksKeyResolver(sources={profile.profile_ref: source}, fetcher=network)

    async def run() -> None:
        first = asyncio.create_task(
            resolver.resolve_key(profile=profile, kid_hint="shared", algorithm_hint="RS256")
        )
        await asyncio.wait_for(network.started.wait(), timeout=1)
        resolver.invalidate(profile.profile_ref)
        network.release.set()
        with pytest.raises(DomainTechnicalError) as error:
            await first
        assert error.value.code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
        network.keys["a"] = [_jwk("rotated")]
        assert (
            await resolver.resolve_key(profile=profile, kid_hint="shared", algorithm_hint="RS256")
            is None
        )
        assert (
            await resolver.resolve_key(profile=profile, kid_hint="rotated", algorithm_hint="RS256")
            is not None
        )

    asyncio.run(run())
    assert network.calls == ["a", "a"]
