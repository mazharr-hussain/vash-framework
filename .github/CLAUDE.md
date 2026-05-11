# VASH 3.0 — GitHub Automation Rules

## Trigger Rules
Issue with label vash-activity → triggers ava.yml
Issue with label vash-parallel → triggers parallel.yml
PR merged to main → triggers notify.yml

## Commit Message Format
Task [ID]: [Name] | Type: [ARTIFACT/MANUAL] | AvA: [score]

## Branch Rules
One branch per activity: task-[id]-[short-name]
Auto-merge after AvA passes threshold.
Delete branch after merge.

## File Protection Rules
Never commit to knowledge/ without human approval.
Always commit runtime/ files together as one commit.
knowledge/laws.md is read-only — never modify.
