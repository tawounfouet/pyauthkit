"""M5 approved static JWK sets. No HTTP and no JWT-supplied key authority.

[ARCH: Ports & Adapters] [SECURITY: Cross-Profile Key Isolation]
The key set is operator-supplied at composition time. It can never be selected
from iss, jku, x5u or an unverified claim. Only RSA verification keys are admitted.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from types import MappingProxyType

from pyauthkit.domain.jwt import TrustedJwtVerificationProfile, strict_json_object
from pyauthkit.domain.trust import TrustProfileRef


class StaticJwtProfileResolver:
    """Frozen, exact profile-ref lookup; references alone confer no authority."""

    __slots__ = ("_profiles",)

    def __init__(self, profiles: Mapping[TrustProfileRef, TrustedJwtVerificationProfile]) -> None:
        checked: dict[TrustProfileRef, TrustedJwtVerificationProfile] = {}
        for ref, profile in profiles.items():
            if not isinstance(ref, TrustProfileRef) or not isinstance(
                profile, TrustedJwtVerificationProfile
            ) or ref != profile.profile_ref:
                raise ValueError("invalid JWT profile catalog")
            checked[ref] = profile
        if not checked:
            raise ValueError("empty JWT profile catalog")
        object.__setattr__(self, "_profiles", MappingProxyType(checked))

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("JWT profile catalog is immutable")

    async def resolve(
        self, *, profile_ref: TrustProfileRef
    ) -> TrustedJwtVerificationProfile | None:
        return self._profiles.get(profile_ref)


def _validate_public_rsa_jwk(raw: str) -> tuple[str, str]:
    """Validate public-only JWK metadata, returning (kid, canonical JSON)."""
    if type(raw) is not str:
        raise ValueError("invalid JWK")
    jwk = strict_json_object(raw.encode("utf-8"), maximum=4096)
    if not jwk.keys() <= {"kty", "kid", "alg", "use", "key_ops", "n", "e"}:
        raise ValueError("unapproved or private JWK member")
    kid = jwk.get("kid")
    if (
        type(kid) is not str
        or not 1 <= len(kid) <= 128
        or not kid.isascii()
        or not kid.isprintable()
    ):
        raise ValueError("invalid key identifier")
    if jwk.get("kty") != "RSA" or jwk.get("alg", "RS256") != "RS256":
        raise ValueError("incompatible JWK algorithm")
    if jwk.get("use", "sig") != "sig" or jwk.get("key_ops", ["verify"]) != ["verify"]:
        raise ValueError("incompatible JWK operations")
    for name in ("n", "e"):
        value = jwk.get(name)
        if type(value) is not str or not value or len(value) > 1024:
            raise ValueError("invalid RSA JWK component")
        # Canonical base64url components are additionally checked by the JOSE library.
        if re.fullmatch(r"[A-Za-z0-9_-]+", value) is None:
            raise ValueError("invalid RSA JWK encoding")
    return kid, json.dumps(jwk, sort_keys=True, separators=(",", ":"))


class StaticJwksKeyResolver:
    """Key selection bounded to pre-approved immutable profile-specific sets."""

    __slots__ = ("_sets",)

    def __init__(self, keysets: Mapping[TrustProfileRef, tuple[str, ...]]) -> None:
        checked: dict[TrustProfileRef, MappingProxyType[str, str]] = {}
        for profile_ref, raw_keys in keysets.items():
            if (
                not isinstance(profile_ref, TrustProfileRef)
                or type(raw_keys) is not tuple
                or not 1 <= len(raw_keys) <= 32
            ):
                raise ValueError("invalid approved JWK set")
            keys: dict[str, str] = {}
            for raw in raw_keys:
                kid, normalized = _validate_public_rsa_jwk(raw)
                if kid in keys:
                    raise ValueError("ambiguous key identifier in approved JWK set")
                keys[kid] = normalized
            checked[profile_ref] = MappingProxyType(keys)
        if not checked:
            raise ValueError("no approved JWK key sets")
        object.__setattr__(self, "_sets", MappingProxyType(checked))

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("approved JWK sets are immutable")

    async def resolve_key(
        self,
        *,
        profile: TrustedJwtVerificationProfile,
        kid_hint: str,
        algorithm_hint: str,
    ) -> str | None:
        if algorithm_hint != "RS256" or algorithm_hint not in profile.allowed_algorithms:
            return None
        keys = self._sets.get(profile.profile_ref)
        if keys is None or profile.profile_ref.scope_ref != profile.scope_ref:
            return None
        return keys.get(kid_hint)
