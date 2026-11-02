"""Bounded Argon2 KDF execution without blocking the event loop.

Async cancellation cannot stop native Argon2 already executing in a thread.
The permit is released when that underlying worker REALLY finishes, not when
a caller times out. This protects memory capacity after engine timeouts.
"""

import asyncio
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import BoundedSemaphore


class KDFCapacityExhausted(Exception):
    """No spare KDF work slot; safely reject instead of an unbounded backlog."""


class KDFWorkerPool:
    """Finite worker threads and finite in-flight+queued permits per process."""

    __slots__ = (
        "_executor",
        "_permits",
        "_closed",
        "_max_memory_cost_kib",
    )

    def __init__(
        self,
        *,
        max_workers: int = 2,
        max_inflight: int = 4,
        max_memory_cost_kib: int = 65536,
        memory_budget_kib: int = 131072,
    ) -> None:
        values = (max_workers, max_inflight, max_memory_cost_kib, memory_budget_kib)
        if (
            any(type(value) is not int for value in values)
            or not 1 <= max_workers <= max_inflight <= 64
            or max_memory_cost_kib < 19456
            or max_workers * max_memory_cost_kib > memory_budget_kib
        ):
            raise ValueError("invalid KDF worker or memory budget")
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="pyauthkit-kdf"
        )
        self._permits = BoundedSemaphore(max_inflight)
        self._max_memory_cost_kib = max_memory_cost_kib
        self._closed = False

    @property
    def max_memory_cost_kib(self) -> int:
        return self._max_memory_cost_kib

    async def run(self, operation: Callable[[], bool]) -> bool:
        """Submit without blocking; cancellation keeps the worker's permit."""
        if self._closed or not self._permits.acquire(blocking=False):
            raise KDFCapacityExhausted("password verification capacity unavailable")
        try:
            future: Future[bool] = self._executor.submit(operation)
        except Exception:
            self._permits.release()
            raise KDFCapacityExhausted("password verification capacity unavailable") from None
        future.add_done_callback(self._release)
        return await asyncio.shield(asyncio.wrap_future(future))

    def _release(self, _future: Future[bool]) -> None:
        self._permits.release()

    def close(self, *, wait: bool = True) -> None:
        """Operator lifecycle hook: stop new submissions and drain on shutdown."""
        self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=False)
