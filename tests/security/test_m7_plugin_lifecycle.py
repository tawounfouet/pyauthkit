"""M7 managed plugin lifetime: failure, cleanup order, timeout and cancellation."""

import asyncio
from types import SimpleNamespace

import pytest

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.outcome import RejectedOutcome
from pyauthkit.plugins import PluginAdmissionRejected, PluginGrant, admission, lifecycle
from pyauthkit.plugins.lifecycle import activate_approved_authenticators


class ManagedVerifier:
    def __init__(
        self,
        name: str,
        closed: list[str],
        *,
        method: EvidenceMethod = EvidenceMethod.API_KEY,
        raise_close: bool = False,
        slow_close: bool = False,
    ) -> None:
        self.name = name
        self.closed = closed
        self.selected_method = method
        self.raise_close = raise_close
        self.slow_close = slow_close

    @property
    def method(self) -> EvidenceMethod:
        return self.selected_method

    async def verify(self, request: object, context: object) -> RejectedOutcome:
        return RejectedOutcome()

    async def aclose(self) -> None:
        if self.slow_close:
            await asyncio.sleep(1)
        self.closed.append(self.name)
        if self.raise_close:
            raise RuntimeError("private-canary-close")


class Factory:
    SPI_MAJOR = 1

    def __init__(self, result: object) -> None:
        self.result = result

    def __call__(self) -> object:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class Point:
    def __init__(self, factory: Factory) -> None:
        self.factory = factory

    def load(self) -> Factory:
        return self.factory


def admitted(
    monkeypatch: pytest.MonkeyPatch,
    *results: object,
) -> None:
    approved = []
    metadata: dict[int, SimpleNamespace] = {}
    for index, result in enumerate(results):
        method = EvidenceMethod.API_KEY if index == 0 else EvidenceMethod.JWT
        grant = PluginGrant(
            distribution="m7-fixture",
            version="1.0.0",
            name=f"synthetic-{index}",
            target=f"module:factory_{index}",
            method=method,
        )
        point = Point(Factory(result))
        candidate = SimpleNamespace(
            _entry_point=point,
            distribution=grant.distribution,
            version=grant.version,
            group=grant.group,
            name=grant.name,
            target=grant.target,
        )
        metadata[id(point)] = candidate
        approved.append((candidate, grant))

    def preflight(_candidates: object, *, grants: object) -> tuple[object, ...]:
        return tuple(approved)

    # Isolate lifecycle semantics; integration tests exercise real metadata.
    monkeypatch.setattr(lifecycle, "_preflight_candidates", preflight)
    monkeypatch.setattr(admission, "_candidate_for", lambda point: metadata[id(point)])


def test_managed_lifetime_closes_in_reverse_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    first = ManagedVerifier("first", closed)
    second = ManagedVerifier("second", closed, method=EvidenceMethod.JWT)
    admitted(monkeypatch, first, second)

    async def scenario() -> None:
        async with activate_approved_authenticators((), grants=()) as plugins:
            assert plugins == (first, second)
            assert closed == []
        assert closed == ["second", "first"]

    asyncio.run(scenario())


def test_partial_factory_failure_unwinds_prior_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    admitted(monkeypatch, ManagedVerifier("first", closed), RuntimeError("secret-factory"))

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="activation rejected") as error:
            async with activate_approved_authenticators((), grants=()):
                pytest.fail("partial admission must never yield")
        assert "secret-factory" not in str(error.value)
        assert closed == ["first"]

    asyncio.run(scenario())


def test_post_creation_spi_failure_still_closes_rejected_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    admitted(
        monkeypatch,
        ManagedVerifier("first", closed),
        ManagedVerifier("wrong-method", closed),
    )

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected):
            async with activate_approved_authenticators((), grants=()):
                pytest.fail("inconsistent plugin method was admitted")
        assert closed == ["wrong-method", "first"]

    asyncio.run(scenario())


def test_cleanup_failure_is_sanitized_but_other_closers_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    admitted(
        monkeypatch,
        ManagedVerifier("first", closed),
        ManagedVerifier("second", closed, method=EvidenceMethod.JWT, raise_close=True),
    )

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="shutdown failed") as error:
            async with activate_approved_authenticators((), grants=()):
                pass
        assert closed == ["second", "first"]
        assert "private-canary-close" not in str(error.value)

    asyncio.run(scenario())


def test_caller_cancellation_still_runs_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    admitted(monkeypatch, ManagedVerifier("single", closed))

    async def scenario() -> None:
        ready = asyncio.Event()

        async def worker() -> None:
            async with activate_approved_authenticators((), grants=()):
                ready.set()
                await asyncio.sleep(30)

        task = asyncio.create_task(worker())
        await ready.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed == ["single"]

    asyncio.run(scenario())


def test_close_timeout_reports_failed_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    admitted(monkeypatch, ManagedVerifier("slow", closed, slow_close=True))

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="shutdown failed"):
            async with activate_approved_authenticators(
                (), grants=(), cleanup_timeout_seconds=0.01
            ):
                pass
        assert closed == []

    asyncio.run(scenario())


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("inf"), float("nan"), True, 31.0])
def test_invalid_cleanup_timeout_rejected(timeout: float) -> None:
    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="timeout"):
            async with activate_approved_authenticators(
                (), grants=(), cleanup_timeout_seconds=timeout
            ):
                pass

    asyncio.run(scenario())


def test_unhandled_caller_exception_is_not_relabelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[str] = []
    admitted(monkeypatch, ManagedVerifier("single", closed))

    async def scenario() -> None:
        with pytest.raises(LookupError, match="application error"):
            async with activate_approved_authenticators((), grants=()):
                raise LookupError("application error")
        assert closed == ["single"]

    asyncio.run(scenario())


def test_sync_close_only_plugin_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SyncOnly:
        @property
        def method(self) -> EvidenceMethod:
            return EvidenceMethod.API_KEY

        async def verify(self, request: object, context: object) -> RejectedOutcome:
            return RejectedOutcome()

        def close(self) -> None:
            raise RuntimeError("never call blocking synchronous closer")

    admitted(monkeypatch, SyncOnly())

    async def scenario() -> None:
        with pytest.raises(PluginAdmissionRejected, match="activation rejected"):
            async with activate_approved_authenticators((), grants=()):
                pytest.fail("unsupported resource contract must not yield")

    asyncio.run(scenario())
