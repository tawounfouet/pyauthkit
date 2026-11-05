"""Experimental M6 audit commit contract, separate from M2 best-effort events.

A receipt is a local commit acknowledgment, NOT cryptographic proof of
tamper-resistance, distribution, exactly-once delivery or host authenticity.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol

from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.events import AuthenticationEvent

_HEX_128 = re.compile(r"[0-9a-f]{32}\Z")
_HEX_256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True, repr=False)
class AuditAttemptId:
    """Host-generated 128-bit random ID, unique per authentication attempt."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or _HEX_128.fullmatch(self.value) is None:
            raise ValueError("invalid audit attempt ID")

    def __repr__(self) -> str:
        return "AuditAttemptId(<opaque>)"


@dataclass(frozen=True, slots=True, repr=False)
class AuditDecisionRecord:
    """Bounded audit input; the adapter HMACs identifiers before persistence."""

    attempt_id: AuditAttemptId
    event: AuthenticationEvent
    profile: TrustProfileRef
    subject: ScopedSubjectRef | None = None
    principal_type: PrincipalType | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.attempt_id, AuditAttemptId)
            or not isinstance(self.event, AuthenticationEvent)
            or not isinstance(self.profile, TrustProfileRef)
            or not math.isfinite(self.event.duration_ms)
            or not 0 <= self.event.duration_ms <= 3_600_000
        ):
            raise ValueError("invalid audit decision record")
        success = self.event.result_status == "AUTHENTICATED"
        if success != (self.subject is not None and self.principal_type is not None):
            raise ValueError("audit subject/result mismatch")
        if success and (
            not isinstance(self.subject, ScopedSubjectRef)
            or not isinstance(self.principal_type, PrincipalType)
            or self.subject.scope_ref != self.profile.scope_ref
        ):
            raise ValueError("audit subject outside trusted scope")
        if not success and (self.subject is not None or self.principal_type is not None):
            raise ValueError("unexpected audit subject")

    def __repr__(self) -> str:
        return "AuditDecisionRecord(<redacted, verified-result-bound>)"


@dataclass(frozen=True, slots=True, repr=False)
class AuditCommitReceipt:
    """Locally committed receipt, bound to one attempt and one decision."""

    attempt_id: AuditAttemptId
    record_id: str
    sequence: int
    result_status: str
    decision_tag: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.attempt_id, AuditAttemptId)
            or type(self.record_id) is not str
            or _HEX_128.fullmatch(self.record_id) is None
            or type(self.sequence) is not int
            or self.sequence < 1
            or self.result_status not in ("AUTHENTICATED", "REJECTED", "ERROR")
            or type(self.decision_tag) is not str
            or _HEX_256.fullmatch(self.decision_tag) is None
        ):
            raise ValueError("invalid audit commit receipt")

    def __repr__(self) -> str:
        return "AuditCommitReceipt(<local-commit, untrusted-as-global-proof>)"


class RequiredAuditCommitter(Protocol):
    """The host must independently qualify the injected storage authority."""

    async def commit(self, record: AuditDecisionRecord) -> AuditCommitReceipt: ...
