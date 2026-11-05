"""M6 trusted configuration value objects. DDD: immutable bootstrap values.

A syntactically valid source is not an authority. Only the host's explicit
SourcePolicy admits it. A snapshot contains references, never secret material.
"""

import math
import re
from dataclasses import dataclass

from pyauthkit.application.host_context import HostBinding
from pyauthkit.domain.secret import SecretRef

_IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


class ConfigurationRejected(ValueError):
    """Sanitized bootstrap denial. Do not include untrusted values in messages."""


@dataclass(frozen=True, slots=True, repr=False)
class SourceProvenance:
    source_id: str
    source_kind: str
    revision: str

    def __post_init__(self) -> None:
        for value in (self.source_id, self.source_kind, self.revision):
            if not isinstance(value, str) or not _IDENT.fullmatch(value):
                raise ConfigurationRejected("invalid source provenance")

    def __repr__(self) -> str:
        return "SourceProvenance(<host-asserted>)"


@dataclass(frozen=True, slots=True, repr=False)
class SourcePolicy:
    """An allowlist supplied by the host, never by the loaded mapping itself."""

    approved_sources: frozenset[tuple[str, str]]

    def __post_init__(self) -> None:
        if not isinstance(self.approved_sources, frozenset) or not self.approved_sources:
            raise ConfigurationRejected("invalid source policy")
        for pair in self.approved_sources:
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or any(not isinstance(v, str) or not _IDENT.fullmatch(v) for v in pair)
            ):
                raise ConfigurationRejected("invalid source policy")

    def admit(self, provenance: SourceProvenance) -> None:
        if not isinstance(provenance, SourceProvenance) or (
            provenance.source_id, provenance.source_kind
        ) not in self.approved_sources:
            raise ConfigurationRejected("configuration source not approved")

    def __repr__(self) -> str:
        return "SourcePolicy(<host-approved>)"


@dataclass(frozen=True, slots=True, repr=False)
class ConfigurationGeneration:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value < 1:
            raise ConfigurationRejected("invalid configuration generation")

    def __repr__(self) -> str:
        return "ConfigurationGeneration(<host-controlled>)"


@dataclass(frozen=True, slots=True, repr=False)
class AuditDeliveryPolicy:
    mode: str = "best_effort"

    def __post_init__(self) -> None:
        if self.mode != "best_effort":
            # No durable/atomic committer is provided by M2 or this bootstrap.
            raise ConfigurationRejected("unsupported audit delivery policy")

    def __repr__(self) -> str:
        return "AuditDeliveryPolicy(best_effort, non-durable)"


@dataclass(frozen=True, slots=True, repr=False)
class ConfigurationSnapshot:
    """Deeply immutable *one-generation* host policy for one engine instance."""

    schema_version: int
    generation: ConfigurationGeneration
    provenance: SourceProvenance
    bindings: tuple[HostBinding, ...]
    timeout_seconds: float
    audit_delivery: AuditDeliveryPolicy
    secret_refs: tuple[SecretRef, ...] = ()

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ConfigurationRejected("unsupported configuration schema")
        if not isinstance(self.generation, ConfigurationGeneration):
            raise ConfigurationRejected("invalid configuration generation")
        if not isinstance(self.provenance, SourceProvenance):
            raise ConfigurationRejected("invalid source provenance")
        if not isinstance(self.bindings, tuple) or not self.bindings:
            raise ConfigurationRejected("invalid host bindings")
        if not all(isinstance(v, HostBinding) for v in self.bindings):
            raise ConfigurationRejected("invalid host bindings")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(self.timeout_seconds)
            or not 0 < self.timeout_seconds <= 30
        ):
            raise ConfigurationRejected("invalid verification timeout")
        if not isinstance(self.audit_delivery, AuditDeliveryPolicy):
            raise ConfigurationRejected("invalid audit delivery policy")
        if not isinstance(self.secret_refs, tuple) or not all(
            isinstance(ref, SecretRef) for ref in self.secret_refs
        ):
            raise ConfigurationRejected("invalid secret references")
        if len(set(self.secret_refs)) != len(self.secret_refs):
            raise ConfigurationRejected("duplicate secret reference")
        # Reuse M2's authoritative duplicate-route and scope/profile validation.
        from pyauthkit.application.host_context import HostTrustCatalog

        try:
            HostTrustCatalog(self.bindings)
        except ValueError:
            raise ConfigurationRejected("invalid host binding catalog") from None

    def __repr__(self) -> str:
        return "ConfigurationSnapshot(<trusted, non-secret, immutable>)"
