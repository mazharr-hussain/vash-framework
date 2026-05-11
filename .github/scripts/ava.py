#!/usr/bin/env python3
"""
VASH 3.0 — AvA Orchestrator
Manages the complete AvA loop for a single activity.
Runs on GitHub Actions VM using Claude Code CLI with OAuth token.
LAW 1: Python stdlib only — no pip installs
LAW 2: Fully automated — no manual steps
LAW 3: Standard subprocess patterns — no reinvention
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

TASK_ID = os.environ.get("TASK_ID", "")
REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", "."))
MAX_ROUNDS = 3
STALEMATE_THRESHOLD = 3  # score improvement below this = stalemate


def log(msg):
    print(f"[VASH AvA] {msg}", flush=True)


def read_file(path):
    try:
        return (REPO_ROOT / path).read_text(encoding="utf-8")
    except Exception:
        return ""


def write_file(path, content):
    full_path = REPO_ROOT / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


def run_claude(prompt, context_files=None):
    """Run Claude Code CLI with a prompt and optional context files."""
    cmd = ["claude", "--print", "--no-markdown"]
    if context_files:
        for f in context_files:
            cmd += ["--add-dir", str(REPO_ROOT / f)]
    cmd += [prompt]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")}
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Claude Code timed out after 300 seconds"
    except FileNotFoundError:
        return "ERROR: Claude Code CLI not found — ensure npm install -g @anthropic-ai/claude-code ran"


def get_activity(task_id):
    """Read current activity from activity list."""
    content = read_file("knowledge/activity_list.md")
    pattern = rf"ID: {re.escape(task_id)}\n(.*?)(?=\n---|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""


def get_threshold(task_id):
    """Extract threshold from activity."""
    activity = get_activity(task_id)
    match = re.search(r"THRESHOLD:\s*(\d+)", activity)
    return int(match.group(1)) if match else 88


def parse_score(text):
    """Extract score from Senior review output."""
    match = re.search(r"SCORE:\s*(\d+)", text)
    return int(match.group(1)) if match else 0


def parse_verdict(text):
    """Extract verdict from Senior review output."""
    match = re.search(r"VERDICT:\s*(APPROVED|MODIFY|FAIL)", text)
    return match.group(1) if match else "FAIL"


def update_activity_status(task_id, status):
    """Update activity STATUS in activity_list.md."""
    content = read_file("knowledge/activity_list.md")
    tid = re.escape(task_id)
    pattern = rf"(ID: {tid}.*?STATUS:)\s*\w+"
    updated = re.sub(pattern, rf"\1 {status}", content, flags=re.DOTALL)
    write_file("knowledge/activity_list.md", updated)


def run_ava_loop(task_id):
    """Run complete AvA loop for given task ID."""
    if not task_id:
        log("ERROR: No TASK_ID provided")
        sys.exit(1)

    log(f"Starting AvA loop for activity {task_id}")
    threshold = get_threshold(task_id)
    tid = task_id.replace(".", "-")
    laws = read_file("knowledge/laws.md")
    activity = get_activity(task_id)
    checklist = read_file("knowledge/checklists/artifact.md")

    scores = []

    for round_num in range(1, MAX_ROUNDS + 1):
        log(f"Round {round_num}/{MAX_ROUNDS}")

        # ── JUNIOR: Generate artifact ──────────────────────
        objections = ""
        if round_num > 1:
            prev_log = read_file(f"runtime/ava_logs/{tid}_round{round_num-1}.md")
            obj_match = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|SCORE:|\Z)", prev_log, re.DOTALL)
            objections = obj_match.group(1).strip() if obj_match else ""

        junior_prompt = f"""You are the VASH Junior Creator.
Activity: {activity}
Laws: {laws}
Checklist: {checklist}
{"Previous objections to address: " + objections if objections else ""}

Produce the complete artifact for this activity.
Design and planning only — no actual software code.
Full content — never summarise.
Apply all three laws.
Save to runtime/artifacts/{tid}_artifact.md
Output the artifact content only."""

        log("Junior generating artifact...")
        junior_output = run_claude(junior_prompt)
        write_file(f"runtime/artifacts/{tid}_artifact.md", junior_output)
        log(f"Artifact saved: runtime/artifacts/{tid}_artifact.md")

        # ── SENIOR: Review artifact ─────────────────────────
        senior_prompt = f"""You are the VASH Senior Validator.
Activity: {activity}
Laws: {laws}
Checklist: {checklist}
Artifact to review:
{junior_output}

Review this artifact independently.
Score 0-100. Check all checklist items.
Output in this exact format:
SCORE: [number]
VERDICT: APPROVED / MODIFY / FAIL
CHECKLIST:
[item]: PASS/FAIL
LAWS:
LAW1 VANILLA: PASS/FAIL — [reason]
LAW2 AGENT: PASS/FAIL — [reason]
LAW3 SKILLS: PASS/FAIL — [reason]
OBJECTIONS:
[numbered list or NONE]
CORRECTIONS:
[exact fixes or NONE]"""

        log("Senior reviewing artifact...")
        senior_output = run_claude(senior_prompt)
        score = parse_score(senior_output)
        verdict = parse_verdict(senior_output)
        scores.append(score)
        log(f"Round {round_num} score: {score}/100 — {verdict}")

        # Save AvA log
        ava_log = f"# AvA Log — Activity {task_id} Round {round_num}\n"
        ava_log += f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n\n"
        ava_log += senior_output
        write_file(f"runtime/ava_logs/{tid}_round{round_num}.md", ava_log)

        # ── EVALUATE ───────────────────────────────────────
        if score >= threshold:
            log(f"APPROVED — score {score} meets threshold {threshold}")
            verdict = "APPROVED"
            break

        # Stalemate detection
        if len(scores) >= 2:
            improvement = scores[-1] - scores[-2]
            if improvement < STALEMATE_THRESHOLD:
                log(f"Stalemate detected — improvement {improvement} < {STALEMATE_THRESHOLD}")
                if score >= 80:
                    log("Score >= 80 — auto-approving with warning")
                    verdict = "APPROVED"
                    break
                else:
                    log("Score < 80 — escalating to human")
                    verdict = "ESCALATE"
                    break

        if round_num == MAX_ROUNDS:
            log(f"Max rounds reached — final verdict: {verdict}")

    # ── WRITE SUMMARY ──────────────────────────────────────
    summary = f"# YOUR REVIEW — Activity {task_id}\n\n"
    summary += f"**Score:** {score}/100\n"
    summary += f"**Verdict:** {verdict}\n\n"
    summary += f"**Artifact:** runtime/artifacts/{tid}_artifact.md\n\n"
    if verdict == "APPROVED":
        summary += f"→ APPROVED {task_id} — proceed to next activity\n"
    elif verdict == "MODIFY":
        summary += f"→ MODIFY {task_id} [paste corrections]\n"
    else:
        summary += f"→ REJECTED {task_id} [reason] — rebuild required\n"

    write_file(f"runtime/validation/{tid}_summary.md", summary)

    # Update activity status
    if verdict == "APPROVED":
        update_activity_status(task_id, "PASS")
    elif verdict in ("FAIL", "ESCALATE"):
        update_activity_status(task_id, "FAIL")

    log(f"AvA complete — {verdict} ({score}/100)")
    return verdict


if __name__ == "__main__":
    result = run_ava_loop(TASK_ID)
    sys.exit(0 if result in ("APPROVED",) else 1)
