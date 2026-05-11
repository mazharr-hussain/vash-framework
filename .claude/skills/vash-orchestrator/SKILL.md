---
name: vash-orchestrator
description: Manage the complete VASH AvA loop from start to finish. Use to run a full activity end-to-end including prompt generation, Junior creation, Senior review, loop management, and result saving. Handles parallel activities, stalemate detection, and escalation. Built custom — no marketplace equivalent for VASH-specific AvA orchestration.
---

# VASH Orchestrator Skill

## Source
BUILT NEW — no marketplace equivalent found.
Search log: .claude/skills/search_log.md
Reason: VASH-specific AvA loop, activity list integration,
and escalation rules require custom implementation.
Uses multi-agent-patterns skill for loop structure.

## When To Use
- To run any single activity end-to-end
- To run a group of PARALLEL_SAFE activities
- When managing AvA loop from Python script on GitHub VM

## Single Activity Orchestration

```
STEP 1: PROMPT
Invoke: prompt-engineer skill
Input: activity ID
Output: locked prompt saved to runtime/prompts/

STEP 2: CREATE (Junior)
Invoke: vash-creator skill with locked prompt
Output: artifact saved to runtime/artifacts/

STEP 3: VALIDATE (Senior)
Invoke: vash-validator skill
Output: score and verdict in runtime/ava_logs/

STEP 4: EVALUATE
Read score from ava_log.
IF score ≥ threshold → DONE → notify human
IF score < threshold AND round < 3 → LOOP back to STEP 2
   Pass objections and corrections to Junior
IF round = 3 → check stalemate

STEP 5: STALEMATE CHECK
Read last 2 rounds from ava_logs.
IF score improvement < 3 points:
  Score ≥ 80 → AUTO-APPROVE with warning flag
  Score 70-79 → ESCALATE to human
  Score < 70 → FAIL
IF no stalemate → continue loop

STEP 6: FINAL SAVE
Move artifact from runtime/drafts/ to runtime/artifacts/
Write summary to runtime/validation/[task_id]_summary.md
Update STATUS in knowledge/activity_list.md
```

## Parallel Activity Orchestration

```
STEP 1: READ ACTIVITY LIST
Identify all PENDING activities with PARALLEL_SAFE: YES
Check DEPENDS_ON — skip if dependency not PASS

STEP 2: SPAWN PARALLEL SESSIONS
For each parallel activity:
  Run complete single activity orchestration
  Each runs independently — no shared context

STEP 3: COLLECT RESULTS
Wait for all parallel sessions to complete
Compile results into consolidated summary

STEP 4: HUMAN NOTIFICATION
Send consolidated summary to human
List all activities with scores and verdicts
Present as single approval decision
```

## Human Notification Format
```
════ VASH ACTIVITY COMPLETE ════
ACTIVITY: [ID] — [Name]
TYPE: [ARTIFACT/MANUAL]
AVA ROUNDS: [n]
SCORE: [score]/100
VERDICT: [APPROVED/MODIFY/FAIL]
ARTIFACT: runtime/artifacts/[task_id]_artifact.md

SUMMARY: [2 plain English sentences]

→ APPROVED [task_id] — proceed to next
→ REJECTED [task_id] [reason] — rebuild
→ MODIFY [task_id] [correction] — fix and resubmit
════════════════════════════════
```

## Escalation Triggers
Escalate to human immediately if:
- Score < 60 after any round
- MODIFY cycle count ≥ 2
- LAW 1 violation detected
- Code found in design artifact
