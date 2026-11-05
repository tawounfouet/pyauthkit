"""M6 adapter from approved SecretRef into the existing M4 HMAC key port.

[ARCH: Ports & Adapters] [SECURITY: Explicit Consumer / Scope + Version]
The snapshot contains only references. The adapter retrieves material for each
verification; it neither caches secrets nor chooses a fallback provider.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Never

from pyauthkit.configuration.models import ConfigurationRejected, ConfigurationSnapshot
from pyauthkit.configuration.secrets import (
    SecretAccessPolicy,
    SecretGrant,
    SecretResolutionUnavailable,
    resolve_authorized_secret,
)
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.ports.api_key_crypto import ApiKeyProtectionKey
from pyauthkit.ports.secrets import SecretResolver

_KEY_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


class ScopedApiKeySecretSource:
    """Read-only mapping from an M4 key reference to a verified M6 SecretRef.

    A configured key is admitted for exactly one scope and one purpose. The
    mapping must cover all declared secret references, preventing silent
    partially-wired configuration. This is NOT an isolation boundary against
    arbitrary hostile Python code running within the host process.
    """

    __slots__ = ("_snapshot", "_policy", "_resolver", "_bindings", "_approved_refs")

    def __init__(
        self,
        *,
        snapshot: ConfigurationSnapshot,
        access_policy: SecretAccessPolicy,
        resolver: SecretResolver,
        bindings: Mapping[tuple[TrustedScopeRef, str], SecretRef],
    ) -> None:
        if (
            not isinstance(snapshot, ConfigurationSnapshot)
            or not isinstance(access_policy, SecretAccessPolicy)
            or not callable(getattr(resolver, "resolve", None))
            or not isinstance(bindings, Mapping)
            or not bindings
            or len(bindings) > 128
        ):
            raise ConfigurationRejected("invalid API key secret composition")
        expected_scopes = {
            binding.scope_ref
            for binding in snapshot.bindings
            if EvidenceMethod.API_KEY in binding.allowed_methods
        }
        checked: dict[tuple[TrustedScopeRef, str], SecretRef] = {}
        approved: dict[TrustedScopeRef, set[str]] = {}
        used_refs: set[SecretRef] = set()
        for item, ref in bindings.items():
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], TrustedScopeRef)
                or not isinstance(item[1], str)
                or _KEY_REF.fullmatch(item[1]) is None
                or not isinstance(ref, SecretRef)
            ):
                raise ConfigurationRejected("invalid API key secret binding")
            scope, key_name = item
            if (
                scope not in expected_scopes
                or ref.namespace != scope.value
                or ref.purpose != "verify"
                or ref not in snapshot.secret_refs
                or SecretGrant(ref.provider, ref.namespace, ref.purpose)
                not in access_policy.allowed
                or ref in used_refs
            ):
                raise ConfigurationRejected("unapproved API key secret binding")
            checked[(scope, key_name)] = ref
            approved.setdefault(scope, set()).add(key_name)
            used_refs.add(ref)
        if set(approved) != expected_scopes or used_refs != set(snapshot.secret_refs):
            raise ConfigurationRejected("incomplete API key secret binding")
        object.__setattr__(self, "_snapshot", snapshot)
        object.__setattr__(self, "_policy", access_policy)
        object.__setattr__(self, "_resolver", resolver)
        object.__setattr__(self, "_bindings", MappingProxyType(checked))
        object.__setattr__(
            self,
            "_approved_refs",
            MappingProxyType({k: frozenset(v) for k, v in approved.items()}),
        )

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("approved secret bindings are immutable")

    def __repr__(self) -> str:
        return "ScopedApiKeySecretSource(<approved, no secret cache>)"

    @property
    def approved_refs(self) -> Mapping[TrustedScopeRef, frozenset[str]]:
        return self._approved_refs

    async def get_key(
        self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
    ) -> ApiKeyProtectionKey | None:
        """Never resolve a key from another scope or a non-approved version."""
        if not isinstance(scope_ref, TrustedScopeRef) or not isinstance(
            protection_key_ref, str
        ):
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        ref = self._bindings.get((scope_ref, protection_key_ref))
        if ref is None:
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        try:
            material = await resolve_authorized_secret(
                snapshot=self._snapshot,
                policy=self._policy,
                resolver=self._resolver,
                ref=ref,
                purpose="verify",
            )
        except SecretResolutionUnavailable:
            raise DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE) from None
        if len(material) != 32:
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        return ApiKeyProtectionKey(material)

    async def preflight(self) -> None:
        """Admit readiness before an engine is activated, without caching bytes.

        The provider can become unavailable or revoke a key after this check.
        Per-verification resolution still fails closed in that case.
        """
        for scope, key_name in self._bindings:
            await self.get_key(scope_ref=scope, protection_key_ref=key_name)
