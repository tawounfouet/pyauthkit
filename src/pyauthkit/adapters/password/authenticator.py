"""M3 production password verifier SPI wired to the existing M2 final gate.

A cryptographic password match produces only an INTERNAL VerifiedOutcome.
The M2 policy gate remains the sole producer of final Authenticated results.
"""

import asyncio
from datetime import UTC, datetime

from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.identity import PrincipalType
from pyauthkit.domain.outcome import AuthenticatorOutcome, ErrorOutcome, RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.temporal import Clock, ObservedAt
from pyauthkit.password.capacity import KDFCapacityExhausted, KDFWorkerPool
from pyauthkit.password.records import (
    PasswordRecordAmbiguous,
    PasswordRecordFound,
    PasswordRecordMissing,
    PasswordRecordUnavailable,
    is_scoped_human_record,
    record_is_admissible,
)
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.ports.password_credentials import PasswordCredentialResolver
from pyauthkit.ports.password_hashing import (
    InvalidPasswordHash,
    PasswordHashProcessingError,
    PasswordHashVerifier,
)


class _UTCClock:
    """Default adapter clock, separate from the immutable domain model."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class PasswordAuthenticator:
    """Scoped resolver + real KDF + freshness check; no user management.

    [GoF: Strategy via M2 Authenticator SPI] [DIP: narrow resolver and KDF ports]
    The host must configure rate limiting, admission and trusted route bindings.
    """

    __slots__ = ("_resolver", "_hash_verifier", "_workers", "_dummy_hash", "_clock")

    def __init__(
        self,
        *,
        resolver: PasswordCredentialResolver,
        hash_verifier: PasswordHashVerifier,
        workers: KDFWorkerPool,
        dummy_hash: str,
        clock: Clock | None = None,
    ) -> None:
        if not isinstance(workers, KDFWorkerPool):
            raise ValueError("bounded KDF workers required")
        if not callable(resolver.resolve) or not callable(resolver.is_current):
            raise ValueError("approved scoped credential resolver required")
        if not callable(hash_verifier.verify) or not callable(hash_verifier.validate_hash):
            raise ValueError("password hash verifier required")
        if hash_verifier.max_memory_cost_kib > workers.max_memory_cost_kib:
            raise ValueError("KDF verifier exceeds worker memory envelope")
        # An operator supplies a real Argon2id hash created at trusted bootstrap.
        # The dummy's plaintext is NOT accepted by the missing-user path.
        hash_verifier.validate_hash(dummy_hash)
        self._resolver = resolver
        self._hash_verifier = hash_verifier
        self._workers = workers
        self._dummy_hash = dummy_hash
        self._clock = clock if clock is not None else _UTCClock()

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.PASSWORD

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> AuthenticatorOutcome:
        """Only return verified outcome after legitimate, scoped proof checks."""
        if (
            request.evidence.method is not EvidenceMethod.PASSWORD
            or context.method is not EvidenceMethod.PASSWORD
            or context.correlation_id != request.correlation_id
            or context.scope_ref != context.profile_ref.scope_ref
        ):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)

        hint = request.claimed_identity
        if hint is None:
            return await self._mask_rejection(request.evidence.opaque_payload)
        try:
            lookup = await self._resolver.resolve(
                scope_ref=context.scope_ref,
                identifier_kind=hint.identifier_kind,
                identifier_value=hint.identifier_value,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)

        if isinstance(lookup, PasswordRecordUnavailable):
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if isinstance(lookup, (PasswordRecordMissing, PasswordRecordAmbiguous)):
            return await self._mask_rejection(request.evidence.opaque_payload)
        if not isinstance(lookup, PasswordRecordFound):
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)

        record = lookup.record
        if not is_scoped_human_record(record, context.scope_ref):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        if not record_is_admissible(record, at=ObservedAt.from_clock(self._clock)):
            return await self._mask_rejection(request.evidence.opaque_payload)
        try:
            # Validate BEFORE submitting expensive native KDF work.
            self._hash_verifier.validate_hash(record.encoded_hash)
            match = await self._workers.run(
                lambda: self._hash_verifier.verify(
                    password=request.evidence.opaque_payload, encoded_hash=record.encoded_hash
                )
            )
        except asyncio.CancelledError:
            raise
        except KDFCapacityExhausted:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        except (InvalidPasswordHash, PasswordHashProcessingError):
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)
        if match is not True:
            return RejectedOutcome()

        try:
            current = await self._resolver.is_current(record=record)
        except asyncio.CancelledError:
            raise
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        # A stale or revoked record is never accepted, even after a good KDF.
        if current is not True or not record_is_admissible(
            record, at=ObservedAt.from_clock(self._clock)
        ):
            return RejectedOutcome()
        return _issue_verified_outcome(
            context,
            subject=record.subject_ref,
            principal_type=PrincipalType.HUMAN,
            verified_at=ObservedAt.from_clock(self._clock),
        )

    async def _mask_rejection(self, password: bytes) -> AuthenticatorOutcome:
        """Mitigate enumeration: perform an approved dummy KDF for absent users.

        Not a constant-time guarantee: HTTP response shaping, quota, account
        canonicalization and side-channel tests are duties of the host.
        """
        try:
            await self._workers.run(
                lambda: self._hash_verifier.verify(
                    password=password, encoded_hash=self._dummy_hash
                )
            )
        except asyncio.CancelledError:
            raise
        except KDFCapacityExhausted:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)
        return RejectedOutcome()
