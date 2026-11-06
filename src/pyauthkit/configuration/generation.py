"""Explicit M6 prepare-then-CAS generation orchestration.

The host chooses the authoritative ledger, config source and candidate builder.
The function never modifies a running engine or switches traffic itself.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from pyauthkit.ports.generation import GenerationFloorLedger

from .bootstrap import M6Runtime
from .models import ConfigurationRejected, ConfigurationSnapshot


def _preflight_floor(snapshot: ConfigurationSnapshot, ledger: GenerationFloorLedger) -> int:
    if not isinstance(snapshot, ConfigurationSnapshot):
        raise ConfigurationRejected("invalid generation snapshot")
    try:
        floor = ledger.read_floor()
    except asyncio.CancelledError:
        raise
    except Exception:
        raise ConfigurationRejected("authoritative generation ledger unavailable") from None
    if type(floor) is not int or floor < 1:
        raise ConfigurationRejected("invalid authoritative generation floor")
    if snapshot.generation.value < floor:
        raise ConfigurationRejected("stale configuration generation")
    return floor


def _commit_candidate(
    snapshot: ConfigurationSnapshot,
    ledger: GenerationFloorLedger,
    floor: int,
    runtime: M6Runtime,
) -> M6Runtime:
    if not isinstance(runtime, M6Runtime) or runtime.snapshot is not snapshot:
        raise ConfigurationRejected("candidate was not composed for this generation")
    try:
        ledger.compare_and_advance(
            expected_floor=floor,
            generation=snapshot.generation.value,
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        # The engine has not been returned to the host for activation.
        raise ConfigurationRejected("generation commit rejected") from None
    return runtime


def prepare_with_generation_ledger(
    snapshot: ConfigurationSnapshot,
    *,
    ledger: GenerationFloorLedger,
    build: Callable[[int], M6Runtime],
) -> M6Runtime:
    """Synchronous, fail-closed bootstrap with atomic generation CAS.

    The host's trusted builder must consume the floor (e.g. as
    `minimum_generation`). Candidate readiness is checked before committing
    the generation. A failed builder cannot advance the ledger.
    """
    floor = _preflight_floor(snapshot, ledger)
    runtime = build(floor)
    return _commit_candidate(snapshot, ledger, floor, runtime)


async def prepare_with_generation_ledger_async(
    snapshot: ConfigurationSnapshot,
    *,
    ledger: GenerationFloorLedger,
    build: Callable[[int], Awaitable[M6Runtime]],
) -> M6Runtime:
    """Async builder variant for real M4 secret preflight, same CAS semantics.

    Ledger operations are synchronous and may briefly block the bootstrap
    task. Host infrastructure can run this startup sequence in a worker.
    Cancellation before CAS leaves the floor unchanged.
    """
    floor = _preflight_floor(snapshot, ledger)
    runtime = await build(floor)
    return _commit_candidate(snapshot, ledger, floor, runtime)
