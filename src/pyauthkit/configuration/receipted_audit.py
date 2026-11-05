"""M6 experimental commit-before-return host gateway.

This does NOT enable configuration mode `audit_delivery=required`. It
demonstrates the separate application contract needed for that future mode:
verify using unchanged M2, commit a result-bound attempt record, then return
the decision only when a validated local receipt has been received.

The host must route ALL relevant calls through this gateway, not through a
separately held M2 engine. Privileged in-process code is not a sandbox.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Callable, Iterable
from typing import Literal, Never, cast

from pyauthkit.adapters.audit_required_sqlite import SqliteRequiredAuditCommitter
from pyauthkit.application.host_context import HostTrustCatalog, TrustedEntryContext
from pyauthkit.application.policy import FinalRule
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthenticationResult, AuthError, Rejected
from pyauthkit.ports.authenticator import Authenticator
from pyauthkit.ports.events import AuthenticationEvent
from pyauthkit.ports.required_audit import (
    AuditAttemptId,
    AuditCommitReceipt,
    AuditDecisionRecord,
    RequiredAuditCommitter,
)

from .bootstrap import M6Runtime, compose_authentication_engine
from .models import ConfigurationRejected, ConfigurationSnapshot


class ReceiptedDecisionGateway:
    """Experimental host-side audit gateway for a single M6 generation."""

    __slots__ = ("_base", "_committer", "_monotonic")

    _base: M6Runtime
    _committer: RequiredAuditCommitter
    _monotonic: Callable[[], float]

    def __init__(
        self,
        *,
        base: M6Runtime,
        committer: RequiredAuditCommitter,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if (
            not isinstance(base, M6Runtime)
            or base.engine._sink is not None
            or not callable(getattr(committer, "commit", None))
            or not callable(monotonic)
        ):
            raise ConfigurationRejected("unapproved receipted audit gateway")
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "_committer", committer)
        object.__setattr__(self, "_monotonic", monotonic)

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("receipted gateway is immutable")

    def __repr__(self) -> str:
        return "ReceiptedDecisionGateway(<experimental, no-direct-engine>)"

    @property
    def catalog(self) -> HostTrustCatalog:
        return self._base.catalog

    async def authenticate(
        self,
        request: AuthenticationRequest,
        *,
        entry: TrustedEntryContext,
        attempt_id: AuditAttemptId,
    ) -> AuthenticationResult:
        """No authenticated result escapes without a matching commit receipt.

        A duplicate attempt ID is a technical failure, not permission to
        replay a previously successful result. An ambiguous cancellation may
        leave a committed record but never returns a positive response.
        """
        if not isinstance(request, AuthenticationRequest):
            raise ValueError("invalid authentication request")
        if not isinstance(attempt_id, AuditAttemptId) or not self.catalog.owns(entry):
            return AuthError(request.correlation_id, TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        started = self._monotonic()
        try:
            result = await self._base.engine.authenticate(request, entry=entry)
        except asyncio.CancelledError:
            raise
        except Exception:
            return AuthError(request.correlation_id, TechnicalErrorCode.INTERNAL_ERROR)
        status: Literal["AUTHENTICATED", "REJECTED", "ERROR"]
        if isinstance(result, Authenticated):
            # Authenticated.__new__ is deliberately annotated Never. Mypy
            # does not narrow this restricted runtime variant automatically.
            verified = cast(Authenticated, result)
            status = "AUTHENTICATED"
            subject = verified.principal.subject
            principal_type = verified.principal.principal_type
        elif isinstance(result, Rejected):
            status = "REJECTED"
            subject = None
            principal_type = None
        else:
            status = "ERROR"
            subject = None
            principal_type = None
            if not isinstance(result, AuthError):
                result = AuthError(request.correlation_id, TechnicalErrorCode.INTERNAL_ERROR)
        elapsed = (self._monotonic() - started) * 1000
        if not math.isfinite(elapsed) or not 0 <= elapsed <= 3_600_000:
            return AuthError(request.correlation_id, TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        try:
            record = AuditDecisionRecord(
                attempt_id=attempt_id,
                event=AuthenticationEvent(
                    correlation_id=request.correlation_id,
                    method=request.evidence.method,
                    result_status=status,
                    duration_ms=elapsed,
                ),
                profile=entry.profile_ref,
                subject=subject,
                principal_type=principal_type,
            )
            receipt = await self._committer.commit(record)
            if (
                not isinstance(receipt, AuditCommitReceipt)
                or receipt.attempt_id != attempt_id
                or receipt.result_status != status
            ):
                raise ValueError("untrusted audit commit receipt")
        except asyncio.CancelledError:
            raise
        except Exception:
            return AuthError(request.correlation_id, TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        return result


def compose_receipted_audit_gateway(
    snapshot: ConfigurationSnapshot,
    *,
    authenticators: Iterable[Authenticator],
    committer: RequiredAuditCommitter,
    final_rule: FinalRule | None = None,
    minimum_generation: int = 1,
) -> ReceiptedDecisionGateway:
    """Candidate boundary, not an approved `required` config composition.

    This stage supports only the generic v1 M2 route, with no secret refs
    or v2 JWT profile material. M4/M5-specific consumers require separate
    non-bypassable composition and independent verification before G7.
    """
    if not isinstance(snapshot, ConfigurationSnapshot) or snapshot.schema_version != 1:
        raise ConfigurationRejected("receipted audit candidate requires legacy v1")
    if snapshot.secret_refs or snapshot.jwt_profiles:
        raise ConfigurationRejected("receipted audit lacks approved consumer coverage")
    if type(committer) is not SqliteRequiredAuditCommitter:
        # Fakes and arbitrary port implementations must never activate the
        # candidate's positive route through the approved factory.
        raise ConfigurationRejected("unapproved auditable commit store")
    base = compose_authentication_engine(
        snapshot,
        authenticators=authenticators,
        final_rule=final_rule,
        event_sink=None,
        minimum_generation=minimum_generation,
    )
    return ReceiptedDecisionGateway(base=base, committer=committer)
