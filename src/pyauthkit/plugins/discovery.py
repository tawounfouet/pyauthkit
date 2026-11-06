"""Opt-in discovery of installed authenticator entry point *metadata* only.

No entry point is loaded here. Distribution metadata is descriptive, not a
signature, trust decision, or Python sandbox. A host must grant exact identities
before executing any third-party code.
"""

import re
from dataclasses import dataclass, field
from importlib.metadata import EntryPoint, entry_points

ENTRY_POINT_GROUP = "pyauthkit.authenticators.v1"
ENTRY_POINT_GROUP_V2 = "pyauthkit.authenticators.v2"
SPI_MAJOR = 1
SPI_MAJOR_V2 = 2

_DISTRIBUTION = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_ENTRY_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+!_-]{0,127}\Z")
_TARGET = re.compile(
    r"(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*:(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*\Z",
    re.ASCII,
)


class PluginAdmissionRejected(ValueError):
    """Sanitized bootstrap rejection. Never interpolate third-party metadata."""


def canonical_distribution(name: str) -> str:
    """Normalize a package name using Python packaging name separator rules."""
    if not isinstance(name, str) or not 1 <= len(name) <= 128:
        raise PluginAdmissionRejected("invalid plugin distribution metadata")
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    if _DISTRIBUTION.fullmatch(normalized) is None:
        raise PluginAdmissionRejected("invalid plugin distribution metadata")
    return normalized


@dataclass(frozen=True, slots=True, repr=False)
class PluginCandidate:
    """Inert metadata snapshot; explicitly NOT admitted, loaded, or executable."""

    distribution: str
    version: str
    group: str
    name: str
    target: str
    _entry_point: EntryPoint = field(repr=False, compare=False)

    def __repr__(self) -> str:
        return "PluginCandidate(<untrusted distribution metadata>)"


def _candidate_for(point: EntryPoint) -> PluginCandidate:
    """Read metadata and bound it before treating a candidate as selectable."""
    try:
        if not isinstance(point, EntryPoint) or point.group not in (ENTRY_POINT_GROUP, ENTRY_POINT_GROUP_V2):
            raise PluginAdmissionRejected("invalid plugin entry point")
        distribution = point.dist
        if distribution is None:
            raise PluginAdmissionRejected("missing plugin distribution identity")
        raw_name = distribution.metadata.get("Name")
        version = distribution.version
        name, target = point.name, point.value
        if not isinstance(raw_name, str) or not isinstance(version, str):
            raise PluginAdmissionRejected("invalid plugin distribution metadata")
        if (
            not _VERSION.fullmatch(version)
            or not _ENTRY_NAME.fullmatch(name)
            or not _TARGET.fullmatch(target)
        ):
            raise PluginAdmissionRejected("invalid plugin entry point metadata")
        return PluginCandidate(
            canonical_distribution(raw_name), version, point.group, name, target, point
        )
    except PluginAdmissionRejected:
        raise
    except Exception:
        raise PluginAdmissionRejected("plugin metadata inspection failed") from None


def discover_authenticator_plugins(
    *, enabled: bool = False, group: str = ENTRY_POINT_GROUP
) -> tuple[PluginCandidate, ...]:
    """List installed candidates only when enabled by an authoritative host.

    This function never imports plugin modules, calls EntryPoint.load(), or
    instantiates plugin factories. Duplicate names are ambiguous and rejected.
    """
    if type(enabled) is not bool:
        raise PluginAdmissionRejected("invalid discovery switch")
    if group not in (ENTRY_POINT_GROUP, ENTRY_POINT_GROUP_V2):
        raise PluginAdmissionRejected("unsupported plugin SPI group")
    if not enabled:
        return ()
    try:
        points = entry_points(group=group)
        candidates = tuple(_candidate_for(point) for point in points)
        if any(candidate.group != group for candidate in candidates):
            raise PluginAdmissionRejected("plugin group mismatch")
        identities = [(candidate.group, candidate.name) for candidate in candidates]
        if len(identities) != len(set(identities)):
            raise PluginAdmissionRejected("ambiguous plugin entry point")
        return tuple(
            sorted(candidates, key=lambda c: (c.distribution, c.name, c.version, c.target))
        )
    except PluginAdmissionRejected:
        raise
    except Exception:
        raise PluginAdmissionRejected("plugin discovery failed") from None
