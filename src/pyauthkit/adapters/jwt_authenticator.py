"""M5 JWT bearer authenticator implementing the existing M2 async SPI.

[GoF: Strategy] [ARCH: Ports & Adapters] [SECURITY: Signature Before Identity]
Host-approved profile -> strict JWS structure -> approved RSA key -> PyJWT
signature -> signed claims policy -> internal VerifiedOutcome. The existing M2
AuthenticationPolicyGate alone decides final authentication, never IAM access.
"""

from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime
from typing import Never

from pyauthkit.application._verification import _issue_verified_outcome
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.identity import ScopedSubjectRef
from pyauthkit.domain.jwt import TrustedJwtVerificationProfile, parse_compact_jws
from pyauthkit.domain.outcome import AuthenticatorOutcome, ErrorOutcome, RejectedOutcome
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.temporal import Clock, ObservedAt
from pyauthkit.ports.authenticator import VerificationContext
from pyauthkit.ports.jwt import (
    SignedTokenVerifier,
    TrustedJwtProfileResolver,
    VerificationKeyResolver,
)


class _UTCClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def _numeric_date(claims: dict[str, object], name: str, *, required: bool) -> float | None:
    value = claims.get(name)
    if value is None:
        if required:
            raise ValueError("missing required JWT date")
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 4102444800:
        raise ValueError("invalid JWT NumericDate")
    return float(value)


def _claims_match(
    claims: dict[str, object], profile: TrustedJwtVerificationProfile, *, now: float
) -> str | None:
    """Validate signed claims. Roles, scopes and tenant hints never grant access."""
    issuer = claims.get("iss")
    subject = claims.get("sub")
    audience = claims.get("aud")
    if type(issuer) is not str or issuer != profile.issuer:
        return None
    if type(subject) is not str or not 1 <= len(subject) <= 256 or not subject.strip():
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in subject):
        return None
    if type(audience) is str:
        if audience != profile.audience:
            return None
    elif type(audience) is list:
        if (
            not audience
            or not all(type(item) is str and item for item in audience)
            or profile.audience not in audience
        ):
            return None
    else:
        return None
    # A token that declares confirmation-key binding is not a plain bearer token.
    # M5 has no DPoP/mTLS proof verification capability.
    if "cnf" in claims:
        return None
    try:
        exp = _numeric_date(claims, "exp", required=True)
        nbf = _numeric_date(claims, "nbf", required=False)
        iat = _numeric_date(claims, "iat", required=profile.max_age_seconds is not None)
    except ValueError:
        return None
    if exp is None or now >= exp + profile.clock_skew_seconds:
        return None
    if nbf is not None and now + profile.clock_skew_seconds < nbf:
        return None
    if iat is not None:
        if iat > now + profile.clock_skew_seconds:
            return None
        if profile.max_age_seconds is not None and now - iat > profile.max_age_seconds:
            return None
    if "jti" in claims and (type(claims["jti"]) is not str or not claims["jti"]):
        return None
    return subject


class JWTAuthenticator:
    """Explicitly registered verifier. No implicit issuer, JWKS or final allow."""

    __slots__ = ("_profiles", "_keys", "_crypto", "_clock")

    def __init__(
        self,
        *,
        profile_resolver: TrustedJwtProfileResolver,
        key_resolver: VerificationKeyResolver,
        signature_verifier: SignedTokenVerifier,
        clock: Clock | None = None,
    ) -> None:
        if (
            not callable(getattr(profile_resolver, "resolve", None))
            or not callable(getattr(key_resolver, "resolve_key", None))
            or not callable(getattr(signature_verifier, "verify_signature", None))
            or (clock is not None and not callable(getattr(clock, "now", None)))
        ):
            raise ValueError("approved profile, key, crypto and clock contracts required")
        object.__setattr__(self, "_profiles", profile_resolver)
        object.__setattr__(self, "_keys", key_resolver)
        object.__setattr__(self, "_crypto", signature_verifier)
        object.__setattr__(self, "_clock", clock if clock is not None else _UTCClock())

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("JWT authenticator composition is immutable")

    def __repr__(self) -> str:
        return "JWTAuthenticator(<redacted, operator-configured>)"

    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.JWT

    async def verify(
        self, request: AuthenticationRequest, context: VerificationContext
    ) -> AuthenticatorOutcome:
        if (
            request.evidence.method is not EvidenceMethod.JWT
            or context.method is not EvidenceMethod.JWT
            or context.correlation_id != request.correlation_id
            or context.profile_ref.scope_ref != context.scope_ref
        ):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        try:
            profile = await self._profiles.resolve(profile_ref=context.profile_ref)
        except asyncio.CancelledError:
            raise
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if not isinstance(profile, TrustedJwtVerificationProfile) or (
            profile.scope_ref != context.scope_ref or profile.profile_ref != context.profile_ref
        ):
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)

        raw = request.evidence.opaque_payload
        parsed = parse_compact_jws(raw, max_token_bytes=profile.max_token_bytes)
        if parsed is None:
            return RejectedOutcome()
        header = parsed.protected_header
        if header["alg"] not in profile.allowed_algorithms or header["typ"] != profile.expected_typ:
            return RejectedOutcome()
        kid = header["kid"]
        if type(kid) is not str:
            return RejectedOutcome()
        try:
            key = await self._keys.resolve_key(
                profile=profile, kid_hint=kid, algorithm_hint="RS256"
            )
        except asyncio.CancelledError:
            raise
        except DomainTechnicalError as error:
            return ErrorOutcome(error.code)
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.DEPENDENCY_UNAVAILABLE)
        if key is None:
            return RejectedOutcome()
        if type(key) is not str:
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        try:
            verified_claims = await self._crypto.verify_signature(
                compact_jws=raw, approved_key=key, approved_algorithm="RS256"
            )
        except asyncio.CancelledError:
            raise
        except DomainTechnicalError as error:
            return ErrorOutcome(error.code)
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.INTERNAL_ERROR)
        if type(verified_claims) is not dict:
            return RejectedOutcome()
        try:
            verified_at = ObservedAt.from_clock(self._clock)
            subject_id = _claims_match(verified_claims, profile, now=verified_at.value.timestamp())
            if subject_id is None:
                return RejectedOutcome()
            subject = ScopedSubjectRef(subject_id, profile.issuer, context.scope_ref)
        except Exception:
            return ErrorOutcome(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION)
        return _issue_verified_outcome(
            context,
            subject=subject,
            principal_type=profile.principal_type,
            verified_at=verified_at,
        )
