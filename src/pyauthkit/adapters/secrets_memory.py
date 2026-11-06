"""Synthetic-only test adapter, NOT a durable or production secret vault."""

from collections.abc import Mapping

from pyauthkit.domain.secret import SecretRef


class SyntheticSecretResolver:
    """Lookup with exact provider/namespace/key/version/purpose matching."""

    __slots__ = ("_secrets", "_revoked")

    def __init__(
        self,
        secrets: Mapping[SecretRef, bytes],
        *,
        revoked: frozenset[SecretRef] = frozenset(),
    ) -> None:
        if not all(
            isinstance(ref, SecretRef) and type(value) is bytes and value
            for ref, value in secrets.items()
        ):
            raise ValueError("invalid synthetic secret store")
        if not isinstance(revoked, frozenset) or not all(
            isinstance(ref, SecretRef) for ref in revoked
        ):
            raise ValueError("invalid revocation set")
        self._secrets = dict(secrets)
        self._revoked = revoked

    async def resolve(self, *, ref: SecretRef, purpose: str) -> bytes:
        if not isinstance(ref, SecretRef) or ref.purpose != purpose:
            raise ValueError("secret unavailable")
        if ref in self._revoked or ref not in self._secrets:
            raise ValueError("secret unavailable")
        return self._secrets[ref]

    def __repr__(self) -> str:
        return "SyntheticSecretResolver(<redacted>)"
