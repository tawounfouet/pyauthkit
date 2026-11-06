"""M4 PR-07C API key Authenticator, conforming to the M2 async SPI.

[GoF: Strategy] [ARCH: Ports & Adapters] [SECURITY: Fail Closed]
This adapter can only issue an INTERNAL VerifiedOutcome after full-secret
verification and post-proof version/state check. AuthenticationEngine + final
AuthenticationPolicyGate alone may produce Authenticated.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Never

from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.domain.api_key import (
    ApiKeyAmbiguous,
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordStatus,
    ApiKeyUnavailable,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.api_key_format import OpaqueApiKeyParser
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.outcome import AuthenticatorOutcome, ErrorOutcome, RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.temporal import Clock, ObservedAt
from pyauthkit.ports.api_key import ApiKeyCredentialResolver
from pyauthkit.ports.api_key_crypto import ApiKeyProofVerifier
from pyauthkit.ports.api_key_guard import ApiKeyAttemptGuard
from pyauthkit.ports.authenticator import VerificationContext


class _UTCClock:
    """Production UTC time source; tests may inject a deterministic clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


def _admissible(record: ApiKeyVerifierRecord, *, at: ObservedAt) -> bool:
    """Conservative time/state acceptance, never an IAM authorization grant.

    Current MVP rule: missing expiration cannot be a positive AuthN record.
    Lifetime and usage policies remain owned by the trusted host.
    """
    if record.status is not ApiKeyRecordStatus.ACTIVE:
        return False
    if record.expires_at is None or at.value >= record.expires_at.value:
        return False
    return record.not_before is None or at.value >= record.not_before.value


class ApiKeyAuthenticator:
    """Scoped lookup -> full-secret proof -> freshness -> INTERNAL outcome.

    The host must supply a non-permissive attempt guard, resolver, key source
    through proof verifier, and final M2 policy. No credentials are issued.
    """

    __slots__ = ("_resolver", "_proof", "_guard", "_clock")

    _resolver: ApiKeyCredentialResolver
    _proof: ApiKeyProofVerifier
    _guard: ApiKeyAttemptGuard
    _clock: Clock

    def __init__(
        self,
        *,
        resolver: ApiKeyCredentialResolver,
        proof_verifier: ApiKeyProofVerifier,
        attempt_guard: ApiKeyAttemptGuard,
        clock: Clock | None = None,
    ) -> None:
        if (
            not callable(getattr(resolver, "resolve", None))
            or not callable(getattr(resolver, "is_current", None))
            or not callable(getattr(proof_verifier, "verify", None))
            or not callable(getattr(attempt_guard, "admit", None))
        ):
            raise ValueError("scoped resolver, cryptographic verifier and guard required")
        if clock is not None and not callable(getattr(clock, "now", None)):
            raise ValueError("invalid authoritative clock")
        object.__setattr__(self, "_resolver", resolver)
        object.__setattr__(self, "_proof", proof_verifier)
        object.__setattr__(self, "_guard", attempt_guard)
        object.__setattr__(self, "_clock", clock if clock is not None else _UTCClock())

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("API key authenticator composition is immutable")

    def __repr__(self) -> str:
        return "ApiKeyAuthenticator(<redacted, operator-configured>)"

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    def _now(self) -> ObservedAt:
        try:
            return ObservedAt.from_clock(self._clock)
        except Exception:
            # Time is a trust input. Fail closed without leaking clock internals.
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION) from None

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> AuthenticatorOutcome:
        """Never trust request.observed_at or caller-selected tenant as a clock/scope."""
        if (
            request.evidence.method is not EvidenceMethod.API_KEY
            or context.method is not EvidenceMethod.API_KEY
            or context.correlation_id != request.correlation_id
            or context.scope_ref != context.profile_ref.scope_ref
        ):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)

        presented = OpaqueApiKeyParser.parse(request.evidence.opaque_payload)
        try:
            admitted = await self._guard.admit(
                scope_ref=context.scope_ref,
                correlation_id=context.correlation_id,
                key_id=presented.key_id if presented is not None else None,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if admitted is not True:
            return RejectedOutcome()
        if presented is None:
            return RejectedOutcome()

        try:
            lookup = await self._resolver.resolve(
                scope_ref=context.scope_ref, key_id=presented.key_id
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if isinstance(lookup, ApiKeyMissing):
            return RejectedOutcome()
        if isinstance(lookup, ApiKeyUnavailable):
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if isinstance(lookup, ApiKeyAmbiguous):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if not isinstance(lookup, ApiKeyFound):
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)

        record = lookup.record
        if (
            record.scope_ref != context.scope_ref
            or record.subject_ref.scope_ref != context.scope_ref
            or record.key_id != presented.key_id
        ):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if not _admissible(record, at=self._now()):
            return RejectedOutcome()

        try:
            matches = await self._proof.verify(
                scope_ref=context.scope_ref, presented=presented, record=record
            )
        except asyncio.CancelledError:
            raise
        except DomainTechnicalError as error:
            return ErrorOutcome(error.code)
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)
        if matches is not True:
            return RejectedOutcome()

        try:
            still_current = await self._resolver.is_current(record=record)
        except asyncio.CancelledError:
            raise
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        after_proof = self._now()
        if still_current is not True or not _admissible(record, at=after_proof):
            return RejectedOutcome()
        return _issue_verified_outcome(
            context,
            subject=record.subject_ref,
            principal_type=record.principal_type,
            verified_at=after_proof,
        )
