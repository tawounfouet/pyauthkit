"""M4 PR-07B: SPI contract is async and never emits final M2 AuthN results."""

import asyncio
import base64

import pytest

from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.domain.api_key import ApiKeyRecordStatus, ApiKeyVerifierRecord
from pyauthkit.domain.api_key_format import OpaqueApiKeyParser
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.ports.api_key_crypto import (
    ApiKeyProofVerifier,
    ApiKeyProtectionKey,
    ApiKeyProtectionKeySource,
)


@pytest.mark.contract
def test_plain_stdlib_hmac_adapter_satisfies_async_proof_port() -> None:
    scope = TrustedScopeRef("tenant-only")
    keyref = "hmac-v1"
    key_bytes = bytes(range(32, 64))
    secret_bytes = bytes(range(32))
    selector = base64.urlsafe_b64encode(bytes(range(16))).rstrip(b"=")
    raw = b"ak1." + selector + b"." + base64.urlsafe_b64encode(secret_bytes).rstrip(b"=")
    presented = OpaqueApiKeyParser.parse(raw)
    assert presented is not None

    class KeySource:
        async def get_key(
            self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
        ) -> ApiKeyProtectionKey | None:
            assert scope_ref == scope
            assert protection_key_ref == keyref
            return ApiKeyProtectionKey(key_bytes)

    source: ApiKeyProtectionKeySource = KeySource()
    adapter: ApiKeyProofVerifier = HmacApiKeyVerifier(
        key_source=source, approved_refs={scope: frozenset({keyref})}
    )
    # A negative digest is a cryptographic mismatch, never AuthN success.
    record = ApiKeyVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef(subject_id="svc", issuer_ref="test-issuer", scope_ref=scope),
        principal_type=PrincipalType.SERVICE,
        key_id=presented.key_id,
        verifier_digest=bytes(32),
        verifier_algorithm="hmac-sha256",
        protection_key_ref=keyref,
        status=ApiKeyRecordStatus.ACTIVE,
        version=1,
    )
    assert asyncio.run(adapter.verify(scope_ref=scope, presented=presented, record=record)) is False
