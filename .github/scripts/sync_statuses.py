#!/usr/bin/env python3
"""
VASH 3.0 — Sync activity statuses to GitHub Project.
Runs standalone — does not depend on setup_project.
Reads:
  1. runtime/validation/ for pipeline-completed activities
  2. KNOWN_STATUSES for manually approved activities
Updates GitHub Project item Status field for each.
"""
import os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from project_lib import ProjectClient

# Manually approved activities not yet in validation files
KNOWN_STATUSES = {
    "0.10": "PASS",
    "0.11": "PASS",
    "0.12": "PASS",
}

def read_validation_statuses() -> dict:
    """Read all validation summary files and extract verdicts."""
    statuses = {}
    val_dir = Path("runtime/validation")
    if not val_dir.exists():
        return statuses

    for f in val_dir.glob("*_summary.md"):
        # Extract task_id from filename e.g. 0-1_summary.md -> 0.1
        tid = re.match(r"(\d+-\d+)_summary", f.name)
        if not tid:
            continue
        task_id = tid.group(1).replace("-", ".")
        content = f.read_text(encoding="utf-8")

        # Extract verdict
        m = re.search(r"\*\*Verdict:\*\*\s*(\w+)", content)
        if not m:
            continue
        verdict = m.group(1).upper()

        # Map verdict to Project status
        if verdict == "APPROVED":
            statuses[task_id] = "PASS"
        elif verdict in ("FAIL", "MODIFY", "RETRY"):
            statuses[task_id] = verdict
        elif verdict == "ESCALATE":
            statuses[task_id] = "FAIL"

    return statuses

def main():
    client = ProjectClient()
    pid = client.get_project_id()
    if not pid:
        print("ERROR: Project not found")
        print("Run 'VASH 3.0 Project Setup' workflow first")
        sys.exit(1)

    # Build final status map
    # Validation files take priority over known statuses
    statuses = {**KNOWN_STATUSES, **read_validation_statuses()}
    print(f"Status map built: {len(statuses)} activities to update\n")

    # Get all project activities
    all_activities = client.get_all_activities()
    if not all_activities:
        print("ERROR: No activities found in Project")
        print("Run 'VASH 3.0 Project Setup' workflow first")
        sys.exit(1)

    print(f"Project has {len(all_activities)} activities\n")

    updated = 0
    skipped = 0

    for activity in all_activities:
        task_id = activity["task_id"]
        current = activity["status"]
        target = statuses.get(task_id, "")

        if not target:
            skipped += 1
            continue

        if target == current:
            icon = {"PASS":"✅","FAIL":"❌","MODIFY":"⚠️","PENDING":"⏳"}.get(current,"?")
            print(f"  {icon} [{task_id}] already {current} — skipped")
            skipped += 1
            continue

        result = client.update_status(task_id, target)
        icon = {"PASS":"✅","FAIL":"❌","MODIFY":"⚠️","IN_PROGRESS":"🔄","PENDING":"⏳"}.get(target,"?")
        print(f"  {icon} [{task_id}] {current} → {target} {'OK' if result else 'FAILED'}")
        if result:
            updated += 1

    print(f"\nDone — {updated} updated, {skipped} skipped")

if __name__ == "__main__":
    main()
