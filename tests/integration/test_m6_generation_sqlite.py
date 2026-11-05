"""M6 persistent generation floor candidate: failure and concurrent restart oracles.

These tests exercise a locally provisioned SQLite reference ledger only.
They do not prove tamper-resistant storage, multi-region consensus or that
a host router has switched active traffic to the returned engine.
"""

import asyncio
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from pyauthkit.adapters.generation_sqlite import (
    GenerationLedgerConflict,
    GenerationLedgerUnavailable,
    SqliteGenerationFloorLedger,
    provision_sqlite_generation_ledger,
)
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    compose_authentication_engine,
    load_approved_configuration,
)
from pyauthkit.configuration.generation import (
    prepare_with_generation_ledger,
    prepare_with_generation_ledger_async,
)
from pyauthkit.configuration.models import ConfigurationRejected
from pyauthkit.domain.evidence import EvidenceMethod


class NoopAuthenticator:
    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.JWT

    async def verify(self, _request: object, _context: object) -> None:
        return None


def snapshot(generation: int = 1):
    return load_approved_configuration(
        {
            "schema_version": 1,
            "routes": [
                {
                    "route_id": "only",
                    "scope": "tenant-a",
                    "profile_id": "j",
                    "profile_version": f"v{generation}",
                    "allowed_methods": ["jwt"],
                }
            ],
            "timeout_seconds": 2.0,
            "audit_delivery": "best_effort",
            "secrets": [],
        },
        provenance=SourceProvenance("trusted-ledger-config", "host", f"r{generation}"),
        policy=SourcePolicy(frozenset({("trusted-ledger-config", "host")})),
        generation=ConfigurationGeneration(generation),
    )


def ledger(tmp_path: Path, *, floor: int = 1) -> SqliteGenerationFloorLedger:
    path = tmp_path / "host-generation.db"
    provision_sqlite_generation_ledger(path, initial_floor=floor)
    return SqliteGenerationFloorLedger(path=path)


def build(snap, *, floor: int):
    return compose_authentication_engine(
        snap, authenticators=(NoopAuthenticator(),), minimum_generation=floor
    )


def test_m6_t36_provisioned_floor_persists_across_independent_reopens(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    path = tmp_path / "host-generation.db"
    assert store.read_floor() == 1
    store.compare_and_advance(expected_floor=1, generation=2)
    assert SqliteGenerationFloorLedger(path=path).read_floor() == 2
    store.compare_and_advance(expected_floor=2, generation=2)
    assert SqliteGenerationFloorLedger(path=path).read_floor() == 2


def test_m6_t36_candidate_commits_only_after_valid_composition(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    snap = snapshot(2)
    runtime = prepare_with_generation_ledger(
        snap,
        ledger=store,
        build=lambda floor: build(snap, floor=floor),
    )
    assert runtime.snapshot is snap
    assert runtime.catalog.resolve_for_host_route("only").profile_ref.version == "v2"
    assert store.read_floor() == 2


def test_m6_t36_failed_candidate_does_not_advance_floor(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    snap = snapshot(2)

    def broken(_floor: int):
        raise RuntimeError("synthetic preflight unavailable")

    with pytest.raises(RuntimeError):
        prepare_with_generation_ledger(snap, ledger=store, build=broken)
    assert store.read_floor() == 1


def test_m6_t36_wrong_snapshot_cannot_consume_ledger_commit(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    snap = snapshot(2)
    wrong = snapshot(3)
    with pytest.raises(ConfigurationRejected, match="not composed"):
        prepare_with_generation_ledger(
            snap, ledger=store, build=lambda floor: build(wrong, floor=floor)
        )
    assert store.read_floor() == 1


def test_m6_t36_reboot_with_old_generation_rejected(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    current = snapshot(2)
    prepare_with_generation_ledger(
        current, ledger=store, build=lambda floor: build(current, floor=floor)
    )
    reopened = SqliteGenerationFloorLedger(path=tmp_path / "host-generation.db")
    with pytest.raises(ConfigurationRejected, match="stale"):
        previous = snapshot(1)
        prepare_with_generation_ledger(
            previous, ledger=reopened, build=lambda floor: build(previous, floor=floor)
        )
    assert reopened.read_floor() == 2


def test_m6_t36_ledger_absent_after_restart_never_falls_back(tmp_path: Path) -> None:
    path = tmp_path / "missing.db"
    with pytest.raises(GenerationLedgerUnavailable, match="missing"):
        SqliteGenerationFloorLedger(path=path)
    assert not path.exists()
    store = ledger(tmp_path)
    (tmp_path / "host-generation.db").unlink()
    with pytest.raises(ConfigurationRejected, match="unavailable"):
        prepare_with_generation_ledger(
            snapshot(2), ledger=store, build=lambda floor: build(snapshot(2), floor=floor)
        )
    assert not (tmp_path / "host-generation.db").exists()


def test_m6_t36_corrupt_or_empty_ledger_denies_activation(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    with sqlite3.connect(tmp_path / "host-generation.db") as conn:
        conn.execute("DELETE FROM generation_floor")
    with pytest.raises(GenerationLedgerUnavailable):
        store.read_floor()
    with pytest.raises(ConfigurationRejected):
        prepare_with_generation_ledger(
            snapshot(2), ledger=store, build=lambda floor: build(snapshot(2), floor=floor)
        )


def test_m6_t36_ledger_cannot_be_reprovisioned_with_lower_floor(tmp_path: Path) -> None:
    store = ledger(tmp_path, floor=4)
    with pytest.raises(GenerationLedgerUnavailable, match="provisioning rejected"):
        provision_sqlite_generation_ledger(tmp_path / "host-generation.db", initial_floor=1)
    assert store.read_floor() == 4


@pytest.mark.parametrize("invalid", [0, -1, 1.0, True, 2**63, "2"])
def test_m6_t36_invalid_floor_provisioning_rejected(tmp_path: Path, invalid) -> None:
    with pytest.raises(GenerationLedgerUnavailable):
        provision_sqlite_generation_ledger(tmp_path / "floor.db", initial_floor=invalid)
    assert not (tmp_path / "floor.db").exists()


def test_m6_t36_symlink_rejected_at_open(tmp_path: Path) -> None:
    ledger(tmp_path)
    alias = tmp_path / "symlink.db"
    try:
        alias.symlink_to(tmp_path / "host-generation.db")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(GenerationLedgerUnavailable, match="symlink"):
        SqliteGenerationFloorLedger(path=alias)


def test_m6_t36_sqlite_floor_is_atomically_compared_across_instances(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    other = SqliteGenerationFloorLedger(path=tmp_path / "host-generation.db")
    store.compare_and_advance(expected_floor=1, generation=2)
    with pytest.raises(GenerationLedgerConflict, match="changed"):
        other.compare_and_advance(expected_floor=1, generation=3)
    assert other.read_floor() == 2


def test_m6_t36_two_concurrent_candidates_cannot_both_commit(tmp_path: Path) -> None:
    path = tmp_path / "host-generation.db"
    provision_sqlite_generation_ledger(path, initial_floor=1)
    barrier = Barrier(2)

    def worker(candidate: int) -> tuple[str, int]:
        store = SqliteGenerationFloorLedger(path=path)
        snap = snapshot(candidate)

        def prepare(floor: int):
            engine = build(snap, floor=floor)
            barrier.wait(timeout=5)
            return engine

        try:
            prepare_with_generation_ledger(snap, ledger=store, build=prepare)
            return ("ok", candidate)
        except ConfigurationRejected:
            return ("denied", candidate)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(worker, (2, 3)))
    assert sorted(status for status, _ in outcomes) == ["denied", "ok"]
    winning_generation = next(generation for status, generation in outcomes if status == "ok")
    assert SqliteGenerationFloorLedger(path=path).read_floor() == winning_generation


def test_m6_t36_same_generation_restart_is_allowed_only_if_floor_unchanged(
    tmp_path: Path,
) -> None:
    store = ledger(tmp_path, floor=2)
    snap = snapshot(2)
    assert (
        prepare_with_generation_ledger(
            snap, ledger=store, build=lambda floor: build(snap, floor=floor)
        ).snapshot
        is snap
    )
    store.compare_and_advance(expected_floor=2, generation=3)
    with pytest.raises(ConfigurationRejected, match="stale"):
        prepare_with_generation_ledger(
            snap, ledger=store, build=lambda floor: build(snap, floor=floor)
        )


def test_m6_t36_async_preflight_failure_keeps_floor_unchanged(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    snap = snapshot(2)

    async def prepare(floor: int):
        assert floor == 1
        await asyncio.sleep(0)
        raise RuntimeError("synthetic vault failure")

    with pytest.raises(RuntimeError):
        asyncio.run(prepare_with_generation_ledger_async(snap, ledger=store, build=prepare))
    assert store.read_floor() == 1


def test_m6_t36_async_candidate_returns_after_persistent_commit(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    snap = snapshot(2)

    async def prepare(floor: int):
        await asyncio.sleep(0)
        return build(snap, floor=floor)

    runtime = asyncio.run(prepare_with_generation_ledger_async(snap, ledger=store, build=prepare))
    assert runtime.snapshot is snap
    assert SqliteGenerationFloorLedger(path=tmp_path / "host-generation.db").read_floor() == 2


def test_m6_t36_failed_database_transaction_is_fail_closed(tmp_path: Path) -> None:
    store = ledger(tmp_path)
    path = tmp_path / "host-generation.db"
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE generation_floor")
    with pytest.raises(GenerationLedgerUnavailable):
        store.compare_and_advance(expected_floor=1, generation=2)


def test_m6_t36_sqlite_single_host_only_tampering_caveat(tmp_path: Path) -> None:
    """Tests do not imply authentication against a privileged DB replacement."""
    store = ledger(tmp_path)
    assert "reference-only" in repr(store)
    if os.name == "posix":
        assert (tmp_path / "host-generation.db").stat().st_mode & 0o777 == 0o600
