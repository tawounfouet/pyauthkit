"""Narrow, low-cardinality M6 metrics port, distinct from security audit.

Neither telemetry observation nor exporter acknowledgement is an audit receipt.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Protocol

from pyauthkit.domain.evidence import EvidenceMethod

type AuthnOutcome = Literal["AUTHENTICATED", "REJECTED", "ERROR"]


@dataclass(frozen=True, slots=True, repr=False)
class AuthenticationMetricsSample:
    """Only method, bounded outcome and duration. Never an identity or trace ID."""

    method: EvidenceMethod
    outcome: AuthnOutcome
    duration_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.method, EvidenceMethod):
            raise ValueError("invalid authentication metric method")
        if self.outcome not in ("AUTHENTICATED", "REJECTED", "ERROR"):
            raise ValueError("invalid authentication metric outcome")
        if (
            type(self.duration_seconds) not in (int, float)
            or not math.isfinite(self.duration_seconds)
            or not 0 <= self.duration_seconds <= 3600
        ):
            raise ValueError("invalid authentication metric duration")

    @property
    def labels(self) -> tuple[tuple[str, str], ...]:
        """Stable bounded labels. No untrusted issuer, tenant, URL or correlation."""
        return (("method", self.method.value), ("outcome", self.outcome))

    def __repr__(self) -> str:
        return "AuthenticationMetricsSample(<bounded, identity-free>)"


class AuthenticationMetricsRecorder(Protocol):
    """Host-owned adapter for a counter and duration histogram."""

    async def record_attempt(self, sample: AuthenticationMetricsSample) -> None: ...
