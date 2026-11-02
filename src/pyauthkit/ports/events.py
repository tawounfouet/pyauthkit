"""Minimal redacted event projection; neither persistence nor delivery guaranteed."""

from dataclasses import dataclass
from typing import Literal, Protocol

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.temporal import CorrelationId


@dataclass(frozen=True, slots=True, repr=False)
class AuthenticationEvent:
    """No identity claims, credential bytes, error repr or subject identifiers."""

    correlation_id: CorrelationId
    method: EvidenceMethod
    result_status: Literal["AUTHENTICATED", "REJECTED", "ERROR"]
    duration_ms: float

    def __repr__(self) -> str:
        return "AuthenticationEvent(<redacted>)"


class AuthenticationEventSink(Protocol):
    """Optional best-effort sink. Strong/durable audit is outside M2."""

    async def emit(self, event: AuthenticationEvent) -> None: ...
