"""Host-controlled admission before loading third-party Python code.

A plugin factory is an opt-in zero-argument callable with SPI_MAJOR = 1.
It returns an existing Authenticator port, never an AuthenticationResult.
Admission is not code isolation or a supply-chain signature verification.
"""

import inspect
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import cast

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.ports.authenticator import Authenticator

from .discovery import (
    ENTRY_POINT_GROUP,
    SPI_MAJOR,
    PluginAdmissionRejected,
    PluginCandidate,
    _candidate_for,
    canonical_distribution,
)


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
                or self.group != ENTRY_POINT_GROUP
                or type(self.spi_major) is not int
                or self.spi_major != SPI_MAJOR
                or not isinstance(self.method, EvidenceMethod)
            ):
                raise PluginAdmissionRejected("invalid host plugin grant")
        except PluginAdmissionRejected:
            raise
        except Exception:
            raise PluginAdmissionRejected("invalid host plugin grant") from None

    def __repr__(self) -> str:
        return "PluginGrant(<operator-approved exact identity and method>)"


def load_approved_authenticators(
    candidates: Iterable[PluginCandidate], *, grants: Iterable[PluginGrant]
) -> tuple[Authenticator, ...]:
    """Preflight ALL allowlisted candidates before executing ANY plugin.

    Unknown installed candidates are ignored. Every requested grant must
    match exactly one installed distribution/version/group/name/target. Once
    loaded, the factory SPI and method are checked before returning instances
    to the existing immutable composition root.

    A failed bootstrap returns no instances; code executed before a failure
    cannot be rolled back by Python. Do not call during live request handling.
    """
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

        seen_grants: set[tuple[str, str]] = set()
        seen_methods: set[EvidenceMethod] = set()
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
    except PluginAdmissionRejected:
        raise
    except Exception:
        raise PluginAdmissionRejected("plugin admission preflight failed") from None

    instances: list[Authenticator] = []
    for candidate, grant in selected:
        try:
            factory: object = candidate._entry_point.load()
            if (
                type(getattr(factory, "SPI_MAJOR", None)) is not int
                or getattr(factory, "SPI_MAJOR", None) != grant.spi_major
                or not callable(factory)
            ):
                raise PluginAdmissionRejected("unsupported plugin SPI")
            instance: object = cast(Callable[[], object], factory)()
            if (
                getattr(instance, "method", None) is not grant.method
                or not inspect.iscoroutinefunction(getattr(instance, "verify", None))
            ):
                raise PluginAdmissionRejected("invalid plugin authenticator")
            instances.append(cast(Authenticator, instance))
        except Exception:
            # Sanitized: plugin exceptions may contain credentials or host settings.
            raise PluginAdmissionRejected("plugin activation rejected") from None
    return tuple(instances)
