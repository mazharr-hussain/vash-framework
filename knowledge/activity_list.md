# VASH 3.0 — Activity List

## Format
Each activity follows this structure:
ID: [phase.number]
NAME: [activity name]
TYPE: [ARTIFACT / MANUAL]
PHASE: [phase name]
PARALLEL_SAFE: [YES / NO]
DEPENDS_ON: [activity IDs or NONE]
DESCRIPTION: [what to produce]
OUTPUT_PATH: [where to save]
CHECKLIST: [which checklist to use]
THRESHOLD: [minimum AvA score]
STATUS: [PENDING / IN_PROGRESS / PASS / FAIL / MODIFY]

## Phase 0: Repository Setup
---
ID: 0.1
NAME: Create repository structure
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: NONE
DESCRIPTION: Create complete vash3-framework folder
structure with README.md in each folder
OUTPUT_PATH: README.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PASS
---

Commit everything with message:
"Task 0.1: Initialize vash3-framework repository structure"
