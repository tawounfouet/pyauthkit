"""Explicit bounded best-effort audit delivery for M2 compatibility."""

import asyncio
import math

from pyauthkit.ports.events import AuthenticationEvent, AuthenticationEventSink


class BoundedBestEffortAuditSink:
    """A bounded submission call, NOT a proof that an event persisted."""

    __slots__ = ("_delegate", "_timeout")

    def __init__(self, delegate: AuthenticationEventSink, *, timeout_seconds: float = 1.0):
        if (
            not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 10
        ):
            raise ValueError("invalid audit timeout")
        self._delegate = delegate
        self._timeout = float(timeout_seconds)

    async def emit(self, event: AuthenticationEvent) -> None:
        async with asyncio.timeout(self._timeout):
            await self._delegate.emit(event)

    def __repr__(self) -> str:
        return "BoundedBestEffortAuditSink(<non-durable>)"
