"""Small dependency-inversion port for host-approved secret providers."""

from typing import Protocol

from pyauthkit.domain.secret import SecretRef


class SecretResolver(Protocol):
    """Resolve only when explicitly admitted by the host's access policy."""

    async def resolve(self, *, ref: SecretRef, purpose: str) -> bytes: ...
