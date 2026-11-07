"""Explicitly host-owned dependencies for SPI v2 authenticator factories.

A factory receives this validated, immutable *reference bundle* only after
the host admits its distribution. Underlying ports are host-managed objects.
The bundle is not an OS sandbox, cryptographic capability, or a mechanism for
authenticating the Python caller. In-process third-party code remains trusted.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pyauthkit.application.host_context import HostBinding
from pyauthkit.configuration.models import ConfigurationSnapshot
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.trust import TrustProfileRef

from .discovery import PluginAdmissionRejected

# Every role has an explicit narrow callable contract, not a scalar secret.
_PORT_ROLES = {
    "record_resolver": "resolve",
    "attempt_guard": "admit",
    "hash_verifier": "verify",
    "key_resolver": "resolve",
    "clock": "now",
    "event_sink": "emit",
}

# Candidate M7 v2 least-privilege compatibility policy. A role's method
# signature alone does not grant it to every authentication method.
_METHOD_PORT_ROLES: Mapping[EvidenceMethod, frozenset[str]] = MappingProxyType(
    {
        EvidenceMethod.PASSWORD: frozenset(
            {"record_resolver", "attempt_guard", "hash_verifier", "clock", "event_sink"}
        ),
        EvidenceMethod.API_KEY: frozenset(
            {"record_resolver", "attempt_guard", "hash_verifier", "clock", "event_sink"}
        ),
        EvidenceMethod.JWT: frozenset(
            {"key_resolver", "record_resolver", "attempt_guard", "clock", "event_sink"}
        ),
    }
)


@dataclass(frozen=True, slots=True, repr=False)
class PluginHostServices:
    """One host-approved route and method; no user-controlled tenant selection.

    The host is solely responsible for constructing this object from its
    approved M6 snapshot and for injecting appropriately scoped ports.
    """

    binding: HostBinding
    method: EvidenceMethod
    ports: Mapping[str, object]

    def __post_init__(self) -> None:
        try:
            if not isinstance(self.binding, HostBinding) or not isinstance(
                self.method, EvidenceMethod
            ):
                raise PluginAdmissionRejected("invalid plugin host binding")
            if self.method not in self.binding.allowed_methods:
                raise PluginAdmissionRejected("plugin method not approved for host route")
            if not isinstance(self.ports, Mapping):
                raise PluginAdmissionRejected("invalid plugin host ports")
            owned: dict[str, object] = {}
            for role, port in self.ports.items():
                if (
                    not isinstance(role, str)
                    or role not in _PORT_ROLES
                    or role not in _METHOD_PORT_ROLES.get(self.method, frozenset())
                ):
                    raise PluginAdmissionRejected("unsupported plugin host port")
                if not callable(getattr(port, _PORT_ROLES[role], None)):
                    raise PluginAdmissionRejected("invalid plugin host port")
                owned[role] = port
            if not owned or len(owned) > len(_PORT_ROLES):
                raise PluginAdmissionRejected("invalid plugin host ports")
            object.__setattr__(self, "ports", MappingProxyType(owned))
        except PluginAdmissionRejected:
            raise
        except Exception:
            # A port descriptor or Mapping.items() can raise with secret text.
            raise PluginAdmissionRejected("invalid plugin host ports") from None

    @classmethod
    def from_snapshot(
        cls,
        snapshot: ConfigurationSnapshot,
        *,
        route_id: str,
        method: EvidenceMethod,
        ports: Mapping[str, object],
    ) -> "PluginHostServices":
        """Bind to an EXACT operator-approved M6 route, never a caller claim."""
        try:
            if not isinstance(snapshot, ConfigurationSnapshot) or not isinstance(route_id, str):
                raise PluginAdmissionRejected("invalid host plugin snapshot")
            matches = [binding for binding in snapshot.bindings if binding.route_id == route_id]
            if len(matches) != 1:
                raise PluginAdmissionRejected("plugin host route not configured")
            return cls(matches[0], method, ports)
        except PluginAdmissionRejected:
            raise
        except Exception:
            raise PluginAdmissionRejected("invalid host plugin snapshot") from None

    @property
    def scope_ref(self) -> TrustedScopeRef:
        return self.binding.scope_ref

    @property
    def profile_ref(self) -> TrustProfileRef:
        return self.binding.profile_ref

    def port(self, role: str) -> object:
        """Select a preapproved port; no dynamic import or fallback."""
        if not isinstance(role, str) or role not in self.ports:
            raise PluginAdmissionRejected("plugin host port not admitted")
        return self.ports[role]

    def __repr__(self) -> str:
        return "PluginHostServices(<host-bound, ports redacted>)"
