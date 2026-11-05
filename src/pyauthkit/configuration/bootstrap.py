"""Compose an M6 runtime without changing the existing M2 authentication API."""

from collections.abc import Iterable
from dataclasses import dataclass

from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate, FinalRule
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.ports.authenticator import Authenticator
from pyauthkit.ports.events import AuthenticationEventSink

from .audit import BoundedBestEffortAuditSink
from .models import ConfigurationRejected, ConfigurationSnapshot


@dataclass(frozen=True, slots=True, repr=False)
class M6Runtime:
    """One generation: catalog and engine are built together and never reloaded."""

    snapshot: ConfigurationSnapshot
    catalog: HostTrustCatalog
    engine: AuthenticationEngine

    def __repr__(self) -> str:
        return "M6Runtime(<one approved generation>)"


def compose_authentication_engine(
    snapshot: ConfigurationSnapshot,
    *,
    authenticators: Iterable[Authenticator],
    final_rule: FinalRule | None = None,
    event_sink: AuthenticationEventSink | None = None,
    minimum_generation: int = 1,
) -> M6Runtime:
    """Fail before activation if any method is missing or generation is stale.

    `minimum_generation` must be supplied from a trustworthy host-owned
    external generation ledger to provide anti-rollback across restarts.
    Without that ledger this function cannot guarantee crash-safe rollback.
    """
    if not isinstance(snapshot, ConfigurationSnapshot):
        raise ConfigurationRejected("invalid configuration snapshot")
    if type(minimum_generation) is not int or minimum_generation < 1:
        raise ConfigurationRejected("invalid generation floor")
    if snapshot.generation.value < minimum_generation:
        raise ConfigurationRejected("configuration generation is stale")
    if snapshot.secret_refs:
        # A configured secret must not be treated as ready before an approved
        # consumer is explicitly wired. A preflight lookup alone is not enough.
        raise ConfigurationRejected("secret consumer composition not implemented")
    if final_rule is not None and not callable(final_rule):
        raise ConfigurationRejected("invalid final rule")
    try:
        catalog = HostTrustCatalog(snapshot.bindings)
        builder = AuthenticatorRegistryBuilder()
        for authenticator in authenticators:
            builder.register(authenticator)
        registry = builder.freeze()
        approved: set[EvidenceMethod] = {
            method for binding in snapshot.bindings for method in binding.allowed_methods
        }
        for method in approved:
            registry.resolve(method)
        gate = AuthenticationPolicyGate(catalog, final_rule=final_rule)
        engine = AuthenticationEngine(
            policy=gate,
            registry=registry,
            timeout_seconds=snapshot.timeout_seconds,
            event_sink=(
                BoundedBestEffortAuditSink(event_sink)
                if event_sink is not None
                else None
            ),
        )
    except Exception:
        # Never expose an adapter's exception text or raw config values.
        raise ConfigurationRejected("authentication composition rejected") from None
    return M6Runtime(snapshot, catalog, engine)
