"""M3-T22/T39: bounded native workers, queue saturation, safe shutdown."""

import asyncio
from threading import Event, Lock

import pytest

from pyauthkit.password.capacity import KDFCapacityExhausted, KDFWorkerPool


def test_m3_t22_120_simultaneous_attempts_bounded_workers_and_queue() -> None:
    pool = KDFWorkerPool(
        max_workers=2,
        max_inflight=3,
        max_memory_cost_kib=19456,
        memory_budget_kib=38912,
    )
    entered, release = Event(), Event()
    lock = Lock()
    active = 0
    peak = 0

    def work() -> bool:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        entered.set()
        try:
            return release.wait(5)
        finally:
            with lock:
                active -= 1

    async def scenario() -> None:
        held = [asyncio.create_task(pool.run(work)) for _ in range(3)]
        assert await asyncio.to_thread(entered.wait, 2)
        flood = [asyncio.create_task(pool.run(work)) for _ in range(117)]
        await asyncio.sleep(0.05)
        release.set()
        results = await asyncio.gather(*held, *flood, return_exceptions=True)
        assert sum(result is True for result in results) == 3
        assert sum(isinstance(result, KDFCapacityExhausted) for result in results) == 117
        assert peak <= 2

    try:
        asyncio.run(scenario())
    finally:
        release.set()
        pool.close()


def test_m3_t39_shutdown_drains_running_native_work_and_refuses_new_jobs() -> None:
    pool = KDFWorkerPool(
        max_workers=1, max_inflight=1, max_memory_cost_kib=19456, memory_budget_kib=19456
    )
    entered, release = Event(), Event()

    def work() -> bool:
        entered.set()
        return release.wait(5)

    async def scenario() -> None:
        job = asyncio.create_task(pool.run(work))
        assert await asyncio.to_thread(entered.wait, 2)
        closer = asyncio.create_task(asyncio.to_thread(pool.close))
        await asyncio.sleep(0.05)
        assert not closer.done()
        release.set()
        assert await job
        await closer
        with pytest.raises(KDFCapacityExhausted):
            await pool.run(lambda: True)

    try:
        asyncio.run(scenario())
    finally:
        release.set()
        pool.close()
