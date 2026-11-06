"""M4 smoke: verify an authentic API Key with only the installed wheel.

The fixture uses synthetic bytes from a publicly documented HMAC vector.
This is a wheel import/composition smoke, NOT issuance, deployment or a GO.
"""

import asyncio
import base64
import hashlib
import hmac
from datetime import UTC, datetime

from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.domain.api_key import ApiKeyRecordStatus, ApiKeyVerifierRecord
from pyauthkit.domain.api_key_format import OpaqueApiKeyParser
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.ports.api_key_crypto import ApiKeyProtectionKey


def encoded(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


async def smoke() -> None:
    scope = TrustedScopeRef("tenant-a:production")
    selector = encoded(bytes(range(16)))
    secret = bytes(range(32))
    material = bytes(range(32, 64))
    presented = OpaqueApiKeyParser.parse(b"ak1." + selector + b"." + encoded(secret))
    assert presented is not None
    frame_parts = (scope.value.encode("ascii"), b"ak1", selector, secret)
    message = b"pyauthkit-api-key-v1\x00" + b"".join(
        len(part).to_bytes(4, "big") + part for part in frame_parts
    )
    digest = hmac.new(material, message, hashlib.sha256).digest()
    record = ApiKeyVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("service-test", "fixture-issuer", scope),
        principal_type=PrincipalType.SERVICE,
        key_id=selector.decode("ascii"),
        verifier_digest=digest,
        verifier_algorithm="hmac-sha256",
        protection_key_ref="fixture-v1",
        status=ApiKeyRecordStatus.ACTIVE,
        version=1,
        expires_at=ObservedAt(datetime(2027, 11, 5, tzinfo=UTC)),
    )

    class Source:
        async def get_key(
            self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
        ) -> ApiKeyProtectionKey | None:
            if scope_ref == scope and protection_key_ref == "fixture-v1":
                return ApiKeyProtectionKey(material)
            return None

    verifier = HmacApiKeyVerifier(
        key_source=Source(),
        approved_refs={scope: frozenset({"fixture-v1"})},
    )
    assert await verifier.verify(scope_ref=scope, presented=presented, record=record)
    bad_secret = bytearray(secret)
    bad_secret[-1] ^= 1
    changed = OpaqueApiKeyParser.parse(b"ak1." + selector + b"." + encoded(bytes(bad_secret)))
    assert changed is not None
    assert not await verifier.verify(scope_ref=scope, presented=changed, record=record)
    print("M4 ISOLATED WHEEL CRYPTO SMOKE PASS")


if __name__ == "__main__":
    asyncio.run(smoke())
