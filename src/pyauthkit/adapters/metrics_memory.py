"""Bounded synthetic memory recorder for M6 metrics unit tests.

Not a Prometheus, OpenTelemetry or durable provider implementation.
"""

from pyauthkit.ports.metrics import AuthenticationMetricsSample


class InMemoryAuthenticationMetricsRecorder:
    __slots__ = ("_samples", "_capacity")

    def __init__(self, *, capacity: int = 1000) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 10000:
            raise ValueError("invalid metrics capacity")
        self._samples: list[AuthenticationMetricsSample] = []
        self._capacity = capacity

    @property
    def samples(self) -> tuple[AuthenticationMetricsSample, ...]:
        return tuple(self._samples)

    async def record_attempt(self, sample: AuthenticationMetricsSample) -> None:
        if not isinstance(sample, AuthenticationMetricsSample):
            raise ValueError("invalid authentication metric")
        if len(self._samples) == self._capacity:
            raise RuntimeError("metrics buffer full")
        self._samples.append(sample)

    def __repr__(self) -> str:
        return "InMemoryAuthenticationMetricsRecorder(<bounded, non-durable>)"
