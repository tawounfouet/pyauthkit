"""M6 deterministic, fail-closed source precedence for non-security timeouts.

[ARCH: Explicit Policy] Only the host's authoritative mapping defines trust.
Additional sources are allowed to override *only* timeout_seconds, under an
independently supplied policy and a fixed low-to-high precedence. No dict merge.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace

from .models import (
    ConfigurationGeneration,
    ConfigurationRejected,
    ConfigurationSnapshot,
    SourcePolicy,
    SourceProvenance,
)
from .sources import load_approved_configuration

type SourceIdentity = tuple[str, str]
type OperationalLayer = tuple[SourceProvenance, Mapping[str, object]]


@dataclass(frozen=True, slots=True, repr=False)
class SourceLayerPolicy:
    """Exact host-authorized order. Overrides run low-to-high priority.

    Trust-bearing keys have no override path. There is no default source,
    environment inspection, missing-layer fallback or partial source merge.
    """

    authority: SourceIdentity
    operational_overrides: tuple[SourceIdentity, ...] = ()

    def __post_init__(self) -> None:
        if (
            type(self.authority) is not tuple
            or len(self.authority) != 2
            or type(self.operational_overrides) is not tuple
            or len(self.operational_overrides) > 4
            or any(type(v) is not tuple or len(v) != 2 for v in self.operational_overrides)
        ):
            raise ConfigurationRejected("invalid source precedence policy")
        identities = (self.authority, *self.operational_overrides)
        if len(set(identities)) != len(identities):
            raise ConfigurationRejected("duplicate source in precedence policy")
        try:
            SourcePolicy(frozenset(identities))
        except (ValueError, TypeError):
            raise ConfigurationRejected("invalid source precedence policy") from None

    def __repr__(self) -> str:
        return "SourceLayerPolicy(<host-controlled precedence>)"


def load_layered_configuration(
    authority_mapping: Mapping[str, object],
    *,
    authority_provenance: SourceProvenance,
    operational_layers: tuple[OperationalLayer, ...],
    layering_policy: SourceLayerPolicy,
    source_policy: SourcePolicy,
    generation: ConfigurationGeneration,
) -> ConfigurationSnapshot:
    """Admit exact source identities; overlay only a validated bounded timeout.

    Each input remains external and untrusted until admitted. Operational
    layers cannot change routes, tenants, JWT profiles, secrets or audit
    delivery. The host remains responsible for verifying source provenance
    and revisions, as well as deploying the resulting generation atomically.
    """
    if not isinstance(layering_policy, SourceLayerPolicy):
        raise ConfigurationRejected("missing source precedence policy")
    if not isinstance(source_policy, SourcePolicy):
        raise ConfigurationRejected("invalid source policy")
    if (
        not isinstance(authority_provenance, SourceProvenance)
        or (
            authority_provenance.source_id,
            authority_provenance.source_kind,
        )
        != layering_policy.authority
    ):
        raise ConfigurationRejected("unapproved authoritative source")
    source_policy.admit(authority_provenance)
    if (
        type(operational_layers) is not tuple
        or len(operational_layers) != len(layering_policy.operational_overrides)
    ):
        raise ConfigurationRejected("incomplete source precedence chain")

    validated: list[tuple[SourceProvenance, float]] = []
    for index, layer in enumerate(operational_layers):
        if type(layer) is not tuple or len(layer) != 2:
            raise ConfigurationRejected("invalid operational layer")
        provenance, values = layer
        if not isinstance(provenance, SourceProvenance):
            raise ConfigurationRejected("invalid operational provenance")
        if (provenance.source_id, provenance.source_kind) != (
            layering_policy.operational_overrides[index]
        ):
            raise ConfigurationRejected("operational precedence mismatch")
        source_policy.admit(provenance)
        if not isinstance(values, Mapping) or set(values) != {"timeout_seconds"}:
            raise ConfigurationRejected("operational source changed trust-bearing fields")
        raw_timeout = values["timeout_seconds"]
        if (
            type(raw_timeout) not in (float, int)
            or not math.isfinite(raw_timeout)
            or not 0 < raw_timeout <= 30
        ):
            raise ConfigurationRejected("invalid operational verification timeout")
        validated.append((provenance, float(raw_timeout)))

    snapshot = load_approved_configuration(
        authority_mapping,
        provenance=authority_provenance,
        policy=source_policy,
        generation=generation,
    )
    if not validated:
        return snapshot

    effective_timeout = validated[-1][1]
    return replace(
        snapshot,
        timeout_seconds=effective_timeout,
        operational_sources=tuple(provenance for provenance, _ in validated),
    )
