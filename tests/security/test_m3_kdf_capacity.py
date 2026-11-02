"""Capacity exhaustion and cancellation retain permits until real completion."""

import asyncio
from threading import Event

import pytest

from pyauthkit.password.capacity import KDFCapacityExhausted, KDFWorkerPool


def test_kdf_worker_budget_rejects_overcommit() -> None:
    with pytest.raises(ValueError):
        KDFWorkerPool(max_workers=3, max_memory_cost_kib=65536, memory_budget_kib=131072)


def test_kdf_capacity_exhaustion_is_fail_closed() -> None:
    pool = KDFWorkerPool(max_workers=1, max_inflight=1, memory_budget_kib=65536)
    ready, release = Event(), Event()

    def work() -> bool:
        ready.set()
        return release.wait(5)

    async def scenario() -> None:
        task = asyncio.create_task(pool.run(work))
        assert await asyncio.to_thread(ready.wait, 2)
        with pytest.raises(KDFCapacityExhausted):
            await pool.run(lambda: True)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # Even after cancellation the native worker is still busy.
        with pytest.raises(KDFCapacityExhausted):
            await pool.run(lambda: True)
        release.set()
        # Drain pool in another thread, avoiding event loop blocking.
        await asyncio.to_thread(pool.close)
    try:
        asyncio.run(scenario())
    finally:
        release.set()
        pool.close()
