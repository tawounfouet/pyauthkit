"""Explicit async authentication pipeline with two mandatory policy checks.

M2 ships no production verifier. Test-only fakes establish the synthetic
positive path. No session, token, IAM account or permission is issued here.
"""

import asyncio
import math
import time
from collections.abc import Callable
from typing import Literal

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.outcome import (
    ErrorOutcome,
    RejectedOutcome,
    VerifiedOutcome,
    normalize_non_success,
)
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, AuthenticationResult, AuthError, Rejected
from pyauthkit.ports.authenticator import AuthenticatorLookup, VerificationContext
from pyauthkit.ports.events import AuthenticationEvent, AuthenticationEventSink

from ._verification import _verified_matches_attempt
from .host_context import TrustedEntryContext
from .policy import AuthenticationPolicyGate, VerificationPermitted


class AuthenticationEngine:
    """Per-attempt host trust -> preflight -> verifier -> final policy -> audit."""

    __slots__ = ("_policy", "_registry", "_timeout_seconds", "_monotonic", "_sink")

    def __init__(
        self,
        *,
        policy: AuthenticationPolicyGate,
        registry: AuthenticatorLookup,
        timeout_seconds: float = 3.0,
        monotonic: Callable[[], float] | None = None,
        event_sink: AuthenticationEventSink | None = None,
    ) -> None:
        if not isinstance(policy, AuthenticationPolicyGate):
            raise ValueError("invalid authentication policy gate")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("invalid verification timeout")
        object.__setattr__(self, "_policy", policy)
        object.__setattr__(self, "_registry", registry)
        object.__setattr__(self, "_timeout_seconds", timeout_seconds)
        object.__setattr__(
            self, "_monotonic", monotonic if monotonic is not None else time.monotonic
        )
        object.__setattr__(self, "_sink", event_sink)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("authentication engine composition cannot be mutated")

    async def authenticate(
        self, request: AuthenticationRequest, *, entry: TrustedEntryContext
    ) -> AuthenticationResult:
        """The only ordinary engine entrypoint; no supplied outcomes or permissions."""
        if not isinstance(request, AuthenticationRequest):
            raise ValueError("invalid authentication request")
        start = self._monotonic()
        try:
            preflight = self._policy.preflight(request, entry=entry)
            if isinstance(preflight, (Rejected, AuthError)):
                result: AuthenticationResult = preflight
            elif isinstance(preflight, VerificationPermitted):
                result = await self._verify(request, entry=entry)
            else:
                result = AuthError(request.correlation_id, TechnicalErrorCode.INTERNAL_ERROR)
        except asyncio.CancelledError:
            raise
        except Exception:
            result = AuthError(request.correlation_id, TechnicalErrorCode.INTERNAL_ERROR)

        await self._emit_event(request.evidence.method, result, request, start)
        return result

    async def _verify(
        self, request: AuthenticationRequest, *, entry: TrustedEntryContext
    ) -> AuthenticationResult:
        try:
            authenticator = self._registry.resolve(request.evidence.method)
        except Exception:
            return AuthError(request.correlation_id, TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)

        context = VerificationContext(
            entry.scope_ref,
            entry.profile_ref,
            request.evidence.method,
            request.correlation_id,
            object(),
        )
        try:
            async with asyncio.timeout(self._timeout_seconds):
                outcome = await authenticator.verify(request, context)
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            return AuthError(request.correlation_id, TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        except DomainTechnicalError as error:
            return AuthError(request.correlation_id, error.code)
        except Exception:
            return AuthError(request.correlation_id, TechnicalErrorCode.INTERNAL_ERROR)

        if isinstance(outcome, (RejectedOutcome, ErrorOutcome)):
            return normalize_non_success(outcome, correlation_id=request.correlation_id)
        if not isinstance(outcome, VerifiedOutcome):
            return AuthError(request.correlation_id, TechnicalErrorCode.INTERNAL_ERROR)
        if not _verified_matches_attempt(outcome, context):
            return AuthError(request.correlation_id, TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        return self._policy.final_decision(request, entry=entry, context=context, outcome=outcome)

    async def _emit_event(
        self,
        method: EvidenceMethod,
        result: AuthenticationResult,
        request: AuthenticationRequest,
        start: float,
    ) -> None:
        if self._sink is None:
            return
        status: Literal["AUTHENTICATED", "REJECTED", "ERROR"]
        if isinstance(result, Authenticated):
            status = "AUTHENTICATED"
        elif isinstance(result, Rejected):
            status = "REJECTED"
        else:
            status = "ERROR"
        event = AuthenticationEvent(
            correlation_id=request.correlation_id,
            method=method,
            result_status=status,
            duration_ms=max(0.0, (self._monotonic() - start) * 1000),
        )
        try:
            await self._sink.emit(event)
        except asyncio.CancelledError:
            raise
        except Exception:
            # M2 best-effort: mandatory/durable audit is explicitly out of scope.
            pass
