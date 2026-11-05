"""M6 trusted configuration value objects. DDD: immutable bootstrap values.

A syntactically valid source is not an authority. Only the host's explicit
SourcePolicy admits it. A snapshot contains references, never secret material.
"""

import ipaddress
import math
import re
from dataclasses import dataclass

from pyauthkit.application.host_context import HostBinding
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.trust import TrustProfileRef

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
        if (
            not isinstance(provenance, SourceProvenance)
            or (provenance.source_id, provenance.source_kind) not in self.approved_sources
        ):
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
class StaticJwtKeySource:
    """Host-selected identifier for a public JWK set, never token-derived."""

    keyset_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.keyset_ref, str) or not _IDENT.fullmatch(self.keyset_ref):
            raise ConfigurationRejected("invalid static JWT keyset reference")

    def __repr__(self) -> str:
        return "StaticJwtKeySource(<approved reference>)"


@dataclass(frozen=True, slots=True, repr=False)
class HttpsJwtKeySource:
    """An approved HTTPS source and a bounded public IP allowlist."""

    source: ApprovedJwksSource
    allowed_ips: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source, ApprovedJwksSource):
            raise ConfigurationRejected("invalid JWKS source")
        if (
            type(self.allowed_ips) is not tuple
            or not 1 <= len(self.allowed_ips) <= 16
            or len(set(self.allowed_ips)) != len(self.allowed_ips)
        ):
            raise ConfigurationRejected("invalid JWKS destination allowlist")
        for raw in self.allowed_ips:
            if type(raw) is not str:
                raise ConfigurationRejected("invalid JWKS destination allowlist")
            try:
                address = ipaddress.ip_address(raw)
            except ValueError:
                raise ConfigurationRejected("invalid JWKS destination allowlist") from None
            if (
                not address.is_global
                or address.is_multicast
                or isinstance(address, ipaddress.IPv6Address)
                and address.ipv4_mapped is not None
                or str(address) != raw
            ):
                raise ConfigurationRejected("unapproved JWKS destination")

    def __repr__(self) -> str:
        return "HttpsJwtKeySource(<pinned, host-controlled>)"


@dataclass(frozen=True, slots=True, repr=False)
class JwtTrustBinding:
    """One M5 JWT profile and exactly one host-approved source of public keys."""

    profile: TrustedJwtVerificationProfile
    keys: StaticJwtKeySource | HttpsJwtKeySource

    def __post_init__(self) -> None:
        if not isinstance(self.profile, TrustedJwtVerificationProfile):
            raise ConfigurationRejected("invalid JWT trust profile")
        if not isinstance(self.keys, (StaticJwtKeySource, HttpsJwtKeySource)):
            raise ConfigurationRejected("invalid JWT key source")
        if (
            isinstance(self.keys, HttpsJwtKeySource)
            and self.keys.source.profile_ref != self.profile.profile_ref
        ):
            raise ConfigurationRejected("JWKS source/profile mismatch")

    def __repr__(self) -> str:
        return "JwtTrustBinding(<host-approved, redacted>)"


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
    jwt_profiles: tuple[JwtTrustBinding, ...] = ()
    operational_sources: tuple[SourceProvenance, ...] = ()

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version not in (1, 2):
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
        if type(self.operational_sources) is not tuple or not all(
            isinstance(source, SourceProvenance) for source in self.operational_sources
        ):
            raise ConfigurationRejected("invalid operational source provenance")
        if type(self.jwt_profiles) is not tuple or not all(
            isinstance(binding, JwtTrustBinding) for binding in self.jwt_profiles
        ):
            raise ConfigurationRejected("invalid JWT configuration")
        if self.schema_version == 1:
            if self.jwt_profiles:
                raise ConfigurationRejected("JWT trust profiles require configuration schema v2")
        else:
            expected: set[TrustProfileRef] = {
                binding.profile_ref
                for binding in self.bindings
                if EvidenceMethod.JWT in binding.allowed_methods
            }
            declared = tuple(binding.profile.profile_ref for binding in self.jwt_profiles)
            if (
                len(declared) != len(set(declared))
                or set(declared) != expected
                or len(declared) > 128
            ):
                raise ConfigurationRejected("JWT trust profile coverage mismatch")
        # Reuse M2's authoritative duplicate-route and scope/profile validation.
        from pyauthkit.application.host_context import HostTrustCatalog

        try:
            HostTrustCatalog(self.bindings)
        except ValueError:
            raise ConfigurationRejected("invalid host binding catalog") from None

    def __repr__(self) -> str:
        return "ConfigurationSnapshot(<trusted, non-secret, immutable>)"
