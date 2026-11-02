"""Immutable time and trace values with an injectable Clock contract."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

_TRACE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


@dataclass(frozen=True, slots=True, repr=False)
class CorrelationId:
    """Non-bearer trace key, generated or validated at the host boundary."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _TRACE_PATTERN.fullmatch(self.value):
            raise ValueError("invalid correlation identifier")

    def __repr__(self) -> str:
        return "CorrelationId(<redacted>)"


class Clock(Protocol):
    """Time source injected by the caller, not read implicitly by the domain."""

    def now(self) -> datetime: ...


@dataclass(frozen=True, slots=True)
class ObservedAt:
    """UTC instant. Naive or incompatible timestamps fail closed."""

    value: datetime

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, datetime)
            or self.value.tzinfo is None
            or self.value.utcoffset() is None
        ):
            raise ValueError("timezone-aware instant required")
        object.__setattr__(self, "value", self.value.astimezone(UTC))

    @classmethod
    def from_clock(cls, clock: Clock) -> "ObservedAt":
        """Use an injected clock. No hidden wall-clock access."""
        return cls(clock.now())
