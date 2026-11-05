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


def test_m4_candidate_catalog_contains_exactly_40_oracles_and_16_gates() -> None:
    import re

    text = (ROOT / "docs/qualification/M4_CANDIDATE_ORACLE_CATALOG_V1.md").read_text(
        encoding="utf-8"
    )
    expected_oracles = [f"M4-T{i:02d}" for i in range(1, 41)]
    expected_gates = [f"G5-{i:02d}" for i in range(1, 17)]
    assert re.findall(r"^\\| (M4-T\\d{2}) \\|", text, re.M) == expected_oracles
    assert re.findall(r"^\\| (G5-\\d{2}) \\|", text, re.M) == expected_gates
    assert "PROPOSED - NOT CANONICAL / NOT APPROVED" in text
    assert "PENDING" in text


def test_m4_decision_packet_keeps_human_governance_outstanding() -> None:
    text = (ROOT / "docs/qualification/M4_GOVERNANCE_DECISION_PACKET.md").read_text(
        encoding="utf-8"
    )
    assert "Decision A" in text and "Decision B" in text
    assert "NON RENSEIGNE" in text
    assert "NO-GO" in text
    assert "Autorisation de merge" in text
