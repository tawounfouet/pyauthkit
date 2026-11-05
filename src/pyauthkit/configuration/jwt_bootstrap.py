"""M6 v2 host-owned JWT trust composition using the existing M5 verifier.

[ARCH: Ports & Adapters] [SECURITY: No Unverified Token-Selected Authority]
Static keysets are supplied out-of-band by the host; HTTPS sources require a
second exact host-controlled egress grant. No network request occurs at
composition time. A source declaration is NOT independent network assurance.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Never

from pyauthkit.adapters.jwks_cache import CachedApprovedJwksKeyResolver
from pyauthkit.adapters.jwks_https import PinnedHttpsJwksFetcher
from pyauthkit.adapters.jwt_authenticator import JWTAuthenticator
from pyauthkit.adapters.jwt_crypto import PyJwtRs256Verifier
from pyauthkit.adapters.jwt_static import StaticJwksKeyResolver, StaticJwtProfileResolver
from pyauthkit.application.policy import FinalRule
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.temporal import Clock
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.authenticator import Authenticator
from pyauthkit.ports.events import AuthenticationEventSink
from pyauthkit.ports.jwt import VerificationKeyResolver

from .bootstrap import M6Runtime, _compose_approved_runtime
from .models import (
    ConfigurationRejected,
    ConfigurationSnapshot,
    HttpsJwtKeySource,
    StaticJwtKeySource,
)

type EgressGrants = Mapping[TrustProfileRef, tuple[str, str, tuple[str, ...]]]


class _ExactProfileKeyRouter:
    """One resolver per profile source kind; never try a different provider."""

    __slots__ = ("_static", "_remote", "_static_refs", "_remote_refs")

    _static: VerificationKeyResolver | None
    _remote: VerificationKeyResolver | None
    _static_refs: frozenset[TrustProfileRef]
    _remote_refs: frozenset[TrustProfileRef]

    def __init__(
        self,
        *,
        static: VerificationKeyResolver | None,
        remote: VerificationKeyResolver | None,
        static_refs: frozenset[TrustProfileRef],
        remote_refs: frozenset[TrustProfileRef],
    ) -> None:
        if not (static_refs or remote_refs) or static_refs & remote_refs:
            raise ConfigurationRejected("invalid JWT key routing policy")
        if (static_refs and static is None) or (remote_refs and remote is None):
            raise ConfigurationRejected("incomplete JWT key resolver")
        object.__setattr__(self, "_static", static)
        object.__setattr__(self, "_remote", remote)
        object.__setattr__(self, "_static_refs", static_refs)
        object.__setattr__(self, "_remote_refs", remote_refs)

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("JWT key router is immutable")

    def __repr__(self) -> str:
        return "_ExactProfileKeyRouter(<operator-approved>)"

    async def resolve_key(
        self,
        *,
        profile: TrustedJwtVerificationProfile,
        kid_hint: str,
        algorithm_hint: str,
    ) -> str | None:
        ref = profile.profile_ref
        if ref.scope_ref != profile.scope_ref:
            return None
        selected: VerificationKeyResolver | None
        if ref in self._static_refs:
            selected = self._static
        elif ref in self._remote_refs:
            selected = self._remote
        else:
            return None
        if selected is None:
            return None
        return await selected.resolve_key(
            profile=profile, kid_hint=kid_hint, algorithm_hint=algorithm_hint
        )


def compose_trusted_jwt_runtime(
    snapshot: ConfigurationSnapshot,
    *,
    approved_static_keysets: Mapping[str, tuple[str, ...]],
    approved_jwks_egress: EgressGrants | None = None,
    other_authenticators: Iterable[Authenticator] = (),
    final_rule: FinalRule | None = None,
    clock: Clock | None = None,
    event_sink: AuthenticationEventSink | None = None,
    minimum_generation: int = 1,
) -> M6Runtime:
    """Build a one-generation real M5 JWT verifier from approved v2 policy.

    The host must independently supply exact public JWK sets or HTTPS JWKS
    egress grants. A token can contribute only a kid hint within the already
    approved source. PyJWT is an optional dependency for actual verification.
    """
    if not isinstance(snapshot, ConfigurationSnapshot) or snapshot.schema_version != 2:
        raise ConfigurationRejected("JWT composition requires schema v2")
    if not snapshot.jwt_profiles or snapshot.secret_refs:
        raise ConfigurationRejected("unsupported JWT and secret consumer combination")
    if type(minimum_generation) is not int or minimum_generation < 1:
        raise ConfigurationRejected("invalid generation floor")
    if snapshot.generation.value < minimum_generation:
        raise ConfigurationRejected("configuration generation is stale")
    if not isinstance(approved_static_keysets, Mapping):
        raise ConfigurationRejected("invalid approved static keysets")
    if approved_jwks_egress is not None and not isinstance(approved_jwks_egress, Mapping):
        raise ConfigurationRejected("invalid approved JWKS egress policy")
    try:
        profiles = {item.profile.profile_ref: item.profile for item in snapshot.jwt_profiles}
        static_sets: dict[TrustProfileRef, tuple[str, ...]] = {}
        remotes: dict[TrustProfileRef, ApprovedJwksSource] = {}
        remote_ips: dict[TrustProfileRef, tuple[str, ...]] = {}
        used_keysets: set[str] = set()
        for item in snapshot.jwt_profiles:
            ref = item.profile.profile_ref
            source = item.keys
            if isinstance(source, StaticJwtKeySource):
                if source.keyset_ref in used_keysets:
                    raise ConfigurationRejected("reused JWT static keyset authority")
                keyset = approved_static_keysets[source.keyset_ref]
                if type(keyset) is not tuple or not keyset:
                    raise ConfigurationRejected("invalid approved public JWK set")
                static_sets[ref] = keyset
                used_keysets.add(source.keyset_ref)
            elif isinstance(source, HttpsJwtKeySource):
                remotes[ref] = source.source
                remote_ips[ref] = source.allowed_ips
            else:
                raise ConfigurationRejected("unapproved JWT key source")

        # Exact extrinsic admissions: a compromised config mapping cannot add
        # a different public keyset or direct HTTPS egress without host consent.
        if set(approved_static_keysets) != used_keysets:
            raise ConfigurationRejected("unapproved static keyset admission")
        grants = approved_jwks_egress if approved_jwks_egress is not None else {}
        if set(grants) != set(remotes):
            raise ConfigurationRejected("unapproved JWKS egress admission")
        for ref, source in remotes.items():
            if grants[ref] != (source.source_id, source.uri, remote_ips[ref]):
                raise ConfigurationRejected("JWKS egress grant mismatch")

        static_resolver: VerificationKeyResolver | None = (
            StaticJwksKeyResolver(static_sets) if static_sets else None
        )
        remote_resolver: VerificationKeyResolver | None = None
        if remotes:
            transport = PinnedHttpsJwksFetcher(sources=remotes, allowed_ips=remote_ips)
            remote_resolver = CachedApprovedJwksKeyResolver(sources=remotes, fetcher=transport)
        key_router = _ExactProfileKeyRouter(
            static=static_resolver,
            remote=remote_resolver,
            static_refs=frozenset(static_sets),
            remote_refs=frozenset(remotes),
        )
        jwt_authenticator = JWTAuthenticator(
            profile_resolver=StaticJwtProfileResolver(profiles),
            key_resolver=key_router,
            signature_verifier=PyJwtRs256Verifier(),
            clock=clock,
        )
        others = tuple(other_authenticators)
        if any(auth.method is EvidenceMethod.JWT for auth in others):
            raise ConfigurationRejected("duplicate JWT authenticator")
        return _compose_approved_runtime(
            snapshot,
            authenticators=(jwt_authenticator, *others),
            admitted_secret_refs=frozenset(),
            admitted_jwt_refs=frozenset(profiles),
            final_rule=final_rule,
            event_sink=event_sink,
            minimum_generation=minimum_generation,
        )
    except Exception:
        # Do not reflect raw config, provider data or cryptographic errors.
        raise ConfigurationRejected("JWT trust bootstrap rejected") from None
