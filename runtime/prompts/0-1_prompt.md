# Junior Prompt — Round 2
You are the VASH 3.0 Junior Creator — targeted fix mode.

ACTIVITY ID: 0.1

THREE LAWS:
﻿# VASH 3.0 — Three Laws

LAW 1 VANILLA FIRST:
Platform infrastructure: open source and free tier always.
No paid platform until VASH generates revenue.
VASH development: Claude AI + GitHub + Python only.
No cost cap on Claude for VASH development.
Software built BY VASH: open source, database-agnostic,
cloud-agnostic. Technology decided per project by agents.

LAW 2 AGENT OVER HUMAN:
If an agent can do it a human must not.
Automate everything possible.
Human only: provides brief and approves milestones.

LAW 3 SKILLS OVER REINVENTION:
Search GitHub, marketplace, and community before building.
Reuse existing skills over creating from scratch.
Document every search: what was searched, what was found,
what was reused, what was built new and why.

PARALLEL RULE:
Activities marked PARALLEL_SAFE: YES can run together.
Activities with dependencies must run sequentially.
Python orchestrator manages parallel execution.


CURRENT ARTIFACT:

# VASH 3.0 — Virtual AI Software House

**Version:** 3.0  
**Status:** Design Phase  
**Governed by:** Three Laws (see `knowledge/laws.md`)  
**Tooling:** Claude AI + GitHub + Python only (LAW 1 VANILLA FIRST)

---

## What is VASH 3.0?

VASH 3.0 is a framework for building a Virtual AI Software House — an autonomous, agent-driven system capable of delivering complete software projects from brief to deployed product, with minimal human involvement. Humans provide the brief and approve milestones. Agents do everything else.

VASH is not a single tool. It is a framework that orchestrates teams of specialised AI agents across a full software development lifecycle (SDLC), using structured debate (Agent vs Agent — AvA) to ensure quality at every stage.

---

## Three Laws

Every file, decision, and design in this repository is governed by the Three Laws:

**LAW 1 — VANILLA FIRST**  
Platform infrastructure: open source and free tier always. No paid platform until VASH generates revenue. VASH development tooling: Claude AI + GitHub + Python only. Software built BY VASH: open source, database-agnostic, cloud-agnostic. Technology decided per project by agents.

**LAW 2 — AGENT OVER HUMAN**  
If an agent can do it, a human must not. Automate everything possible. Human role: provides brief and approves milestones only.

**LAW 3 — SKILLS OVER REINVENTION**  
Search GitHub, marketplace, and community before building. Reuse existing skills over creating from scratch. Document every search: what was searched, what was found, what was reused, what was built new and why.

---

## Repository Structure

```
vash3-framework/
│
├── README.md                          ← This file — repository overview and structure map
├── CLAUDE.md                          ← Global laws and identity for Claude Code
│
├── .claude/                           ← Claude Code configuration
│   ├── CLAUDE.md                      ← Automation workflow rules
│   ├── agents/                        ← Subagent definitions (isolated context windows)
│   │   ├── README.md
│   │   ├── junior-creator/
│   │   │   └── agent.md               ← Junior Creator subagent definition
│   │   ├── senior-validator/
│   │   │   └── agent.md               ← Senior Validator subagent definition
│   │   └── prompt-engineer/
│   │       └── agent.md               ← Prompt Engineer subagent definition
│   ├── hooks/                         ← Automated event hooks for Claude Code
│   │   ├── README.md
│   │   ├── post-write.sh              ← Logs all file writes to runtime/
│   │   ├── pre-delete.sh             ← Protects knowledge/ from deletion
│   │   └── session-end.sh            ← Triggers end-of-session save sequence
│   └── skills/                        ← Reusable named capabilities for Claude
│       ├── README.md
│       ├── search_log.md              ← LAW 3 compliance: all skill searches documented
│       ├── code-reviewer/
│       │   └── SKILL.md               ← Adversarial artifact review skill
│       ├── multi-agent-patterns/
│       │   └── SKILL.md               ← AvA loop orchestration patterns skill
│       ├── prompt-engineer/
│       │   └── SKILL.md               ← Optimal prompt generation skill
│       ├── senior-architect/
│       │   └── SKILL.md               ← Architecture decision review skill
│       ├── vash-creator/
│       │   └── SKILL.md               ← VASH artifact generation skill (Junior)
│       ├── vash-orchestrator/
│       │   └── SKILL.md               ← Full AvA loop management skill
│       └── vash-validator/
│           └── SKILL.md               ← VASH artifact scoring skill (Senior)
│
├── .github/                           ← GitHub automation layer
│   ├── CLAUDE.md                      ← GitHub-specific automation rules for Claude
│   ├── scripts/                       ← Python orchestration scripts
│   │   ├── README.md
│   │   ├── ava.py                     ← Main AvA loop orchestrator (entry point)
│   │   ├── ava_lib.py                 ← Shared AvA logic library
│   │   ├── ava_main.py                ← AvA session runner (Junior + Senior calls)
│   │   ├── build_prompts.py           ← Prompt assembly from activity definitions
│   │   ├── parallel.py                ← Parallel activity execution manager
│   │   └── parse_result.py            ← AvA score extraction and threshold check
│   └── workflows/                     ← GitHub Actions workflow definitions
│       ├── README.md
│       ├── ava.yml                    ← Triggered by issue label vash-activity
│       ├── parallel.yml               ← Triggered by issue label vash-parallel
│       └── notify.yml                 ← Triggered on PR merge to main
│
├── decisions/                         ← Architecture Decision Records (ADRs)
│   ├── README.md
│   └── [id]_decision.md               ← One file per decision (immutable once ACCEPTED)
│
├── knowledge/                         ← Read-only framework knowledge base
│   ├── CLAUDE.md                      ← Domain knowledge reading rules for Claude
│   ├── laws.md                        ← The Three Laws — authoritative source
│   ├── activity_list.md               ← Complete sequenced activity list with statuses
│   ├── p1_instructions.md             ← Instructions for P1 (human owner) role
│   ├── p2_instructions.md             ← Instructions for P2 (human approver) role
│   ├── routine_instructions.md        ← Routine operation instructions for agents
│   ├── checklists/                    ← Quality checklists per artifact type
│   │   ├── artifact.md                ← Checklist for TYPE: ARTIFACT activities
│   │   ├── ava.md                     ← Checklist for AvA review sessions
│   │   ├── manual_step.md             ← Checklist for TYPE: MANUAL activities
│   │   └── prompt.md                  ← Checklist for prompt quality review
│   └── tech_providers/                ← Vendor and platform research (Phase 3 input)
│       ├── README.md
│       ├── ai_models.md               ← AI model options for software built BY VASH
│       ├── cloud_free_tier.md         ← Free tier infrastructure options
│       └── platforms.md               ← AvA and pipeline platform options
│
├── runtime/                           ← Live workflow output (agent-written only)
│   ├── artifacts/                     ← Approved artifacts from completed activities
│   │   └── README.md
│   ├── ava_logs/                      ← Round-by-round AvA review logs
│   │   └── README.md
│   ├── drafts/                        ← Work-in-progress drafts before AvA entry
│   │   └── README.md
│   ├── prompts/                       ← Prompts used to generate each artifact
│   │   └── README.md
│   ├── triggers/                      ← Trigger files watched by GitHub Actions
│   │   └── README.md
│   └── validation/                    ← Final validation summaries per activity
│       └── README.md
│
└── vash_framework/                    ← VASH design documents (the framework itself)
    ├── agents/                        ← Agent role definitions and AvA protocol
    │   └── README.md
    ├── architecture/                  ← System architecture and technology decisions
    │   └── README.md
    ├── blueprint/                     ← Master blueprint and build roadmap
    │   └── README.md
    ├── platform/                      ← Platform design specifications
    │   └── README.md
    ├── skills/                        ← Skills taxonomy and catalog
    │   └── README.md
    └── vision/                        ← Vision, objectives, scope, stakeholders
        └── README.md
```

---

## Folder Reference

### `CLAUDE.md` — Global Laws

The root `CLAUDE.md` defines the VASH identity and Three Laws for Claude Code. It is the authoritative instruction set that governs every Claude session in this repository. Contains: identity statement, Three Laws, AvA rules, and output rules.

---

### `.claude/` — Claude Code Configuration

All Claude Code runtime configuration lives here. Subfolders contain agent definitions, hooks, and skills. Nothing in `.claude/` is a design artifact — it is tooling configuration that enables VASH workflow automation.

**`.claude/CLAUDE.md`**  
Automation workflow rules specific to Claude Code execution: one-activity-at-a-time enforcement, prompt-save-first rule, AvA-before-push rule, and no-next-activity-without-approval rule.

**`.claude/agents/`**  
Subagent definitions. Each subfolder contains one `agent.md` file describing a subagent that runs in an isolated context window. Subagents are used when task isolation, parallel execution, or clean-context review is required.

| Agent | Role |
|---|---|
| `junior-creator` | Generates VASH artifacts with no knowledge of Senior review |
| `senior-validator` | Reviews and scores artifacts with no knowledge of Junior generation |
| `prompt-engineer` | Produces optimised prompts for VASH activities |

**`.claude/hooks/`**  
Shell scripts executed automatically in response to Claude Code events. Hooks enforce workflow rules without human intervention, satisfying LAW 2 AGENT OVER HUMAN.

| Hook | Trigger | Purpose |
|---|---|---|
| `post-write.sh` | After any file write | Logs write events to runtime/ |
| `pre-delete.sh` | Before any file deletion | Blocks deletion of protected knowledge/ files |
| `session-end.sh` | When Claude Code session ends | Triggers save sequence for all runtime output |

**`.claude/skills/`**  
Named, reusable capabilities that Claude executes on demand using the `/skill-name` syntax. Skills must be searched before built (LAW 3). The `search_log.md` documents every search performed before each skill was created or sourced.

| Skill | Source | Purpose |
|---|---|---|
| `prompt-engineer` | Marketplace (adapted) | Generate optimal prompts for VASH activities |
| `code-reviewer` | Marketplace (adapted) | Validate artifact quality against checklists |
| `senior-architect` | Marketplace (adapted) | Review architecture decisions |
| `multi-agent-patterns` | Marketplace (adapted) | Orchestrate AvA loops between agents |
| `vash-creator` | Built custom | Generate VASH artifacts as Junior Creator |
| `vash-validator` | Built custom | Score and review artifacts as Senior Validator |
| `vash-orchestrator` | Built custom | Manage the complete AvA loop end-to-end |

---

### `.github/` — GitHub Automation Layer

The automation infrastructure that makes VASH run on GitHub without human operation. Complies with LAW 1 (open source GitHub Actions only) and LAW 2 (fully automated).

**`.github/CLAUDE.md`**  
GitHub-specific rules for Claude: trigger conditions for each workflow, commit message format, branch naming convention, auto-merge rules, and file protection rules.

**`.github/scripts/`**  
Python-only scripts (LAW 1) that orchestrate the AvA loop, manage parallel execution, and process results.

| Script | Purpose |
|---|---|
| `ava.py` | Entry point: reads trigger, runs full AvA loop |
| `ava_lib.py` | Shared library: state management, file I/O, scoring |
| `ava_main.py` | Session runner: calls Junior, then Senior, per round |
| `build_prompts.py` | Assembles prompts from activity definitions and laws |
| `parallel.py` | Identifies PARALLEL_SAFE activities, runs them concurrently |
| `parse_result.py` | Extracts numeric score from Senior output, checks threshold |

**`.github/workflows/`**  
GitHub Actions YAML definitions. All workflows use open source actions only (LAW 1).

| Workflow | Trigger | Purpose |
|---|---|---|
| `ava.yml` | Issue labelled `vash-activity` | Run AvA loop for a single activity |
| `parallel.yml` | Issue labelled `vash-parallel` | Run multiple PARALLEL_SAFE activities simultaneously |
| `notify.yml` | PR merged to main | Send completion notification to human owner |

---

### `decisions/` — Architecture Decision Records

Every significant technology or design decision in VASH 3.0 is recorded here as an Architecture Decision Record (ADR). ADRs are immutable once ACCEPTED — they are superseded, never edited. This provides a permanent audit trail of why VASH is designed the way it is.

**Naming convention:** `[id]_decision.md`  
**Example:** `0-2_decision.md`

Each ADR contains: ID, title, status (PROPOSED / ACCEPTED / SUPERSEDED), context, decision, and consequences.

---

### `knowledge/` — Framework Knowledge Base

The read-only source of truth for all VASH rules, instructions, checklists, and provider research. Agents read from `knowledge/` but never write to it without human approval (enforced by `.claude/hooks/pre-delete.sh` and `.github/CLAUDE.md`).

**`knowledge/laws.md`**  
The authoritative Three Laws document. Read-only always. Every Claude session in this repository reads this file first.

**`knowledge/activity_list.md`**  
The complete sequenced list of all VASH 3.0 design activities, organised by phase. Each entry includes: ID, name, type, phase, parallel safety, dependencies, description, output path, checklist reference, score threshold, and current status. This is the master plan for VASH 3.0 design.

**`knowledge/p1_instructions.md`**  
Role instructions for P1 (the human owner). Defines what P1 does, when they interact with the system, and what decisions require P1 input.

**`knowledge/p2_instructions.md`**  
Role instructions for P2 (the human approver). Defines the approval process and what P2 reviews before milestones are accepted.

**`knowledge/routine_instructions.md`**  
Standard operating procedures for recurring agent tasks — how to start an activity, how to trigger AvA, how to handle MODIFY decisions.

**`knowledge/checklists/`**  
Quality enforcement checklists, one per artifact type. Agents complete the relevant checklist before submitting any artifact to AvA review.

| Checklist | Used for |
|---|---|
| `artifact.md` | All TYPE: ARTIFACT activities |
| `ava.md` | AvA review sessions (Senior role) |
| `manual_step.md` | TYPE: MANUAL activities |
| `prompt.md` | Prompt quality review before generation |

**`knowledge/tech_providers/`**  
Research documents on technology options used during Phase 3 (Technology Decisions). Agents read these files when evaluating platform choices. All options listed comply with LAW 1 VANILLA FIRST (free tier, open source).

| File | Contents |
|---|---|
| `ai_models.md` | AI model options for software built BY VASH |
| `cloud_free_tier.md` | Free tier compute, storage, and database options |
| `platforms.md` | AvA debate management and pipeline platform options |

---

### `runtime/` — Live Workflow Output

All agent-generated output during VASH design activities is stored here. The `runtime/` directory is the live working area — it is written by agents and committed to GitHub automatically after each successful AvA round. Humans do not write to `runtime/`.

**`runtime/artifacts/`**  
Completed, AvA-approved artifacts. One file per activity. Files here represent the final approved design output for each completed activity.

Naming: `[task_id]_artifact.md` — Example: `0-1_artifact.md`

**`runtime/ava_logs/`**  
Full round-by-round AvA debate logs. One file per round per activity. Contains: task ID, round number, artifact reference, Senior review comments, score, and decision (APPROVED / MODIFY / FAIL).

Naming: `[task_id]_round[n].md` — Example: `0-1_round1.md`

**`runtime/drafts/`**  
Work-in-progress artifact drafts before formal AvA entry. Used when complex activities need intermediate saving. Drafts do not trigger AvA. When ready, moved to `runtime/artifacts/`.

Naming: `[task_id]_draft_[version].md` — Example: `1-2_draft_v2.md`

**`runtime/prompts/`**  
Every prompt used to generate VASH artifacts, saved before generation begins. If a prompt is revised between AvA rounds, each version is saved separately.

Naming: `[task_id]_prompt.md` — Example: `0-1_prompt.md`  
Revised: `[task_id]_prompt_r[n].md` — Example: `0-1_prompt_r2.md`

**`runtime/triggers/`**  
Trigger files written by P1 (human owner) to initiate GitHub Actions AvA workflows. GitHub Actions watches this folder. When a trigger file appears, `ava.yml` fires automatically.

Naming: `[task_id]_trigger.md` — Example: `0-1_trigger.md`

Each trigger file contains: TASK_ID, ACTIVITY name, REQUESTED_BY, and TIMESTAMP (ISO-8601).

**`runtime/validation/`**  
Final validation summaries written after each activity completes. Contains the definitive record of: task ID, activity name, final AvA score, decision, number of rounds, key Senior feedback, and status written back to `knowledge/activity_list.md`.

Naming: `[task_id]_summary.md` — Example: `0-1_summary.md`

---

### `vash_framework/` — The VASH Design Documents

The core design output of the entire VASH 3.0 framework. Every artifact produced across all design phases is stored in a subfolder here. These documents collectively describe what VASH 3.0 is, how it works, what it uses, and how it will be built.

**`vash_framework/vision/`**  
Phase 1 artifacts. The north star documents that define VASH at the highest level. Once approved, vision documents are read-only references — never modified.

| File | Activity | Contents |
|---|---|---|
| `1-1_vision.md` | 1.1 | What VASH is, what problem it solves, who it serves |
| `1-2_objectives.md` | 1.2 | Measurable objectives and success metrics per phase |
| `1-3_scope.md` | 1.3 | What VASH does and does not do; constraints and assumptions |
| `1-4_stakeholders.md` | 1.4 | Stakeholder map: roles, needs, interaction points |

**`vash_framework/agents/`**  
Phase 2 artifacts. The complete agent architecture — who the agents are, how they interact, what protocols govern them, and how they move through the full SDLC.

| File | Activity | Contents |
|---|---|---|
| `2-1_agent_registry.md` | 2.1 | All 10 agent roles: identity, persona, Jr/Sr, skills domain, AvA role |
| `2-2_ava_protocol.md` | 2.2 | AvA rules: two layers, scoring, max rounds, stalemate, escalation |
| `2-3_groups.md` | 2.3 | 7 group configurations: roles, AvA pairings, phases covered |
| `2-4_handshakes.md` | 2.4 | Handshake contracts: data schema, required fields, validation rules |
| `2-5_sdlc_phases.md` | 2.5 | All 24 SDLC phases: purpose, entry/exit criteria, roles, artifacts |

**`vash_framework/architecture/`**  
Phase 3 artifacts. Technology decision records for every platform and infrastructure choice in VASH. All selections comply with LAW 1 (free tier, open source). Decisions reference `decisions/` ADRs.

| File | Activity | Contents |
|---|---|---|
| `3-1_ava_platform.md` | 3.1 | AvA debate management platform decision |
| `3-2_hitl_platform.md` | 3.2 | Human-in-the-loop approval channel decision |
| `3-3_model_routing.md` | 3.3 | AI model routing for software built BY VASH |
| `3-4_infrastructure.md` | 3.4 | Compute, storage, database platform for VASH engine |
| `3-5_state_management.md` | 3.5 | Pipeline state and agent memory management |
| `3-6_storage.md` | 3.6 | Artifact and log storage strategy |
| `3-7_adr_master.md` | 3.7 | Master ADR consolidating all technology decisions |

**`vash_framework/skills/`**  
Phase 4 artifacts. Complete skills taxonomy, governance rules, and skill catalogs covering all agent domains. All entries document the prior search performed before any skill was created (LAW 3).

| File | Activity | Contents |
|---|---|---|
| `4-1_skills_governance.md` | 4.1 | Taxonomy, naming, versioning, single-responsibility rule |
| `4-2_orchestration_skills.md` | 4.2 | Pipeline, routing, AvA, human gateway skills |
| `4-3_analysis_skills.md` | 4.3 | Requirements, domain, risk, compliance skills |
| `4-4_architecture_skills.md` | 4.4 | HLD, ADR, data model, security design skills |
| `4-5_engineering_skills.md` | 4.5 | Code generation, refactoring, integration, API skills |
| `4-6_quality_skills.md` | 4.6 | Test generation, chaos, performance, E2E skills |
| `4-7_operations_skills.md` | 4.7 | IaC, CI/CD, monitoring, SRE, deployment skills |
| `4-8_domain_pack.md` | 4.8 | Domain pack schema, freshness rules, creation process |

**`vash_framework/platform/`**  
Phase 5 artifacts. Detailed platform design specifications — how each platform component is configured and integrated in the VASH engine.

| File | Activity | Contents |
|---|---|---|
| `5-1_repo_structure.md` | 5.1 | Final GitHub repository structure for VASH engine and all projects |
| `5-2_gha_design.md` | 5.2 | Complete GitHub Actions automation architecture |
| `5-3_human_gateway.md` | 5.3 | Human gateway complete flow design |
| `5-4_model_router.md` | 5.4 | Model router design for client projects |
| `5-5_state_design.md` | 5.5 | Pipeline state management design |
| `5-6_cost_tracking.md` | 5.6 | Cost tracking and budget enforcement design |

**`vash_framework/blueprint/`**  
Phase 6 artifacts. The master consolidated blueprint — the single source of truth for building the actual VASH engine. All prior phase outputs converge here.

| File | Activity | Contents |
|---|---|---|
| `6-1_blueprint.md` | 6.1 | Complete VASH engine technical blueprint |
| `6-2_build_roadmap.md` | 6.2 | Sequenced build plan: phases, dependencies, milestones |
| `6-3_first_project.md` | 6.3 | First real project VASH will build when operational |

---

## Workflow Overview

```
Human (P1) creates issue with label vash-activity
              ↓
GitHub Actions ava.yml triggers
              ↓
build_prompts.py assembles prompt from activity definition + laws
              ↓
ava_main.py calls Junior Creator (Claude Code — isolated context)
              ↓
Junior produces artifact → saved to runtime/artifacts/
              ↓
ava_main.py calls Senior Validator (Claude Code — isolated context)
              ↓
Senior reviews → score + decision → saved to runtime/ava_logs/
              ↓
        Score ≥ threshold?
       /                  \
     YES                   NO (rounds < 3)
      ↓                       ↓
 Validation              Revise prompt
 summary saved           Run next round
      ↓                       ↓
 PR created             Score ≥ threshold?
      ↓                 /              \
Human (P2)           YES              NO (round 3)
 approves             ↓                   ↓
      ↓          Validation          Escalate to
  Merged to       summary            human P2
   main           saved
      ↓
notify.yml fires
      ↓
Human notified of completion
```

---

## Activity Phases

| Phase | Name | Activities | Status |
|---|---|---|---|
| Phase 0 | Repository Setup | 0.1 – 0.13 | In Progress |
| Phase 1 | VASH Engine Vision | 1.1 – 1.4 | Pending |
| Phase 2 | Agent Architecture | 2.1 – 2.5 | Pending |
| Phase 3 | Technology Decisions | 3.1 – 3.7 | Pending |
| Phase 4 | Skills Architecture | 4.1 – 4.8 | Pending |
| Phase 5 | Platform Design | 5.1 – 5.6 | Pending |
| Phase 6 | VASH Engine Blueprint | 6.1 – 6.3 | Pending |

Total activities: 38  
All phases documented in: `knowledge/activity_list.md`

---

## File Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Artifact | `[id]_artifact.md` | `0-1_artifact.md` |
| AvA log | `[id]_round[n].md` | `0-1_round1.md` |
| Prompt | `[id]_prompt.md` | `0-1_prompt.md` |
| Trigger | `[id]_trigger.md` | `0-1_trigger.md` |
| Validation | `[id]_summary.md` | `0-1_summary.md` |
| Decision | `[id]_decision.md` | `0-2_decision.md` |
| Draft | `[id]_draft_[v].md` | `1-2_draft_v2.md` |

IDs use hyphens in filenames: `0-1` = activity 0.1

---

## Branch and Commit Conventions

**Branch:** `task-[id]-[short-name]` — Example: `task-0-1-repo-structure`  
**Commit:** `Task [ID]: [Name] | Type: [ARTIFACT/MANUAL] | AvA: [score]`  
**Merge:** Auto-merge after AvA passes threshold. Branch deleted after merge.  
**Protected:** `knowledge/` — never committed without human approval.

---

## Law Compliance Summary

| Law | How this repository complies |
|---|---|
| LAW 1 VANILLA FIRST | Tooling: Claude AI + GitHub + Python only. All workflows use open source actions. No paid services. |
| LAW 2 AGENT OVER HUMAN | GitHub Actions triggers AvA automatically. Agents generate, review, commit, and open PRs. Human only approves. |
| LAW 3 SKILLS OVER REINVENTION | All skills documented with search log in `.claude/skills/search_log.md`. Marketplace skills reused where found. |


LOCKED SECTIONS — DO NOT MODIFY THESE:

- ## What is VASH 3.0?
- ## Three Laws
- ## Folder Reference
- ## Workflow Overview
- ## Activity Phases
- ## File Naming Conventions
- ## Branch and Commit Conventions
- ## Law Compliance Summary

FAILED SECTIONS — FIX ONLY THESE:

- ## Repository Structure: activity requires README.md in each folder; 16 of 33 folders are missing README.md with no justification

REQUIRED CORRECTIONS:

- ## Repository Structure: activity requires README.md in each folder; 16 of 33 folders are missing README.md with no justification

YOUR TASK:

Rewrite the full artifact.

Copy locked sections exactly — no changes.

Fix only the failed sections using the corrections above.

Maintain consistency and coherence across all sections.

Output the complete rewritten artifact now: