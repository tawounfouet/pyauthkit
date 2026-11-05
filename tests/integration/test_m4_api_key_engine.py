"""M4 PR-07C real HMAC -> scoped record -> M2 policy integration tests.

All keys, HMACs and records are synthetic and generated for this test only.
No actual host storage, concurrency CAS or deployed HTTP proxy is qualified.
"""

import asyncio
import base64
from datetime import UTC, datetime

import pytest

from pyauthkit.adapters.api_key_authenticator import ApiKeyAuthenticator
from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistryBuilder
from pyauthkit.domain.api_key import (
    ApiKeyAmbiguous,
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordStatus,
    ApiKeyUnavailable,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import ClaimedIdentity, PrincipalType, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthError, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.api_key_crypto import ApiKeyProtectionKey
from pyauthkit.ports.events import AuthenticationEvent

SCOPE = TrustedScopeRef("tenant-a:production")
OTHER_SCOPE = TrustedScopeRef("tenant-b:production")
KEY_REF = "hmac-v1"
KEY_BYTES = bytes(range(32, 64))
SECRET = bytes(range(32))
SELECTOR = bytes(range(16))
DIGEST_A = bytes.fromhex("540574633838c98c95e6afd36e8712768ade3a211ebf7bed39f55caccad22184")
WHEN = datetime(2026, 11, 5, tzinfo=UTC)
EXPIRY = datetime(2027, 11, 5, tzinfo=UTC)


def _encode(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def _wire(secret: bytes = SECRET) -> bytes:
    return b"ak1." + _encode(SELECTOR) + b"." + _encode(secret)


def _record(
    *,
    status: ApiKeyRecordStatus = ApiKeyRecordStatus.ACTIVE,
    scope: TrustedScopeRef = SCOPE,
    expiry: datetime | None = EXPIRY,
    not_before: datetime | None = None,
    version: int = 1,
) -> ApiKeyVerifierRecord:
    return ApiKeyVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("service-a", "issuer-a", scope),
        principal_type=PrincipalType.SERVICE,
        key_id=_encode(SELECTOR).decode("ascii"),
        verifier_digest=DIGEST_A,
        verifier_algorithm="hmac-sha256",
        protection_key_ref=KEY_REF,
        status=status,
        version=version,
        not_before=ObservedAt(not_before) if not_before is not None else None,
        expires_at=ObservedAt(expiry) if expiry is not None else None,
    )


class FixedClock:
    def __init__(self, instant: datetime = WHEN) -> None:
        self.instant = instant

    def now(self) -> datetime:
        return self.instant


class ControlledGuard:
    def __init__(self) -> None:
        self.permit: object = True
        self.outage = False
        self.calls: list[tuple[TrustedScopeRef, str | None]] = []

    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        key_id: str | None,
    ) -> bool:
        self.calls.append((scope_ref, key_id))
        if self.outage:
            raise RuntimeError("SENSITIVE HOST ERROR")
        return self.permit  # type: ignore[return-value]


class ControlledOwner:
    def __init__(self, record: ApiKeyVerifierRecord | None = None) -> None:
        self.records = [record] if record is not None else []
        self.outage = False
        self.freshness_outage = False
        self.lookups: list[tuple[TrustedScopeRef, str]] = []
        self.current_checks = 0

    async def resolve(self, *, scope_ref: TrustedScopeRef, key_id: str):
        self.lookups.append((scope_ref, key_id))
        if self.outage:
            return ApiKeyUnavailable()
        matches = [
            row for row in self.records if row.scope_ref == scope_ref and row.key_id == key_id
        ]
        if len(matches) == 0:
            return ApiKeyMissing()
        if len(matches) > 1:
            return ApiKeyAmbiguous()
        return ApiKeyFound(matches[0])

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        self.current_checks += 1
        if self.freshness_outage:
            raise RuntimeError("SENSITIVE STORE ERROR")
        return len(self.records) == 1 and self.records[0] is record


class ControlledKeySource:
    def __init__(self) -> None:
        self.outage = False
        self.calls = 0

    async def get_key(
        self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
    ) -> ApiKeyProtectionKey | None:
        self.calls += 1
        if self.outage:
            raise RuntimeError("SENSITIVE KEY SOURCE ERROR")
        if scope_ref == SCOPE and protection_key_ref == KEY_REF:
            return ApiKeyProtectionKey(KEY_BYTES)
        return None


class CollectedEvents:
    def __init__(self) -> None:
        self.items: list[AuthenticationEvent] = []

    async def emit(self, event: AuthenticationEvent) -> None:
        self.items.append(event)


class Harness:
    def __init__(
        self,
        *,
        record: ApiKeyVerifierRecord | None = None,
        final_allow: bool | None = True,
        clock: FixedClock | None = None,
    ) -> None:
        self.owner = ControlledOwner(record if record is not None else _record())
        self.guard = ControlledGuard()
        self.key_source = ControlledKeySource()
        self.clock = clock if clock is not None else FixedClock()
        self.events = CollectedEvents()
        self.catalog = HostTrustCatalog(
            [
                HostBinding(
                    "route-a",
                    SCOPE,
                    TrustProfileRef("api-profile", "v1", SCOPE),
                    frozenset({EvidenceMethod.API_KEY}),
                )
            ]
        )
        self.proof = HmacApiKeyVerifier(
            key_source=self.key_source, approved_refs={SCOPE: frozenset({KEY_REF})}
        )
        self.authenticator = ApiKeyAuthenticator(
            resolver=self.owner,
            proof_verifier=self.proof,
            attempt_guard=self.guard,
            clock=self.clock,
        )
        registry = AuthenticatorRegistryBuilder()
        registry.register(self.authenticator)
        self.engine = AuthenticationEngine(
            policy=AuthenticationPolicyGate(
                self.catalog,
                final_rule=(None if final_allow is None else lambda _subject, _entry: final_allow),
            ),
            registry=registry.freeze(),
            event_sink=self.events,
        )

    def request(
        self, raw: bytes | None = None, claimed_tenant: str | None = None
    ) -> AuthenticationRequest:
        hint = (
            ClaimedIdentity("service", "untrusted", claimed_tenant=claimed_tenant)
            if claimed_tenant is not None
            else None
        )
        return AuthenticationRequest(
            PresentedEvidence(EvidenceMethod.API_KEY, raw if raw is not None else _wire()),
            CorrelationId("m4-integration"),
            claimed_identity=hint,
            # A caller-supplied timestamp is untrusted and must not override host UTC.
            observed_at=ObservedAt(datetime(2030, 1, 1, tzinfo=UTC)),
        )

    def authenticate(self, request: AuthenticationRequest | None = None):
        return asyncio.run(
            self.engine.authenticate(
                self.request() if request is None else request,
                entry=self.catalog.resolve_for_host_route("route-a"),
            )
        )


@pytest.mark.integration
def test_full_secret_hmac_and_explicit_m2_allow_produce_authenticated() -> None:
    harness = Harness()
    result = harness.authenticate()
    assert isinstance(result, Authenticated)
    assert result.principal.subject.scope_ref == SCOPE
    assert result.principal.subject.subject_id == "service-a"
    assert result.principal.method is EvidenceMethod.API_KEY
    assert harness.owner.current_checks == 1
    assert [event.result_status for event in harness.events.items] == ["AUTHENTICATED"]


@pytest.mark.security
@pytest.mark.parametrize("final_allow", [None, False])
def test_valid_proof_cannot_bypass_final_policy(final_allow: bool | None) -> None:
    harness = Harness(final_allow=final_allow)
    result = harness.authenticate()
    assert isinstance(result, Rejected)
    assert harness.owner.current_checks == 1
    assert not hasattr(result, "principal")


@pytest.mark.security
def test_one_byte_secret_mutation_never_authenticates() -> None:
    harness = Harness()
    changed = bytearray(SECRET)
    changed[-1] ^= 0x01
    result = harness.authenticate(harness.request(raw=_wire(bytes(changed))))
    assert isinstance(result, Rejected)
    assert harness.owner.current_checks == 0
    assert harness.key_source.calls == 1


@pytest.mark.security
def test_malformed_bearer_is_guarded_but_never_looked_up() -> None:
    harness = Harness()
    result = harness.authenticate(harness.request(raw=b"ak1.invalid.truncated"))
    assert isinstance(result, Rejected)
    assert harness.guard.calls == [(SCOPE, None)]
    assert harness.owner.lookups == []
    assert harness.key_source.calls == 0


@pytest.mark.security
@pytest.mark.parametrize("not_admitted", [False, None, 1])
def test_guard_requires_exact_bool_true(not_admitted: object) -> None:
    harness = Harness()
    harness.guard.permit = not_admitted
    result = harness.authenticate()
    assert isinstance(result, Rejected)
    assert harness.owner.lookups == []


@pytest.mark.security
def test_guard_outage_is_technical_not_permissive() -> None:
    harness = Harness()
    harness.guard.outage = True
    result = harness.authenticate()
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert harness.owner.lookups == []


@pytest.mark.security
def test_missing_selector_never_reaches_proof() -> None:
    harness = Harness()
    harness.owner.records.clear()
    result = harness.authenticate()
    assert isinstance(result, Rejected)
    assert harness.key_source.calls == 0


@pytest.mark.security
def test_ambiguous_records_cannot_pick_first() -> None:
    harness = Harness()
    harness.owner.records.append(_record())
    result = harness.authenticate()
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
    assert harness.key_source.calls == 0


@pytest.mark.security
def test_store_unavailable_is_technical_error() -> None:
    harness = Harness()
    harness.owner.outage = True
    result = harness.authenticate()
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


@pytest.mark.security
@pytest.mark.parametrize(
    "status",
    [
        ApiKeyRecordStatus.DISABLED,
        ApiKeyRecordStatus.SUSPENDED,
        ApiKeyRecordStatus.REVOKED,
        ApiKeyRecordStatus.EXPIRED,
    ],
)
def test_inactive_record_fails_before_cryptography(status: ApiKeyRecordStatus) -> None:
    harness = Harness(record=_record(status=status))
    assert isinstance(harness.authenticate(), Rejected)
    assert harness.key_source.calls == 0


@pytest.mark.security
@pytest.mark.parametrize(
    "record",
    [
        _record(expiry=None),
        _record(expiry=WHEN),
        _record(expiry=datetime(2026, 11, 4, tzinfo=UTC)),
        _record(not_before=datetime(2026, 11, 6, tzinfo=UTC)),
    ],
)
def test_missing_expiry_expired_or_not_yet_valid_rejected(record: ApiKeyVerifierRecord) -> None:
    harness = Harness(record=record)
    result = harness.authenticate()
    assert isinstance(result, Rejected)
    assert harness.key_source.calls == 0


@pytest.mark.security
def test_post_hmac_revocation_version_change_blocks_verified_outcome() -> None:
    harness = Harness()
    real_proof = harness.proof

    class RevokeAfterProof:
        async def verify(self, *, scope_ref, presented, record) -> bool:
            match = await real_proof.verify(scope_ref=scope_ref, presented=presented, record=record)
            harness.owner.records[:] = [_record(status=ApiKeyRecordStatus.REVOKED, version=2)]
            return match

    harness.authenticator = ApiKeyAuthenticator(
        resolver=harness.owner,
        proof_verifier=RevokeAfterProof(),
        attempt_guard=harness.guard,
        clock=harness.clock,
    )
    registry = AuthenticatorRegistryBuilder()
    registry.register(harness.authenticator)
    harness.engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(harness.catalog, final_rule=lambda _subject, _entry: True),
        registry=registry.freeze(),
    )
    result = harness.authenticate()
    assert isinstance(result, Rejected)
    assert harness.owner.current_checks == 1


@pytest.mark.security
def test_inflight_time_expiry_blocks_success_after_hmac() -> None:
    harness = Harness(record=_record(expiry=datetime(2026, 11, 6, tzinfo=UTC)))
    proof = harness.proof

    class AdvanceClockAfterProof:
        async def verify(self, *, scope_ref, presented, record) -> bool:
            match = await proof.verify(scope_ref=scope_ref, presented=presented, record=record)
            harness.clock.instant = datetime(2026, 11, 6, tzinfo=UTC)
            return match

    authenticator = ApiKeyAuthenticator(
        resolver=harness.owner,
        proof_verifier=AdvanceClockAfterProof(),
        attempt_guard=harness.guard,
        clock=harness.clock,
    )
    registry = AuthenticatorRegistryBuilder()
    registry.register(authenticator)
    harness.engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(harness.catalog, final_rule=lambda _subject, _entry: True),
        registry=registry.freeze(),
    )
    assert isinstance(harness.authenticate(), Rejected)


@pytest.mark.security
def test_freshness_source_outage_is_technical() -> None:
    harness = Harness()
    harness.owner.freshness_outage = True
    result = harness.authenticate()
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


@pytest.mark.security
def test_key_source_outage_is_technical() -> None:
    harness = Harness()
    harness.key_source.outage = True
    result = harness.authenticate()
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE


@pytest.mark.security
def test_mismatched_tenant_claim_rejected_by_m2_preflight() -> None:
    harness = Harness()
    result = harness.authenticate(harness.request(claimed_tenant="tenant-b:production"))
    assert isinstance(result, Rejected)
    assert harness.guard.calls == []
    assert harness.owner.lookups == []


@pytest.mark.security
def test_foreign_tenant_record_does_not_pass_scope_guard() -> None:
    harness = Harness()
    harness.owner.records[:] = [_record(scope=OTHER_SCOPE)]
    assert isinstance(harness.authenticate(), Rejected)
    assert harness.key_source.calls == 0


@pytest.mark.security
def test_redacted_event_has_no_secret_or_id_in_repr() -> None:
    harness = Harness()
    harness.authenticate()
    assert len(harness.events.items) == 1
    assert "service-a" not in repr(harness.events.items[0])
    assert "tenant-a" not in repr(harness.events.items[0])
    assert "AAECAwQ" not in repr(harness.events.items[0])
    assert "012345" not in repr(harness.events.items[0])


@pytest.mark.security
def test_authenticator_cannot_be_constructed_without_guard() -> None:
    harness = Harness()
    with pytest.raises(ValueError, match="required"):
        ApiKeyAuthenticator(
            resolver=harness.owner, proof_verifier=harness.proof, attempt_guard=None
        )


@pytest.mark.security
def test_m4_not_before_exact_utc_boundary_is_conditionally_admissible() -> None:
    """M4-T10: before is denied, at the inclusive nbf boundary policy may allow."""
    record = _record(not_before=WHEN)
    too_early = Harness(
        record=record,
        clock=FixedClock(datetime(2026, 11, 4, tzinfo=UTC)),
    )
    assert isinstance(too_early.authenticate(), Rejected)
    at_boundary = Harness(record=record, clock=FixedClock(WHEN))
    assert isinstance(at_boundary.authenticate(), Authenticated)
    assert at_boundary.owner.current_checks == 1


@pytest.mark.security
def test_m4_t04_selector_only_never_reaches_credential_owner() -> None:
    """M4-T04: a selector without a secret is not authentication evidence."""
    harness = Harness()
    raw = b"ak1." + _encode(SELECTOR) + b"."
    result = harness.authenticate(harness.request(raw=raw))
    assert isinstance(result, Rejected)
    assert harness.guard.calls == [(SCOPE, None)]
    assert harness.owner.lookups == []
    assert harness.key_source.calls == 0


@pytest.mark.security
def test_m4_t14_foreign_host_context_is_rejected_before_key_access() -> None:
    """M4-T14: M2 must own the context; a foreign catalog cannot inject it."""
    harness = Harness()
    foreign_catalog = HostTrustCatalog(
        [
            HostBinding(
                "foreign",
                OTHER_SCOPE,
                TrustProfileRef("api-profile", "v1", OTHER_SCOPE),
                frozenset({EvidenceMethod.API_KEY}),
            )
        ]
    )
    result = asyncio.run(
        harness.engine.authenticate(
            harness.request(), entry=foreign_catalog.resolve_for_host_route("foreign")
        )
    )
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
    assert harness.guard.calls == []
    assert harness.owner.lookups == []


@pytest.mark.security
def test_m4_t23_revoke_between_lookup_and_proof_never_promotes() -> None:
    """M4-T23: even a correct MAC computed after owner revocation is stale."""
    harness = Harness()
    actual_proof = harness.proof

    class RevokeBeforeProof:
        async def verify(self, *, scope_ref, presented, record) -> bool:
            harness.owner.records[:] = [
                _record(status=ApiKeyRecordStatus.REVOKED, version=2)
            ]
            return await actual_proof.verify(
                scope_ref=scope_ref, presented=presented, record=record
            )

    verifier = ApiKeyAuthenticator(
        resolver=harness.owner,
        proof_verifier=RevokeBeforeProof(),
        attempt_guard=harness.guard,
        clock=harness.clock,
    )
    registry = AuthenticatorRegistryBuilder()
    registry.register(verifier)
    harness.engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(
            harness.catalog, final_rule=lambda _subject, _entry: True
        ),
        registry=registry.freeze(),
    )
    result = harness.authenticate()
    assert isinstance(result, Rejected)
    assert harness.owner.current_checks == 1


@pytest.mark.security
def test_m4_t33_owner_timeout_cancels_inflight_lookup_without_late_success() -> None:
    """M4-T33: async owner cleanup is observed after engine timeout."""
    harness = Harness()

    class StuckOwner:
        def __init__(self) -> None:
            self.started = False
            self.cancelled = False

        async def resolve(self, *, scope_ref, key_id):
            self.started = True
            try:
                await asyncio.sleep(3600)
            finally:
                self.cancelled = True

        async def is_current(self, *, record):
            raise AssertionError("must never reach freshness")

    owner = StuckOwner()
    verifier = ApiKeyAuthenticator(
        resolver=owner,
        proof_verifier=harness.proof,
        attempt_guard=harness.guard,
        clock=harness.clock,
    )
    registry = AuthenticatorRegistryBuilder()
    registry.register(verifier)
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(
            harness.catalog, final_rule=lambda _subject, _entry: True
        ),
        registry=registry.freeze(),
        timeout_seconds=0.05,
    )
    result = asyncio.run(
        engine.authenticate(
            harness.request(),
            entry=harness.catalog.resolve_for_host_route("route-a"),
        )
    )
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert owner.started and owner.cancelled
    assert not hasattr(result, "principal")


@pytest.mark.security
def test_m4_t36_registry_with_only_password_never_falls_back() -> None:
    """M4-T36: absence of API_KEY cannot invoke an unrelated method."""
    harness = Harness()

    class PasswordOnly:
        @property
        def method(self) -> EvidenceMethod:
            return EvidenceMethod.PASSWORD

        async def verify(self, request, context):
            raise AssertionError("API_KEY request must not reach PASSWORD")

    registry = AuthenticatorRegistryBuilder()
    registry.register(PasswordOnly())
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(
            harness.catalog, final_rule=lambda _subject, _entry: True
        ),
        registry=registry.freeze(),
    )
    result = asyncio.run(
        engine.authenticate(
            harness.request(),
            entry=harness.catalog.resolve_for_host_route("route-a"),
        )
    )
    assert isinstance(result, AuthError)
    assert result.error_code is TechnicalErrorCode.INVALID_TRUST_CONFIGURATION
