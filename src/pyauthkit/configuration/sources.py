"""Strict MVP host-mapping and JSON readers. No implicit source merge.

The host controls both the mapping and its provenance. Supplying a
SourceProvenance inside a client request would not make it trustworthy.
"""

import json
import math
from collections.abc import Mapping, Sequence
from typing import cast
from urllib.parse import urlsplit

from pyauthkit.application.host_context import HostBinding
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import PrincipalType
from pyauthkit.domain.jwks import ApprovedJwksSource
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.trust import TrustProfileRef

from .models import (
    AuditDeliveryPolicy,
    ConfigurationGeneration,
    ConfigurationRejected,
    ConfigurationSnapshot,
    HttpsJwtKeySource,
    JwtTrustBinding,
    SourcePolicy,
    SourceProvenance,
    StaticJwtKeySource,
)

_ROOT_KEYS = frozenset({"schema_version", "routes", "timeout_seconds", "audit_delivery", "secrets"})
_ROOT_KEYS_V2 = _ROOT_KEYS | {"jwt_profiles"}
_JWT_KEYS = frozenset(
    {
        "scope",
        "profile_id",
        "profile_version",
        "issuer",
        "audience",
        "expected_typ",
        "allowed_algorithms",
        "principal_type",
        "max_token_bytes",
        "clock_skew_seconds",
        "max_age_seconds",
        "key_source",
    }
)
_STATIC_JWT_KEYS = frozenset({"kind", "keyset_ref"})
_HTTPS_JWT_KEYS = frozenset(
    {
        "kind",
        "source_id",
        "uri",
        "ttl_seconds",
        "timeout_seconds",
        "max_response_bytes",
        "max_keys",
        "allowed_ips",
    }
)
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


def _parse_jwt_profiles(raw: object) -> tuple[JwtTrustBinding, ...]:
    """Strict v2 trust profiles. No default issuer, audience, alg or key authority."""
    entries = _sequence(raw)
    if len(entries) > 128:
        raise ConfigurationRejected("too many JWT profiles")
    profiles: list[JwtTrustBinding] = []
    for value in entries:
        item = _fields(value, _JWT_KEYS)
        try:
            scope = TrustedScopeRef(_text(item["scope"]))
            profile_ref = TrustProfileRef(
                _text(item["profile_id"]), _text(item["profile_version"]), scope
            )
            issuer = _text(item["issuer"])
            issuer_uri = urlsplit(issuer)
            if (
                issuer_uri.scheme != "https"
                or issuer_uri.hostname is None
                or issuer_uri.username is not None
                or issuer_uri.password is not None
                or issuer_uri.query
                or issuer_uri.fragment
                or "*" in issuer
            ):
                raise ValueError("invalid host-approved JWT issuer")
            algorithms = _sequence(item["allowed_algorithms"])
            if not algorithms or len(algorithms) != len(set(_text(a) for a in algorithms)):
                raise ValueError("invalid JWT algorithm policy")
            profile = TrustedJwtVerificationProfile(
                scope_ref=scope,
                profile_ref=profile_ref,
                issuer=issuer,
                audience=_text(item["audience"]),
                expected_typ=_text(item["expected_typ"]),
                allowed_algorithms=frozenset(_text(a) for a in algorithms),
                principal_type=PrincipalType(_text(item["principal_type"])),
                max_token_bytes=item["max_token_bytes"],  # type: ignore[arg-type]
                clock_skew_seconds=item["clock_skew_seconds"],  # type: ignore[arg-type]
                max_age_seconds=item["max_age_seconds"],  # type: ignore[arg-type]
            )
            raw_source = item["key_source"]
            if not isinstance(raw_source, Mapping):
                raise ValueError("missing JWT key source")
            kind = _text(raw_source.get("kind"))
            if kind == "static":
                keyset = _fields(raw_source, _STATIC_JWT_KEYS)
                keys: StaticJwtKeySource | HttpsJwtKeySource = StaticJwtKeySource(
                    _text(keyset["keyset_ref"])
                )
            elif kind == "jwks_https":
                remote = _fields(raw_source, _HTTPS_JWT_KEYS)
                source = ApprovedJwksSource(
                    profile_ref=profile_ref,
                    source_id=_text(remote["source_id"]),
                    uri=_text(remote["uri"]),
                    ttl_seconds=remote["ttl_seconds"],  # type: ignore[arg-type]
                    timeout_seconds=remote["timeout_seconds"],  # type: ignore[arg-type]
                    max_response_bytes=remote["max_response_bytes"],  # type: ignore[arg-type]
                    max_keys=remote["max_keys"],  # type: ignore[arg-type]
                )
                keys = HttpsJwtKeySource(
                    source=source,
                    allowed_ips=tuple(_text(ip) for ip in _sequence(remote["allowed_ips"])),
                )
            else:
                raise ValueError("unapproved JWT key source kind")
            profiles.append(JwtTrustBinding(profile=profile, keys=keys))
        except (ValueError, TypeError, AttributeError):
            raise ConfigurationRejected("invalid JWT trust configuration") from None
    return tuple(profiles)


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
    if not isinstance(mapping, Mapping):
        raise ConfigurationRejected("invalid configuration fields")
    version = mapping.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise ConfigurationRejected("unsupported configuration schema")
    expected_keys = _ROOT_KEYS if version == 1 else _ROOT_KEYS_V2
    if set(mapping) != expected_keys:
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
            jwt_profiles=(_parse_jwt_profiles(mapping["jwt_profiles"]) if version == 2 else ()),
        )
    except (ValueError, TypeError):
        raise ConfigurationRejected("configuration bootstrap rejected") from None


_MAX_CONFIG_JSON_BYTES = 262144
_MAX_CONFIG_JSON_NODES = 8192


def _unique_json_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicates at ANY depth before a dict can erase evidence."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationRejected("duplicate configuration member")
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> object:
    raise ConfigurationRejected("invalid JSON configuration constant")


def load_approved_json_configuration(
    raw: bytes,
    *,
    provenance: SourceProvenance,
    policy: SourcePolicy,
    generation: ConfigurationGeneration,
) -> ConfigurationSnapshot:
    """Safely decode one host-approved JSON document to the strict mapping API.

    An already-materialized dict cannot reveal duplicate JSON member names.
    Use this entrypoint when JSON ambiguity must be detected before the
    security-sensitive source/profile validation. No file/env/network reads.
    """
    if not isinstance(policy, SourcePolicy):
        raise ConfigurationRejected("invalid source policy")
    policy.admit(provenance)
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_CONFIG_JSON_BYTES:
        raise ConfigurationRejected("invalid JSON configuration byte budget")
    try:
        document = cast(
            object,
            json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_unique_json_members,
                parse_constant=_reject_json_constant,
            ),
        )
    except ConfigurationRejected:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise ConfigurationRejected("invalid JSON configuration") from None
    if not isinstance(document, dict) or not all(isinstance(key, str) for key in document):
        raise ConfigurationRejected("expected JSON configuration object")
    visited = 0

    def visit(node: object, depth: int) -> None:
        nonlocal visited
        visited += 1
        if visited > _MAX_CONFIG_JSON_NODES or depth > 12:
            raise ConfigurationRejected("JSON configuration complexity exceeded")
        if isinstance(node, dict):
            for key, value in node.items():
                if not isinstance(key, str):
                    raise ConfigurationRejected("invalid JSON configuration member")
                visit(value, depth + 1)
        elif isinstance(node, list):
            for value in node:
                visit(value, depth + 1)
        elif isinstance(node, float) and not math.isfinite(node):
            raise ConfigurationRejected("invalid JSON configuration number")

    visit(document, 0)
    return load_approved_configuration(
        cast(dict[str, object], document),
        provenance=provenance,
        policy=policy,
        generation=generation,
    )
