#!/usr/bin/env python3
"""
Build Junior and Senior prompts for the current activity.
Outputs as GITHUB_OUTPUT environment variables.
LAW 1: Python stdlib only
"""
import os, re, sys
from pathlib import Path

TASK_ID = os.environ.get("TASK_ID", "")
REPO = Path(os.environ.get("GITHUB_WORKSPACE", "."))
GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT", "")

def rf(path):
    try: return (REPO / path).read_text(encoding="utf-8")
    except: return ""

def get_activity(task_id):
    content = rf("plan/activity_list.md")
    m = re.search(rf"ID: {re.escape(task_id)}\n(.*?)(?=\n---|\Z)", content, re.DOTALL)
    return m.group(0) if m else ""

def get_threshold(task_id):
    m = re.search(r"THRESHOLD:\s*(\d+)", get_activity(task_id))
    return int(m.group(1)) if m else 88

def get_output_path(task_id):
    m = re.search(r"OUTPUT_PATH:\s*(.+)", get_activity(task_id))
    return m.group(1).strip() if m else ""

if not TASK_ID:
    print("No TASK_ID"); sys.exit(1)

tid = TASK_ID.replace(".", "-")
activity = get_activity(TASK_ID)
laws = rf("method/laws.md")
checklist = rf("method/ava/checklists/artifact.md")
threshold = get_threshold(TASK_ID)
output_path = get_output_path(TASK_ID)

# Save prompt file
prompt_path = REPO / f"audit/prompts/{tid}_prompt.md"
prompt_path.parent.mkdir(parents=True, exist_ok=True)

# Get previous objections if any
prev_log = ""
for i in range(3, 0, -1):
    log = rf(f"audit/ava_logs/{tid}_round{i}.md")
    if log:
        prev_log = log
        break

obj_match = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", prev_log, re.DOTALL)
objections = obj_match.group(1).strip() if obj_match and obj_match.group(1).strip() != "NONE" else ""

# Check if artifact already exists
artifact_exists = (REPO / f"audit/artifacts/{tid}_artifact.md").exists()
existing_size = (REPO / f"audit/artifacts/{tid}_artifact.md").stat().st_size if artifact_exists else 0
skip_junior = artifact_exists and existing_size > 200

junior_prompt = f"""You are the VASH 3.0 Junior Creator. TASK: {TASK_ID}

ACTIVITY:
{activity}

LAWS:
{laws}

CHECKLIST:
{checklist}

{"OBJECTIONS TO ADDRESS:" + objections if objections else ""}

INSTRUCTIONS:
1. Read the activity definition carefully
2. Produce the complete artifact - design and planning only, NO code
3. Apply all three VASH laws
4. Write to: audit/artifacts/{tid}_artifact.md
5. Also write to: {output_path}
6. Full content - never summarise

Begin now."""

senior_prompt = f"""You are the VASH 3.0 Senior Validator. TASK: {TASK_ID}
THRESHOLD: {threshold}/100

ACTIVITY:
{activity}

LAWS:
{laws}

CHECKLIST:
{checklist}

INSTRUCTIONS:
1. Read the artifact at: audit/artifacts/{tid}_artifact.md
2. Review adversarially - you have no memory of how it was produced
3. Score 0-100 against checklist and laws
4. Write your review to: audit/ava_logs/{tid}_round1.md

Use EXACTLY this format in the log file:
SCORE: [0-100]
VERDICT: APPROVED / MODIFY / FAIL
CHECKLIST:
[each item]: PASS/FAIL
LAWS:
LAW1 VANILLA: PASS/FAIL - [reason]
LAW2 AGENT: PASS/FAIL - [reason]
LAW3 SKILLS: PASS/FAIL - [reason]
OBJECTIONS:
[numbered list or NONE]
CORRECTIONS:
[exact fixes or NONE]

Begin review now."""

# Save prompt
prompt_path.write_text(junior_prompt, encoding="utf-8")

# Write to GITHUB_OUTPUT
if GITHUB_OUTPUT:
    with open(GITHUB_OUTPUT, 'a') as f:
        f.write(f"junior_prompt<<PROMPT_EOF\n{junior_prompt}\nPROMPT_EOF\n")
        f.write(f"senior_prompt<<PROMPT_EOF\n{senior_prompt}\nPROMPT_EOF\n")
        f.write(f"task_id={TASK_ID}\n")
        f.write(f"skip_junior={str(skip_junior).lower()}\n")
        f.write(f"threshold={threshold}\n")

print(f"Prompts built for {TASK_ID} — skip_junior={skip_junior}")
