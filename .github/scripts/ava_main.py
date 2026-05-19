#!/usr/bin/env python3
"""
VASH 3.0 — AvA Entry Point
Called by GitHub Actions workflow.
Reads TASK_ID from environment, runs Orchestrator, exits 0 always.
LAW 1: Python stdlib only
"""
import os
import sys
from pathlib import Path

# Add scripts directory to path for ava_lib import
sys.path.insert(0, str(Path(__file__).parent))
from ava_lib import Orchestrator


def main():
    task_id = os.environ.get("TASK_ID", "").strip()
    repo_root = Path(os.environ.get("GITHUB_WORKSPACE", "."))

    orchestrator = Orchestrator(repo_root)

    # Auto-detect next activity from Project if no TASK_ID provided
    if not task_id:
        print("[VASH AvA] No TASK_ID — auto-detecting next activity from Project...")
        activity = orchestrator.project.get_next_activity()
        if activity:
            task_id = activity["task_id"]
            print(f"[VASH AvA] Next activity: {task_id} — {activity['name']}")
        else:
            print("[VASH AvA] No pending activities found in Project")
            sys.exit(0)

    try:
        result = orchestrator.run(task_id)
        print(f"[VASH AvA] Final result: {result}")
    except Exception as e:
        print(f"[VASH AvA] Unexpected error: {e}")
        # Write error summary if possible
        try:
            orchestrator._write_error_summary(task_id, str(e))
        except Exception:
            pass

    # Always exit 0 so commit step runs
    sys.exit(0)


if __name__ == "__main__":
    main()
