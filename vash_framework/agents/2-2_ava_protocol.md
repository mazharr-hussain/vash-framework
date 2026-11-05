# VASH 3.0 — AvA Protocol Rulebook
Amendments marked "Amended by 2.6" are PROPOSED: they take effect when ADR-001 is ACCEPTED; until then the earlier text (git history) applies.

## What Is AvA

Agent vs Agent (AvA) is the adversarial quality control mechanism built into every VASH activity. Every artifact is produced by a Junior agent and challenged by a Senior agent before any human sees it. The two agents run in isolated context windows — the Senior has no memory of how the Junior produced the artifact.

---

## Layer 1: Internal AvA (Within Activity)

This runs inside every single activity automatically.

### Participants
- **Junior Creator:** Generates the artifact. Model from the pool configuration (Amended by 2.6).
- **Senior Validator:** Reviews the artifact adversarially. Runs on a different vendor from the Junior
  (rule R4); owner exception for VASH's own development while it uses Claude (OD-1): same vendor
  allowed, isolated contexts, preferably different models, canary checks once the injector exists
  (7.9).

### Flow
```
ROUND N:
1. Junior receives locked prompt from Prompt Engineer
2. Junior generates artifact
3. Artifact saved to runtime/drafts/[task_id]_draft.md
3a. Gate 1 (deterministic, Amended by 2.6): format, required sections, links, schema, secret scan,
    no-code check for design artifacts; for code, tests and linters. A Gate 1 failure returns to the
    Junior with the failure list; the Senior is not invoked and the round is not scored.
4. Senior receives artifact + checklist (no Junior context)
5. Senior scores 0-100 and lists objections
6. Score saved to runtime/ava_logs/[task_id]_round[n].md

EVALUATE:
Score ≥ threshold → APPROVED → artifact promoted to runtime/artifacts/
Score < threshold AND round < 3 → Junior addresses objections → repeat
Round = 3 → stalemate check
Round = 3, below threshold, no stalemate → ESCALATE to human, never APPROVED (Amended by 2.6)
```

### Scoring Rules
- Score ≥ threshold: APPROVED
- Score 10+ below threshold: MODIFY (Junior revises)
- Score 20+ below threshold after round 2: FAIL
- Any LAW 1 violation: automatic FAIL regardless of score
- Any code found in design artifact: automatic FAIL

### Stalemate Detection
Triggered when score improvement < 3 points over 2 consecutive rounds.

| Score + Stalemate | Action (Amended by 2.6 — no approval below threshold, rule R5) |
|-------------------|--------|
| ≥ threshold | APPROVED (normal rule) |
| 70 to below threshold | ESCALATE to human with the score trend |
| < 70 | FAIL — rebuild from scratch |

### Thresholds By Artifact Type

| Artifact Type | Minimum Score | Reason |
|---------------|--------------|--------|
| Architecture decision | 90 | Critical — high impact if wrong |
| Technology selection | 90 | Critical — lock-in risk |
| Vision / objectives | 90 | Critical — north star document |
| Agent registry | 90 | Critical — defines all roles |
| AvA protocol | 90 | Critical — governs all quality |
| SDLC phases | 90 | Critical — governs all workflow |
| Platform design | 88 | High importance |
| Process / workflow | 88 | High importance |
| Skills catalog | 88 | High importance |
| Manual step plan | 88 | Standard (raised to the floor by 2.6) |
| Stakeholder map | 88 | Standard (raised to the floor by 2.6) |
| Reference document | 88 | Standard (raised to the floor by 2.6) |

Floor (Amended by 2.6, rule R5): no threshold is below 88. Thresholds are read from the activity list
(VASH) or the project's project-stack.json (projects); a value below 88 is refused by Stage 0. The floor applies from activity 2.6 onward; completed activities keep their recorded thresholds.

---

## Layer 2: Cross-Role AvA (Between Roles)

This runs for critical artifacts where a second perspective from a different role adds value.

### When Triggered
- Architecture artifacts → SA Senior reviews + additional senior-architect skill pass
- Technology decisions → SA Senior + DE Senior both review
- Security-sensitive designs → SE Senior + DevOps Senior both review

### Flow
```
Primary Senior reviews → score A
Secondary Senior (different role) reviews → score B
Final score = lower of A and B
Both objections lists merged
Junior addresses all objections
```

### Cross-Role Pairs
| Primary Role | Cross-Reviewer | Artifact Type |
|--------------|----------------|---------------|
| Solution Architect | DevOps Engineer | Infrastructure design |
| Data Engineer | Software Engineer | API + data model |
| AI/ML Engineer | QA Engineer | AI evaluation framework |
| DevOps Engineer | Solution Architect | CI/CD pipeline |

---

## Layer 3: Human Gateway

This runs after Internal AvA passes. Human sees a plain-English summary only.

### What Human Receives
```
════ VASH ACTIVITY COMPLETE ════
ACTIVITY: [ID] — [Name]
SCORE: [score]/100
VERDICT: APPROVED

SUMMARY: [2 plain English sentences]

→ APPROVED [task_id]
→ REJECTED [task_id] [reason]
→ MODIFY [task_id] [correction]
════════════════════════════════
```

### Human Decision Rules
| Decision | When | Effect |
|----------|------|--------|
| APPROVED | Artifact meets expectations | Pipeline proceeds to next activity |
| REJECTED | Artifact misses the mark entirely | Junior rebuilds from scratch |
| MODIFY | Minor corrections needed | Junior applies specific corrections and resubmits |

### Human Is Never Asked To
- Review AvA debate logs
- Score artifacts
- Choose between technical alternatives (SA does this)
- Debug pipeline failures

---

## Canary Checks (Added by 2.6, rule R11)
- At the interval set in the pool configuration (VASH) or project-stack.json (projects), the canary
  injector plants a known defect in a copy of the artifact under review.
- The Senior must report it as an objection. A missed canary invalidates that round's score and is
  recorded in the AvA log (CANARY: CAUGHT / MISSED).
- Two missed canaries in a row escalate the Senior route to the human for change.

---

## Escalation Protocol

### Auto-Escalation Triggers
| Trigger | Action |
|---------|--------|
| Score < 60 after any round | Immediate escalation to human |
| MODIFY cycle count ≥ 2 | Escalation with full AvA history |
| Stalemate + score 70-79 | Escalation with score trend |
| LAW 1 violation detected | Immediate FAIL + escalation |

### Escalation Format
```
ESCALATION REQUIRED
Activity: [ID] — [Name]
Reason: [specific trigger]
Rounds completed: [n]
Scores: [round 1: X] [round 2: Y] [round 3: Z]
Last objections: [list]
Recommended action: REJECTED or MODIFY [specific fix]
```

---

## AvA Log Format

Every round produces a log saved to runtime/ava_logs/[task_id]_round[n].md

```
# AvA Log — Activity [ID] Round [N]
Timestamp: [ISO-8601 UTC]

SCORE: [0-100]
THRESHOLD: [minimum]
VERDICT: APPROVED / MODIFY / FAIL

CHECKLIST:
[item]: PASS/FAIL

LAWS:
LAW1 VANILLA: PASS/FAIL — [reason]
LAW2 AGENT: PASS/FAIL — [reason]
LAW3 SKILLS: PASS/FAIL — [reason]

GATE1: PASS/FAIL — [checks run]
SENIOR_ROUTE: [vendor / model]   JUNIOR_ROUTE: [vendor / model]
CANARY: NONE / CAUGHT / MISSED

OBJECTIONS:
OBJ-001: [issue at exact location in artifact]
OBJ-002: [issue at exact location]

CORRECTIONS:
OBJ-001: [exact fix]
OBJ-002: [exact fix]
```

---

## Max Rounds Rule
Maximum 3 rounds per activity per AvA session.
If 3 rounds complete without reaching threshold:
- Apply stalemate rule
- If stalemate does not resolve: FAIL
- Human decides: REJECTED (rebuild) or MODIFY (specific fix)
