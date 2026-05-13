# VASH 3.0 — Repository Structure

**VASH** — Virtual AI Software House — is an agent-driven framework that designs, plans, and orchestrates the building of software products entirely through AI agents, with humans approving milestones but never building manually.

This repository is the VASH 3.0 engine design workspace. It holds the knowledge, automation, runtime outputs, and design artifacts produced as the framework is planned phase by phase. The actual VASH engine is the subject of this design process, not the content of this repository.

---

## How This Repository Works

The VASH 3.0 design process follows a structured activity list, executed phase by phase. Each activity produces an artifact. Every artifact passes through an Agent vs Agent (AvA) review loop before it is committed. No artifact is accepted below its defined quality threshold.

Three laws govern everything:

**LAW 1 — VANILLA FIRST**: All platform infrastructure is open source and free tier. VASH development uses Claude AI, GitHub, and Python only. Software built by VASH is open source, cloud-agnostic, and database-agnostic.

**LAW 2 — AGENT OVER HUMAN**: If an agent can do it, a human must not. Humans provide briefs and approve milestones only.

**LAW 3 — SKILLS OVER REINVENTION**: Search before building. Reuse existing skills and tools before creating new ones. Every search is documented: what was searched, what was found, what was reused, and what was built new and why.

---

## Top-Level Folder Map

```
vash3-framework/
├── .claude/               Claude Code configuration (agents, hooks, skills)
├── .github/               GitHub automation (workflows, Python scripts)
├── decisions/             Architecture Decision Records (ADRs)
├── knowledge/             Framework laws, activity list, checklists, tech references
├── runtime/               Live working directory for all AvA activity
├── vash_framework/        Design outputs produced by VASH agents across all phases
└── CLAUDE.md              Global project instructions for Claude Code
```

---

## Folder Reference

### `.claude/`

Claude Code configuration directory. Contains all agent definitions, hook scripts, and skill definitions that power the VASH 3.0 automation layer.

**Purpose**: Configure how Claude Code behaves when operating within this repository. Everything in this folder governs automated agent behaviour, not human behaviour.

**README purpose**: Explain how Claude Code is configured for this repository, which agents, hooks, and skills are defined, and how they collectively power the VASH 3.0 automation layer.

---

#### `.claude/agents/`

Subagent definitions. Each agent runs in its own isolated context window, enabling parallel or independent execution without contaminating the main session.

**Agents defined here:**

| Agent | Role |
|---|---|
| junior-creator | Generates VASH artifacts in an isolated context |
| senior-validator | Reviews and scores artifacts in an isolated context |
| prompt-engineer | Produces optimised prompts in an isolated context |

Each agent definition specifies the agent's identity, its permitted tools, and its expected behaviour. Agents are the primary execution units for all AvA rounds.

**README purpose**: Explain which agents exist, what each does, and how they are invoked within the AvA loop.

---

#### `.claude/hooks/`

Hook scripts that execute automatically in response to Claude Code lifecycle events. Hooks enforce workflow rules without requiring human intervention.

**Hooks defined here:**

| Hook | Trigger | Purpose |
|---|---|---|
| post-write | After any file write | Log what was written and when |
| pre-delete | Before any file deletion | Protect the knowledge directory from accidental removal |
| session-end | When a Claude Code session ends | Trigger save of all runtime output files |

Hooks never modify the laws or activity list. They are the enforcement layer for workflow integrity.

**README purpose**: Explain which hooks are active, when they fire, and what they protect.

---

#### `.claude/skills/`

Skill definitions. Skills are named, reusable capabilities that Claude Code executes on demand. Each skill file defines a specific behaviour.

**Skills defined here:**

| Skill | Source | Purpose |
|---|---|---|
| prompt-engineer | Marketplace | Generates optimal prompts for VASH activities |
| code-reviewer | Marketplace | Validates artifact quality against checklists |
| senior-architect | Marketplace | Reviews architecture decisions |
| multi-agent-patterns | Marketplace | Orchestrates multi-agent interaction patterns |
| vash-creator | Custom built | Generates VASH artifacts in Junior Creator role |
| vash-validator | Custom built | Scores and reviews artifacts in Senior Validator role |
| vash-orchestrator | Custom built | Manages the full AvA loop end-to-end |

Marketplace skills were found via GitHub and Claude marketplace search before custom skills were built. This satisfies LAW 3 — Skills over Reinvention. The search log is maintained in this folder.

**README purpose**: Explain which skills are available, which were found via search versus built new, and how each skill is invoked.

---

### `.github/`

GitHub automation directory. Contains all GitHub Actions workflows and the Python scripts that power AvA orchestration, parallel execution, and notifications.

**Purpose**: Enable fully automated AvA pipeline execution triggered by GitHub issues, with no manual build steps required. Satisfies LAW 2 — Agent over Human.

---

#### `.github/workflows/`

GitHub Actions workflow definitions. Each workflow file defines a trigger condition and the sequence of automated steps that follow.

**Workflows defined here:**

| Workflow | Trigger | Purpose |
|---|---|---|
| ava.yml | Issue with label `vash-activity` | Runs the full AvA loop for a single activity |
| parallel.yml | Issue with label `vash-parallel` | Runs multiple PARALLEL_SAFE activities concurrently |
| notify.yml | PR merged to main | Sends a completion summary to the human owner |

All workflows use only GitHub-native capabilities (GitHub Actions, GitHub-hosted runners, GitHub Secrets). No paid external CI platform is used. This satisfies LAW 1 — Vanilla First.

**README purpose**: Explain which workflows exist, what triggers them, and what each one does from trigger to completion.

---

#### `.github/scripts/`

Python orchestration scripts executed inside GitHub Actions runners. These scripts are the intelligence layer that the workflows call.

**Scripts defined here:**

| Script | Purpose |
|---|---|
| ava.py | Entry point for the AvA loop. Loads activity, runs Junior and Senior sessions, manages rounds and scoring |
| ava_lib.py | Shared library of AvA helper functions used by ava.py and ava_main.py |
| ava_main.py | Coordinate multiple AvA rounds and handle escalation logic |
| build_prompts.py | Constructs optimised prompts by assembling activity definition, laws, checklist, and rules |
| parse_result.py | Parses Senior Validator output to extract score and decision |
| parallel.py | Manages concurrent execution of PARALLEL_SAFE activities using matrix strategy |

All scripts are Python only. No third-party orchestration platform. This satisfies LAW 1. Scripts call the Claude Code CLI to run agent sessions — no direct API calls, no separate AI platform.

**README purpose**: Explain what each script does, how they chain together, and what inputs and outputs flow between them.

---

### `decisions/`

Architecture Decision Records (ADRs). Every major architecture, platform, and agent design choice is recorded here as an immutable decision document.

**Format for each decision:**
- ID — sequential identifier
- Title — short imperative phrase describing the decision
- Status — PROPOSED, ACCEPTED, or SUPERSEDED
- Context — why this decision was needed
- Decision — what was decided
- Consequences — what changes as a result

**Rules:**
- One file per decision
- Decisions are immutable once ACCEPTED — if a decision changes, it is superseded by a new ADR, never edited
- No decision is deleted; the history is permanent

**README purpose**: Explain the ADR format, the naming convention, and the rule that accepted decisions are immutable.

---

### `knowledge/`

The permanent reference layer for the VASH 3.0 framework. Everything an agent needs to understand the rules, the plan, the checklists, and the technology landscape is stored here.

**Purpose**: Single source of truth for laws, activities, quality standards, and technology options. Knowledge files are read by agents at the start of every session. They are updated only by approved activities — never edited ad hoc.

**README purpose**: Explain what reference material lives here, how agents use it at session start, and the rule that knowledge files are updated only through approved activities.

---

#### `knowledge/checklists/`

Quality checklists used during AvA review. Every artifact type has a corresponding checklist that defines what must be present before a Senior Validator can approve.

**Checklists defined here:**

| Checklist | Used for |
|---|---|
| artifact.md | All TYPE: ARTIFACT activities — pre-generation and AvA readiness checks |
| manual_step.md | All TYPE: MANUAL activities — human completion verification |
| ava.md | AvA round validation — round management, scoring, decision recording |
| prompt.md | Prompt quality review — clarity, completeness, law compliance |

Checklists are the enforcement mechanism for quality. A Senior Validator uses the relevant checklist when computing their score. No checklist, no valid AvA round.

**README purpose**: Explain which checklists exist, when each is used, and the rule that no artifact passes without checklist compliance.

---

#### `knowledge/tech_providers/`

Technology reference documents. Used during Phase 3 activities when agents evaluate and select technology options for the VASH engine and for software built by VASH.

**Documents defined here:**

| Document | Contents |
|---|---|
| ai_models.md | Claude models for VASH development; model routing options for client projects |
| platforms.md | AvA management platforms, human-in-loop platforms, reviewed for LAW 1 compliance |
| cloud_free_tier.md | Free tier compute, database, storage, and cache options across major cloud providers |

These documents are read-only reference material during technology decision activities. They are not updated by agents mid-activity. They represent the landscape of options at the time VASH was designed.

**README purpose**: Explain which technology reference files exist and when each is read.

---

### `runtime/`

The live working directory for all AvA activity. Every prompt generated, every artifact produced, every AvA log written, and every validation summary saved lands in a subfolder of `runtime/`.

**Purpose**: Provide a clean, structured, auditable record of all automated activity within a session or pipeline run. Runtime contents represent work in progress and completed outputs.

---

#### `runtime/artifacts/`

Completed VASH artifacts that have passed AvA review. This is the permanent output store for all approved activity results.

**Naming convention**: `[task_id]_artifact.md`

**Rules:**
- Only approved artifacts are stored here — nothing below threshold
- Full content always — no summaries, no truncation
- Artifacts are the source of truth for each completed activity

**README purpose**: Explain the naming convention and the rule that only approved, full-content artifacts live here.

---

#### `runtime/ava_logs/`

AvA round logs, one file per round per task. These are the verbatim records of every Junior and Senior exchange.

**Naming convention**: `[task_id]_round[n].md`

**Contents of each log:**
- Task ID and name
- Round number
- Junior artifact reference
- Senior review comments by section
- Score out of 100
- Decision: APPROVED, MODIFY, or FAIL

**Rules:**
- Every round is logged, including rounds that do not pass
- Logs are never edited after writing
- If a task reaches round 3 with no APPROVED decision, the log records escalation to human

**README purpose**: Explain the naming convention, the contents structure, and the rule that all rounds are logged regardless of outcome.

---

#### `runtime/drafts/`

Work-in-progress content from active AvA sessions. Content in drafts is temporary — it is either promoted to artifacts upon approval or discarded if the activity fails.

**Rules:**
- Drafts are never committed to main branch
- Drafts are cleared at the end of each completed activity cycle
- No artifact is treated as approved until it exits drafts and enters artifacts

**README purpose**: Explain that drafts are temporary, uncommitted, and cleared on activity completion.

---

#### `runtime/prompts/`

Generated prompts for Junior Creator sessions. Every prompt is saved before a Junior session begins — no session starts without a saved prompt.

**Naming convention**: `[task_id]_prompt.md`

**Contents of each prompt:**
- Activity definition (ID, name, description, output path)
- Three laws verbatim
- Relevant checklist verbatim
- Session rules and output format instructions

**Rules:**
- Prompts are saved before the session begins, not after
- Prompts are never edited during a session
- If a round is re-run, the new prompt is saved as a new file with round suffix

**README purpose**: Explain the naming convention, the contents structure, and the rule that prompts are saved before sessions begin.

---

#### `runtime/triggers/`

Activity trigger definitions. Triggers are the structured input files that initiate AvA pipeline runs from GitHub Actions.

**Purpose**: Encode the activity to be run, its parameters, and any runtime overrides in a form that the Python orchestrator can parse. Triggers are created by the notification or human approval workflow and consumed by the AvA workflow.

**Contents of each trigger:**
- Activity ID
- Round number (1 on first run, incremented on retry)
- Parallel flag
- Any human-provided overrides

**README purpose**: Explain what triggers contain, how they are created, and how they are consumed by the pipeline.

---

#### `runtime/validation/`

Validation summaries produced at the end of each activity cycle. A validation summary is the final record of the AvA outcome for a completed activity.

**Naming convention**: `[task_id]_summary.md`

**Contents:**
- Task ID and name
- Final score
- Final decision (APPROVED or ESCALATED)
- Round count
- Date and time of approval
- Summary of Senior objections that were resolved

**Rules:**
- One summary per activity — written only when the activity reaches a terminal state
- Summaries are the basis for updating the activity list STATUS field
- No activity is marked APPROVED in the activity list without a corresponding validation summary

**README purpose**: Explain the naming convention, the contents structure, and the rule that validation summaries gate activity list updates.

---

### `vash_framework/`

The primary design output directory. All artifacts produced by VASH agents during the design process live here, organised by phase.

**Purpose**: Build up the complete VASH 3.0 framework design, phase by phase, as the activity list progresses. When all phases are complete, this folder contains the full specification for building the actual VASH engine.

The subfolders in `vash_framework/` correspond directly to the phases in the activity list. Phase outputs are cumulative — later phases build on earlier ones.

**README purpose**: Explain how design outputs are organised by phase, how subfolders map to the activity list, and that this folder represents the cumulative specification for the VASH engine.

---

#### `vash_framework/vision/`

Phase 1 outputs. The vision layer — the north star documents that define what VASH is and what it is for.

**Documents produced here:**
- `1-1_vision.md` — Complete VASH 3.0 vision: what it is, what problem it solves, who it serves, how it differs from existing solutions
- `1-2_objectives.md` — Measurable objectives and success criteria per phase
- `1-3_scope.md` — Scope and boundaries: in-scope, out-of-scope, constraints, and assumptions
- `1-4_stakeholders.md` — Stakeholder map: roles, needs, and interaction points

Vision documents are read-only references once approved. They are never modified after acceptance. Later phases reference vision documents as the authority for why a design choice was made.

**README purpose**: Explain which vision documents exist here, what each covers, and the rule that approved vision documents are immutable references.

---

#### `vash_framework/agents/`

Phase 2 outputs. The agent architecture layer — the complete design of all agent roles, the AvA protocol, group configurations, handshake contracts, and SDLC phases.

**Documents produced here:**
- `2-1_agent_registry.md` — All 10 agent roles with identity, persona, Junior/Senior definition, skills domain, and AvA role
- `2-2_ava_protocol.md` — AvA protocol rulebook: two AvA layers, scoring thresholds, max rounds, stalemate rules, escalation triggers
- `2-3_groups.md` — Seven group configurations: roles per group, AvA pairings, phases covered, parallel rules
- `2-4_handshakes.md` — Handshake contracts: data schema and validation rules for every role-to-role handoff
- `2-5_sdlc_phases.md` — All 24 SDLC phases: name, purpose, entry criteria, exit criteria, roles, artifacts, parallel safety

Agent architecture documents are the specification for how the VASH engine will operate. They are technology-agnostic — no stack is locked in at this phase.

**README purpose**: Explain which agent architecture documents exist here and what each one specifies.

---

#### `vash_framework/architecture/`

Phase 3 outputs. The technology decisions layer — evaluated and justified choices for every component of the VASH engine platform.

**Documents produced here:**
- `3-1_ava_platform.md` — Selected AvA debate management platform with scoring and justification
- `3-2_hitl_platform.md` — Selected human-in-loop platform for approval channels
- `3-3_model_routing.md` — AI model routing rules for software built by VASH, not for VASH development
- `3-4_infrastructure.md` — Selected compute, storage, and database for the VASH engine platform
- `3-5_state_management.md` — Selected state and memory management approach
- `3-6_storage.md` — Selected artifact and log storage strategy
- `3-7_adr_master.md` — Master Architecture Decision Record consolidating all Phase 3 decisions

Every Phase 3 document confirms free tier compliance and open source compliance. No technology is selected without this confirmation. This satisfies LAW 1 — Vanilla First.

**README purpose**: Explain which architecture documents exist here and that every selection must confirm LAW 1 compliance.

---

#### `vash_framework/skills/`

Phase 4 outputs. The skills architecture layer — the complete catalog of all skills that VASH agents will use.

**Documents produced here:**
- `4-1_skills_governance.md` — Skills taxonomy, naming conventions, versioning, single responsibility rule, no-AI-inside rule, reuse search requirement
- `4-2_orchestration_skills.md` — Pipeline, routing, AvA, and human gateway skills with signatures, inputs, and outputs
- `4-3_analysis_skills.md` — Requirements, domain, risk, and compliance analysis skills
- `4-4_architecture_skills.md` — HLD, ADR, data model, and security design skills
- `4-5_engineering_skills.md` — Code generation, refactoring, integration, and API skills
- `4-6_quality_skills.md` — Test generation, chaos, performance, and E2E quality skills
- `4-7_operations_skills.md` — IaC, CI/CD, monitoring, SRE, and deployment operations skills
- `4-8_domain_pack.md` — Domain pack template and governance: schema, freshness rules, sensitivity levels, creation and approval process

For every skill catalogued, the search log documents what was searched before the skill was defined. Skills found in existing marketplaces or repositories are marked as reuse candidates. LAW 3 — Skills over Reinvention — is enforced at this phase.

**README purpose**: Explain which skills catalog documents exist here and that every skill entry must include a search record per LAW 3.

---

#### `vash_framework/platform/`

Phase 5 outputs. The platform design layer — the detailed design specifications for every component of the VASH engine platform.

**Documents produced here:**
- `5-1_repo_structure.md` — Final repository structure for the VASH engine and all projects it will build
- `5-2_gha_design.md` — Complete GitHub Actions automation architecture: all workflows, triggers, scripts, and flow
- `5-3_human_gateway.md` — Human gateway design: message formats, approval routing, rate limiting, identity verification
- `5-4_model_router.md` — Model router design for software built by VASH: routing rules, fallback chains, cost tracking
- `5-5_state_design.md` — Pipeline state management design: state schema, checkpoint format, recovery logic
- `5-6_cost_tracking.md` — Cost tracking and budget enforcement: token costs per project, alerts, usage reporting

Platform design documents are the bridge between technology decisions (Phase 3) and the build roadmap (Phase 6). They specify how the selected technologies are assembled into a working system.

**README purpose**: Explain which platform design documents exist here and that they must align with technology selections from Phase 3.

---

#### `vash_framework/blueprint/`

Phase 6 outputs. The master blueprint layer — the final, consolidated specification for building the VASH engine.

**Documents produced here:**
- `6-1_blueprint.md` — Complete VASH engine technical blueprint: single source of truth combining all phase outputs
- `6-2_build_roadmap.md` — Sequenced build plan: phases, dependencies, milestones, estimated effort, parallel opportunities
- `6-3_first_project.md` — Definition of the first real project VASH will build when operational

The blueprint is the terminal output of the entire VASH 3.0 design process. When `6-1_blueprint.md` is approved, the design phase is complete and the build phase begins.

All documents in this folder have the highest AvA threshold of the entire activity list. They synthesise every prior phase and must demonstrate full coherence.

**README purpose**: Explain which blueprint documents exist here and that this folder represents the terminal output of the VASH 3.0 design process.

---

## AvA Loop Summary

Every artifact in this repository was produced by the following cycle:

1. A GitHub issue with label `vash-activity` is created by the human owner or the notify workflow
2. GitHub Actions triggers the AvA workflow
3. The Python orchestrator builds an optimised prompt for the Junior Creator
4. Junior Creator generates the artifact in an isolated context
5. Senior Validator reviews the artifact against the relevant checklist and assigns a score out of 100
6. If score meets the activity threshold: APPROVED — artifact is committed, activity list updated, notification sent
7. If score is below threshold: MODIFY — Junior is re-prompted with Senior feedback, up to 3 rounds total
8. If 3 rounds complete without APPROVED: ESCALATED — human is notified to review and decide

No artifact in this repository was manually written without passing through this process.

---

## Three Laws Compliance Summary

| Law | How This Repository Complies |
|---|---|
| LAW 1 — Vanilla First | GitHub for version control and automation; Python for scripts; Claude AI for agent sessions; all free tier; no paid platforms during design phase |
| LAW 2 — Agent over Human | All artifact generation, review, scoring, committing, and notification is automated; human provides brief and approves milestones only |
| LAW 3 — Skills over Reinvention | Four marketplace skills installed before custom skills were built; search log maintained in skills folder; custom skills built only for VASH-specific functions with no marketplace equivalent |

---

## Navigation Quick Reference

| What you need | Where to look |
|---|---|
| Framework laws | `knowledge/laws.md` |
| Activity plan and status | `knowledge/activity_list.md` |
| Quality checklists | `knowledge/checklists/` |
| Technology reference | `knowledge/tech_providers/` |
| Agent, hook, skill config | `.claude/` |
| GitHub automation | `.github/` |
| Completed artifacts | `runtime/artifacts/` |
| AvA round records | `runtime/ava_logs/` |
| Validation summaries | `runtime/validation/` |
| Design outputs by phase | `vash_framework/` |
| Architecture decisions | `decisions/` |