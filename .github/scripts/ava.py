#!/usr/bin/env python3
"""
VASH 3.0 — AvA Orchestrator
Manages the complete AvA loop for a single activity.
Runs on GitHub Actions VM using Claude Code CLI with OAuth token.
LAW 1: Python stdlib only — no pip installs
LAW 2: Fully automated — no manual steps
LAW 3: Standard subprocess patterns — no reinvention

SMART RESUME: If artifact already exists, runs validation only.
If artifact does not exist, runs full Junior → Senior AvA loop.
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
STALEMATE_THRESHOLD = 3


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


def file_exists(path):
    return (REPO_ROOT / path).exists()


def run_claude(prompt):
    """Run Claude Code CLI with a prompt."""
    cmd = ["claude", "--print", "--no-markdown", prompt]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ,
                 "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")}
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Claude Code timed out after 300 seconds"
    except FileNotFoundError:
        return "ERROR: Claude Code CLI not found"


def get_activity(task_id):
    content = read_file("knowledge/activity_list.md")
    pattern = rf"ID: {re.escape(task_id)}\n(.*?)(?=\n---|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""


def get_threshold(task_id):
    activity = get_activity(task_id)
    match = re.search(r"THRESHOLD:\s*(\d+)", activity)
    return int(match.group(1)) if match else 88


def parse_score(text):
    match = re.search(r"SCORE:\s*(\d+)", text)
    return int(match.group(1)) if match else 0


def parse_verdict(text):
    match = re.search(r"VERDICT:\s*(APPROVED|MODIFY|FAIL)", text)
    return match.group(1) if match else "FAIL"


def update_activity_status(task_id, status):
    content = read_file("knowledge/activity_list.md")
    tid = re.escape(task_id)
    pattern = rf"(ID: {tid}.*?STATUS:)\s*\w+"
    updated = re.sub(pattern, rf"\1 {status}", content, flags=re.DOTALL)
    write_file("knowledge/activity_list.md", updated)


def run_senior_validation(task_id, artifact_content, round_num=1):
    """Run Senior validation on existing or new artifact."""
    tid = task_id.replace(".", "-")
    threshold = get_threshold(task_id)
    activity = get_activity(task_id)
    laws = read_file("knowledge/laws.md")
    checklist = read_file("knowledge/checklists/artifact.md")

    log(f"Senior validating artifact — round {round_num}")

    senior_prompt = f"""You are the VASH 3.0 Senior Validator.
Activity: {activity}
Laws: {laws}
Checklist: {checklist}
Artifact to review:
{artifact_content}

Review this artifact independently and adversarially.
Score 0-100. Check every checklist item.
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

    senior_output = run_claude(senior_prompt)
    score = parse_score(senior_output)
    verdict = parse_verdict(senior_output)

    # Save AvA log
    ava_log = f"# AvA Log — Activity {task_id} Round {round_num}\n"
    ava_log += f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
    ava_log += f"MODE: {'VALIDATION ONLY (artifact existed)' if round_num == 1 else 'FULL AVA'}\n\n"
    ava_log += senior_output
    write_file(f"runtime/ava_logs/{tid}_round{round_num}.md", ava_log)

    log(f"Score: {score}/100 — {verdict} (threshold: {threshold})")
    return score, verdict, senior_output, threshold


def run_junior_creation(task_id, objections=""):
    """Run Junior creation for a new artifact."""
    tid = task_id.replace(".", "-")
    activity = get_activity(task_id)
    laws = read_file("knowledge/laws.md")
    checklist = read_file("knowledge/checklists/artifact.md")

    log("Junior generating artifact...")

    junior_prompt = f"""You are the VASH 3.0 Junior Creator.
Activity: {activity}
Laws: {laws}
Checklist: {checklist}
{"Previous objections to address: " + objections if objections else ""}

Produce the complete artifact for this activity.
Design and planning only — no actual software code.
Full content — never summarise.
Apply all three VASH laws.
Output the artifact content only."""

    output = run_claude(junior_prompt)
    write_file(f"runtime/artifacts/{tid}_artifact.md", output)
    log(f"Artifact saved: runtime/artifacts/{tid}_artifact.md")
    return output


def write_summary(task_id, score, verdict, senior_output):
    """Write owner-facing summary."""
    tid = task_id.replace(".", "-")
    summary = f"# YOUR REVIEW — Activity {task_id}\n\n"
    summary += f"**Score:** {score}/100\n"
    summary += f"**Verdict:** {verdict}\n\n"
    summary += f"**Artifact:** runtime/artifacts/{tid}_artifact.md\n\n"

    # Extract Senior summary if available
    sum_match = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", senior_output, re.DOTALL)
    if sum_match and sum_match.group(1).strip() not in ("NONE", ""):
        summary += f"**Issues Found:**\n{sum_match.group(1).strip()}\n\n"

    if verdict == "APPROVED":
        summary += f"→ APPROVED {task_id}\n"
    elif verdict == "MODIFY":
        summary += f"→ MODIFY {task_id} [paste specific corrections]\n"
    else:
        summary += f"→ REJECTED {task_id} [reason]\n"

    write_file(f"runtime/validation/{tid}_summary.md", summary)


def run_ava_loop(task_id):
    if not task_id:
        log("ERROR: No TASK_ID provided")
        sys.exit(1)

    tid = task_id.replace(".", "-")
    artifact_path = f"runtime/artifacts/{tid}_artifact.md"
    ava_log_path = f"runtime/ava_logs/{tid}_round1.md"

    log(f"Starting AvA for activity {task_id}")

    # ── SMART RESUME: Check if artifact already exists ─────
    if file_exists(artifact_path) and file_exists(ava_log_path):
        log("Artifact and AvA log already exist — running validation only")
        artifact_content = read_file(artifact_path)
        score, verdict, senior_output, threshold = run_senior_validation(
            task_id, artifact_content, round_num=1
        )

        # If existing artifact passes — done
        if score >= threshold:
            verdict = "APPROVED"
            log(f"Existing artifact APPROVED — score {score}/{threshold}")
        else:
            log(f"Existing artifact needs improvement — score {score}/{threshold}")
            # Run one revision round
            objections = re.search(
                r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", senior_output, re.DOTALL
            )
            obj_text = objections.group(1).strip() if objections else ""
            artifact_content = run_junior_creation(task_id, obj_text)
            score, verdict, senior_output, threshold = run_senior_validation(
                task_id, artifact_content, round_num=2
            )
            if score >= threshold:
                verdict = "APPROVED"

    else:
        # ── FULL AVA LOOP: No existing artifact ────────────
        log("No existing artifact — running full AvA loop")
        scores = []

        for round_num in range(1, MAX_ROUNDS + 1):
            log(f"Round {round_num}/{MAX_ROUNDS}")

            # Get objections from previous round
            objections = ""
            if round_num > 1:
                prev_log = read_file(f"runtime/ava_logs/{tid}_round{round_num-1}.md")
                obj_match = re.search(
                    r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", prev_log, re.DOTALL
                )
                objections = obj_match.group(1).strip() if obj_match else ""

            artifact_content = run_junior_creation(task_id, objections)
            score, verdict, senior_output, threshold = run_senior_validation(
                task_id, artifact_content, round_num
            )
            scores.append(score)

            if score >= threshold:
                verdict = "APPROVED"
                break

            # Stalemate check
            if len(scores) >= 2:
                improvement = scores[-1] - scores[-2]
                if improvement < STALEMATE_THRESHOLD:
                    log(f"Stalemate — improvement {improvement} < {STALEMATE_THRESHOLD}")
                    if score >= 80:
                        verdict = "APPROVED"
                        log("Score >= 80 — auto-approving")
                    else:
                        verdict = "ESCALATE"
                        log("Score < 80 — escalating to human")
                    break

            if round_num == MAX_ROUNDS:
                log(f"Max rounds reached — final: {verdict}")

    # ── WRITE SUMMARY AND UPDATE STATUS ───────────────────
    write_summary(task_id, score, verdict, senior_output)

    if verdict == "APPROVED":
        update_activity_status(task_id, "PASS")
    elif verdict in ("FAIL", "ESCALATE"):
        update_activity_status(task_id, "FAIL")

    log(f"AvA complete — {verdict} ({score}/100)")
    return verdict


if __name__ == "__main__":
    result = run_ava_loop(TASK_ID)
    sys.exit(0 if result == "APPROVED" else 1)
