# Validation Summary — Activity 2.6
Re-baseline VASH as an application framework (Blueprint v8.2 merge)

| Round | Score | Threshold | Verdict | Log |
|---|---|---|---|---|
| 1 | 82 | 90 | MODIFY (18 objections) | runtime/ava_logs/2-6_round1.md |
| 2 | 89 | 90 | MODIFY (8 objections) | runtime/ava_logs/2-6_round2.md |
| 3 | 92 | 90 | APPROVED | runtime/ava_logs/2-6_round3.md |
| 4 | 86 | 90 | MODIFY 1, session round 1: MODIFY (8 objections, wrong facts on releases and freellmpool) | runtime/ava_logs/2-6_round4.md |
| 5 | 92 | 90 | MODIFY 1, session round 2: APPROVED | runtime/ava_logs/2-6_round5.md |
| 6 | 93 | 90 | MODIFY 2 (OD-1 answered), session round 1: APPROVED | runtime/ava_logs/2-6_round6.md |

Gate 1 (run before every round): all 14 sections present, canonical and runtime copies identical,
findings C1-C11 resolved with file references, no code fences except directory trees.
Round 3 non-blocking notes OBJ-027 to OBJ-030 applied after the round (ADR debt timing, 7.2 audit path,
licences_allowed[] notation, 3.3 cost wording and initial ai-manifest.json in 7.2).

MODIFY 1 (owner, 5 Nov 2026): include Ollama, OpenRouter and free-claude-code - Section 9.2a / 9.6, OD-7.
Round 5 notes OBJ-035 (end rule "7.7 or earlier under OD-7" everywhere) and OBJ-039 to OBJ-043 applied
after the round.

MODIFY 2 (owner, 5 Nov 2026): OD-1 answered - Claude is the main AI tooling for VASH's own work until
the owner changes it by a new ADR; projects stay $0. Round 6 notes OBJ-044 to OBJ-051 applied after the round.

Known limitation: Junior and Senior ran on the same vendor in isolated contexts (owner exception OD-1,
recorded in each log).

Outputs: vash_framework/architecture/2-6_application_framework.md (= runtime/artifacts/2-6_artifact.md),
decisions/ADR-001-vash-application-framework.md (PROPOSED), decisions/2-6_decision.md (PENDING),
amendments marked "Amended by 2.6" (PROPOSED until ADR-001 is ACCEPTED), knowledge/checklists/code.md.

Human action: set decisions/2-6_decision.md to APPROVED / REJECTED / MODIFY, change ADR-001 Status to
ACCEPTED, and answer OD-2 to OD-7 (OD-1 answered).
