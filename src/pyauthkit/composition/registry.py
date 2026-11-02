"""No auto-discovery: a bootstrap builder creates one frozen verifier snapshot."""

from collections.abc import Mapping
from types import MappingProxyType

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.ports.authenticator import Authenticator


class AuthenticatorNotConfigured(Exception):
    """Unknown verifier method, without any implicit fallback."""


class AuthenticatorRegistry:
    """Frozen exact-method lookup of already-approved verifier instances."""

    __slots__ = ("_entries",)

    def __init__(self, entries: Mapping[EvidenceMethod, Authenticator]) -> None:
        if not entries:
            raise ValueError("empty authenticator registry")
        checked: dict[EvidenceMethod, Authenticator] = {}
        for method, authenticator in entries.items():
            if not isinstance(method, EvidenceMethod) or authenticator.method != method:
                raise ValueError("invalid registry method binding")
            if not callable(authenticator.verify):
                raise ValueError("invalid authenticator contract")
            checked[method] = authenticator
        object.__setattr__(self, "_entries", MappingProxyType(checked))

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("authenticator registry cannot be mutated")

    def resolve(self, method: EvidenceMethod) -> Authenticator:
        """Exact match only. Never try another mechanism on failure."""
        result = self._entries.get(method)
        if result is None:
            raise AuthenticatorNotConfigured("authenticator is not configured")
        return result


class AuthenticatorRegistryBuilder:
    """Mutable only during controlled operator bootstrap."""

    __slots__ = ("_entries", "_frozen")

    def __init__(self) -> None:
        self._entries: dict[EvidenceMethod, Authenticator] = {}
        self._frozen = False

    def register(self, authenticator: Authenticator) -> None:
        if self._frozen:
            raise RuntimeError("authenticator registry is frozen")
        method = authenticator.method
        if not isinstance(method, EvidenceMethod) or not callable(authenticator.verify):
            raise ValueError("invalid authenticator contract")
        if method in self._entries:
            raise ValueError("duplicate authenticator method")
        self._entries[method] = authenticator

    def freeze(self) -> AuthenticatorRegistry:
        if self._frozen:
            raise RuntimeError("authenticator registry is frozen")
        registry = AuthenticatorRegistry(self._entries)
        self._frozen = True
        return registry
