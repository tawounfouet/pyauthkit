"""Test-only independent OS-process inspection of a local audit receipt.

Requires an explicit synthetic test marker, a generated audit path and an
attempt ID. Does not accept arbitrary signing keys or expose stored content.
Not a power-loss, anti-tamper or multi-host distributed durability test.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from pyauthkit.adapters.audit_required_sqlite import (
    RequiredAuditAttemptConflict,
    SqliteRequiredAuditCommitter,
)
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.events import AuthenticationEvent
from pyauthkit.ports.required_audit import AuditAttemptId, AuditDecisionRecord


def main() -> int:
    if os.environ.get("PYA_M6_TEST_RESTART_ONLY") != "SYNTHETIC_LOCAL_TEST":
        return 1
    try:
        location = Path(os.environ["PYA_M6_TEST_AUDIT_PATH"])
        attempt = AuditAttemptId(os.environ["PYA_M6_TEST_ATTEMPT"])
        committer = SqliteRequiredAuditCommitter(
            path=location,
            signing_key=bytes(range(64, 96)),
            key_id="synthetic-audit-v1",
        )
        prior = committer.inspect_receipt(attempt)
        if prior is None or prior.result_status != "AUTHENTICATED":
            return 1
        # A different decision with a consumed ID must never return a
        # previously valid receipt or create another audit record.
        rejected = AuditDecisionRecord(
            attempt_id=attempt,
            event=AuthenticationEvent(
                correlation_id=CorrelationId("restart-synthetic"),
                method=EvidenceMethod.API_KEY,
                result_status="REJECTED",
                duration_ms=0.0,
            ),
            profile=TrustProfileRef("api-auth", "v1", TrustedScopeRef("tenant-a:production")),
        )
        try:
            asyncio.run(committer.commit(rejected))
        except RequiredAuditAttemptConflict:
            pass
        else:
            return 1
        if committer.inspect_receipt(attempt) != prior:
            return 1
    except Exception:
        # Never reveal paths, SQL diagnostics or credential data.
        return 1
    print("M6_SYNTHETIC_RESTART_RECEIPT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
