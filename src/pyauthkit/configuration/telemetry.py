"""M6 best-effort separation of audited events and low-cardinality metrics.

The existing M2 event carries a redacted correlation key. This layer projects
only a bounded metric sample into the metrics recorder and never forwards raw
event attributes as labels. Per-destination failures are isolated; neither
event submission nor metric observation proves durable audit.
"""

from __future__ import annotations

import asyncio
import math

from pyauthkit.ports.events import AuthenticationEvent, AuthenticationEventSink
from pyauthkit.ports.metrics import AuthenticationMetricsRecorder, AuthenticationMetricsSample


class BestEffortTelemetrySink:
    """Compose independent audit and metrics destinations with finite budgets."""

    __slots__ = ("_audit", "_metrics", "_timeout_seconds")

    _audit: AuthenticationEventSink | None
    _metrics: AuthenticationMetricsRecorder | None
    _timeout_seconds: float

    def __init__(
        self,
        *,
        audit_sink: AuthenticationEventSink | None,
        metrics_recorder: AuthenticationMetricsRecorder | None,
        timeout_seconds: float = 0.2,
    ) -> None:
        if audit_sink is None and metrics_recorder is None:
            raise ValueError("no telemetry destination configured")
        if (
            type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 0.4
        ):
            raise ValueError("invalid telemetry timeout")
        if audit_sink is not None and not callable(getattr(audit_sink, "emit", None)):
            raise ValueError("invalid audit sink")
        if metrics_recorder is not None and not callable(
            getattr(metrics_recorder, "record_attempt", None)
        ):
            raise ValueError("invalid metrics recorder")
        object.__setattr__(self, "_audit", audit_sink)
        object.__setattr__(self, "_metrics", metrics_recorder)
        object.__setattr__(self, "_timeout_seconds", float(timeout_seconds))

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("telemetry composition is immutable")

    def __repr__(self) -> str:
        return "BestEffortTelemetrySink(<non-durable, bounded labels>)"

    async def emit(self, event: AuthenticationEvent) -> None:
        """Never allow failure of audit to prevent a separate metrics attempt."""
        if not isinstance(event, AuthenticationEvent):
            raise ValueError("invalid authentication event")

        if self._audit is not None:
            try:
                async with asyncio.timeout(self._timeout_seconds):
                    await self._audit.emit(event)
            except asyncio.CancelledError:
                raise
            except Exception:
                # An audit submission error must not be exposed as successful
                # durable delivery; best-effort M2 policy controls the response.
                pass

        if self._metrics is not None:
            try:
                sample = AuthenticationMetricsSample(
                    method=event.method,
                    outcome=event.result_status,
                    duration_seconds=event.duration_ms / 1000,
                )
                async with asyncio.timeout(self._timeout_seconds):
                    await self._metrics.record_attempt(sample)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Never print the source event or provider exception.
                pass
