# Validation Summary — Activity 2.6
Re-baseline VASH as an application framework (Blueprint v8.2 merge)

| Round | Score | Threshold | Verdict | Log |
|---|---|---|---|---|
| 1 | 82 | 90 | MODIFY (18 objections) | runtime/ava_logs/2-6_round1.md |
| 2 | 89 | 90 | MODIFY (8 objections) | runtime/ava_logs/2-6_round2.md |
| 3 | 92 | 90 | APPROVED | runtime/ava_logs/2-6_round3.md |

Gate 1 (run before every round): all 14 sections present, canonical and runtime copies identical,
findings C1-C11 resolved with file references, no code fences except directory trees.
Round 3 non-blocking notes OBJ-027 to OBJ-030 applied after the round (ADR debt timing, 7.2 audit path,
licences_allowed[] notation, 3.3 cost wording and initial ai-manifest.json in 7.2).

Known limitation: Junior and Senior ran on the same vendor in isolated contexts (OD-1 transitional
exception, recorded in each log).

Outputs: vash_framework/architecture/2-6_application_framework.md (= runtime/artifacts/2-6_artifact.md),
decisions/ADR-001-vash-application-framework.md (PROPOSED), decisions/2-6_decision.md (PENDING),
amendments marked "Amended by 2.6" (PROPOSED until ADR-001 is ACCEPTED), knowledge/checklists/code.md.

Human action: set decisions/2-6_decision.md to APPROVED / REJECTED / MODIFY, change ADR-001 Status to
ACCEPTED, and answer OD-1 to OD-6.
