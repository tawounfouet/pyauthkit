"""Fail-closed, per-profile JWKS cache over a host-enforced egress transport.

[ARCH: Ports & Adapters] [SECURITY: Snapshot Cache / Single-Flight]
No default HTTP client is provided. A transport implementing approved DNS,
egress, certificate verification, redirect refusal and response limits must
be injected by the operator. This cache is not a revocation mechanism.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from collections.abc import Callable, Mapping
from types import MappingProxyType

from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile, strict_json_object
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.jwt import ApprovedJwksFetcher

from .jwt_static import _validate_public_rsa_jwk


def _parse_jwks(data: bytes, *, source: ApprovedJwksSource) -> MappingProxyType[str, str]:
    document = strict_json_object(data, maximum=source.max_response_bytes)
    if document.keys() != {"keys"}:
        raise ValueError("unexpected JWKS metadata")
    elements = document.get("keys")
    if not isinstance(elements, list) or not 1 <= len(elements) <= source.max_keys:
        raise ValueError("invalid JWKS key count")
    keys: dict[str, str] = {}
    for element in elements:
        if not isinstance(element, dict):
            raise ValueError("invalid JWKS entry")
        kid, canonical = _validate_public_rsa_jwk(
            json.dumps(element, separators=(",", ":"), ensure_ascii=True)
        )
        if kid in keys:
            raise ValueError("ambiguous JWKS key identifier")
        keys[kid] = canonical
    return MappingProxyType(keys)


class CachedApprovedJwksKeyResolver:
    """Per-profile TTL snapshots; no stale fallback, token-driven refresh or redirects."""

    __slots__ = ("_sources", "_fetcher", "_clock", "_cache", "_locks", "_generations")

    _sources: MappingProxyType[TrustProfileRef, ApprovedJwksSource]
    _fetcher: ApprovedJwksFetcher
    _clock: Callable[[], float]
    _cache: dict[TrustProfileRef, tuple[float, MappingProxyType[str, str]]]
    _locks: dict[TrustProfileRef, asyncio.Lock]
    _generations: dict[TrustProfileRef, int]

    def __init__(
        self,
        *,
        sources: Mapping[TrustProfileRef, ApprovedJwksSource],
        fetcher: ApprovedJwksFetcher,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if not callable(getattr(fetcher, "fetch", None)):
            raise ValueError("operator-approved JWKS transport required")
        if monotonic is not None and not callable(monotonic):
            raise ValueError("invalid cache monotonic clock")
        checked: dict[TrustProfileRef, ApprovedJwksSource] = {}
        for ref, source in sources.items():
            if (
                not isinstance(ref, TrustProfileRef)
                or not isinstance(source, ApprovedJwksSource)
                or source.profile_ref != ref
            ):
                raise ValueError("invalid host-authorized JWKS binding")
            checked[ref] = source
        if not checked or len(checked) > 128:
            raise ValueError("invalid approved JWKS source catalog")
        object.__setattr__(self, "_sources", MappingProxyType(checked))
        object.__setattr__(self, "_fetcher", fetcher)
        object.__setattr__(self, "_clock", monotonic if monotonic is not None else time.monotonic)
        object.__setattr__(self, "_locks", {ref: asyncio.Lock() for ref in checked})
        object.__setattr__(self, "_cache", {})
        object.__setattr__(self, "_generations", {ref: 0 for ref in checked})

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("approved JWKS cache composition is immutable")

    def __repr__(self) -> str:
        return "CachedApprovedJwksKeyResolver(<redacted, host-managed>)"

    def invalidate(self, profile_ref: TrustProfileRef) -> None:
        """Operator-controlled key invalidation; not proof of cluster revocation."""
        if profile_ref in self._generations:
            self._generations[profile_ref] += 1
            self._cache.pop(profile_ref, None)

    def _now(self) -> float:
        try:
            value = self._clock()
            if not math.isfinite(value):
                raise ValueError("invalid clock")
            return value
        except Exception:
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION) from None

    async def _load(self, source: ApprovedJwksSource) -> MappingProxyType[str, str]:
        try:
            async with asyncio.timeout(source.timeout_seconds):
                body = await self._fetcher.fetch(source=source)
        except asyncio.CancelledError:
            raise
        except Exception:
            raise DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE) from None
        try:
            return _parse_jwks(body, source=source)
        except (ValueError, TypeError, UnicodeError):
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION) from None

    async def resolve_key(
        self,
        *,
        profile: TrustedJwtVerificationProfile,
        kid_hint: str,
        algorithm_hint: str,
    ) -> str | None:
        if algorithm_hint != "RS256" or algorithm_hint not in profile.allowed_algorithms:
            return None
        source = self._sources.get(profile.profile_ref)
        if source is None or profile.scope_ref != source.profile_ref.scope_ref:
            return None
        ref = profile.profile_ref
        current = self._cache.get(ref)
        now = self._now()
        if current is not None and now < current[0]:
            return current[1].get(kid_hint)
        async with self._locks[ref]:
            current = self._cache.get(ref)
            now = self._now()
            if current is not None and now < current[0]:
                return current[1].get(kid_hint)
            # One refresh for all unknown kids in this profile; never fetch a kid URL.
            generation = self._generations[ref]
            keyset = await self._load(source)
            if generation != self._generations[ref]:
                raise DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
            self._cache[ref] = (self._now() + source.ttl_seconds, keyset)
            return keyset.get(kid_hint)
