"""Strict MVP host-mapping reader. Never merges unapproved trust sources.

The host controls both the mapping and its provenance. Supplying a
SourceProvenance inside a client request would not make it trustworthy.
"""

from collections.abc import Mapping, Sequence

from pyauthkit.application.host_context import HostBinding
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.trust import TrustProfileRef

from .models import (
    AuditDeliveryPolicy,
    ConfigurationGeneration,
    ConfigurationRejected,
    ConfigurationSnapshot,
    SourcePolicy,
    SourceProvenance,
)

_ROOT_KEYS = frozenset({"schema_version", "routes", "timeout_seconds", "audit_delivery", "secrets"})
_ROUTE_KEYS = frozenset({"route_id", "scope", "profile_id", "profile_version", "allowed_methods"})
_SECRET_KEYS = frozenset({"provider", "namespace", "key_id", "version", "purpose"})


def _fields(value: object, names: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != names:
        raise ConfigurationRejected("invalid configuration fields")
    if not all(isinstance(k, str) for k in value):
        raise ConfigurationRejected("invalid configuration fields")
    return value


def _sequence(value: object) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise ConfigurationRejected("invalid configuration collection")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise ConfigurationRejected("invalid configuration value")
    return value


def load_approved_configuration(
    mapping: Mapping[str, object],
    *,
    provenance: SourceProvenance,
    policy: SourcePolicy,
    generation: ConfigurationGeneration,
) -> ConfigurationSnapshot:
    """Parse an explicit, allowlisted host mapping, rejecting every unknown field.

    There is deliberately no os.environ access, file discovery or merge-by-key.
    Every trust profile and allowed method set is admitted as an atomic binding.
    """
    if not isinstance(policy, SourcePolicy):
        raise ConfigurationRejected("invalid source policy")
    policy.admit(provenance)
    if not isinstance(mapping, Mapping) or set(mapping) != _ROOT_KEYS:
        raise ConfigurationRejected("invalid configuration fields")
    if not all(isinstance(k, str) for k in mapping):
        raise ConfigurationRejected("invalid configuration fields")

    raw_routes = _sequence(mapping["routes"])
    if not 1 <= len(raw_routes) <= 128:
        raise ConfigurationRejected("invalid route count")
    bindings: list[HostBinding] = []
    for raw in raw_routes:
        route = _fields(raw, _ROUTE_KEYS)
        methods_raw = _sequence(route["allowed_methods"])
        if not 1 <= len(methods_raw) <= len(EvidenceMethod):
            raise ConfigurationRejected("invalid allowed method set")
        try:
            methods = frozenset(EvidenceMethod(_text(m)) for m in methods_raw)
            if len(methods) != len(methods_raw):
                raise ValueError("duplicate method")
            scope = TrustedScopeRef(_text(route["scope"]))
            bindings.append(
                HostBinding(
                    _text(route["route_id"]),
                    scope,
                    TrustProfileRef(
                        _text(route["profile_id"]),
                        _text(route["profile_version"]),
                        scope,
                    ),
                    methods,
                )
            )
        except (ValueError, TypeError):
            raise ConfigurationRejected("invalid host binding") from None

    secrets_raw = _sequence(mapping["secrets"])
    if len(secrets_raw) > 128:
        raise ConfigurationRejected("too many secret references")
    secret_refs: list[SecretRef] = []
    for raw in secrets_raw:
        item = _fields(raw, _SECRET_KEYS)
        try:
            secret_refs.append(
                SecretRef(
                    provider=_text(item["provider"]),
                    namespace=_text(item["namespace"]),
                    key_id=_text(item["key_id"]),
                    version=_text(item["version"]),
                    purpose=_text(item["purpose"]),
                )
            )
        except (ValueError, TypeError):
            raise ConfigurationRejected("invalid secret reference") from None

    try:
        return ConfigurationSnapshot(
            schema_version=mapping["schema_version"],  # type: ignore[arg-type]
            generation=generation,
            provenance=provenance,
            bindings=tuple(bindings),
            timeout_seconds=mapping["timeout_seconds"],  # type: ignore[arg-type]
            audit_delivery=AuditDeliveryPolicy(_text(mapping["audit_delivery"])),
            secret_refs=tuple(secret_refs),
        )
    except (ValueError, TypeError):
        raise ConfigurationRejected("configuration bootstrap rejected") from None
