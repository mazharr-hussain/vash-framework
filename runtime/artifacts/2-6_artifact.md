# VASH 3.0 — Application Framework Re-baseline (Blueprint v8.2 Merge)

Activity: 2.6 | Phase 2 — Agent Architecture | Threshold: 90
Status: Awaiting AvA and human decision (decisions/2-6_decision.md)
ADR: decisions/ADR-001-vash-application-framework.md (PROPOSED)

---

## 1. Purpose and Inputs

### 1.1 Purpose
Re-baseline VASH from "a framework that designs software" to **the application framework used by
every application**: one engine, one method, one catalog. Every project (KYC, COMMON, future
applications) uses VASH. This activity merges the owner's Master Architecture Blueprint v8.2 into
the approved VASH design (activities 0.1–2.5), keeping VASH's method and taking v8.2's execution
layer.

### 1.2 Inputs
| Input | Source |
|---|---|
| Master Architecture Blueprint v8.2 (Mazhar Hussain, November 2026) | Supplied by the human owner, 5 Nov 2026 |
| Approved VASH artifacts 1.1–2.5 | vash_framework/vision/, vash_framework/agents/ |
| Laws and tech provider references | knowledge/laws.md, knowledge/tech_providers/ |
| Session validation findings C1–C11 | runtime/prompts/2-6_prompt.md |

### 1.3 Owner positions (5 Nov 2026 session)
| # | Position |
|---|---|
| P1 | VASH is the framework / tool used for any application. It is v8.2's platform core. |
| P2 | VASH, with the human, decides each project's stack, skills, agents and tools. The decision is recorded and made available in the project repository. |
| P3 | The VASH repository is public. KYC and every client project repository is private (GitHub Free). |
| P4 | The merge keeps the VASH method and takes the v8.2 execution layer. |

### 1.4 Terms used in this artifact
| Term | Meaning |
|---|---|
| Activity-list phase (0–7) | VASH's own work plan in knowledge/activity_list.md (e.g. activity-list Phase 7 — Engine Build) |
| SDLC phase (1–8) | What VASH does for a project, from vash_framework/agents/2-5_sdlc_phases.md (e.g. SDLC Phase 3 Architecture Design) |
| Execution stage (0–10) | Blueprint v8.2 stages run for a project after design (build, review, pipeline, release, post-release); not SDLC phases |
| Amendment status | Every "Amended by 2.6" change is PROPOSED and takes effect when ADR-001 is ACCEPTED |

### 1.5 Findings to resolve
| ID | Finding |
|---|---|
| C1 | Paid Claude subscription allowed ("no cost cap") — v8.2 requires $0 |
| C2 | "Claude only" and LiteLLM — v8.2 requires multi-vendor pooling (freellmpool) |
| C3 | Junior and Senior on the same vendor; the script runs one model for both — v8.2 requires the Critic on a different LLM |
| C4 | Stalemate auto-approve at ≥ 80 — v8.2 rejects anything below the floor |
| C5 | No data-privacy rule; intake goes to a cloud model |
| C6 | No deterministic gate before the Senior review |
| C7 | OCI Ampere A1 missing; MVP stack recommends Supabase / Upstash |
| C8 | No catalog, Freeze file, loader or stack-pack concept |
| C9 | Final-merge approval not named in LAW 2 |
| C10 | Scope and CLAUDE.md forbid code until "VASH 4.0" |
| C11 | GitHub Free private-repo limits (minutes, protection, scanning) not designed for |

---

## 2. What VASH Is

### 2.1 Definition
VASH is the **application framework** of the Virtual AI Software House. It has three parts:

| Part | What it is | Examples |
|---|---|---|
| **Method** | How work is done and judged | Laws, AvA protocol, 10 roles, 7 groups, 7 handshakes, SDLC phases, checklists, ADR template |
| **Engine** | What runs the method (built in activity-list Phase 7) | Supervisor graph, deterministic gate tools, loader, cost meter, canary injector, licence verifier, reusable CI workflows |
| **Catalog** | Everything a project may use, vetted once | Stack packs, skills, agent personas, tools, each with licence, version and source |

### 2.2 Three layers
| Layer | Lives in | Holds | Owner |
|---|---|---|---|
| **Core** | VASH repository (public) | Method, engine, catalog index, templates | VASH |
| **Stack pack** | VASH repository, `stacks/<pack>/` | Stack-specific skills, rules, deterministic linters, test runner, deploy and browser-test recipes | VASH |
| **Project** | One private repository per application | Its Freeze file, its ADRs, its audit trail, its code and data | The project, decided through VASH |

### 2.3 Boundary rules
1. The core contains no stack. Oracle APEX, ATP, utPLSQL and PL/SQL linters belong to the
   `oracle-apex` stack pack, not to the core.
2. VASH contains no project data: no client code, requirements, test data, logs or AvA logs about
   a client. Data flows from VASH to projects only.
3. A project never copies a VASH component. It uses the pinned VASH version. An improvement found
   in a project returns to VASH only as a cleaned, generic rule with its test fixtures (Platform
   Rule R8).
4. VASH is versioned like a product: semantic version tags with release notes. Each project pins
   one VASH version in its Freeze file.

---

## 3. Comparison and Merge

### 3.1 Where v8.2 is stronger (taken into VASH)
| Area | v8.2 element taken |
|---|---|
| Deterministic first | Gate 1 scripts run before any AI review (92 / 8 split) |
| Critic independence | Critic on a different model and vendor from the Coder / Junior |
| Hard floor | No approval below the threshold, ever |
| Data privacy | Intake and client data on local Ollama only |
| $0 cost | Pooled free tiers from many vendors, local fallback |
| Reproducibility | Freeze file (`project-stack.json`) and clean-slate loader |
| Code safety | Writes only through an MCP tool with allowed paths; blocking linters |
| Full lifecycle | Stages 0–10 including release and post-release |
| Learning loop | Every novel failure becomes a deterministic check |

### 3.2 Where VASH is stronger (kept)
| Area | VASH element kept |
|---|---|
| Quality method | AvA protocol: checklists, MODIFY / FAIL / ESCALATE, dual-Senior lower score |
| Risk-based thresholds | 90 for critical artifacts, 88 for all others; 88 is the floor (the former 85 standard tier is raised to 88) |
| Roles and groups | 10 roles, 7 groups, sequencing rules (v8.2 has only Supervisor, Coder, Critic) |
| Handshakes | 7 defined contracts between roles and phases |
| Design depth | 8 SDLC phases with human gates (v8.2 compresses these into Stages 1 and 3) |
| Audit trail | Full prompts, round logs, validations and decisions saved and committed |
| LAW 3 proof | Search log: what was searched, found, reused, built |
| Technology neutrality | Roles and phases contain no stack |
| Parallel scheduling | PARALLEL_SAFE and DEPENDS_ON |

### 3.3 Added by the merge (new to both)
| Element | Purpose |
|---|---|
| Cost meter | Measures GitHub minutes, storage and LLM tokens; enforces budgets (Section 8.4) |
| Canary injector | Plants a known defect to prove the Critic catches it (Section 9.4) |
| Licence verifier | Checks every catalog asset's licence before it is forked or frozen |
| Stack packs | Make "swap the stack by changing the Freeze file" real |
| Freeze-change rule | `project-stack.json` changes only through an ACCEPTED ADR |

The tools above (cost meter, canary injector, licence verifier, the Freeze-change check, and the
loader / provisioner of Section 4.1) are **designs pending search**: Section 14.2 lists the candidates
found so far and the activity that completes each LAW 3 search. A tool is built only when the search
finds no reusable one.

---

## 4. Stack Decision and Freeze Lifecycle

### 4.1 Who decides
VASH's agents propose, the human accepts, VASH writes the result into the project. The project
repository never chooses on its own (P2).

| Step | Actor | Output | Gate |
|---|---|---|---|
| 1 Brief intake | PM (Group 1), local model | Validated brief | Human confirms brief |
| 2 Requirements | BA, UI/UX (Group 1) | FRDs | Human approves FRDs |
| 3 Stack proposal | SA (Group 2), DE support | Stack selection from the catalog: stack pack, skills, agents, tools, runner, budget | AvA, threshold 90, cross-role review |
| 4 ADR | SA | `decisions/ADR-NNN-stack.md` in the project, Status PROPOSED | — |
| 5 Human gate | Human owner | Status changed to ACCEPTED | Pipeline resumes only on ACCEPTED |
| 6 Freeze | Engine (deterministic) | `project-stack.json` written from the ACCEPTED ADR | Schema validation |
| 7 Provision | Engine (deterministic) | Submodules pinned, workflows pinned, `.github/` templates, audit folders | Stage 0 passes |
| 8 Use | Loader, every session and run | Only the frozen agents and skills loaded | Stage 0 every run |

### 4.2 Catalog gap
When the stack proposal needs an asset that the catalog does not hold:
1. The SA records the gap in the stack ADR.
2. The Prompt Engineer group searches vendor indexes and vetted MIT community indexes and records
   the search (LAW 3).
3. The licence verifier checks the licence. A licence that does not allow redistribution in a
   public repository is refused for the catalog.
4. AvA review of the asset (threshold 90, technology selection), then a catalog ADR in VASH,
   accepted by the human.
5. The asset is forked into VASH's `external/` (submodule) or added as a VASH skill, and indexed in
   `ai-manifest.json`. Every later project can reuse it.
6. Only then can a project freeze it.

### 4.3 Changing a frozen stack
1. Change request (GitHub issue in the project).
2. New ADR that supersedes the earlier one (`ADR-00N`, "Supersedes ADR-00M").
3. AvA review, human ACCEPTED.
4. The engine rewrites `project-stack.json`; Stage 0 and the full pipeline run.
5. A deterministic check refuses any change to `project-stack.json` that does not name an ACCEPTED
   ADR. Nobody edits the Freeze file by hand.

### 4.4 Upgrading the VASH version of a project
The VASH version pin is part of the Freeze. An upgrade follows 4.3: the ADR cites the VASH release
notes; the pipeline runs every gate on the new version before the pin moves.

### 4.5 Adopting an existing project (KYC)
A project whose stack was chosen before VASH (the first is KYC; its stack is recorded in its own
repository) is adopted, not redesigned:
1. The project's first ADR, "Adopt existing stack" (ADR ids are per repository; cross-repository
   references carry the repository qualifier, e.g. kyc:ADR-001), written by the SA from the project's current
   state, Status PROPOSED.
2. Human ACCEPTED.
3. The engine writes the project's `project-stack.json`; its existing pipeline remains until the
   stack pack covers it.
4. The project's stack-specific pipeline parts move into the stack pack over time; the project then
   calls the pack instead of keeping its own copy.
KYC adoption is activity 7.11 (activity-list Phase 7), carried out in the KYC repository, not in VASH.

---

## 5. v8.2 Stages Mapped onto VASH

| v8.2 Stage | VASH SDLC phase or execution stage | VASH actor | Deterministic or AI | Gate |
|---|---|---|---|---|
| 0 Ownership and dependency check | Before every SDLC phase and execution stage | Engine | Deterministic: Freeze file vs installed versions, VASH version pin; mismatch halts | Halt |
| 1 Requirement intake | SDLC Phase 1 Brief Intake | PM, Group 1 | AI on local model only (R2) | Human confirms brief |
| 2 Work items | SDLC Phase 1 exit / SDLC Phase 2 | PM | Deterministic: issues created with labels through the GitHub CLI; read-only status export each run | — |
| 3 Solution design and ADR gate | SDLC Phases 2–8 | BA, SA, UI/UX, SE, DE with AvA | AI judgment + AvA | ADR ACCEPTED by human |
| 4 Build | Execution stage (project), not an SDLC phase | SE, DE (Coder) | AI, writes only through the MCP write tool with allowed paths (R6) | — |
| 5 Offline review | Every artifact and change | Gate 1 tools, then Senior / Critic | Gate 1 deterministic (tests, linters, schema, secret scan); Gate 2 AI score on a different vendor | Floor; any Gate 1 failure returns to the Junior without AI review |
| 6 Change request | Execution stage (project) | Engine | Deterministic: one squashed commit, standard PR title | — |
| 7 Pipeline execution | Execution stage (project): runs what SDLC Phases 6–7 designed | DevOps role; engine workflows | Deterministic: light jobs hosted, heavy jobs self-hosted (private projects) | Every job green |
| 8 Fix loop | Execution stage (project) | Coder with the error log | AI fix; hard cap 3 attempts, then escalate | Human after 3 |
| 9 Release | Execution stage (project) | Engine | Deterministic: merge after human approval, semantic tag, artifacts | Human approves merge (LAW 2) |
| 10 Post-release | Execution stage (project) | QA role; scheduled workflow | Deterministic: scheduled browser tests against the live app, results as issues | — |

The 92 / 8 rule: every step marked deterministic is a script; AI is used only where the table says
"AI".

---

## 6. Contracts

### 6.1 `project-stack.json` (Freeze file, one per project repository)
Written by the engine from an ACCEPTED ADR. Never edited by hand.

| Field | Required | Meaning |
|---|---|---|
| `schema_version` | Yes | Version of this contract |
| `project.id`, `project.name` | Yes | Project identity |
| `project.repository` | Yes | Owner / name of the project repository |
| `project.visibility` | Yes | `private` for client projects |
| `vash.version` | Yes | Pinned VASH release tag |
| `vash.commit` | Yes | Commit SHA of that tag |
| `stack.pack` | Yes | Stack pack name from the catalog (e.g. `oracle-apex`) |
| `stack.pack_version` | Yes | Version of the pack |
| `stack.platform_version` | Yes | Platform versions Stage 0 checks (e.g. APEX, database, runtime) |
| `agents[]` | Yes | Agent personas loaded: catalog id, source, pinned commit, licence |
| `skills[]` | Yes | Skills loaded: catalog id, source, pinned commit, licence |
| `tools[]` | Yes | MCP servers and CLIs allowed: id, version, checksum |
| `paths.allowed_write[]` | Yes | Paths the MCP write tool may change |
| `models.intake` | Yes | Local model for intake (privacy) |
| `models.coder`, `models.critic` | Yes | Pool routes; the critic route must name a different vendor |
| `thresholds` | Yes | Per artifact type; none below the floor 88 |
| `limits.max_retries` | Yes | Fix-loop cap (3) |
| `canary.interval` | Yes | Number of AvA rounds between canary checks |
| `canary.max_misses` | Yes | Consecutive misses before the critic route is escalated (2) |
| `licences_allowed[]` | No | Project restriction of the VASH-wide allowed list in ai-manifest.json (never wider) |
| `runners.light`, `runners.heavy` | Yes | Hosted image and self-hosted labels |
| `budget` | Yes | Monthly hosted minutes, storage, token budgets, warn and switch percentages |
| `gates.merge` | Yes | How the human merge approval is enforced (Section 8.3) |
| `decisions[]` | Yes | ADR ids this Freeze was written from |

Validation (deterministic, Stage 0): every catalog id exists in the pinned VASH `ai-manifest.json`;
licences are on the allowed list (ai-manifest.json `licences_allowed[]`, narrowed by the project's
`licences_allowed[]`); critic vendor differs from coder vendor; thresholds ≥ 88; the ADRs
listed are ACCEPTED.

### 6.2 `ai-manifest.json` (catalog index, VASH core)
Top level: `schema_version` (version of this contract), `licences_allowed[]` (SPDX ids allowed for
catalog assets), `entries[]` with the fields below.

| Field | Meaning |
|---|---|
| `id` | Unique catalog id |
| `type` | stack-pack / skill / agent / tool / rule-set |
| `source` | Upstream repository or vendor index |
| `fork` | Path under `external/` or `skills/` / `stacks/` |
| `licence` | SPDX id, verified by the licence verifier |
| `version`, `commit` | Pinned version |
| `stacks[]` | Stack packs it applies to (empty = stack-neutral) |
| `adr` | VASH catalog ADR that accepted it |
| `search_log` | Reference to the LAW 3 search record |
| `status` | candidate / accepted / deprecated |

Only `accepted` entries may be frozen by a project.

---

## 7. Target Repository Structures

Final detail is set by activity 5.1; this is the baseline input to it. Folders are created in
activity 7.2.

### 7.1 VASH core (public)
```
vash3-framework/
├── README.md  LICENSE (MIT)  CLAUDE.md (generated from method/laws)
├── ai-manifest.json            catalog index (Section 6.2)
├── method/                     the VASH method
│   ├── laws/                   3 laws (changed only by an ACCEPTED ADR) + platform rules
│   ├── ava/                    protocol, thresholds, checklists
│   ├── roles/ groups/ handshakes/ sdlc/
│   └── templates/              ADR, brief, FRD, project-stack contract
├── knowledge/                  activity list, tech provider references
├── decisions/                  VASH's own ADRs and activity decisions
├── vash_framework/             approved design artifacts (as today)
├── framework/                  the engine (activity-list Phase 7)
│   ├── supervisor/             graph: Supervisor -> Prompt Eng -> Junior/Coder -> Gate 1 -> Senior/Critic
│   ├── pool/                   LLM pool configuration
│   ├── mcp/                    write tool with allowed paths
│   ├── claude/                 tracked hooks and settings, linked by the loader
│   ├── loader/                 clean-slate loader (shell and PowerShell)
│   └── tools/                  stack check, issue creation, status export, PR, cost meter,
│                               canary injector, licence verifier
├── stacks/
│   └── oracle-apex/            first stack pack: skills, rules, linters, test runner, deploy, UI tests
├── skills/                     stack-neutral VASH skills
├── external/                   vetted submodules (licence-checked)
├── iac/                        modules (compute, database, networking) + environments
├── .github/workflows/          VASH's own CI + reusable workflows for projects
├── tests/                      engine tests + linter regression fixtures
├── audit/                      committed: VASH's own prompts, AvA logs, validations, triggers
│                               (today's runtime/ folders, moved in 7.2 with the workflows' paths)
├── runtime/                    git-ignored: checkpoints, raw logs, scratch
└── .claude/                    generated by the loader
```

### 7.2 Project repository (private), written by VASH provisioning
```
<project>/
├── project-stack.json          Freeze file (Section 6.1)
├── decisions/                  project ADRs (stack, changes)
├── audit/                      committed: prompts, AvA logs, validations, metric summaries
├── external/vash               VASH pinned at the frozen version (submodule)
├── .github/workflows/          calls VASH reusable workflows at pinned SHAs
├── <application source>        layout defined by the stack pack
├── data/intake/                git-ignored: raw client input, local model only
├── runtime/                    git-ignored: checkpoints, raw logs, scratch
└── .claude/                    git-ignored: generated by the loader from the Freeze file
```

### 7.3 Structure rules
1. GitHub runs workflows only from `.github/workflows/`. No `pipelines/` folder for GitHub
   Actions.
2. Each tool exists once (no duplicate linter in a skill and in tools; the skill calls the tool).
3. The loader may clear and regenerate `.claude/`, but tracked hooks and settings live in
   `framework/claude/` and are linked from there; the loader copies when symbolic links are not
   available (Windows without Developer Mode).
4. The same names in both layers: `audit/` is the committed audit trail; `runtime/` is always
   git-ignored (checkpoints, raw logs, scratch). Until 7.2 moves them, VASH's audit files stay in
   today's `runtime/` folders and the current output rules (CLAUDE.md) apply.
5. Python dependencies are pinned with hashes.

---

## 8. Visibility, Quotas, Runners and Gates

### 8.1 Visibility model (P3)
| Repository | Visibility | Reason |
|---|---|---|
| VASH | Public, MIT | LAW 1 open source; unlimited hosted minutes; native protection and scanning free |
| KYC, COMMON, client projects | Private | Client code and data |

### 8.2 GitHub Free quotas used in the design
Figures from the provider's published plans; re-verify in activity 3.4 because plans change.

| Quota | Public (VASH) | Private (projects) |
|---|---|---|
| Hosted Linux minutes | Unlimited | 2,000 per month (Windows 2×, macOS 10×) |
| Billing granularity | — | Each job rounded up to a whole minute |
| Branch protection / rulesets enforced | Yes | No |
| Environment required reviewers | Yes | No |
| Code scanning, secret push protection | Free | Paid (not used) |
| Artifact and package storage | Free | 500 MB |
| Self-hosted runner | Not used (untrusted code risk) | Main runner for heavy jobs; possible platform charge announced by the provider — verify in 3.4 |

### 8.3 Gates: where each is enforced
| Gate | VASH (public) | Projects (private) |
|---|---|---|
| Human merge approval | GitHub ruleset: required review + required checks | Pipeline: the merge job runs only when the PR's ADR is ACCEPTED and the owner's approval label is present, set by a user on the allow-list file |
| ADR ACCEPTED before work resumes | Deterministic check | Deterministic check |
| Secret scan | GitHub secret scanning + gitleaks | gitleaks |
| Static analysis | CodeQL + Semgrep | Semgrep + stack-pack linters |
| Freeze file change | Check: names an ACCEPTED ADR | Same |

Residual risk in private projects: GitHub Free does not enforce protection there, so a person with
write access could push directly to the default branch, set the label, or change the allow-list or the
workflow. Mitigations:
1. Only the owner has write access to private project repositories; agents and the engine change them
   only through pull requests.
2. The allow-list file and the workflows are covered by the Freeze-change rule (an ACCEPTED ADR is
   required) and by Gate 1.
3. A scheduled deterministic audit job raises an issue for every commit on the default branch that was
   not merged by the gated merge job, and for every change to the allow-list or workflows.
The risk is accepted for the $0 baseline; the alternative (a paid plan with enforced protection) is
open decision OD-2.

### 8.4 Runner split and cost meter
| Repository | Light jobs (lint, checks, status export) | Heavy jobs (deploy, DB tests, browser tests, AvA / LLM waits) |
|---|---|---|
| VASH | Hosted | Hosted (unlimited) — never self-hosted |
| Private project | Hosted, merged into 1–2 jobs, target ≤ 3 billed minutes per push | Self-hosted OCI A1: one host, one heavy job at a time across all projects |

Runner registration (to verify in 3.4): on a personal GitHub Free account, self-hosted runners are
registered per repository, so the A1 host runs one runner registration per project repository. The
host serialises them: every heavy job takes one host-wide lock before it starts and releases it when it
ends, so only one heavy job runs at a time (rule R13). Alternative: move the private projects into a
free GitHub organization and register one organization-level runner shared by them — availability on
the free organization plan to verify in 3.4.

Cost meter rules (platform rule R10):
- Reads the provider's billing usage for hosted minutes and storage, the pool's token counts, and
  the A1 runner's memory and disk.
- Warn at 70 % of the month's hosted minutes; at 90 % every job of private projects runs on the
  self-hosted runner.
- Output committed as a monthly summary in each repository's audit trail.

Public-repository safety (VASH):
- Workflows triggered by push or manual dispatch only; never a trigger that runs secrets on a
  fork's pull request; outside contributors' workflows need approval.
- Every action pinned to a commit SHA.
- Tokens fine-grained and scoped to the VASH repository only.
- Full-history secret scan before the repository is made public (activity 7.1).

### 8.5 Overflow
GitLab or Azure DevOps mirrors are an emergency option only, decided by ADR when needed; not part of
the baseline. OCI DevOps is not used in the baseline (one CI system).

---

## 9. LLM Strategy

### 9.1 Routing by stage
| Use | Route | Reason |
|---|---|---|
| Intake, any client data | Local Ollama on the A1 VM only | Platform rule R2 (privacy) |
| VASH's own design work (public, no client data) | Free-tier pool | $0 |
| Coder / Junior on project work | Free-tier pool, or local when the input contains client data | $0, privacy |
| Critic / Senior | Free-tier pool, a different vendor from the Coder / Junior | R4 independence |
| Fallback when every free tier is exhausted | Local Ollama | Availability |

### 9.2 Pooling tool
v8.2 names `freellmpool` (MIT, many providers behind one OpenAI-compatible endpoint). It is **not yet
verified** in this session. Activity 3.3 carries out the LAW 3 verification (existence,
maintenance, licence, providers, quota tracking, local fallback). If it fails, the alternative
candidates are LiteLLM (current reference) and others found in the search; the choice is made by ADR.
No custom routing logic is written (platform rule R12).

### 9.3 Different-vendor Critic
The Freeze file names the coder and critic routes; Stage 0 refuses a Freeze in which both name the
same vendor. Model names are never hardcoded in prompts or scripts; they come from the Freeze file
(projects) or the VASH pool configuration (VASH itself).

### 9.4 Canary
Once per configured number of AvA rounds (set in the VASH pool configuration for VASH work, and in project-stack.json `canary.interval` for projects), the canary injector plants a known
defect in a copy of the artifact under review. The Critic must find it. A missed canary invalidates
that round's score, is recorded in the audit trail, and after two misses in a row the critic route is
escalated to the human for change.

### 9.5 Transitional rule for VASH development
Until the engine runs on the pool (exit of activity 7.7, activity-list Phase 7), VASH's own development may continue
with the Claude tooling already in use. This is an explicit, time-limited exception to LAW 1
(open decision OD-1). No client project depends on a paid service.

---

## 10. Hardware and Free-Tier Constraints
Re-verify every figure in activity 3.4.

| Resource | Constraint used in the design |
|---|---|
| OCI Ampere A1 (Always Free) | v8.2 sizes one VM at 2 OCPU / 12 GB; the Always Free allowance is published as 4 OCPU / 24 GB in total, leaving room for a second VM |
| A1 workload | Self-hosted runner + Ollama with one 7B coder model + browser tests + database CLI on one VM: one job at a time across all projects (host-wide lock, Section 8.4); the model is unloaded after intake |
| A1 risks | Idle-instance reclaim policy and regional capacity shortages — handled in 3.4 |
| Autonomous Database (Always Free) | Session limit (v8.2: 30): database connections serialized |
| GitHub | Section 8.2 |
| Architecture | ARM64: every tool for the self-hosted runner must have a Linux ARM64 build, pinned with checksums |

---

## 11. Resolution of Findings

| ID | Change | Files |
|---|---|---|
| C1 | LAW 1 now requires $0 for everything VASH builds and runs; a time-limited exception for VASH's own development tooling (9.5, OD-1) | knowledge/laws.md, CLAUDE.md, vision/1-2_objectives.md, tech_providers/platforms.md |
| C2 | Multi-vendor pooling through a vetted tool; "Claude only" removed; LiteLLM becomes a fallback candidate pending 3.3 | agents/2-1_agent_registry.md, tech_providers/ai_models.md |
| C3 | Senior / Critic must run on a different vendor; enforced by Stage 0 and the AvA protocol | agents/2-2_ava_protocol.md, agents/2-1_agent_registry.md |
| C4 | Stalemate auto-approve removed: below threshold is never approved; 70 to below threshold escalates to the human; < 70 fails; round 3 below threshold without stalemate escalates | agents/2-2_ava_protocol.md, .claude/skills/vash-orchestrator/SKILL.md, .claude/skills/multi-agent-patterns/SKILL.md |
| C5 | Platform rule R2: client data and intake on the local model only | knowledge/laws.md, agents/2-5_sdlc_phases.md |
| C6 | Gate 1 deterministic checks before every Senior review | agents/2-2_ava_protocol.md |
| C7 | OCI A1 and Autonomous Database added; MVP recommendation replaced | tech_providers/cloud_free_tier.md |
| C8 | Catalog, Freeze file, loader, stack packs, freeze lifecycle | this artifact Sections 2, 4, 6, 7; agents/2-5_sdlc_phases.md |
| C9 | LAW 2 names the human approvals: brief, ADRs, milestones, final merge | knowledge/laws.md, CLAUDE.md |
| C10 | Engine code in scope from activity-list Phase 7, after the blueprint (6.1) is approved; design-only until then | vision/1-3_scope.md, vision/1-1_vision.md, CLAUDE.md, knowledge/activity_list.md |
| C11 | Visibility model, runner split, gates per visibility, cost meter | this artifact Section 8; tech_providers/cloud_free_tier.md |

Known implementation gaps (fixed in activity-list Phase 7, not in this design activity): the AvA
script (.github/scripts/ava.py) still contains the stalemate auto-approve at ≥ 80 and calls one model
for Junior and Senior — interim instruction: the orchestrator never auto-approves (the amended skills
above); the two model routes are added in 7.7 and the CODE activity type in 7.8; the AvA
workflows pin actions by tag, not commit SHA; the repository has no LICENSE file.

---

## 12. Changes to the Activity List
All changes are marked "Amended by 2.6" in knowledge/activity_list.md.
1. New activity 2.6 (this activity), depends on 2.5, threshold 90.
2. Activities 3.1–3.6 depend on 2.6 (and through it on 2.5); their descriptions now include:
   3.1 supervisor / AvA platform (v8.2 candidate LangGraph); 3.2 human-in-loop (ADR gate, merge gate,
   residual risk); 3.3 model routing (pool verification, critic vendor, local intake); 3.4
   infrastructure (A1, Autonomous Database, GitHub quotas, runner registration); 3.5 state (GitHub
   Projects, status export, graph checkpoints); 3.6 storage (audit/ committed, runtime/ ignored).
3. Descriptions amended: 3.3 (routing also for VASH's own work after 7.7), 4.1 (catalog and stack-pack
   governance, licence verifier search), 4.6 (canary injector search), 4.8 (stack packs alongside domain
   packs), 5.1 (finalise Section 7, loader search), 5.2 (finalise Section 8, pinning search), 5.4 (pool
   routing, no LiteLLM default), 5.6 (cost meter and its search).
4. New activity type CODE with checklist knowledge/checklists/code.md (Gate 1 green, tests, linters,
   SHA pins, licence check, AvA on the change) for engine build activities. Registered in the activity
   list format (TYPE: ARTIFACT / MANUAL / CODE) and in knowledge/CLAUDE.md checklist selection. Until the
   licence verifier exists (7.9), the licence check is the interim check of code.md: the
   asset's SPDX licence file is read and recorded in the AvA log and checked against the allowed list.
5. Provisional activity-list Phase 7 — Engine Build (confirmed or changed by 6.2):

| ID | Name | Type | Depends on |
|---|---|---|---|
| 7.1 | Prepare VASH for public visibility: automated history secret scan, LICENSE, SHA pins, safe triggers, token scopes; only the visibility switch is human | CODE | 6.2 |
| 7.2 | Create the core repository structure (Section 7.1), move runtime/ audit folders to audit/, create the initial ai-manifest.json (schema_version, licences_allowed[]) (output: the structure itself; record in audit/validation/) | CODE | 7.1 |
| 7.3 | Freeze contract validator and Stage 0 check | CODE | 7.2 |
| 7.4 | Clean-slate loader (shell and PowerShell) and status export | CODE | 7.3 |
| 7.5 | Deterministic Gate 1 tools (linters, schema, secret scan) and regression fixtures | CODE | 7.3 |
| 7.6 | A1 VM, self-hosted runner and local model (IaC) | CODE | 7.2 |
| 7.7 | LLM pool configuration, different-vendor Critic, local intake, and the AvA scripts switched to two model routes — exit ends OD-1 | CODE | 7.3, 7.6 |
| 7.8 | Supervisor graph with ADR gate, hard floor and fix-loop cap; AvA scripts aligned (no stalemate auto-approve, CODE type) | CODE | 7.5, 7.7 |
| 7.9 | Cost meter, canary injector, licence verifier | CODE | 7.8 |
| 7.10 | Reusable workflows (light hosted, heavy self-hosted with host-wide lock) | CODE | 7.9 |
| 7.11 | First stack pack `oracle-apex` and adoption of KYC (ADR "Adopt existing stack" in the KYC repository) | CODE | 7.10 |

## 13. Open Decisions for the Human Owner
| ID | Decision | Recommendation |
|---|---|---|
| OD-1 | Allow VASH's own development to keep using the existing Claude tooling until 7.7 exits | Yes, time-limited |
| OD-2 | Human merge approval in private projects: approval label + ACCEPTED ADR, enforced by the pipeline, with the residual risk and mitigations of Section 8.3 accepted | Yes (a paid plan would be needed for enforced protection) |
| OD-3 | One CI system (GitHub Actions); OCI DevOps and mirrors only by later ADR | Yes |
| OD-4 | Repository model: VASH public core, one private repository per project | Yes |
| OD-5 | Engine code in scope from activity-list Phase 7, after 6.1 is approved | Yes |
| OD-6 | Repository name: keep `vash3-framework` as the platform core (no separate "predictive-profit-platform-core") | Keep `vash3-framework` |

---

## 14. LAW Compliance and LAW 3 Search Record

### 14.1 Laws
| Law | How this artifact complies |
|---|---|
| LAW 1 Vanilla First | $0 baseline; open-source and free-tier only; public MIT core; the single paid dependency is named, time-limited and open for decision (OD-1) |
| LAW 2 Agent Over Human | Every repeated step is deterministic and automated; the human only approves brief, ADRs, milestones and final merge |
| LAW 3 Skills Over Reinvention | Catalog-first; external tools reused (pooling tool, linters, scanners, runner, IaC modules); nothing built where a vetted tool exists |

### 14.2 Search record
| Searched | Found | Reused / decision |
|---|---|---|
| Blueprint v8.2 tool list (freellmpool, LangGraph, utPLSQL, Playwright, SQLcl, Terraform, Ollama, Semgrep rules, agent personas, Oracle skills) | Named by the owner; not verified in this session | Verification assigned: 3.1 (LangGraph), 3.3 (pool, Ollama), 3.4 (Terraform, A1), 4.x (skills, personas, licences) |
| Existing VASH artifacts 1.1–2.5 | Method complete; execution layer missing | Kept and amended (Section 11) |
| The owner's existing private project pipeline (KYC) | Generic patterns that work on GitHub Free private repositories | Source for the `oracle-apex` stack pack (7.11), generic parts only; patterns adopted as VASH rules: actions pinned to commit SHAs, hashed dependencies, short artifact retention, one report per run |
| Licence verifier | Candidates: ScanCode Toolkit (Apache-2.0), licensee (MIT), REUSE tool | Search completed and decided in 4.1 (catalog governance); build only if none fits |
| Cost meter | Candidates: GitHub billing usage API through the GitHub CLI; the pooling tool's own quota tracking | Search completed in 3.3 / 5.6; the meter only combines existing sources |
| Canary injector | Candidates: mutation-testing tools (for code); no known tool for design artifacts | Search completed in 4.6 (quality skills); built only for what no tool covers |
| Clean-slate loader and provisioner | Candidates: GitHub template repositories, Copier / Cookiecutter (scaffolding), git submodules | Search completed in 5.1; built only as a thin script over the chosen tools |
| Action and dependency pinning | Candidates: pinact (MIT), ratchet (Apache-2.0), Dependabot (GitHub, free) | Search completed in 5.2 |
| Orchestration frameworks (1.1 search: AutoGPT, CrewAI, LangGraph, AutoGen, MetaGPT, Agency Swarm) | Recorded in 1.1 | LangGraph remains the v8.2 candidate, decided in 3.1 |
