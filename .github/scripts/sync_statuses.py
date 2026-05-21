#!/usr/bin/env python3
"""
VASH 3.0 — Sync activity statuses to GitHub Project.
Reads validation results from runtime/validation/
and updates Project items accordingly.
Run once via workflow_dispatch.
"""
import os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from project_lib import ProjectClient

# Known statuses from completed pipeline runs + manual approvals
KNOWN_STATUSES = {
    "0.1":  "PASS",    # AvA score 89 — APPROVED
    "0.2":  "FAIL",    # AvA score 82 — below threshold 88
    "0.3":  "PASS",    # AvA score 94 — APPROVED
    "0.10": "PASS",    # human approved
    "0.11": "PASS",    # human approved
    "0.12": "PASS",    # manual — token added
    "0.13": "PASS",    # human approved
    "1.1":  "MODIFY",  # AvA score 81 — needs corrections
}

def get_status_from_validation(task_id: str) -> str:
    """Read status from validation summary if available."""
    tid = task_id.replace(".", "-")
    path = Path(f"runtime/validation/{tid}_summary.md")
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8")
    m = re.search(r"\*\*Verdict:\*\*\s*(\w+)", content)
    if not m:
        return ""
    verdict = m.group(1).upper()
    if verdict == "APPROVED":
        return "PASS"
    return verdict  # FAIL, MODIFY, RETRY

def main():
    client = ProjectClient()
    pid = client.get_project_id()
    if not pid:
        print("ERROR: Project not found — run setup_project workflow first")
        sys.exit(1)

    # Build status map: validation files take priority over known statuses
    all_activities = client.get_all_activities()
    print(f"Found {len(all_activities)} activities in Project\n")

    updated = 0
    for activity in all_activities:
        task_id = activity["task_id"]
        current = activity["status"]

        # Check validation file first
        status = get_status_from_validation(task_id)

        # Fall back to known statuses
        if not status:
            status = KNOWN_STATUSES.get(task_id, "")

        # Skip if no update needed
        if not status or status == current:
            continue

        result = client.update_status(task_id, status)
        icon = {"PASS": "✅", "FAIL": "❌", "MODIFY": "⚠️",
                "IN_PROGRESS": "🔄", "PENDING": "⏳"}.get(status, "?")
        print(f"  {icon} [{task_id}] {current} → {status} {'OK' if result else 'FAILED'}")
        updated += 1

    print(f"\n✅ Updated {updated} activities")

if __name__ == "__main__":
    main()
