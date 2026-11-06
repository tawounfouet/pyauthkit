"""M4 PR-07B: independent HMAC vector and adversarial full-secret checks."""

import asyncio
import base64
import copy
import pickle
from datetime import UTC, datetime

import pytest

from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.domain.api_key import ApiKeyRecordStatus, ApiKeyVerifierRecord
from pyauthkit.domain.api_key_format import OpaqueApiKeyParser, ParsedOpaqueApiKey
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import ObservedAt
from pyauthkit.ports.api_key_crypto import ApiKeyProtectionKey

SCOPE = TrustedScopeRef("tenant-a:production")
OTHER_SCOPE = TrustedScopeRef("tenant-b:production")
KEY_REF = "hmac-v1"
SERVER_KEY = bytes(range(32, 64))
SELECTOR = bytes(range(16))
SECRET = bytes(range(32))
# Independent output generated with OpenSSL HMAC-SHA256 on the explicit
# length-prefixed message documented in ADR-0016. No self-derived oracle.
OPENSSL_EXPECTED = bytes.fromhex("540574633838c98c95e6afd36e8712768ade3a211ebf7bed39f55caccad22184")


def _encode(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def _presented(selector: bytes = SELECTOR, secret: bytes = SECRET) -> ParsedOpaqueApiKey:
    raw = b"ak1." + _encode(selector) + b"." + _encode(secret)
    result = OpaqueApiKeyParser.parse(raw)
    assert isinstance(result, ParsedOpaqueApiKey)
    return result


def _record(
    scope: TrustedScopeRef = SCOPE,
    key_id: str = _presented().key_id,
    digest: bytes = OPENSSL_EXPECTED,
    key_ref: str = KEY_REF,
    algorithm: str = "hmac-sha256",
) -> ApiKeyVerifierRecord:
    return ApiKeyVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef(
            subject_id="service-1", issuer_ref="issuer-1", scope_ref=scope
        ),
        principal_type=PrincipalType.SERVICE,
        key_id=key_id,
        verifier_digest=digest,
        verifier_algorithm=algorithm,
        protection_key_ref=key_ref,
        status=ApiKeyRecordStatus.ACTIVE,
        version=1,
        not_before=ObservedAt(datetime(2026, 1, 1, tzinfo=UTC)),
    )


class ControlledKeySource:
    def __init__(self) -> None:
        self.keys: dict[tuple[TrustedScopeRef, str], ApiKeyProtectionKey] = {
            (SCOPE, KEY_REF): ApiKeyProtectionKey(SERVER_KEY),
        }
        self.calls: list[tuple[TrustedScopeRef, str]] = []

    async def get_key(
        self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
    ) -> ApiKeyProtectionKey | None:
        self.calls.append((scope_ref, protection_key_ref))
        return self.keys.get((scope_ref, protection_key_ref))


def _verifier(
    source: ControlledKeySource,
    policy: dict[TrustedScopeRef, frozenset[str]] | None = None,
) -> HmacApiKeyVerifier:
    return HmacApiKeyVerifier(
        key_source=source,
        approved_refs=policy or {SCOPE: frozenset({KEY_REF})},
    )


@pytest.mark.security
def test_independent_openssl_vector_accepts_full_key_only() -> None:
    source = ControlledKeySource()
    verifier = _verifier(source)
    assert asyncio.run(verifier.verify(scope_ref=SCOPE, presented=_presented(), record=_record()))
    assert source.calls == [(SCOPE, KEY_REF)]


@pytest.mark.security
@pytest.mark.parametrize("position", [0, 1, 15, 16, 31])
def test_one_byte_secret_mutation_never_matches(position: int) -> None:
    changed = bytearray(SECRET)
    changed[position] ^= 1
    assert not asyncio.run(
        _verifier(ControlledKeySource()).verify(
            scope_ref=SCOPE, presented=_presented(secret=bytes(changed)), record=_record()
        )
    )


@pytest.mark.security
def test_wrong_selector_even_with_correct_secret_fails_before_key_lookup() -> None:
    source = ControlledKeySource()
    changed = bytearray(SELECTOR)
    changed[-1] ^= 1
    result = asyncio.run(
        _verifier(source).verify(
            scope_ref=SCOPE, presented=_presented(selector=bytes(changed)), record=_record()
        )
    )
    assert result is False
    assert source.calls == []


@pytest.mark.security
def test_cross_tenant_record_never_matches_or_fetches_foreign_key() -> None:
    source = ControlledKeySource()
    assert not asyncio.run(
        _verifier(source).verify(
            scope_ref=SCOPE, presented=_presented(), record=_record(scope=OTHER_SCOPE)
        )
    )
    assert source.calls == []


@pytest.mark.security
def test_digest_cannot_be_replayed_under_another_approved_scope() -> None:
    source = ControlledKeySource()
    source.keys[(OTHER_SCOPE, KEY_REF)] = ApiKeyProtectionKey(SERVER_KEY)
    verifier = _verifier(source, {SCOPE: frozenset({KEY_REF}), OTHER_SCOPE: frozenset({KEY_REF})})
    assert not asyncio.run(
        verifier.verify(
            scope_ref=OTHER_SCOPE, presented=_presented(), record=_record(scope=OTHER_SCOPE)
        )
    )


@pytest.mark.security
def test_digest_tampering_is_rejected() -> None:
    tampered = bytearray(OPENSSL_EXPECTED)
    tampered[0] ^= 0x80
    assert not asyncio.run(
        _verifier(ControlledKeySource()).verify(
            scope_ref=SCOPE, presented=_presented(), record=_record(digest=bytes(tampered))
        )
    )


@pytest.mark.security
def test_unknown_hmac_key_reference_fails_closed_without_lookup() -> None:
    source = ControlledKeySource()
    with pytest.raises(DomainTechnicalError) as exc:
        asyncio.run(
            _verifier(source).verify(
                scope_ref=SCOPE, presented=_presented(), record=_record(key_ref="unapproved")
            )
        )
    assert exc.value.code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
    assert source.calls == []


@pytest.mark.security
def test_missing_approved_hmac_key_is_technical_failure() -> None:
    source = ControlledKeySource()
    source.keys.clear()
    with pytest.raises(DomainTechnicalError) as exc:
        asyncio.run(
            _verifier(source).verify(scope_ref=SCOPE, presented=_presented(), record=_record())
        )
    assert exc.value.code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


@pytest.mark.security
def test_unsupported_algorithm_has_no_fallback() -> None:
    source = ControlledKeySource()
    with pytest.raises(DomainTechnicalError) as exc:
        asyncio.run(
            _verifier(source).verify(
                scope_ref=SCOPE,
                presented=_presented(),
                record=_record(algorithm="sha256", digest=OPENSSL_EXPECTED),
            )
        )
    assert exc.value.code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
    assert source.calls == []


@pytest.mark.security
def test_invalid_protection_key_material_never_passes() -> None:
    with pytest.raises(ValueError):
        ApiKeyProtectionKey(b"short")
    with pytest.raises(ValueError):
        ApiKeyProtectionKey(bytearray(SERVER_KEY))  # type: ignore[arg-type]
    source = ControlledKeySource()
    source.keys[(SCOPE, KEY_REF)] = b"not material"  # type: ignore[assignment]
    with pytest.raises(DomainTechnicalError) as exc:
        asyncio.run(
            _verifier(source).verify(scope_ref=SCOPE, presented=_presented(), record=_record())
        )
    assert exc.value.code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION


@pytest.mark.security
def test_key_material_does_not_leak_in_repr_copy_or_pickle() -> None:
    key = ApiKeyProtectionKey(SERVER_KEY)
    assert "32" not in repr(key)
    assert "redacted" in repr(key)
    with pytest.raises(AttributeError):
        key._material = b"unsafe"  # type: ignore[misc]
    with pytest.raises(TypeError):
        copy.deepcopy(key)
    with pytest.raises(TypeError):
        pickle.dumps(key)


@pytest.mark.security
def test_protection_policy_is_immutable_and_scoped() -> None:
    source = ControlledKeySource()
    policy = {SCOPE: frozenset({KEY_REF})}
    verifier = _verifier(source, policy)
    policy[SCOPE] = frozenset({"unapproved"})
    assert asyncio.run(verifier.verify(scope_ref=SCOPE, presented=_presented(), record=_record()))
    with pytest.raises(AttributeError):
        verifier._key_source = source  # type: ignore[misc]


@pytest.mark.security
@pytest.mark.parametrize(
    "invalid",
    [
        {},
        {SCOPE: frozenset()},
        {SCOPE: {"hmac-v1"}},
        {"tenant-a": frozenset({"hmac-v1"})},
        {SCOPE: frozenset({"bad ref"})},
    ],
)
def test_unsafe_bootstrap_policies_are_rejected(invalid: object) -> None:
    with pytest.raises(ValueError):
        HmacApiKeyVerifier(
            key_source=ControlledKeySource(),
            approved_refs=invalid,  # type: ignore[arg-type]
        )


@pytest.mark.security
def test_verifier_never_returns_an_authenticated_principal() -> None:
    result = asyncio.run(
        _verifier(ControlledKeySource()).verify(
            scope_ref=SCOPE, presented=_presented(), record=_record()
        )
    )
    assert result is True
    assert type(result) is bool


@pytest.mark.security
def test_key_source_failure_never_falls_back() -> None:
    class BrokenSource:
        async def get_key(
            self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
        ) -> ApiKeyProtectionKey | None:
            raise DomainTechnicalError(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)

    verifier = HmacApiKeyVerifier(
        key_source=BrokenSource(), approved_refs={SCOPE: frozenset({KEY_REF})}
    )
    with pytest.raises(DomainTechnicalError) as exc:
        asyncio.run(verifier.verify(scope_ref=SCOPE, presented=_presented(), record=_record()))
    assert exc.value.code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


@pytest.mark.security
def test_cancellation_propagates_from_async_key_source() -> None:
    class CancellableSource:
        async def get_key(
            self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
        ) -> ApiKeyProtectionKey | None:
            raise asyncio.CancelledError

    verifier = HmacApiKeyVerifier(
        key_source=CancellableSource(), approved_refs={SCOPE: frozenset({KEY_REF})}
    )
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(verifier.verify(scope_ref=SCOPE, presented=_presented(), record=_record()))
