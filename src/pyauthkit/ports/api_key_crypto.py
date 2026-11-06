"""M4 API-key cryptographic contracts. No secret manager imposed on the core.

[ARCH: Dependency Inversion] [SECURITY: Explicit Host Key Authority]
These ports cannot establish final authentication, status or revocation policy.
"""

from __future__ import annotations

from typing import Never, Protocol, SupportsIndex

from pyauthkit.domain.api_key import ApiKeyVerifierRecord
from pyauthkit.domain.api_key_format import ParsedOpaqueApiKey
from pyauthkit.domain.scope import TrustedScopeRef


class ApiKeyProtectionKey:
    """Redacted immutable in-process HMAC material supplied by a trusted owner.

    Expected: exactly 32 random bytes. Python cannot guarantee zeroization
    of an immutable bytes object. Never log, pickle or generic-serialize.
    """

    __slots__ = ("_material",)

    _material: bytes

    def __init__(self, material: bytes) -> None:
        if type(material) is not bytes or len(material) != 32:
            raise ValueError("invalid API-key protection material")
        object.__setattr__(self, "_material", material)

    @property
    def material(self) -> bytes:
        """Sensitive. Only an admitted verifier should access this property."""
        return self._material

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("protection material is immutable")

    def __repr__(self) -> str:
        return "ApiKeyProtectionKey(<redacted>)"

    def __deepcopy__(self, _memo: dict[int, object]) -> Never:
        raise TypeError("HMAC protection material cannot be deep-copied")

    def __reduce_ex__(self, _protocol: SupportsIndex) -> Never:
        raise TypeError("HMAC protection material cannot be pickled")


class ApiKeyProtectionKeySource(Protocol):
    """Trusted, async scope- and version-qualified key retrieval.

    None means an approved key cannot be found. A source outage must raise,
    never silently return another key or an implicitly trusted default.
    """

    async def get_key(
        self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
    ) -> ApiKeyProtectionKey | None: ...


class ApiKeyProofVerifier(Protocol):
    """Check only full-secret cryptographic match; NOT AuthenticationResult."""

    async def verify(
        self,
        *,
        scope_ref: TrustedScopeRef,
        presented: ParsedOpaqueApiKey,
        record: ApiKeyVerifierRecord,
    ) -> bool: ...
