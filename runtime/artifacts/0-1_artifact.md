Now I have all the context needed. Producing the artifact.

# VASH 3.0 — Repository Structure
**Activity:** 0.1 — Create repository structure
**Output path:** runtime/artifacts/0.1_artifact.md
**Date:** 2026-05-14

---

## 1. Complete Folder Hierarchy

```
vash3-framework/
├── README.md
├── CLAUDE.md
│
├── .claude/
│   ├── CLAUDE.md
│   ├── agents/
│   │   ├── README.md
│   │   ├── junior-creator.md
│   │   ├── senior-validator.md
│   │   └── prompt-engineer.md
│   ├── hooks/
│   │   ├── README.md
│   │   ├── post-write-log.sh
│   │   ├── pre-delete-protect.sh
│   │   └── session-end-trigger.sh
│   └── skills/
│       ├── README.md
│       ├── prompt-engineer.md
│       ├── code-reviewer.md
│       ├── senior-architect.md
│       ├── multi-agent-patterns.md
│       ├── vash-creator.md
│       ├── vash-validator.md
│       └── vash-orchestrator.md
│
├── .github/
│   ├── CLAUDE.md
│   ├── workflows/
│   │   ├── README.md
│   │   ├── ava.yml
│   │   ├── parallel.yml
│   │   └── notify.yml
│   └── scripts/
│       ├── README.md
│       ├── ava.py
│       └── parallel.py
│
├── knowledge/
│   ├── CLAUDE.md
│   ├── README.md
│   ├── laws.md
│   ├── activity_list.md
│   ├── checklists/
│   │   ├── README.md
│   │   ├── artifact.md
│   │   ├── manual_step.md
│   │   ├── ava.md
│   │   └── prompt.md
│   └── tech_providers/
│       ├── README.md
│       ├── platforms.md
│       ├── ai_models.md
│       └── cloud_free_tier.md
│
├── runtime/
│   ├── README.md
│   ├── artifacts/
│   │   └── README.md
│   ├── prompts/
│   │   └── README.md
│   ├── ava_logs/
│   │   └── README.md
│   └── validation/
│       └── README.md
│
└── vash_framework/
    ├── README.md
    ├── vision/
    │   └── README.md
    ├── agents/
    │   └── README.md
    ├── architecture/
    │   └── README.md
    ├── skills/
    │   └── README.md
    ├── platform/
    │   └── README.md
    └── blueprint/
        └── README.md
```

---

## 2. Folder Purposes

### Root

| Path | Purpose |
|------|---------|
| `vash3-framework/` | Root of the VASH 3.0 framework repository; the single source of truth for all design, planning, and automation artifacts. |
| `CLAUDE.md` | Declares the three global laws and VASH identity that Claude must apply to every session in this repository. |

---

### `.claude/`

| Path | Purpose |
|------|---------|
| `.claude/` | Contains all Claude Code configuration: agents, hooks, and skills that automate the VASH development workflow. |
| `.claude/CLAUDE.md` | Defines workflow automation rules — one activity at a time, AvA before push, and available skills index. |
| `.claude/agents/` | Holds subagent definition files that give each Claude sub-session its specific identity, constraints, and task scope. |
| `.claude/hooks/` | Contains hook scripts that fire on Claude Code events — logging writes, protecting knowledge files, and triggering session-end actions. |
| `.claude/skills/` | Stores all skill definition files (marketplace-installed and custom-built) that Claude invokes to execute VASH workflow steps. |

---

### `.github/`

| Path | Purpose |
|------|---------|
| `.github/` | Holds all GitHub-specific configuration including the CLAUDE.md context for CI runners and all automation workflows and scripts. |
| `.github/CLAUDE.md` | Provides Claude Code with the GitHub Actions runner context, available secrets, and pipeline execution rules. |
| `.github/workflows/` | Contains all GitHub Actions YAML workflow files that automate the AvA loop, parallel execution, and human notifications. |
| `.github/scripts/` | Contains the Python orchestration scripts (`ava.py`, `parallel.py`) that Claude Code executes inside GitHub Actions runners. |

---

### `knowledge/`

| Path | Purpose |
|------|---------|
| `knowledge/` | The immutable domain knowledge base — laws, activity list, checklists, and technology reference data that agents read but never modify. |
| `knowledge/CLAUDE.md` | Defines reading rules for agents: which files to load per task type, checklist selection logic, and minimal-load principle. |
| `knowledge/laws.md` | Defines the three non-negotiable VASH laws (Vanilla First, Agent Over Human, Skills Over Reinvention) and the parallel execution rule. |
| `knowledge/activity_list.md` | The complete ordered list of all VASH activities across all phases — the master pipeline that drives all agent work. |
| `knowledge/checklists/` | Holds one checklist per activity type (artifact, manual step, AvA validation, prompt review) that agents use for quality gates. |
| `knowledge/tech_providers/` | Stores reference data on evaluated technology options — AI models, cloud free tiers, and AvA platform candidates — used in Phase 3 decisions. |

---

### `runtime/`

| Path | Purpose |
|------|---------|
| `runtime/` | All generated runtime output — every artifact, prompt, AvA log, and validation summary produced during VASH activity execution. |
| `runtime/artifacts/` | Stores the primary output artifact for each activity, saved as `[task_id]_artifact.md` and never overwritten once approved. |
| `runtime/prompts/` | Stores the prompt given to Junior Creator before each activity run, saved as `[task_id]_prompt.md` for full traceability. |
| `runtime/ava_logs/` | Stores the round-by-round AvA debate log for each activity, saved as `[task_id]_round[n].md` for audit and stalemate detection. |
| `runtime/validation/` | Stores the final Senior Validator summary for each completed activity, saved as `[task_id]_summary.md` with score and decision. |

---

### `vash_framework/`

| Path | Purpose |
|------|---------|
| `vash_framework/` | The core design output of VASH 3.0 — all phase artifacts that together define the complete VASH engine specification. |
| `vash_framework/vision/` | Holds Phase 1 artifacts: the VASH north-star vision, objectives, success metrics, scope boundaries, and stakeholder map. |
| `vash_framework/agents/` | Holds Phase 2 artifacts: the 10-agent registry, AvA protocol rulebook, group configurations, handshake contracts, and SDLC phases. |
| `vash_framework/architecture/` | Holds Phase 3 artifacts: all technology decisions and the Architecture Decision Record master that consolidates every platform and tooling choice. |
| `vash_framework/skills/` | Holds Phase 4 artifacts: the complete skills taxonomy, governance rules, and per-category skills catalogs across all SDLC domains. |
| `vash_framework/platform/` | Holds Phase 5 artifacts: the concrete platform design — repo structure, GitHub Actions architecture, human gateway, model router, state management, and cost tracking. |
| `vash_framework/blueprint/` | Holds Phase 6 artifacts: the master VASH engine technical blueprint, build roadmap, and first project definition. |

---

## 3. README.md Content Templates

Each README.md in the repository follows a standard template tailored to its folder's role. Full content for each is defined below.

---

### `README.md` (root)

```markdown
# VASH 3.0 — Virtual AI Software House

VASH 3.0 is an agent-driven framework that designs, builds, and validates
software products without human engineers writing code. Agents debate every
artifact through AvA (Adversarial Validation Architecture) before anything
is approved.

## Three Laws

1. **Vanilla First** — Open source and free tier always. Claude + GitHub + Python only for VASH development.
2. **Agent Over Human** — If an agent can do it, a human must not. Human approves only.
3. **Skills Over Reinvention** — Search before build. Reuse over reinvent. Document every search.

## Repository Layout

| Folder | Contents |
|--------|----------|
| `.claude/` | Agents, hooks, and skills for Claude Code automation |
| `.github/` | GitHub Actions workflows and Python orchestration scripts |
| `knowledge/` | Laws, activity list, checklists, tech provider reference data |
| `runtime/` | All generated artifacts, prompts, AvA logs, and validation summaries |
| `vash_framework/` | Phase-by-phase design output — the VASH engine specification |

## Status

See `knowledge/activity_list.md` for current pipeline status.
All activity output is in `runtime/`.
```

---

### `.claude/agents/README.md`

```markdown
# VASH 3.0 — Subagent Definitions

This folder contains the definition files for Claude Code subagents.
Each file instructs a sub-session of Claude to adopt a specific identity
and execute a scoped task within the VASH workflow.

## Agents

| File | Identity | Role |
|------|----------|------|
| `junior-creator.md` | Junior Creator | Generates artifacts from prompts |
| `senior-validator.md` | Senior Validator | Reviews and scores artifacts via AvA |
| `prompt-engineer.md` | Prompt Engineer | Generates optimal prompts for each activity |

## Usage

Subagents are invoked by the Python orchestrator (`ava.py`) using Claude Code CLI.
Each sub-session receives its definition file as context and operates in isolation
with no memory of other sessions.

## Law Compliance

- LAW 2: Agents execute — humans approve only.
- LAW 3: Definitions searched in Claude Code marketplace before writing custom ones.
```

---

### `.claude/hooks/README.md`

```markdown
# VASH 3.0 — Hook Scripts

This folder contains shell scripts that execute in response to Claude Code
lifecycle events. Hooks enforce VASH rules automatically without human
intervention.

## Hooks

| File | Trigger | Purpose |
|------|---------|---------|
| `post-write-log.sh` | After any file write | Appends a timestamped entry to the runtime audit log |
| `pre-delete-protect.sh` | Before any file delete | Blocks deletion of files inside `knowledge/` |
| `session-end-trigger.sh` | On session end | Commits runtime output and triggers GitHub notification workflow |

## Configuration

Hooks are registered in `.claude/settings.json` under the `hooks` key.
See `.claude/CLAUDE.md` for the full automation rules.

## Law Compliance

- LAW 2: All hook logic is automated — no human action required.
```

---

### `.claude/skills/README.md`

```markdown
# VASH 3.0 — Skills

This folder contains all skill definition files available to Claude in VASH sessions.

## Marketplace Skills (searched and installed — LAW 3)

| File | Source | Purpose |
|------|--------|---------|
| `prompt-engineer.md` | Marketplace | Generates optimal prompts for VASH activities |
| `code-reviewer.md` | Marketplace | Adversarial review of artifact quality |
| `senior-architect.md` | Marketplace | Reviews architecture and technology decisions |
| `multi-agent-patterns.md` | Marketplace | Manages AvA loop and agent coordination patterns |

## Custom VASH Skills (built only after marketplace search — LAW 3)

| File | Purpose |
|------|---------|
| `vash-creator.md` | Junior Creator — generates VASH artifacts from prompts |
| `vash-validator.md` | Senior Validator — scores and reviews artifacts against VASH checklists |
| `vash-orchestrator.md` | Manages the complete AvA loop end-to-end |

## Search Documentation

All marketplace searches are documented in `runtime/artifacts/0-5_artifact.md`
(Activity 0.5 — Search and install marketplace skills).
```

---

### `.github/workflows/README.md`

```markdown
# VASH 3.0 — GitHub Actions Workflows

This folder contains all GitHub Actions workflow files that automate the
VASH pipeline on GitHub-hosted runners.

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `ava.yml` | Issue with label `vash-activity` | Runs the full AvA loop for a single activity |
| `parallel.yml` | Issue with label `vash-parallel` | Runs multiple PARALLEL_SAFE activities simultaneously |
| `notify.yml` | PR merged to main | Sends summary notification to human via configured channel |

## Authentication

All workflows use `CLAUDE_CODE_OAUTH_TOKEN` from GitHub repository secrets.
This token enables Claude Code to run on GitHub VMs using the Claude.ai subscription.
See Activity 0.12 for manual token setup instructions.

## Law Compliance

- LAW 1: GitHub Actions free tier. No paid CI runners.
- LAW 2: Workflows are fully automated — human triggers via GitHub issue only.
```

---

### `.github/scripts/README.md`

```markdown
# VASH 3.0 — Python Orchestration Scripts

This folder contains the Python scripts that GitHub Actions workflows execute
to manage the AvA loop and parallel activity processing.

## Scripts

| File | Purpose |
|------|---------|
| `ava.py` | Orchestrates the full AvA loop: reads activity, generates prompt, calls Junior, calls Senior, manages rounds and scores, escalates if needed |
| `parallel.py` | Identifies PARALLEL_SAFE activities, runs them concurrently via subprocess, collects and merges results |

## Design Principles

- Python only (LAW 1 — VASH development tooling: Claude + GitHub + Python only)
- No external dependencies beyond Python standard library where possible
- All reads from `knowledge/`, all writes to `runtime/`
- Scripts are generated by agents — not written by humans (LAW 2)

## Law Compliance

- LAW 1: Python only. No third-party orchestration platforms.
- LAW 2: Scripts are fully automated — no human editing of pipeline logic.
```

---

### `knowledge/README.md`

```markdown
# VASH 3.0 — Knowledge Base

This folder contains the immutable domain knowledge that all agents read
before executing any task. Files here are never modified by agents during
activity execution.

## Contents

| File / Folder | Purpose |
|---------------|---------|
| `laws.md` | The three non-negotiable VASH laws |
| `activity_list.md` | Complete ordered activity pipeline across all phases |
| `checklists/` | Quality checklists per activity type |
| `tech_providers/` | Technology option reference data for Phase 3 decisions |

## Reading Rules

- Always read `laws.md` before any task
- Load only what the current task requires
- See `CLAUDE.md` in this folder for detailed reading rules

## Protection

Files in this folder are protected by the `pre-delete-protect.sh` hook.
No file inside `knowledge/` may be deleted by an automated session.
```

---

### `knowledge/checklists/README.md`

```markdown
# VASH 3.0 — Checklists

This folder contains the quality checklists that agents use as gates
before submitting work to AvA review or marking activities complete.

## Checklists

| File | Used For |
|------|---------|
| `artifact.md` | Every activity with TYPE: ARTIFACT |
| `manual_step.md` | Every activity with TYPE: MANUAL |
| `ava.md` | Senior Validator during every AvA review round |
| `prompt.md` | Prompt Engineer before saving any prompt file |

## Usage

Junior Creator reads the relevant checklist before generating.
Senior Validator reads `ava.md` before scoring.
Checklist selection is determined by activity TYPE field in `activity_list.md`.
```

---

### `knowledge/tech_providers/README.md`

```markdown
# VASH 3.0 — Technology Providers Reference

This folder contains reference data on evaluated technology options.
These files are read exclusively during Phase 3 (Technology Decisions) activities.

## Files

| File | Contents |
|------|---------|
| `platforms.md` | AvA debate management and orchestration platforms with free tier confirmation |
| `ai_models.md` | AI model options for software built BY VASH — routing, cost, and capability data |
| `cloud_free_tier.md` | Cloud infrastructure free tier options for compute, storage, and database |

## Law Compliance

- LAW 1: Only free tier options are included. Paid-only platforms are excluded.
- LAW 3: All options were searched before any technology was selected.

## Update Policy

These files are updated only via a VASH activity — never edited directly by humans.
```

---

### `runtime/README.md`

```markdown
# VASH 3.0 — Runtime Output

This folder contains all generated output from VASH activity execution.
Every file here was produced by an agent, never by a human.

## Structure

| Folder | Contents | Naming Convention |
|--------|---------|-------------------|
| `artifacts/` | Primary activity output | `[task_id]_artifact.md` |
| `prompts/` | Prompts given to Junior Creator | `[task_id]_prompt.md` (e.g. `0-1_prompt.md`) |
| `ava_logs/` | Round-by-round AvA debate records | `[task_id]_round[n].md` |
| `validation/` | Final Senior Validator summary per activity | `[task_id]_summary.md` |

## Rules

- Never skip saving. Every activity produces output in all four subfolders.
- Never summarise. Full content only.
- Files are never deleted once written.
- task_id uses hyphen notation: `0-1` for activity `0.1`.

## Law Compliance

- LAW 2: All files here are written by agents automatically — never by humans.
```

---

### `runtime/artifacts/README.md`

```markdown
# VASH 3.0 — Artifacts

This folder stores the primary output artifact for every completed activity.

## Naming

`[task_id]_artifact.md` — e.g. `0-1_artifact.md` for activity 0.1

## Lifecycle

1. Junior Creator generates the artifact content.
2. Senior Validator reviews it via AvA (up to 3 rounds).
3. When score meets threshold, artifact is saved here as final.
4. Artifact is referenced in the validation summary.

## Status

Artifacts saved here have passed AvA review and met the threshold score
defined in `knowledge/activity_list.md` for their activity.
```

---

### `runtime/prompts/README.md`

```markdown
# VASH 3.0 — Prompts

This folder stores the prompt saved before each Junior Creator session.

## Naming

`[task_id]_prompt.md` — e.g. `0-1_prompt.md` for activity 0.1

## Lifecycle

1. Prompt Engineer generates the optimal prompt for the activity.
2. Prompt is saved here before Junior Creator is invoked.
3. Junior Creator reads this file at session start.

## Purpose

Saving prompts provides full traceability: for any artifact, the exact
instructions given to Junior Creator can be reviewed and improved.
```

---

### `runtime/ava_logs/README.md`

```markdown
# VASH 3.0 — AvA Logs

This folder stores the round-by-round AvA debate record for each activity.

## Naming

`[task_id]_round[n].md` — e.g. `0-1_round1.md`, `0-1_round2.md`

## Contents Per Log

Each round log captures:
- Round number and activity ID
- Junior Creator artifact submitted
- Senior Validator score (0–100)
- Senior Validator feedback and required changes
- Junior Creator revision response (if round > 1)
- Decision: APPROVED / REJECTED / ESCALATED

## Rules

- Maximum 3 rounds per activity.
- If round 3 ends below threshold: ESCALATED — human reviews.
- Logs are never deleted — stalemate detection reads full history.
```

---

### `runtime/validation/README.md`

```markdown
# VASH 3.0 — Validation Summaries

This folder stores the final validation summary for each completed activity.

## Naming

`[task_id]_summary.md` — e.g. `0-1_summary.md` for activity 0.1

## Contents Per Summary

Each summary captures:
- Activity ID, name, and phase
- Final score achieved
- Threshold required
- Number of rounds taken
- Decision: APPROVED / ESCALATED
- Link to final artifact in `runtime/artifacts/`
- Link to full AvA log in `runtime/ava_logs/`

## Usage

Summaries are the input to the notify workflow — the human approval notification
is generated from this file after a successful AvA run.
```

---

### `vash_framework/README.md`

```markdown
# VASH 3.0 — Framework Design Output

This folder is the product of all VASH design activities. It contains the
complete specification for the VASH engine, phase by phase.

## Phases

| Folder | Phase | Contents |
|--------|-------|---------|
| `vision/` | Phase 1 | North star, objectives, scope, stakeholder map |
| `agents/` | Phase 2 | Agent registry, AvA protocol, groups, handshakes, SDLC phases |
| `architecture/` | Phase 3 | All technology decisions and the ADR master |
| `skills/` | Phase 4 | Skills taxonomy, governance, and all per-category catalogs |
| `platform/` | Phase 5 | Platform design — repo, GitHub Actions, human gateway, model router, state, cost |
| `blueprint/` | Phase 6 | Master technical blueprint, build roadmap, first project definition |

## Status

Each folder contains only APPROVED artifacts — files that have passed AvA
review and met their threshold score. See `runtime/validation/` for scores.

## Law Compliance

- LAW 1: All design decisions documented here respect open source and free tier constraints.
- LAW 2: All content was generated by agents — no human wrote these documents.
- LAW 3: All technology choices document the search performed before selection.
```

---

### `vash_framework/vision/README.md`

```markdown
# Phase 1 — VASH Engine Vision

This folder contains the foundational vision artifacts for VASH 3.0.
These documents define what VASH is, what it must achieve, and who it serves.
All downstream phases depend on the decisions made here.

## Artifacts

| File | Activity | Contents |
|------|----------|---------|
| `1-1_vision.md` | 1.1 | Complete VASH vision — problem, solution, differentiation |
| `1-2_objectives.md` | 1.2 | Measurable objectives and success metrics per phase |
| `1-3_scope.md` | 1.3 | In-scope vs out-of-scope, constraints, assumptions |
| `1-4_stakeholders.md` | 1.4 | Stakeholder map — roles, needs, interaction points |

## Dependencies

Phase 1 depends on: Activity 0.13 (end-to-end pipeline test — APPROVED).
Phase 2 depends on: All Phase 1 artifacts — APPROVED.
```

---

### `vash_framework/agents/README.md`

```markdown
# Phase 2 — Agent Architecture

This folder contains the complete agent architecture for VASH 3.0.
These documents define how agents are structured, how they debate,
how they hand off work, and what the full SDLC sequence looks like.

## Artifacts

| File | Activity | Contents |
|------|----------|---------|
| `2-1_agent_registry.md` | 2.1 | 10 agent roles — identity, persona, skills, AvA role |
| `2-2_ava_protocol.md` | 2.2 | AvA rulebook — scoring, rounds, escalation, parallel rules |
| `2-3_groups.md` | 2.3 | 7 group configurations — roles, pairings, phases |
| `2-4_handshakes.md` | 2.4 | Role-to-role handoff contracts — schemas and validation |
| `2-5_sdlc_phases.md` | 2.5 | All 24 SDLC phases — entry/exit criteria, roles, artifacts |

## Dependencies

Phase 2 depends on: All Phase 1 artifacts — APPROVED.
Phase 3 depends on: Activity 2.5 — APPROVED.
```

---

### `vash_framework/architecture/README.md`

```markdown
# Phase 3 — Technology Decisions

This folder contains all technology evaluation and selection artifacts for VASH 3.0.
Every decision here is backed by a documented search (LAW 3) and confirms
free tier availability (LAW 1).

## Artifacts

| File | Activity | Contents |
|------|----------|---------|
| `3-1_ava_platform.md` | 3.1 | AvA debate management platform decision |
| `3-2_hitl_platform.md` | 3.2 | Human-in-the-loop platform decision |
| `3-3_model_routing.md` | 3.3 | AI model routing for client projects |
| `3-4_infrastructure.md` | 3.4 | Infrastructure platform for VASH engine |
| `3-5_state_management.md` | 3.5 | State and memory management decision |
| `3-6_storage.md` | 3.6 | Storage and artifact management decision |
| `3-7_adr_master.md` | 3.7 | Architecture Decision Record — all decisions consolidated |

## Dependencies

Phase 3 depends on: Activity 2.5 — APPROVED.
Phase 4 and 5 depend on: Activity 3.7 — APPROVED.
```

---

### `vash_framework/skills/README.md`

```markdown
# Phase 4 — Skills Architecture

This folder contains the complete skills taxonomy and all per-category
skill catalogs for VASH 3.0. Skills are the atomic units of agent capability.

## Artifacts

| File | Activity | Contents |
|------|----------|---------|
| `4-1_skills_governance.md` | 4.1 | Taxonomy, naming, versioning, single responsibility, reuse rules |
| `4-2_orchestration_skills.md` | 4.2 | Pipeline, routing, AvA, human gateway skills |
| `4-3_analysis_skills.md` | 4.3 | Requirements, domain, risk, compliance skills |
| `4-4_architecture_skills.md` | 4.4 | HLD, ADR, data model, security design skills |
| `4-5_engineering_skills.md` | 4.5 | Code generation, refactoring, integration, API skills |
| `4-6_quality_skills.md` | 4.6 | Test generation, chaos, performance, E2E skills |
| `4-7_operations_skills.md` | 4.7 | IaC, CI/CD, monitoring, SRE, deployment skills |
| `4-8_domain_pack.md` | 4.8 | Domain pack schema, freshness rules, creation process |

## Law Compliance

- LAW 3: Every skill documents the marketplace/community search performed before it was built.
```

---

### `vash_framework/platform/README.md`

```markdown
# Phase 5 — Platform Design

This folder contains the concrete platform design for VASH 3.0.
These documents translate Phase 3 technology decisions into
specific implementation designs.

## Artifacts

| File | Activity | Contents |
|------|----------|---------|
| `5-1_repo_structure.md` | 5.1 | Final GitHub repo structure — folders, naming, branches |
| `5-2_gha_design.md` | 5.2 | GitHub Actions architecture — workflows, scripts, OAuth |
| `5-3_human_gateway.md` | 5.3 | Human approval channel design — messages, routing, identity |
| `5-4_model_router.md` | 5.4 | Model router design for client projects — routing, fallbacks, costs |
| `5-5_state_design.md` | 5.5 | Pipeline state schema, checkpoints, recovery logic |
| `5-6_cost_tracking.md` | 5.6 | Cost tracking per client project — limits, alerts, reporting |

## Dependencies

Phase 5 depends on: Activity 3.7 (ADR master — APPROVED).
Phase 6 depends on: Activities 4.8 and 5.6 — both APPROVED.
```

---

### `vash_framework/blueprint/README.md`

```markdown
# Phase 6 — VASH Engine Blueprint

This folder contains the master output of the entire VASH 3.0 design process.
These documents are the final deliverable — the complete specification
for building the actual VASH engine.

## Artifacts

| File | Activity | Contents |
|------|----------|---------|
| `6-1_blueprint.md` | 6.1 | Master technical blueprint — all phases consolidated |
| `6-2_build_roadmap.md` | 6.2 | Build sequence — phases, dependencies, milestones, parallelism |
| `6-3_first_project.md` | 6.3 | First real project VASH will build — scope, domain pack, timeline |

## Purpose

The blueprint is the handoff document. When Phase 6 is APPROVED, the design
phase of VASH 3.0 is complete. The build phase begins from `6-1_blueprint.md`.

## Dependencies

Phase 6 depends on: Activities 4.8 and 5.6 — both APPROVED.
```

---

## 4. Law Compliance Verification

| Law | How This Artifact Complies |
|-----|---------------------------|
| **LAW 1 — Vanilla First** | All referenced tooling (GitHub, Python, Claude Code, GitHub Actions free tier) is open source or free tier. No paid platforms referenced in the structure. |
| **LAW 2 — Agent Over Human** | The `runtime/` folder and all workflow outputs are defined as agent-generated. Human interaction points are confined to issue triggers and PR approvals. |
| **LAW 3 — Skills Over Reinvention** | The `.claude/skills/` folder distinguishes marketplace-sourced skills from custom-built ones. Search documentation is required in skills README. |

---

## 5. Checklist Completion

- [x] `knowledge/laws.md` has been read
- [x] Activity 0.1 description is understood: complete folder structure with README.md in each folder
- [x] Output path confirmed: `runtime/artifacts/0.1_artifact.md`
- [x] Artifact addresses full activity description
- [x] No actual software code — design and planning only
- [x] Language is clear, structured, and complete
- [x] No summaries — full content only
- [x] All three laws are respected in the content
- [x] Threshold score for this activity: 88