# VASH 3.0 — Automation Rules

## Workflow Rules
One activity at a time unless PARALLEL_SAFE: YES.
Always read plan/activity_list.md first.
Always save prompt before starting any work.
Always run AvA before pushing to GitHub.
Never start next activity without APPROVED decision.

## Skills Available
- prompt-engineer: generate optimal prompts
- code-reviewer: validate artifact quality
- senior-architect: review architecture decisions
- vash-creator: generate VASH artifacts (Junior)
- vash-validator: score and review artifacts (Senior)
- vash-orchestrator: manage full AvA loop

## Subagents Available
- junior-creator: own context window, generates artifacts
- senior-validator: own context window, reviews artifacts
- prompt-engineer: own context window, generates prompts
