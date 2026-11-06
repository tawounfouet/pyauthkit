"""Validate *local consistency* of candidate M4 evidence, never certify security.

Checks manifests, 40/16 candidate registers, test names, ADRs and workflow.
GitHub Actions history/log status is intentionally not trusted from JSON alone.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

MANIFEST = Path("docs/qualification/M4_EVIDENCE_MANIFEST.json")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def _test_exists(root: Path, nodeid: str) -> bool:
    path, sep, function = nodeid.partition("::")
    if sep != "::" or not function.startswith("test_"):
        return False
    if ".." in Path(path).parts or not path.startswith(("tests/", "qualification/m4_host/tests/")):
        return False
    source = root / path
    if not source.is_file() or not path.endswith(".py"):
        return False
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeError):
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function
        for node in tree.body
    )


def evaluate(root: Path) -> list[str]:
    """Return safe, non-secret structural errors. No network call is performed."""
    errors: list[str] = []
    manifest_path = root / MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return [f"cannot parse M4 manifest: {type(exc).__name__}"]

    if manifest.get("kind") != "M4_CANDIDATE_EVIDENCE_INDEX_NOT_CERTIFICATION":
        errors.append("manifest must be explicitly labelled candidate")
    if manifest.get("formal_gate") != "NO-GO":
        errors.append("gate promotion requires independent external adjudication")
    if (
        manifest.get("reviewer_identity") is not None
        or manifest.get("acceptance_signature") is not None
    ):
        errors.append("a machine-authored candidate file must not invent signatures")
    if manifest.get("merged") is not False or manifest.get("released") is not False:
        errors.append("candidate must not assert merge or release")
    if (
        manifest.get("normative_catalog_reconciliation")
        != "M4_DETAILED_PLAN_SOURCE_MAPPED_OWNER_ADOPTED_FOR_DEV"
    ):
        errors.append("canonical-plan reconciliation not evidenced")
    owner_merge = manifest.get("maintainer_development_merge_decision", {})
    if (
        not isinstance(owner_merge, dict)
        or owner_merge.get("status") != "AUTHORIZED_TO_MERGE_DEVELOPMENT_ONLY"
        or owner_merge.get("independent_security_gate") != "NO-GO"
        or owner_merge.get("release_and_production") != "NOT_AUTHORIZED"
        or owner_merge.get("decision_file")
        != ("docs/qualification/M4_SOLO_MAINTAINER_DEV_MERGE_AUTHORIZATION_2026-11-05.md")
        or not (root / owner_merge.get("decision_file", "")).is_file()
    ):
        errors.append("owner merge exception is absent, malformed or not scoped to development")
    checkpoint = manifest.get("immutable_technical_checkpoint", {})
    if not isinstance(checkpoint, dict):
        return ["invalid checkpoint structure"]
    segments = checkpoint.get("sha_segments", [])
    if (
        not isinstance(segments, list)
        or len(segments) != 5
        or not all(isinstance(part, str) and len(part) == 8 for part in segments)
        or not SHA.fullmatch("".join(segments))
    ):
        errors.append("checkpoint SHA segments must reconstruct one 40-char lowercase SHA")
    run_id = checkpoint.get("run_id")
    if type(run_id) is not int or run_id <= 0:
        errors.append("invalid CI run ID")
    elif checkpoint.get("workflow_url") != (
        f"https://github.com/tawounfouet/pyauthkit/actions/runs/{run_id}"
    ):
        errors.append("CI URL must match pinned run")
    jobs = checkpoint.get("job_ids", {})
    if not isinstance(jobs, dict) or len(jobs) != 8:
        errors.append("expected exactly eight pinned CI jobs")
    elif any(type(item) is not int or item <= 0 for item in jobs.values()):
        errors.append("invalid CI job IDs")
    if checkpoint.get("ci_jobs_observed") != 8:
        errors.append("wrong expected job count")
    if checkpoint.get("core_tests_passed_observed") != 207:
        errors.append("wrong historical default suite count")
    if checkpoint.get("reference_host_tests_passed_observed") != 12:
        errors.append("wrong historical host suite count")

    oracles = manifest.get("oracles", [])
    gates = manifest.get("g5", [])
    if not isinstance(oracles, list) or len(oracles) != 40:
        errors.append("expected 40 oracle rows")
        oracles = []
    if not isinstance(gates, list) or len(gates) != 16:
        errors.append("expected 16 G5 rows")
        gates = []
    expected_oracles = [f"M4-T{i:02d}" for i in range(1, 41)]
    expected_gates = [f"G5-{i:02d}" for i in range(1, 17)]
    if [item.get("id") for item in oracles] != expected_oracles:
        errors.append("oracle IDs must match M4-T01..M4-T40 in order")
    if [item.get("id") for item in gates] != expected_gates:
        errors.append("G5 IDs must match G5-01..G5-16 in order")

    for item in oracles:
        oid = item.get("id", "unknown")
        if item.get("independent_adjudication") != "PENDING":
            errors.append(f"{oid}: unsanctioned adjudication")
        if item.get("evidence_tier") not in {
            "CODE_TEST",
            "REFERENCE_HOST",
            "CI_RUN",
            "NOT_OBSERVED",
        }:
            errors.append(f"{oid}: unknown evidence tier")
        tests = item.get("test_nodes")
        if not isinstance(tests, list):
            errors.append(f"{oid}: test_nodes is not a list")
            continue
        if item.get("evidence_tier") in {"CODE_TEST", "REFERENCE_HOST"} and not tests:
            errors.append(f"{oid}: test evidence missing")
        for node in tests:
            if not isinstance(node, str) or not _test_exists(root, node):
                errors.append(f"{oid}: missing test function {node!r}")
    for criterion in gates:
        cid = criterion.get("id", "unknown")
        if (
            criterion.get("review_status") != "PENDING"
            or criterion.get("approval") != "NOT_RECORDED"
        ):
            errors.append(f"{cid}: no signed acceptance available")
        links = criterion.get("oracle_links", [])
        if (
            not isinstance(links, list)
            or not links
            or any(x not in expected_oracles for x in links)
        ):
            errors.append(f"{cid}: missing/unknown mapped oracle")
    for doc in manifest.get("adrs", []):
        path = doc.get("path", "")
        if (
            not isinstance(path, str)
            or not path.startswith("docs/adr/")
            or not (root / path).is_file()
        ):
            errors.append("missing ADR file")
        if doc.get("decision") != "PROPOSED":
            errors.append("ADR acceptance is not recorded")
    for source in [
        manifest.get("source_of_candidate_oracles"),
        manifest.get("source_of_candidate_gates"),
    ]:
        if not isinstance(source, str) or not (root / source).is_file():
            errors.append("missing candidate registry")
    oracle_source = root / "docs/qualification/M4_2026_11_05_SOURCE_MATRIX.md"
    if oracle_source.is_file():
        source = oracle_source.read_text(encoding="utf-8")
        oracle_rows: list[list[str]] = []
        gate_rows: list[list[str]] = []
        for line in source.splitlines():
            if line.startswith("| M4-T"):
                oracle_rows.append([cell.strip() for cell in line.strip("|").split("|")])
            elif line.startswith("| G5-"):
                gate_rows.append([cell.strip() for cell in line.strip("|").split("|")])
        if len(oracle_rows) != 40 or any(len(row) != 4 for row in oracle_rows):
            errors.append("M4 detailed plan source oracle table malformed")
        else:
            if [row[0] for row in oracle_rows] != expected_oracles:
                errors.append("source M4 oracle IDs changed")
            for observed, item in zip(oracle_rows, oracles, strict=True):
                if observed != [
                    item.get("id"),
                    item.get("priority"),
                    item.get("assertion"),
                    item.get("expected_behavior"),
                ]:
                    errors.append(f"{item.get('id', 'unknown')}: plan/manifest semantic drift")
        if len(gate_rows) != 16 or any(len(row) != 4 for row in gate_rows):
            errors.append("M4 detailed plan source G5 table malformed")
        else:
            if [row[0] for row in gate_rows] != expected_gates:
                errors.append("source G5 IDs changed")
            for observed, item in zip(gate_rows, gates, strict=True):
                if observed != [
                    item.get("id"),
                    item.get("candidate_requirement"),
                    item.get("required_evidence"),
                    item.get("no_go_if"),
                ]:
                    errors.append(f"{item.get('id', 'unknown')}: gate/manifest semantic drift")
    for item in oracles:
        if item.get("technical_status") not in {
            "EVIDENCE_REFERENCED",
            "PARTIAL",
            "MISSING",
        }:
            errors.append(f"{item.get('id', 'unknown')}: invalid technical status")
        if item.get("priority") not in ("P0", "P1"):
            errors.append(f"{item.get('id', 'unknown')}: unknown plan priority")
    workflow = root / ".github/workflows/ci.yml"
    if not workflow.is_file():
        errors.append("CI workflow missing")
    else:
        content = workflow.read_text(encoding="utf-8")
        for token in (
            "m4_host:",
            "qualification/m4_host/tests",
            "python -m mypy src/pyauthkit",
            "python -m ruff format --check .",
            "scripts/check_secret_scan.py",
        ):
            if token not in content:
                errors.append(f"CI workflow missing required invocation: {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = evaluate(args.root)
    for issue in errors:
        print("M4 EVIDENCE INTEGRITY:", issue)
    if errors:
        return 1
    print("M4 candidate evidence index is structurally consistent; no security GO is implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
