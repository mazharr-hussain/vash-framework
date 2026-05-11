#!/usr/bin/env python3
"""
VASH 3.0 — Parallel Activity Orchestrator
Identifies and runs PARALLEL_SAFE activities concurrently.
LAW 1: Python stdlib only
LAW 2: Full automation
LAW 3: Standard concurrent.futures pattern
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", "."))


def log(msg):
    print(f"[VASH Parallel] {msg}", flush=True)


def read_file(path):
    try:
        return (REPO_ROOT / path).read_text(encoding="utf-8")
    except Exception:
        return ""


def get_parallel_activities():
    """Find all PENDING PARALLEL_SAFE activities whose dependencies are PASS."""
    content = read_file("knowledge/activity_list.md")
    activities = []

    pattern = r"ID:\s*(\S+)\n.*?PARALLEL_SAFE:\s*(YES|NO)\n.*?DEPENDS_ON:\s*([^\n]+)\n.*?STATUS:\s*(\w+)"
    for match in re.finditer(pattern, content, re.DOTALL):
        task_id = match.group(1)
        parallel_safe = match.group(2)
        depends_on = match.group(3).strip()
        status = match.group(4)

        if parallel_safe != "YES" or status != "PENDING":
            continue

        # Check all dependencies are PASS
        if depends_on != "NONE":
            deps = [d.strip() for d in depends_on.split(",")]
            deps_met = all(
                f"ID: {dep}\n" in content and
                re.search(rf"ID: {re.escape(dep)}.*?STATUS:\s*PASS", content, re.DOTALL)
                for dep in deps
            )
            if not deps_met:
                continue

        activities.append(task_id)

    return activities


def run_ava_for_activity(task_id):
    """Run ava.py for a single activity."""
    import subprocess
    result = subprocess.run(
        ["python", ".github/scripts/ava.py"],
        env={**os.environ, "TASK_ID": task_id},
        capture_output=True,
        text=True,
        timeout=600
    )
    return task_id, result.returncode, result.stdout, result.stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--find-only", action="store_true")
    args = parser.parse_args()

    activities = get_parallel_activities()
    log(f"Found {len(activities)} parallel-safe pending activities: {activities}")

    if args.find_only:
        # Output matrix format for GitHub Actions
        matrix = {"include": [{"task_id": a} for a in activities]}
        print(json.dumps(matrix))
        return

    if not activities:
        log("No parallel activities to run")
        return

    results = {}
    with ThreadPoolExecutor(max_workers=min(len(activities), 5)) as executor:
        futures = {executor.submit(run_ava_for_activity, a): a for a in activities}
        for future in as_completed(futures):
            task_id, code, stdout, stderr = future.result()
            results[task_id] = "PASS" if code == 0 else "FAIL"
            log(f"Activity {task_id}: {'PASS' if code == 0 else 'FAIL'}")
            if stdout:
                print(stdout)

    passed = sum(1 for v in results.values() if v == "PASS")
    log(f"Parallel run complete: {passed}/{len(activities)} passed")


if __name__ == "__main__":
    main()
