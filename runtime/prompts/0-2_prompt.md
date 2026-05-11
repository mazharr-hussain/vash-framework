# Prompt: Activity 0.2 — Fix corrupted files and create missing files

## Activity ID: 0.2
## Activity Name: Fix repo issues from audit
## Type: ARTIFACT
## Phase: Phase 0 — Repository Setup

## Human Input:
Fix all issues found in the VASH 3.0 repo audit and push corrected files.
Follow AvA protocol.

## Issues To Fix:
PRIORITY 1 — Fix corrupted files:
1. .claude/skills/README.md — null bytes in skill names
2. runtime/prompts/README.md — PowerShell artifacts at bottom
3. runtime/validation/README.md — PowerShell artifacts at bottom
4. runtime/artifacts/README.md — null byte in example

PRIORITY 2 — Create missing files:
5. .github/CLAUDE.md
6. knowledge/tech_providers/ai_models.md
7. knowledge/tech_providers/platforms.md
8. knowledge/tech_providers/cloud_free_tier.md

PRIORITY 3 — Complete activity_list.md:
9. Add all remaining activities Phase 0 to Phase 6

## Laws Applied:
LAW1: All content is open source, free tier, Claude+GitHub+Python for VASH dev
LAW2: Automated fix — no manual steps
LAW3: Using existing file structure — no reinvention

## Output Path: Multiple files in repo
## Checklist: knowledge/checklists/artifact.md
## Threshold: 88
