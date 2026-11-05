"""Offline consistency checks must not create or infer security approvals."""

import json
from pathlib import Path

from scripts.check_m4_evidence import evaluate

ROOT = Path(__file__).resolve().parents[2]


def test_m4_candidate_evidence_index_is_structurally_consistent() -> None:
    assert evaluate(ROOT) == []


def test_m4_manifest_explicitly_keeps_all_approvals_pending() -> None:
    manifest = json.loads(
        (ROOT / "docs/qualification/M4_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["formal_gate"] == "NO-GO"
    assert len(manifest["oracles"]) == 40
    assert len(manifest["g5"]) == 16
    assert all(x["independent_adjudication"] == "PENDING" for x in manifest["oracles"])
    assert all(x["approval"] == "NOT_RECORDED" for x in manifest["g5"])
    assert manifest["reviewer_identity"] is None
    assert manifest["acceptance_signature"] is None
