"""Host-authoritative binding for M2 preflight (PR-04).

DDD: immutable catalog, explicit selection by a trusted host route.
SECURITY: nothing in AuthenticationRequest selects an approved trust profile.
A library cannot authenticate which Python code invoked a host integration.
Only a properly configured host adapter may call resolve_for_host_route().
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Never, cast

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.trust import TrustProfileRef

_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


@dataclass(frozen=True, slots=True, repr=False)
class HostBinding:
    """One operator-approved route binding, never constructed from a request."""

    route_id: str
    scope_ref: TrustedScopeRef
    profile_ref: TrustProfileRef
    allowed_methods: frozenset[EvidenceMethod]

    def __post_init__(self) -> None:
        if not isinstance(self.route_id, str) or not _ROUTE_PATTERN.fullmatch(self.route_id):
            raise ValueError("invalid host route")
        if not isinstance(self.scope_ref, TrustedScopeRef):
            raise ValueError("invalid host scope")
        if not isinstance(self.profile_ref, TrustProfileRef):
            raise ValueError("invalid trust profile")
        if self.scope_ref != self.profile_ref.scope_ref:
            raise ValueError("host scope/profile mismatch")
        if (
            not isinstance(self.allowed_methods, frozenset)
            or not self.allowed_methods
            or not all(isinstance(m, EvidenceMethod) for m in self.allowed_methods)
        ):
            raise ValueError("invalid approved method set")

    def __repr__(self) -> str:
        return "HostBinding(<redacted, operator-controlled>)"


class TrustedEntryContext:
    """Host-catalog-issued context, not buildable through normal constructor.

    Its name and Python-level constructor are not a sandbox. The active
    catalog uses *object identity* to reject unissued/foreign contexts.
    """

    __slots__ = ("_scope_ref", "_profile_ref", "_allowed_methods")

    _scope_ref: TrustedScopeRef
    _profile_ref: TrustProfileRef
    _allowed_methods: frozenset[EvidenceMethod]

    def __new__(cls, *_args: object, **_kwargs: object) -> Never:
        raise TypeError("host entry requires an approved catalog binding")

    @property
    def scope_ref(self) -> TrustedScopeRef:
        return self._scope_ref

    @property
    def profile_ref(self) -> TrustProfileRef:
        return self._profile_ref

    @property
    def allowed_methods(self) -> frozenset[EvidenceMethod]:
        return self._allowed_methods

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("host context cannot be mutated")

    def __repr__(self) -> str:
        return "TrustedEntryContext(<redacted, host-issued>)"


class HostRouteNotConfigured(Exception):
    """No approved route exists; never fallback to another tenant or profile."""


class HostTrustCatalog:
    """Immutable bootstrap snapshot with explicit one-to-one host routes.

    [DDD: Domain Service / Configuration Boundary] [DIP: Host-owned source]
    The caller supplies approved bindings at bootstrap, not by HTTP headers.
    This catalog is not a generic client-selectable trust-profile resolver.
    """

    __slots__ = ("_entries",)

    _entries: MappingProxyType[str, TrustedEntryContext]

    def __init__(self, bindings: Iterable[HostBinding]) -> None:
        entries: dict[str, TrustedEntryContext] = {}
        for binding in bindings:
            if not isinstance(binding, HostBinding):
                raise ValueError("invalid bootstrap binding")
            if binding.route_id in entries:
                raise ValueError("duplicate host route")
            if len(entries) >= 128:
                raise ValueError("host catalog capacity exceeded")
            entry: TrustedEntryContext = cast(
                TrustedEntryContext, object.__new__(cast(type[object], TrustedEntryContext))
            )
            object.__setattr__(entry, "_scope_ref", binding.scope_ref)
            object.__setattr__(entry, "_profile_ref", binding.profile_ref)
            object.__setattr__(entry, "_allowed_methods", binding.allowed_methods)
            entries[binding.route_id] = entry
        if not entries:
            raise ValueError("empty host trust catalog")
        self._entries = MappingProxyType(entries)

    def resolve_for_host_route(self, route_id: str) -> TrustedEntryContext:
        """Resolve ONLY a host-validated route, never a request-selected tenant."""
        if not isinstance(route_id, str):
            raise HostRouteNotConfigured("unconfigured host route")
        entry = self._entries.get(route_id)
        if entry is None:
            raise HostRouteNotConfigured("unconfigured host route")
        return entry

    def owns(self, entry: object) -> bool:
        """Reject forged/foreign contexts, even if their fields are equal."""
        return any(candidate is entry for candidate in self._entries.values())
