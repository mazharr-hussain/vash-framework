# VASH 3.0 — Agent Handshake Contracts

## What Are Handshakes

Handshakes are the defined data contracts between agents at every role-to-role transition. They specify exactly what data is passed, in what format, and what validation must pass before the handoff is accepted.

---

## Handshake 1: Human Owner → Project Manager

**Trigger:** Human submits project brief

**Data Passed:**
```
BRIEF:
  project_name: string (required)
  domain: string (required) — industry/sector
  problem_statement: string (required) — what problem to solve
  target_users: string (required) — who will use it
  constraints: string (optional) — budget, timeline, tech preferences
  out_of_scope: string (optional) — what NOT to build
```

**Validation Rules:**
- project_name must be present and non-empty
- problem_statement must be > 50 characters
- target_users must be present
- If any required field missing → PM returns template to human

**Format:** GitHub Issue body or plain text in P1 chat

---

## Handshake 2: Prompt Engineer → Junior Creator

**Trigger:** PM identifies activity to run

**Data Passed:**
```
LOCKED_PROMPT:
  activity_id: string (required)
  activity_name: string (required)
  task_description: string (required)
  laws_reference: string — path to knowledge/laws.md
  checklist_reference: string — path to relevant checklist
  dependency_artifacts: list[string] — paths to read
  output_path: string (required)
  output_format: string (required)
  threshold: integer (required)
  do_not: list[string] — common mistakes to avoid
```

**Validation Rules:**
- All required fields must be present
- output_path must be within runtime/ or vash_framework/
- threshold must be integer between 70 and 100
- dependency_artifacts paths must exist in repo

**Format:** Saved to runtime/prompts/[task_id]_prompt.md

---

## Handshake 3: Junior Creator → Senior Validator

**Trigger:** Junior completes artifact generation

**Data Passed:**
```
ARTIFACT_REFERENCE:
  task_id: string (required)
  artifact_path: string — runtime/artifacts/[task_id]_artifact.md
  activity_id: string (required)
  round_number: integer (required)
  checklist_path: string (required)
  laws_path: string — knowledge/laws.md
```

**IMPORTANT — What Is NOT Passed:**
- Junior's reasoning or thought process
- Previous Senior objections (Senior reads ava_log directly)
- Any context from Junior's session

**Validation Rules:**
- artifact_path must exist and be non-empty
- Senior reads artifact fresh — no Junior context injected

**Format:** Environment variables passed to Senior Claude session

---

## Handshake 4: Senior Validator → AvA Orchestrator

**Trigger:** Senior completes review

**Data Passed:**
```
AVA_RESULT:
  task_id: string (required)
  round_number: integer (required)
  score: integer 0-100 (required)
  verdict: enum [APPROVED, MODIFY, FAIL] (required)
  checklist_results: dict[item: PASS/FAIL] (required)
  law_results: dict[LAW1/LAW2/LAW3: PASS/FAIL] (required)
  objections: list[{id, location, issue}] (required if MODIFY/FAIL)
  corrections: list[{objection_id, exact_fix}] (required if MODIFY/FAIL)
```

**Validation Rules:**
- score must be integer 0-100
- If verdict is MODIFY or FAIL, objections list must not be empty
- Each objection must have exact location in artifact
- Each correction must reference an objection_id

**Format:** Saved to runtime/ava_logs/[task_id]_round[n].md

---

## Handshake 5: AvA Orchestrator → Human Owner

**Trigger:** Artifact passes AvA threshold OR escalation triggered

**Data Passed (PASS case):**
```
HUMAN_SUMMARY:
  task_id: string (required)
  activity_name: string (required)
  score: integer (required)
  verdict: APPROVED (required)
  summary: string — 2 plain English sentences
  artifact_path: string
  decision_options: list[string] — APPROVED/REJECTED/MODIFY
```

**Data Passed (ESCALATION case):**
```
ESCALATION_SUMMARY:
  task_id: string (required)
  activity_name: string (required)
  reason: string (required) — why escalated
  rounds_completed: integer (required)
  score_trend: list[integer] — scores per round
  last_objections: list[string]
  recommended_action: string
```

**Validation Rules:**
- Summary must be plain English — no technical jargon
- Decision options must be explicitly stated
- Escalation must include recommended action

**Format:** GitHub Issue created by notify.yml + runtime/validation/[task_id]_summary.md

---

## Handshake 6: Group Lead → Next Group Lead

**Trigger:** All activities in a group reach PASS + Human APPROVED

**Data Passed:**
```
GROUP_HANDOFF:
  group_id: string (required)
  group_name: string (required)
  completed_artifacts: list[{activity_id, path, score}] (required)
  key_decisions: list[string] — most important decisions made
  constraints_for_next_group: list[string] — what next group must respect
  open_questions: list[string] — unresolved items next group should address
```

**Validation Rules:**
- All completed_artifacts must have STATUS: PASS in activity_list.md
- key_decisions must reference specific ADR or artifact paths
- open_questions must be documented even if empty list

**Format:** Saved to vash_framework/[group_folder]/handoff.md

---

## Handshake 7: VASH → Human Owner (Project Complete)

**Trigger:** All groups complete and blueprint approved

**Data Passed:**
```
PROJECT_DELIVERABLE:
  project_name: string (required)
  total_artifacts: integer (required)
  artifact_index: list[{activity_id, name, path, score}] (required)
  blueprint_path: string (required)
  total_ava_rounds: integer (required)
  average_ava_score: float (required)
  law_compliance: dict[LAW1/LAW2/LAW3: percentage]
  known_limitations: list[string]
  recommended_next_steps: list[string]
```

**Format:** vash_framework/blueprint/project_deliverable.md

---

## Handshake Validation Summary

| Handshake | From | To | Critical Field |
|-----------|------|----|----------------|
| 1 | Human | PM | problem_statement |
| 2 | Prompt Eng | Junior | output_path |
| 3 | Junior | Senior | artifact_path (no context) |
| 4 | Senior | Orchestrator | score + objections |
| 5 | Orchestrator | Human | plain English summary |
| 6 | Group Lead | Next Group | constraints_for_next_group |
| 7 | VASH | Human | blueprint_path |
