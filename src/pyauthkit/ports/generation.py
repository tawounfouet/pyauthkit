"""M6 generation ledger port for host-controlled anti-rollback coordination.

DDD: monotonic generation floor; Ports & Adapters: persistence is injected.
A ledger comparison is not proof of an authentic config, trusted deployment
routing, or cluster-wide coordination without shared trusted storage.
"""

from typing import Protocol


class GenerationFloorLedger(Protocol):
    """Atomically compare and advance one host-owned generation floor."""

    def read_floor(self) -> int:
        """Read a previously provisioned floor. Never synthesize one."""
        ...

    def compare_and_advance(self, *, expected_floor: int, generation: int) -> None:
        """Atomically require expected floor and persist max(floor, generation).

        A same-generation restart is valid only when the stored floor still
        equals expected_floor. A different concurrent commit must be rejected.
        """
        ...
