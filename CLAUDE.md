# VASH 3.0 — Global Laws

## Identity
You are working on VASH 3.0 — a Virtual AI
Software House framework. Your purpose is to
design and plan the VASH engine. No actual
software code. Follow the activity list in
knowledge/activity_list.md in sequence.

## Three Laws — Never Broken

LAW 1 VANILLA FIRST:
Platform infrastructure: open source, free tier only.
VASH development tooling: Claude + GitHub + Python only.
Software built by VASH: open source, agnostic, no lock-in.

LAW 2 AGENT OVER HUMAN:
Automate everything possible.
Human approves only — never builds manually.

LAW 3 SKILLS OVER REINVENTION:
Search before build.
Reuse over reinvent.
Document what was searched and what was found.

## AvA Rules
Junior generates. Senior reviews.
Max 3 rounds per activity.
Score must meet threshold before pushing.
All scores saved to runtime/ava_logs/

## Output Rules
Every artifact: runtime/artifacts/[task_id]_artifact.md
Every prompt: runtime/prompts/[task_id]_prompt.md
Every AvA log: runtime/ava_logs/[task_id]_round[n].md
Every validation: runtime/validation/[task_id]_summary.md
Never skip saving. Never summarise. Full content always.
