"""M4 HMAC-SHA-256 proof adapter (PR-07B); never a final AuthN decision.

[ARCH: Ports & Adapters] [SECURITY: Domain Separation / Constant-Time Compare]
The trusted host configures scope -> approved protection-key references.
Unknown algorithms, versions and missing key material fail closed, without
a global fallback, another tenant's key or a "default" HMAC key.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Never

from pyauthkit.domain.api_key import ApiKeyVerifierRecord
from pyauthkit.domain.api_key_format import API_KEY_FORMAT_VERSION, ParsedOpaqueApiKey
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.ports.api_key_crypto import ApiKeyProtectionKey, ApiKeyProtectionKeySource

_ALLOWED_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_DOMAIN_TAG = b"pyauthkit-api-key-v1\x00"


def _frame(value: bytes) -> bytes:
    """Length-prefix each byte field, including scope and bearer secret."""
    return len(value).to_bytes(4, "big") + value


def _message(*, scope_ref: TrustedScopeRef, presented: ParsedOpaqueApiKey) -> bytes:
    """Unambiguous, version-bound HMAC message. Internal verifier detail."""
    return _DOMAIN_TAG + b"".join(
        _frame(part)
        for part in (
            scope_ref.value.encode("ascii"),
            presented.format_version.encode("ascii"),
            presented.key_id.encode("ascii"),
            presented.secret_bytes,
        )
    )


class HmacApiKeyVerifier:
    """Evaluate complete-secret HMAC under an operator-approved scope and key.

    The result is only a cryptographic boolean. Credential state, freshness,
    final policy and AuthenticatedPrincipal belong to PR-07C / M2.
    Key retrieval may be async (e.g. KMS); never perform blocking I/O in a
    synchronous callback on the event loop.
    """

    __slots__ = ("_key_source", "_approved_refs")

    _key_source: ApiKeyProtectionKeySource
    _approved_refs: Mapping[TrustedScopeRef, frozenset[str]]

    def __init__(
        self,
        *,
        key_source: ApiKeyProtectionKeySource,
        approved_refs: Mapping[TrustedScopeRef, frozenset[str]],
    ) -> None:
        if not callable(getattr(key_source, "get_key", None)):
            raise ValueError("API-key protection key source required")
        if not isinstance(approved_refs, Mapping) or not 1 <= len(approved_refs) <= 128:
            raise ValueError("nonempty approved key-ref policy required")
        snapshot: dict[TrustedScopeRef, frozenset[str]] = {}
        for scope_ref, refs in approved_refs.items():
            if not isinstance(scope_ref, TrustedScopeRef):
                raise ValueError("invalid approved scope")
            if (
                type(refs) is not frozenset
                or not 1 <= len(refs) <= 32
                or not all(
                    isinstance(ref, str) and _ALLOWED_REF.fullmatch(ref) for ref in refs
                )
            ):
                raise ValueError("invalid approved key-ref set")
            snapshot[scope_ref] = refs
        object.__setattr__(self, "_key_source", key_source)
        object.__setattr__(self, "_approved_refs", MappingProxyType(snapshot))

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("approved API-key verifier policy is immutable")

    def __repr__(self) -> str:
        return "HmacApiKeyVerifier(<redacted, operator-configured>)"

    async def verify(
        self,
        *,
        scope_ref: TrustedScopeRef,
        presented: ParsedOpaqueApiKey,
        record: ApiKeyVerifierRecord,
    ) -> bool:
        if not isinstance(scope_ref, TrustedScopeRef):
            raise ValueError("invalid host-approved scope")
        if not isinstance(presented, ParsedOpaqueApiKey):
            return False
        if not isinstance(record, ApiKeyVerifierRecord):
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if (
            record.scope_ref != scope_ref
            or record.subject_ref.scope_ref != scope_ref
            or record.key_id != presented.key_id
            or presented.format_version != API_KEY_FORMAT_VERSION
        ):
            return False
        if record.verifier_algorithm != "hmac-sha256" or len(record.verifier_digest) != 32:
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if record.protection_key_ref not in self._approved_refs.get(scope_ref, frozenset()):
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)

        key = await self._key_source.get_key(
            scope_ref=scope_ref, protection_key_ref=record.protection_key_ref
        )
        if key is None:
            raise DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if not isinstance(key, ApiKeyProtectionKey):
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)

        candidate_digest = hmac.new(
            key.material, _message(scope_ref=scope_ref, presented=presented), hashlib.sha256
        ).digest()
        # Both operands are exactly 32 bytes, never hex strings or prefixes.
        return hmac.compare_digest(candidate_digest, record.verifier_digest)
