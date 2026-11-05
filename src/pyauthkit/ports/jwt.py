"""Narrow, host-supplied ports for JWT verification. No untrusted key discovery."""

from typing import Protocol

from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.trust import TrustProfileRef


class TrustedJwtProfileResolver(Protocol):
    """Lookup is keyed ONLY by the host-issued M2 profile reference."""

    async def resolve(
        self, *, profile_ref: TrustProfileRef
    ) -> TrustedJwtVerificationProfile | None: ...


class VerificationKeyResolver(Protocol):
    """Choose one public JWK from a preapproved, profile-isolated key set."""

    async def resolve_key(
        self,
        *,
        profile: TrustedJwtVerificationProfile,
        kid_hint: str,
        algorithm_hint: str,
    ) -> str | None: ...


class SignedTokenVerifier(Protocol):
    """Proof using an approved JOSE library, not Python JWT parsing alone."""

    async def verify_signature(
        self, *, compact_jws: bytes, approved_key: str, approved_algorithm: str
    ) -> dict[str, object] | None: ...


class ApprovedJwksFetcher(Protocol):
    """Host-operated HTTPS transport with DNS/egress/TLS/redirect enforcement.

    The core must never instantiate a permissive HTTP client. The adapter
    must enforce the approved source's origin and destination at connect time.
    An untrusted JWT must never contribute any URL or redirect target.
    """

    async def fetch(self, *, source: ApprovedJwksSource) -> bytes: ...
