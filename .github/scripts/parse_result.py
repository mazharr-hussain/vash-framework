#!/usr/bin/env python3
"""
Parse AvA result and write validation summary.
LAW 1: Python stdlib only
"""
import os, re, sys
from pathlib import Path
from datetime import datetime, timezone

TASK_ID = os.environ.get("TASK_ID", "")
REPO = Path(os.environ.get("GITHUB_WORKSPACE", "."))

def rf(path):
    try: return (REPO / path).read_text(encoding="utf-8")
    except: return ""

def wf(path, content):
    p = REPO / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def update_status(task_id, status):
    content = rf("plan/activity_list.md")
    tid = re.escape(task_id)
    updated = re.sub(rf"(ID: {tid}.*?STATUS:)\s*\w+", rf"\1 {status}", content, flags=re.DOTALL)
    wf("plan/activity_list.md", updated)

if not TASK_ID:
    print("No TASK_ID"); sys.exit(0)

tid = TASK_ID.replace(".", "-")

# Find latest AvA log
ava_log = ""
for i in range(5, 0, -1):
    log = rf(f"audit/ava_logs/{tid}_round{i}.md")
    if log:
        ava_log = log
        break

score = 0
verdict = "FAIL"
if ava_log:
    sm = re.search(r"SCORE:\s*(\d+)", ava_log)
    vm = re.search(r"VERDICT:\s*(APPROVED|MODIFY|FAIL)", ava_log)
    score = int(sm.group(1)) if sm else 0
    verdict = vm.group(1) if vm else "FAIL"

# Get threshold
activity = rf("plan/activity_list.md")
tm = re.search(rf"ID: {re.escape(TASK_ID)}.*?THRESHOLD:\s*(\d+)", activity, re.DOTALL)
threshold = int(tm.group(1)) if tm else 88

if score >= threshold:
    verdict = "APPROVED"

# Get objections for summary
obj_match = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", ava_log, re.DOTALL)
issues = obj_match.group(1).strip() if obj_match else "None"

# Write summary
summary = f"# YOUR REVIEW - Activity {TASK_ID}\n\n"
summary += f"**Score:** {score}/100 (threshold: {threshold})\n"
summary += f"**Verdict:** {verdict}\n\n"
summary += f"**Artifact:** audit/artifacts/{tid}_artifact.md\n\n"
if issues and issues != "NONE":
    summary += f"**Issues Found:**\n{issues}\n\n"
if verdict == "APPROVED":
    summary += f"- APPROVED {TASK_ID}\n"
elif verdict == "MODIFY":
    summary += f"- MODIFY {TASK_ID} [paste corrections]\n"
else:
    summary += f"- REJECTED {TASK_ID} [reason]\n"
summary += f"\nTimestamp: {datetime.now(timezone.utc).isoformat()}"

wf(f"audit/validation/{tid}_summary.md", summary)

# Update status
if verdict == "APPROVED":
    update_status(TASK_ID, "PASS")
elif verdict == "FAIL":
    update_status(TASK_ID, "FAIL")

print(f"Result: {verdict} ({score}/100)")
