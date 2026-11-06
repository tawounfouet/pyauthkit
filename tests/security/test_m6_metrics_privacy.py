"""M6-T26: privacy-preserving bounded metrics labels and failure isolation."""

import asyncio

import pytest

from pyauthkit.adapters.audit_memory import InMemoryAuthenticationEventSink
from pyauthkit.adapters.metrics_memory import InMemoryAuthenticationMetricsRecorder
from pyauthkit.configuration.telemetry import BestEffortTelemetrySink
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.ports.events import AuthenticationEvent
from pyauthkit.ports.metrics import AuthenticationMetricsSample

CANARY = "RAW_JWT_AND_SUBJECT_NEVER_A_METRIC_LABEL"


def event(*, status: str = "AUTHENTICATED", duration: float = 7.0):
    return AuthenticationEvent(
        CorrelationId("trace-" + CANARY),
        EvidenceMethod.JWT,
        status,  # type: ignore[arg-type]
        duration,
    )


def test_m6_t26_metric_projection_omits_correlation_and_identity() -> None:
    audit = InMemoryAuthenticationEventSink()
    metrics = InMemoryAuthenticationMetricsRecorder()
    pipeline = BestEffortTelemetrySink(audit_sink=audit, metrics_recorder=metrics)
    asyncio.run(pipeline.emit(event()))
    assert len(audit.events) == len(metrics.samples) == 1
    sample = metrics.samples[0]
    assert sample.labels == (("method", "jwt"), ("outcome", "AUTHENTICATED"))
    assert sample.duration_seconds == 0.007
    assert CANARY not in repr(sample)
    assert CANARY not in repr(pipeline)
    assert CANARY not in repr(metrics)
    assert not hasattr(sample, "correlation_id")
    assert not hasattr(sample, "issuer")
    assert not hasattr(sample, "tenant")
    assert not hasattr(sample, "subject_id")


@pytest.mark.parametrize("status", ["AUTHENTICATED", "REJECTED", "ERROR"])
def test_m6_t26_only_fixed_outcome_dimensions(status: str) -> None:
    recorder = InMemoryAuthenticationMetricsRecorder()
    sink = BestEffortTelemetrySink(audit_sink=None, metrics_recorder=recorder)
    asyncio.run(sink.emit(event(status=status)))
    assert recorder.samples[0].labels == (("method", "jwt"), ("outcome", status))


def test_m6_t26_bad_event_duration_is_not_forwarded_as_metric() -> None:
    audit = InMemoryAuthenticationEventSink()
    metrics = InMemoryAuthenticationMetricsRecorder()
    sink = BestEffortTelemetrySink(audit_sink=audit, metrics_recorder=metrics)
    asyncio.run(sink.emit(event(duration=float("nan"))))
    assert len(audit.events) == 1
    assert metrics.samples == ()


def test_m6_t26_audit_failure_does_not_hide_metrics_or_change_status() -> None:
    class BrokenAudit:
        async def emit(self, _event: AuthenticationEvent) -> None:
            raise RuntimeError(CANARY)

    recorder = InMemoryAuthenticationMetricsRecorder()
    sink = BestEffortTelemetrySink(audit_sink=BrokenAudit(), metrics_recorder=recorder)
    asyncio.run(sink.emit(event()))
    assert len(recorder.samples) == 1


def test_m6_t26_metrics_failure_does_not_hide_audit() -> None:
    class BrokenRecorder:
        async def record_attempt(self, _sample: AuthenticationMetricsSample) -> None:
            raise RuntimeError(CANARY)

    audit = InMemoryAuthenticationEventSink()
    sink = BestEffortTelemetrySink(audit_sink=audit, metrics_recorder=BrokenRecorder())
    asyncio.run(sink.emit(event()))
    assert len(audit.events) == 1


def test_m6_t26_bounded_recorder_never_grows_without_limit() -> None:
    recorder = InMemoryAuthenticationMetricsRecorder(capacity=1)
    sink = BestEffortTelemetrySink(audit_sink=None, metrics_recorder=recorder)
    asyncio.run(sink.emit(event()))
    asyncio.run(sink.emit(event()))
    assert len(recorder.samples) == 1
    assert "non-durable" in repr(recorder)


def test_m6_t26_slow_audit_does_not_block_metrics() -> None:
    class SlowAudit:
        async def emit(self, _event: AuthenticationEvent) -> None:
            await asyncio.sleep(0.05)

    recorder = InMemoryAuthenticationMetricsRecorder()
    sink = BestEffortTelemetrySink(
        audit_sink=SlowAudit(),
        metrics_recorder=recorder,
        timeout_seconds=0.001,
    )
    asyncio.run(sink.emit(event()))
    assert len(recorder.samples) == 1


def test_m6_t26_cancellation_of_metrics_is_not_swallowed() -> None:
    class CancelledRecorder:
        async def record_attempt(self, _sample: AuthenticationMetricsSample) -> None:
            raise asyncio.CancelledError

    sink = BestEffortTelemetrySink(audit_sink=None, metrics_recorder=CancelledRecorder())
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(sink.emit(event()))


def test_m6_t26_invalid_metric_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError):
        AuthenticationMetricsSample(EvidenceMethod.JWT, "trace-123", 0.001)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        AuthenticationMetricsSample(EvidenceMethod.JWT, "ERROR", float("nan"))


def test_m6_t26_telemetry_requires_explicit_destination() -> None:
    with pytest.raises(ValueError):
        BestEffortTelemetrySink(audit_sink=None, metrics_recorder=None)
