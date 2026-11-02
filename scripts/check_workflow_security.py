"""Enforce limited PR workflow permissions and pinned external actions.

Structural policy checker only, not a full YAML security audit.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PINNED_ACTION = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+@[0-9a-f]{40}$")


def check_workflow(path: Path) -> list[str]:
    doc = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(doc, dict):
        return [f"{path}: expected mapping"]
    errors: list[str] = []
    trigger = doc.get("on", {})
    if "pull_request_target" in trigger:
        errors.append(f"{path}: pull_request_target is forbidden")
    is_pr = "pull_request" in trigger
    permissions = doc.get("permissions", {})
    if not isinstance(permissions, dict):
        errors.append(f"{path}: explicit permission mapping required")
    elif is_pr and permissions != {"contents": "read"}:
        errors.append(f"{path}: PR workflow must have contents: read only")
    jobs = doc.get("jobs", {})
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            errors.append(f"{path}: invalid job {job_name}")
            continue
        job_permissions = job.get("permissions")
        if is_pr and job_permissions not in (None, {"contents": "read"}):
            errors.append(f"{path}: PR job {job_name} expands permissions")
        for step in job.get("steps", []):
            action = step.get("uses", "")
            if action and not PINNED_ACTION.fullmatch(action):
                errors.append(f"{path}: unpinned or unsupported action {action}")
    return errors


def main() -> int:
    workflows = Path(__file__).resolve().parents[1] / ".github/workflows"
    errors: list[str] = []
    for path in sorted(workflows.glob("*.yml")):
        errors.extend(check_workflow(path))
    if not workflows.is_dir() or not list(workflows.glob("*.yml")):
        errors.append("workflow directory missing or empty")
    for message in errors:
        print("WORKFLOW POLICY VIOLATION:", message)
    if errors:
        return 1
    print("Workflow SHA pinning and PR permission guard passed (structural only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
