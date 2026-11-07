"""Host-controlled admission before loading third-party Python code.

A v1 factory is a zero-argument callable; an explicitly admitted v2 factory
receives a host-owned service bundle. Neither issues an AuthenticationResult.
Admission is not code isolation or a supply-chain signature verification.
"""

import inspect
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import cast

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.outcome import AuthenticatorOutcome, ErrorOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.ports.authenticator import Authenticator, VerificationContext

from .discovery import (
    ENTRY_POINT_GROUP,
    ENTRY_POINT_GROUP_V2,
    SPI_MAJOR,
    SPI_MAJOR_V2,
    PluginAdmissionRejected,
    PluginCandidate,
    _candidate_for,
    canonical_distribution,
)
from .services import _METHOD_PORT_ROLES, PluginHostServices


@dataclass(frozen=True, slots=True, repr=False)
class PluginGrant:
    """Exact host-owned allowlist record. Never parse it from request evidence."""

    distribution: str
    version: str
    name: str
    target: str
    method: EvidenceMethod
    group: str = ENTRY_POINT_GROUP
    spi_major: int = SPI_MAJOR
    port_roles: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        # Constructing a grant is an operator action, not an admission by itself.
        try:
            from .discovery import _ENTRY_NAME, _TARGET, _VERSION

            if (
                self.distribution != canonical_distribution(self.distribution)
                or not isinstance(self.version, str)
                or _VERSION.fullmatch(self.version) is None
                or not isinstance(self.name, str)
                or _ENTRY_NAME.fullmatch(self.name) is None
                or not isinstance(self.target, str)
                or _TARGET.fullmatch(self.target) is None
                or self.group not in (ENTRY_POINT_GROUP, ENTRY_POINT_GROUP_V2)
                or type(self.spi_major) is not int
                or self.spi_major
                != (SPI_MAJOR if self.group == ENTRY_POINT_GROUP else SPI_MAJOR_V2)
                or not isinstance(self.method, EvidenceMethod)
                or not isinstance(self.port_roles, frozenset)
                or (self.spi_major == SPI_MAJOR and bool(self.port_roles))
                or (
                    self.spi_major == SPI_MAJOR_V2
                    and (
                        not self.port_roles
                        or not self.port_roles.issubset(
                            _METHOD_PORT_ROLES.get(self.method, frozenset())
                        )
                    )
                )
            ):
                raise PluginAdmissionRejected("invalid host plugin grant")
        except PluginAdmissionRejected:
            raise
        except Exception:
            raise PluginAdmissionRejected("invalid host plugin grant") from None

    def __repr__(self) -> str:
        return "PluginGrant(<operator-approved exact identity and method>)"


def _preflight_candidates(
    candidates: Iterable[PluginCandidate],
    *,
    grants: Iterable[PluginGrant],
    service_bindings: Mapping[PluginGrant, PluginHostServices] | None = None,
    reserved_methods: Iterable[EvidenceMethod] = (),
) -> tuple[tuple[PluginCandidate, PluginGrant], ...]:
    """Validate all host grants and distribution metadata without executing plugin code."""
    try:
        available = tuple(candidates)
        approved = tuple(grants)
        if not all(isinstance(c, PluginCandidate) for c in available):
            raise PluginAdmissionRejected("invalid plugin candidates")
        if not all(isinstance(g, PluginGrant) for g in approved):
            raise PluginAdmissionRejected("invalid host plugin grants")
        seen_candidates: set[tuple[str, str]] = set()
        for candidate in available:
            # Re-read the original distribution metadata; never trust copied fields.
            if _candidate_for(candidate._entry_point) != candidate:
                raise PluginAdmissionRejected("plugin metadata changed")
            key = (candidate.group, candidate.name)
            if key in seen_candidates:
                raise PluginAdmissionRejected("ambiguous plugin entry point")
            seen_candidates.add(key)

        reserved = tuple(reserved_methods)
        if not all(isinstance(method, EvidenceMethod) for method in reserved):
            raise PluginAdmissionRejected("invalid reserved authenticator methods")
        seen_grants: set[tuple[str, str]] = set()
        # Before any EntryPoint.load(), reject methods already owned by the
        # host's built-in authenticators. The host must supply this inventory.
        seen_methods: set[EvidenceMethod] = set(reserved)
        selected: list[tuple[PluginCandidate, PluginGrant]] = []
        for grant in approved:
            key = (grant.group, grant.name)
            if key in seen_grants or grant.method in seen_methods:
                raise PluginAdmissionRejected("duplicate plugin grant or method")
            seen_grants.add(key)
            seen_methods.add(grant.method)
            matches = [
                candidate
                for candidate in available
                if candidate.group == grant.group and candidate.name == grant.name
            ]
            if len(matches) != 1:
                raise PluginAdmissionRejected("missing or ambiguous approved plugin")
            candidate = matches[0]
            if (
                candidate.distribution != grant.distribution
                or candidate.version != grant.version
                or candidate.target != grant.target
            ):
                raise PluginAdmissionRejected("plugin distribution or version not approved")
            selected.append((candidate, grant))
        injected = {} if service_bindings is None else dict(service_bindings)
        required = {grant for _candidate, grant in selected if grant.spi_major == SPI_MAJOR_V2}
        if set(injected) != required:
            raise PluginAdmissionRejected("plugin service grants do not match admissions")
        for grant, bundle in injected.items():
            if (
                not isinstance(grant, PluginGrant)
                or not isinstance(bundle, PluginHostServices)
                or grant.method is not bundle.method
                or grant.group != ENTRY_POINT_GROUP_V2
                or grant.port_roles != frozenset(bundle.ports)
            ):
                raise PluginAdmissionRejected("invalid plugin host services")
    except PluginAdmissionRejected:
        raise
    except Exception:
        raise PluginAdmissionRejected("plugin admission preflight failed") from None

    return tuple(selected)


def _instantiate_approved(
    candidate: PluginCandidate,
    grant: PluginGrant,
    *,
    on_created: Callable[[object], None] | None = None,
    services: PluginHostServices | None = None,
) -> Authenticator:
    """Revalidate snapshot metadata at load time, then import a granted entry point.

    Detects mutation between the full batch preflight and this load. This does
    NOT attest that Python will import code owned by the distribution or close
    an import/filesystem time-of-check to time-of-use race.
    """
    observed = _candidate_for(candidate._entry_point)
    if (
        observed != candidate
        or observed.distribution != grant.distribution
        or observed.version != grant.version
        or observed.group != grant.group
        or observed.name != grant.name
        or observed.target != grant.target
    ):
        raise PluginAdmissionRejected("plugin metadata changed before import")
    factory: object = candidate._entry_point.load()
    if (
        type(getattr(factory, "SPI_MAJOR", None)) is not int
        or getattr(factory, "SPI_MAJOR", None) != grant.spi_major
        or not callable(factory)
    ):
        raise PluginAdmissionRejected("unsupported plugin SPI")
    if grant.spi_major == SPI_MAJOR:
        if services is not None:
            raise PluginAdmissionRejected("legacy plugin cannot receive host services")
        instance: object = cast(Callable[[], object], factory)()
    else:
        if services is None or services.method is not grant.method:
            raise PluginAdmissionRejected("plugin host services missing")
        instance = cast(Callable[[PluginHostServices], object], factory)(services)
    # Managed activation observes the instance before post-construction checks,
    # so its aclose hook can run even when its declared method is invalid.
    if on_created is not None:
        on_created(instance)
    method = getattr(instance, "method", None)
    verify = getattr(instance, "verify", None)
    if method is not grant.method or not inspect.iscoroutinefunction(verify):
        raise PluginAdmissionRejected("invalid plugin authenticator")
    verified_instance = cast(Authenticator, instance)
    if grant.spi_major == SPI_MAJOR_V2:
        if services is None:
            raise PluginAdmissionRejected("plugin host services missing")
        return _ScopedAuthenticator(verified_instance, services)
    return verified_instance


class _ScopedAuthenticator:
    """Reject tenant/profile confusion before delegating to admitted v2 code."""

    __slots__ = ("_instance", "_services")

    def __init__(self, instance: Authenticator, services: PluginHostServices) -> None:
        self._instance = instance
        self._services = services

    @property
    def method(self) -> EvidenceMethod:
        return self._services.method

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> AuthenticatorOutcome:
        if (
            request.evidence.method is not self._services.method
            or context.method is not self._services.method
            or context.scope_ref != self._services.scope_ref
            or context.profile_ref != self._services.profile_ref
            or request.correlation_id != context.correlation_id
        ):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        return await self._instance.verify(request, context)

    def __repr__(self) -> str:
        return "_ScopedAuthenticator(<host-scoped, redacted>)"


def load_approved_authenticators(
    candidates: Iterable[PluginCandidate],
    *,
    grants: Iterable[PluginGrant],
    reserved_methods: Iterable[EvidenceMethod] = (),
) -> tuple[Authenticator, ...]:
    """Load approved authenticator instances with caller-owned lifecycle.

    Prefer activate_approved_authenticators for resource-owning plugins.
    This legacy synchronous API cannot unwind async resources if later
    factories fail; it is suitable for explicitly stateless plugins only.
    The host may reserve methods of built-in authenticators at preflight
    to reject collisions before importing any approved plugin module.
    The host must not invoke it while serving authentication requests.
    """
    selected = _preflight_candidates(candidates, grants=grants, reserved_methods=reserved_methods)
    instances: list[Authenticator] = []
    for candidate, grant in selected:
        try:
            instance = _instantiate_approved(candidate, grant)
            instances.append(instance)
        except Exception:
            raise PluginAdmissionRejected("plugin activation rejected") from None
    return tuple(instances)
