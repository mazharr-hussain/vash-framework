#!/usr/bin/env python3
"""
VASH 3.0 — AvA Orchestrator v2
Fixes:
- Pre-creates all output directories before Claude runs
- Generates full prompt before Junior session
- Writes to both runtime/artifacts/ AND canonical output path
- Never overwrites AvA logs — always appends with correct round number
- Always exits 0 so commit step runs
LAW 1: Python stdlib only
LAW 2: Fully automated
LAW 3: Standard patterns
"""

import os, re, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

TASK_ID = os.environ.get("TASK_ID", "")
REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", "."))
MAX_ROUNDS = 3
STALEMATE_MIN = 3


def log(msg):
    print(f"[VASH AvA] {msg}", flush=True)


def rf(path):
    try:
        return (REPO_ROOT / path).read_text(encoding="utf-8")
    except Exception:
        return ""


def wf(path, content):
    full = REPO_ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")


def exists(path):
    return (REPO_ROOT / path).exists()


def pre_authorise_paths(*paths):
    """Pre-create all directories so Claude Code never stalls on permissions."""
    for path in paths:
        full = REPO_ROOT / path
        full.parent.mkdir(parents=True, exist_ok=True)
        if not full.exists():
            full.touch()
    log(f"Pre-authorised {len(paths)} output paths")


def run_claude(prompt):
    """Run Claude Code CLI with prompt."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=300,
            env={**os.environ,
                 "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")}
        )
        output = result.stdout.strip()
        if not output and result.stderr:
            log(f"Claude stderr: {result.stderr[:200]}")
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Claude Code timed out"
    except FileNotFoundError:
        return "ERROR: Claude Code CLI not found"


def get_activity(task_id):
    content = rf("knowledge/activity_list.md")
    pattern = rf"ID: {re.escape(task_id)}\n(.*?)(?=\n---|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(0) if m else ""


def get_output_path(task_id):
    """Get the canonical output path from activity definition."""
    activity = get_activity(task_id)
    m = re.search(r"OUTPUT_PATH:\s*(.+)", activity)
    return m.group(1).strip() if m else ""


def get_threshold(task_id):
    activity = get_activity(task_id)
    m = re.search(r"THRESHOLD:\s*(\d+)", activity)
    return int(m.group(1)) if m else 88


def get_next_round_num(task_id):
    """Find next available round number — never overwrite existing logs."""
    tid = task_id.replace(".", "-")
    n = 1
    while exists(f"runtime/ava_logs/{tid}_round{n}.md"):
        n += 1
    return n


def parse_score(text):
    m = re.search(r"SCORE:\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def parse_verdict(text):
    m = re.search(r"VERDICT:\s*(APPROVED|MODIFY|FAIL)", text)
    return m.group(1) if m else "FAIL"


def update_status(task_id, status):
    content = rf("knowledge/activity_list.md")
    tid = re.escape(task_id)
    updated = re.sub(
        rf"(ID: {tid}.*?STATUS:)\s*\w+",
        rf"\1 {status}", content, flags=re.DOTALL
    )
    wf("knowledge/activity_list.md", updated)


def build_full_prompt(task_id, role, objections=""):
    """Build a complete prompt — not a stub."""
    activity = get_activity(task_id)
    laws = rf("knowledge/laws.md")
    checklist = rf("knowledge/checklists/artifact.md")
    tid = task_id.replace(".", "-")
    output_path = get_output_path(task_id)
    threshold = get_threshold(task_id)

    # Read any dependency artifacts for context
    dep_context = ""
    dep_match = re.search(r"DEPENDS_ON:\s*(.+)", activity)
    if dep_match and dep_match.group(1).strip() != "NONE":
        deps = [d.strip() for d in dep_match.group(1).split(",")]
        for dep in deps[:2]:  # limit to 2 deps to save tokens
            dep_tid = dep.replace(".", "-")
            dep_content = rf(f"runtime/artifacts/{dep_tid}_artifact.md")
            if dep_content:
                dep_context += f"\nDEPENDENCY {dep}:\n{dep_content[:500]}\n"

    if role == "JUNIOR":
        obj_section = ("PREVIOUS SENIOR OBJECTIONS:\n" + objections) if objections else ""
        dep_section = dep_context if dep_context else "None"
        parts = [
            "You are the VASH 3.0 Junior Creator.",
            f"ACTIVITY ID: {task_id}",
            f"ACTIVITY DEFINITION:\n{activity}",
            f"THREE LAWS:\n{laws}",
            f"VALIDATION CHECKLIST:\n{checklist}",
            f"DEPENDENCY CONTEXT:\n{dep_section}",
            obj_section,
            "YOUR TASK:",
            f"Produce the complete artifact for activity {task_id}.",
            "Rules:",
            "- Design and planning only NO actual software code",
            "- Full content never summarise or truncate",
            "- Apply all three VASH laws throughout",
            "- Begin directly with artifact content no preamble",
            "- Do not include process notes or permission commentary",
            "- Write clean artifact content only",
            f"OUTPUT PATH: {output_path}",
            f"THRESHOLD TO PASS: {threshold}/100",
            "Output the complete artifact content now:"
        ]
        return "\n\n".join(p for p in parts if p)

    else:  # SENIOR
        artifact = rf(f"runtime/artifacts/{tid}_artifact.md")
        return f"""You are the VASH 3.0 Senior Validator.
ACTIVITY ID: {task_id}
ACTIVITY DEFINITION:
{activity}

THREE LAWS:
{laws}

VALIDATION CHECKLIST:
{checklist}

ARTIFACT TO REVIEW:
{artifact}

YOUR TASK:
Review this artifact adversarially. You have no memory of how it was produced.
Score 0-100. Check every checklist item.

Output EXACTLY in this format:
SCORE: [0-100]
VERDICT: APPROVED / MODIFY / FAIL
CHECKLIST:
[each checklist item]: PASS/FAIL
LAWS:
LAW1 VANILLA: PASS/FAIL — [one line reason]
LAW2 AGENT: PASS/FAIL — [one line reason]
LAW3 SKILLS: PASS/FAIL — [one line reason]
OBJECTIONS:
[numbered list — or NONE]
CORRECTIONS:
[exact fix per objection — or NONE]"""


def run_ava(task_id):
    if not task_id:
        log("ERROR: No TASK_ID provided")
        sys.exit(1)

    tid = task_id.replace(".", "-")
    threshold = get_threshold(task_id)
    output_path = get_output_path(task_id)
    artifact_path = f"runtime/artifacts/{tid}_artifact.md"

    log(f"Starting AvA for activity {task_id}")
    log(f"Threshold: {threshold} | Output: {output_path}")

    # Pre-authorise ALL output paths before any Claude call
    pre_authorise_paths(
        artifact_path,
        f"runtime/prompts/{tid}_prompt.md",
        f"runtime/ava_logs/{tid}_round1.md",
        f"runtime/validation/{tid}_summary.md",
    )
    if output_path and output_path != "N/A" and output_path != "Multiple files":
        pre_authorise_paths(output_path)

    scores = []
    senior_output = ""
    verdict = "FAIL"
    score = 0

    # Determine starting round
    start_round = get_next_round_num(task_id)
    log(f"Starting from round {start_round}")

    # If artifact exists use it for first Senior pass
    artifact_exists = exists(artifact_path) and (REPO_ROOT / artifact_path).stat().st_size > 100

    for round_num in range(start_round, start_round + MAX_ROUNDS):
        log(f"Round {round_num}")

        # Get objections from previous round
        objections = ""
        if round_num > 1:
            prev = rf(f"runtime/ava_logs/{tid}_round{round_num-1}.md")
            obj_m = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", prev, re.DOTALL)
            if obj_m:
                objections = obj_m.group(1).strip()

        # Junior — skip on first round if artifact already exists
        if round_num == start_round and artifact_exists:
            log("Existing artifact found — skipping Junior generation")
        else:
            log("Junior generating artifact...")
            junior_prompt = build_full_prompt(task_id, "JUNIOR", objections)
            # Save full prompt
            wf(f"runtime/prompts/{tid}_prompt.md", junior_prompt)
            junior_output = run_claude(junior_prompt)

            if not junior_output or junior_output.startswith("ERROR"):
                log(f"Junior failed: {junior_output}")
                wf(artifact_path, f"# Junior generation failed\n{junior_output}")
            else:
                # Strip any process notes from beginning/end
                lines = junior_output.split('\n')
                # Remove lines that are process commentary
                clean_lines = [l for l in lines if not any(x in l.lower() for x in
                    ['write permission', 'not pre-authorized', 'process note', 'note to orchestrator'])]
                clean_output = '\n'.join(clean_lines).strip()
                wf(artifact_path, clean_output)
                # Also write to canonical output path
                if output_path and output_path != "N/A" and output_path != "Multiple files":
                    wf(output_path, clean_output)
                log(f"Artifact saved to {artifact_path}")

        # Senior review
        log("Senior reviewing artifact...")
        senior_prompt = build_full_prompt(task_id, "SENIOR")
        senior_output = run_claude(senior_prompt)

        score = parse_score(senior_output)
        verdict = parse_verdict(senior_output)
        scores.append(score)
        log(f"Round {round_num} score: {score}/100 — {verdict}")

        # Save AvA log with correct round number
        next_round = get_next_round_num(task_id)
        ava_log = f"# AvA Log — Activity {task_id} Round {next_round}\n"
        ava_log += f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n\n"
        ava_log += senior_output
        wf(f"runtime/ava_logs/{tid}_round{next_round}.md", ava_log)

        if score >= threshold:
            verdict = "APPROVED"
            log(f"APPROVED — score {score} meets threshold {threshold}")
            break

        # Stalemate check
        if len(scores) >= 2:
            improvement = scores[-1] - scores[-2]
            if abs(improvement) < STALEMATE_MIN:
                log(f"Stalemate detected — improvement {improvement}")
                if score >= 80:
                    verdict = "APPROVED"
                    log("Score >= 80 — auto-approving")
                else:
                    verdict = "ESCALATE"
                    log("Score < 80 — escalating")
                break

        if round_num >= start_round + MAX_ROUNDS - 1:
            log(f"Max rounds reached — final: {verdict}")
            break

    # Write validation summary
    summary = f"# YOUR REVIEW — Activity {task_id}\n\n"
    summary += f"**Score:** {score}/100\n"
    summary += f"**Verdict:** {verdict}\n\n"
    summary += f"**Artifact:** {artifact_path}\n\n"
    if verdict == "APPROVED":
        summary += f"→ APPROVED {task_id}\n"
    elif verdict == "MODIFY":
        obj_m = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", senior_output, re.DOTALL)
        issues = obj_m.group(1).strip() if obj_m else "See AvA log"
        summary += f"**Issues:**\n{issues}\n\n→ MODIFY {task_id} [corrections]\n"
    else:
        summary += f"→ REJECTED {task_id} [reason]\n"

    wf(f"runtime/validation/{tid}_summary.md", summary)

    # Update activity status
    if verdict == "APPROVED":
        update_status(task_id, "PASS")
    elif verdict in ("FAIL", "ESCALATE"):
        update_status(task_id, "FAIL")

    log(f"AvA complete — {verdict} ({score}/100)")
    sys.exit(0)  # Always exit 0 so commit runs


if __name__ == "__main__":
    run_ava(TASK_ID)
