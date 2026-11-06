"""Local cross-process restart, cancellation and ambiguous commit oracles."""

import asyncio
import os
import sqlite3
import sys
import threading
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from pyauthkit.adapters.audit_required_sqlite import SqliteRequiredAuditCommitter
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.failure import TechnicalErrorCode
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import AuthError
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.ports.required_audit import AuditAttemptId

from .conftest import api_gateway, api_wire, store, stored_rows, tcp_host


@pytest.mark.asyncio
@pytest.mark.integration
async def test_m6_audit_receipt_and_replay_denial_survive_independent_os_process(
    tmp_path: Path,
) -> None:
    committer = store(tmp_path)
    gateway = await api_gateway(committer)
    async with tcp_host(gateway, route="api", method=EvidenceMethod.API_KEY) as url:
        async with httpx.AsyncClient(base_url=url, timeout=4) as client:
            response = await client.post(
                "/authenticate", headers={"Authorization": "ApiKey " + api_wire()}
            )
            assert response.status_code == 200

    records = stored_rows(tmp_path / "receipt.sqlite")
    assert len(records) == 1
    assert records[0][1] == "AUTHENTICATED"
    env = os.environ.copy()
    env.update(
        {
            "PYA_M6_TEST_RESTART_ONLY": "SYNTHETIC_LOCAL_TEST",
            "PYA_M6_TEST_AUDIT_PATH": str(tmp_path / "receipt.sqlite"),
            "PYA_M6_TEST_ATTEMPT": records[0][0],
        }
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "qualification.m6_http.probe_restart",
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _stderr = await asyncio.wait_for(process.communicate(), timeout=8)
    assert process.returncode == 0
    assert stdout.strip() == b"M6_SYNTHETIC_RESTART_RECEIPT_PASS"
    assert stored_rows(tmp_path / "receipt.sqlite") == records


@pytest.mark.asyncio
@pytest.mark.security
async def test_m6_sqlite_cancelled_await_can_later_commit_but_never_replay_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    committer = store(tmp_path)
    gateway = await api_gateway(committer)
    entry = gateway.catalog.resolve_for_host_route("api")
    attempt = AuditAttemptId(uuid4().hex)
    request = AuthenticationRequest(
        PresentedEvidence(EvidenceMethod.API_KEY, api_wire().encode("ascii")),
        CorrelationId("cancelled-audit-request"),
    )

    started = threading.Event()
    original = SqliteRequiredAuditCommitter._commit_sync

    def instrument(self: SqliteRequiredAuditCommitter, record):
        started.set()
        return original(self, record)

    monkeypatch.setattr(SqliteRequiredAuditCommitter, "_commit_sync", instrument)

    with sqlite3.connect(tmp_path / "receipt.sqlite", isolation_level=None) as db:
        db.execute("BEGIN IMMEDIATE")
        pending = asyncio.create_task(
            gateway.authenticate(request, entry=entry, attempt_id=attempt)
        )
        try:
            assert await asyncio.to_thread(started.wait, 1.0)
            assert not pending.done()
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
        finally:
            db.execute("COMMIT")

    # An asyncio cancellation cannot terminate a to_thread SQLite worker.
    # The local transaction may complete after the caller has gone away.
    receipt = None
    for _ in range(100):
        receipt = committer.inspect_receipt(attempt)
        if receipt is not None:
            break
        await asyncio.sleep(0.02)
    assert receipt is not None
    assert receipt.result_status == "AUTHENTICATED"

    # The already committed ID is consumed. No second positive result can
    # be delivered with the same ID, even if the credential remains valid.
    replay = await gateway.authenticate(request, entry=entry, attempt_id=attempt)
    assert isinstance(replay, AuthError)
    assert replay.error_code is TechnicalErrorCode.DEPENDENCY_UNAVAILABLE
    assert committer.inspect_receipt(attempt) == receipt
    assert len(stored_rows(tmp_path / "receipt.sqlite")) == 1
