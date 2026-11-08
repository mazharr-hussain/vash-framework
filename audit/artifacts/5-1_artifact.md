<!-- Activity 5.1 — Design complete GitHub repository structure | Phase 5 | Threshold 88
     Brought forward by owner decision (6 Nov 2026). Source: the structure frozen by the owner (v7, D1-D9),
     also published as the page "VASH Repository Structure". ADR: decisions/ADR-002-repository-structure.md (PROPOSED).
     Written by: H owner · A agent (AvA) · A→H agent then owner approval · E engine (generated) · X upstream (pinned). -->

# VASH Repository Structure

Status: FROZEN by the owner on 6 Nov 2026 (v7, including decision D9). Changes only through a new owner decision. Repository: mazharr-hussain/vash-framework (public, MIT).

Written by: H = human owner · A = agent, reviewed through AvA · A→H = agent, then owner approval · E = engine (generated, no AI) · X = upstream project, pinned

## Overview

```
vash-framework/
├── (root files)            front door, licence, package, catalog index
├── method/                 ① THE METHOD   – how work is done and judged
├── catalog/                ② THE CATALOG  – every technology choice: stacks, LLM, git host, CI, cloud
├── src/vash/               ③ THE ENGINE   – vendor-free core + one adapter per technology
├── bin/                    ③ thin start scripts (no pip needed)
├── scaffold/project/       ④ what VASH writes into a new project repo
├── .github/                CI for VASH + reusable workflows for projects
├── iac/<cloud>/            infrastructure code per cloud (first: OCI Always Free)
├── examples/               a sample project to try VASH end to end
├── tests/                  tests of the engine, catalog and examples
├── docs/                   user documentation + approved design documents
│
│  ── VASH building itself (its own first project) ──
├── project-stack.json      VASH's own freeze
├── plan/                   VASH's own roadmap
├── decisions/              VASH's ADRs and activity decisions
├── audit/                  VASH's own AvA trail
├── .claude/                settings.json tracked; agents/skills/hooks generated
└── runtime/                git-ignored scratch
```

## Root files

The front door of the repository: what a visitor, an installer and the engine read first.

| File | Purpose | By | How it is used | Wave |
|---|---|---|---|---|
| `README.md` | Front page: what VASH is, a 5-minute quick start, links to the docs | A→H | First thing every visitor reads | W1 |
| `LICENSE` | MIT licence text | H | Legal permission for anyone to use, change and share VASH | W1 |
| `GOVERNANCE.md` | Who decides: the owner decides by ADR; contributors propose; AvA review is required for every change | A→H | Read by contributors and users to know how VASH changes | W1 |
| `CONTRIBUTING.md` | How outsiders propose changes: issue first, then PR, AvA review, and how to submit a catalog asset (search record, licence) | A→H | Read before anyone contributes | W1 |
| `SECURITY.md` | How to report a vulnerability privately; which versions get fixes | A→H | Used by security researchers | W1 |
| `CODE_OF_CONDUCT.md` | Behaviour rules (reused Contributor Covenant, Law 3) | X | Applies to issues and PRs | W1 |
| `CHANGELOG.md` | What changed in each release | E | Projects read it before moving their pinned VASH version | W1 |
| `pyproject.toml` | Package definition: name vash (free on PyPI, checked 5 Nov 2026), semver version starting 3.0.0, dependencies, the vash command | A | pip install vash installs the engine and CLI | W1 |
| `requirements.lock` | Exact dependency versions with hashes | E | CI and installs use --require-hashes: reproducible and tamper-proof | W1 |
| `ai-manifest.json` | Catalog index: every accepted asset with type, source, licence, version, commit, use (fork / run), accepting ADR, and the allowed-licence list. Kept at the root (v8.2); generated from catalog/ and the catalog ADRs, never hand-edited | E (from catalog ADRs) | Read by the stack-proposal agent and by vash check (Stage 0) | W1 |
| `project-stack.json` | VASH's own freeze: one choice per category (stack design-only + Python engine, llm routes with Claude for its own work under OD-1, forge GitHub, ci GitHub Actions, cloud none), plus agents, skills, thresholds and budget | E (from an ACCEPTED ADR) | Read by vash load and vash check for VASH's own sessions | W1 |
| `CLAUDE.md` | Instructions for Claude Code sessions, generated from method/laws.md and project-stack.json | E | Claude Code reads it at every session start; a check fails if it differs from its sources | W1 |
| `.env.example` | Names of the API keys a user may set (free providers); never any values | A | Users copy it to .env (git-ignored) | W1 |
| `.gitattributes` | Line endings and text handling: every text file LF, UTF-8 | A | Keeps files identical on Windows, macOS and Linux | W1 |
| `.gitignore` | Ignores runtime/, .env, data/ (incl. data/intake/), caches, and the generated parts of .claude/ (agents/, skills/, hooks/) | A | Keeps secrets and scratch out of git. VASH holds no client data and needs no intake folder; data/intake/ exists only in projects (local Ollama only, never the pool) | W1 |

## method/ — the method

What users adopt: how work is done and judged. Changes here only through an ACCEPTED ADR.

| Path | Purpose | By | How it is used | Wave |
|---|---|---|---|---|
| `method/README.md` | Index of the method and how its parts fit together | A | Entry point for readers | W1 |
| `method/laws.md` | The 3 laws and platform rules R1–R14: the single source of truth | A→H | Generated into every CLAUDE.md; cited by every review | W1 |
| `method/ava/protocol.md` | AvA rulebook: Gate 1, Junior / Senior rounds, scoring, no approval below threshold, stalemate, escalation, canary, log format | A→H | Followed by the AvA runner and every reviewer | W1 |
| `method/ava/thresholds.json` | Threshold per artifact type; floor 88 | A→H | The engine reads the numbers; a project can raise them, never lower them | W1 |
| `method/ava/checklists/artifact.md` | Checklist for design activities (no code) | A | Used by the Senior on ARTIFACT activities | W1 |
| `method/ava/checklists/code.md` | Checklist for code activities (Gate 1, tests, SHA pins, licence) | A | Used on CODE activities | W1 |
| `method/ava/checklists/manual_step.md` | Checklist for human-only steps | A | Used on MANUAL activities | W1 |
| `method/ava/checklists/prompt.md` | Checklist for locked prompts | A | The Prompt Engineer checks prompts with it | W1 |
| `method/ava/checklists/ava.md` | Checklist for an AvA round itself | A | Checks a round was run correctly | W1 |
| `method/roles/registry.md` | The 10 roles: identity, Junior / Senior persona, skills, AvA role; each role links to the catalog/agents files that play it | A→H | Defines who does what in every project | W1 |
| `method/groups/groups.md` | The 7 groups: roles, pairings, phases, sequencing | A→H | Plans which roles work together | W1 |
| `method/handshakes/handshakes.md` | The 7 handovers: required fields and validation rules | A→H | What passes between roles and phases | W1 |
| `method/sdlc/phases.md` | SDLC Phases 1–8: entry / exit criteria, artifacts, human gates | A→H | The design path of every project | W1 |
| `method/sdlc/execution-stages.md` | v8.2 execution stages 0–10 (build, review, pipeline, fix loop, release, post-release): deterministic vs AI, gate at each | A→H | The build path of every project | W1 |
| `method/sdlc/freeze-lifecycle.md` | How a stack is decided, frozen, changed and upgraded; catalog-gap handling | A→H | Followed whenever a project's stack is chosen or changed | W1 |
| `method/templates/brief.md` | Project brief form | A | A human fills it to start a project | W1 |
| `method/templates/frd.md` | Functional requirements document form | A | BA agent output format | W1 |
| `method/templates/adr.md` | ADR form (Status PROPOSED / ACCEPTED / SUPERSEDED) | A | Every decision is written in it | W1 |
| `method/templates/decision.md` | Activity decision form (APPROVED / REJECTED / MODIFY) | A | Written after each AvA | W1 |
| `method/templates/activity.md` | Activity entry format (ID, TYPE ARTIFACT / MANUAL / CODE, DEPENDS_ON, THRESHOLD …) | A | Used to write any plan | W1 |
| `method/templates/prompt.md` | Locked prompt form | A | Prompt Engineer output | W1 |
| `method/templates/ava-log.md` | AvA log form (score, Gate 1, routes, canary, objections) | A | Every review round is logged in it | W1 |
| `method/schemas/project-stack.schema.json` | Formal schema of project-stack.json | A→H | vash check validates every freeze against it | W1 |
| `method/schemas/ai-manifest.schema.json` | Formal schema of ai-manifest.json | A→H | Validates the catalog index | W1 |
| `method/schemas/stack-pack.schema.json` | Formal schema of catalog/stacks/<pack>/stack.json | A→H | Validates every stack pack, so any pack works with the same tools | W1 |

## catalog/ — what a project can be given

Every vetted asset, licence-checked once, reusable by every project. A project loads only what it freezes.

| Path | Purpose | By | How it is used | Wave |
|---|---|---|---|---|
| `catalog/README.md` | How the catalog works: five categories (stacks, llm, forge, ci, cloud) plus skills, agents, hooks; adding an option (search, licence check, AvA, catalog ADR, adapter) | A | Read by contributors | W1 |
| `catalog/search-log.md` | Law 3 record: what was searched, found, reused or built, and why | A | Proof of search before build; linked from ai-manifest.json | W1 |
| `catalog/llm/` | LLM routes, one file each: ollama.md (local; only route for client data), openrouter.md, freellmpool.md, free-claude-code.md (AGPL, run only), claude.md (VASH's own work, OD-1); README.md compares limits and data-use terms | A | A project picks its routes per role in project-stack.json (models.*) | W1 |
| `catalog/forge/` | Git hosts (issues, boards, PRs / merge requests): github.md, gitlab.md, forgejo.md (also Gitea), local.md (plain git: issues as files, merge by the owner); quotas and limits of each | A | A project picks one (forge in project-stack.json); the forge adapter talks to it | W1 |
| `catalog/ci/github-actions/` | Pipeline template for GitHub Actions (calls VASH's reusable workflows by release tag) | A | Copied by vash init when ci = github-actions | W1 |
| `catalog/ci/local-hooks/` | Git hooks (pre-commit, pre-push) that run vash check and Gate 1 on the developer's machine: the no-GitHub, no-CI, $0 fallback | A | Copied by vash init when ci = local-hooks; also usable beside any other CI | W1 |
| `catalog/ci/gitlab-ci/, forgejo-actions/` | Pipeline templates for GitLab CI and Forgejo / Gitea Actions | A | Copied by vash init when chosen | W1 |
| `catalog/cloud/` | Clouds and free tiers: oci-always-free.md (A1, Autonomous Database, Object Storage), more later; each names its iac/<cloud>/ folder | A | A project picks one (cloud in project-stack.json) or none | W1 |
| `catalog/platforms.md` | Orchestration, state, storage and human-in-loop options | A | Read when the engine itself chooses a platform | W1 |
| `catalog/stacks/_template/` | Skeleton every pack copies: stack.json, skills/, rules/, linters/, tests/, deploy/, ui-tests/, outputs/, README.md. A pack may leave a part empty but keeps the folder and says why in its README | A | Copied to start a new stack pack; validated by method/schemas/stack-pack.schema.json | W1 |
| `catalog/stacks/design-only/stack.json` | Pack manifest: no platform, no runtime tools; the outputs it produces | A→H | Stage 0 reads it; nothing to install | W1 |
| `catalog/stacks/design-only/skills/` | Skills for writing a blueprint: requirements, architecture, data model, API contract, test strategy, infrastructure plan | A | Loaded by projects that freeze this pack | W1 |
| `catalog/stacks/design-only/rules/` | Design rules: technology-neutral wording, every requirement traced to a design and a test | A | Checked in every Senior review of the pack's outputs | W1 |
| `catalog/stacks/design-only/linters/` | Gate 1 checks for documents: required sections, links resolve, no code, traceability complete | A | Run before every Senior review | W1 |
| `catalog/stacks/design-only/outputs/` | Layout of the blueprint the pack produces: one folder per SDLC phase plus the assembled blueprint | A | vash init copies it into the project as the place outputs go | W1 |
| `catalog/stacks/design-only/README.md` | What the pack gives (a full blueprint, no code), who it is for, its limits | A | Read before choosing the pack; the default for any new user | W1 |
| `catalog/stacks/oracle-apex/outputs/` | Layout of the APEX application, database scripts and test results the pack produces | A | vash init copies it into the project | W1 |
| `catalog/stacks/oracle-apex/stack.json` | Pack manifest: platform versions, tools, checksums | A→H | Stage 0 checks installed versions against it | W1 |
| `catalog/stacks/oracle-apex/skills/` | APEX / PL/SQL / SQLcl skills for this stack | A / X | Loaded only by projects that freeze this pack | W1 |
| `catalog/stacks/oracle-apex/rules/` | Stack rules: platform isolation, PL/SQL security standards | A | Added to the project's rules when frozen | W1 |
| `catalog/stacks/oracle-apex/linters/` | Gate 1 check configuration (AST isolation linter, PMD) | A | Run before every Senior review of code | W1 |
| `catalog/stacks/oracle-apex/tests/` | Test recipe (utPLSQL) and test-suite generator skill | A | Used by the pipeline's test stage | W1 |
| `catalog/stacks/oracle-apex/deploy/` | Deploy recipe (SQLcl / Liquibase, install and upgrade) | A | Used by the pipeline's deploy stage | W1 |
| `catalog/stacks/oracle-apex/ui-tests/` | Browser test recipe (Playwright) | A | Used by pipeline and post-release tests | W1 |
| `catalog/stacks/oracle-apex/README.md` | What the pack gives, its requirements and limits. Generic only: no client names, schemas or data (a Gate 1 check enforces it) | A | Read before choosing the pack | W1 |
| `catalog/skills/<name>/SKILL.md` | Stack-neutral skills: vash-creator, vash-validator, vash-orchestrator, prompt-engineer, code-reviewer, senior-architect, multi-agent-patterns, canary-verifier | A | Loaded only if listed in the session's project-stack.json | W1 |
| `catalog/agents/<name>.md` | Agents: junior-creator, senior-validator, prompt-engineer, plus vetted personas; each names the method role and side (Junior / Senior) it plays | A / X | Loaded only if frozen | W1 |
| `catalog/hooks/` | Claude Code hooks (post-write, pre-delete, session-end) | A | Linked into .claude/ by the loader when frozen | W1 |
| `catalog/external/` | Vetted upstream projects that VASH may fork or link (use: fork), as pinned git submodules: Oracle skills, agent personas, Semgrep rules | X | Listed in ai-manifest.json. Run-only tools (use: run, e.g. free-claude-code, AGPL) are not submodules: installed at their pinned tag | W1 |

## src/vash/ and bin/ — the engine

The code that runs the method. Built in Phase 7 as CODE activities.

| Path | Purpose | By | How it is used | Wave |
|---|---|---|---|---|
| `src/vash/cli` | The vash command: init, check, load, ava, cost, status. A command whose feature comes in a later wave exists as a stub (e.g. cli/cost.py prints that the cost meter arrives in wave 2 and lists the routes set in project-stack.json) and exits without error | A (CODE) | Users and pipelines run it | W1 |
| `src/vash/supervisor/` | Flow Supervisor → Prompt Engineer → Junior / Coder → Gate 1 → Senior / Critic, with the ADR gate, floor 88 and 3-try fix cap | A (CODE) | Runs every activity and fix loop | W2 |
| `src/vash/ava/` | AvA round runner (replaces .github/scripts/ava*.py) | A (CODE) | Runs Junior / Senior rounds and writes the logs | W1 |
| `src/vash/core/` | Vendor-free core: reads project-stack.json and loads the adapter chosen for each category; no vendor or stack name appears here | A (CODE) | Used by every command | W1 |
| `src/vash/core/exceptions.py` | Named errors with a plain message and the fix: FreezeFileMissing, FreezeInvalid, AdapterNotInstalled, ThresholdNotMet, AdrNotAccepted, RouteUnavailable, NotAvailableYet | A (CODE) | Every command fails with one of these instead of a stack trace | W1 |
| `src/vash/core/interfaces.py` | The adapter contract: one abstract base class per category (ForgeAdapter, CIAdapter, CloudAdapter, LLMAdapter, StackPack) with the exact methods every implementation must provide | A (CODE) | Every real adapter and the fake test adapters inherit from it; a test fails when a method is missing | W1 |
| `src/vash/adapters/forge/` | One adapter per git host (github/ first; gitlab/, forgejo/, local/ later): create issues, read the board, open and merge PRs, export status | A (CODE) | Called for every issue, board, PR and merge action | W1 |
| `src/vash/adapters/ci/` | One adapter per CI system: github-actions/ and local-hooks/ first; gitlab-ci/, forgejo-actions/ later. Start runs, read results, register runners (or install hooks) | A (CODE) | Called by the pipeline stages | W1 |
| `src/vash/adapters/cloud/` | One adapter per cloud (oci/ first): runner VM, database, storage, through iac/<cloud>/ | A (CODE) | Called when a project provisions infrastructure | W1 |
| `src/vash/adapters/llm/` | Model routes for Ollama, OpenRouter, freellmpool, free-claude-code and Claude. Intake never goes through the pool (direct local Ollama). If the pool fails to start, other roles use the one configured fallback route (local Ollama) and the run is logged as degraded. freellmpool pinned with hash; LiteLLM is the replacement candidate | A (CODE) | Sends each role to its route from project-stack.json | W1 |
| `src/vash/mcp/` | Write guard limited to the freeze's allowed_write paths: in wave 1 a plain Python function that refuses any other path; in wave 2 the full MCP server around the same guard | A (CODE) | Build agents write files only through it (R6), from wave 1 | W1 |
| `src/vash/loader/` | Clean-slate loader: rebuilds .claude/ from the freeze, generates CLAUDE.md, exports project status | A (CODE) | Runs at the start of every session and pipeline | W1 |
| `src/vash/tools/` | Deterministic tools: stack check (Stage 0), Gate 1, cost meter, canary injector, licence verifier, issue creation, status export, PR opener. No stack name in code: each reads stack.pack from project-stack.json and loads catalog/stacks/<pack>/stack.json | A (CODE) | Called by the CLI and workflows | W1 |
| `bin/vash-init (+ .ps1)` | Entry point: create a project repository from scaffold/project/, with the chosen forge, CI and cloud | A (CODE) | Calls src/vash/cli init; holds no logic | W1 |
| `bin/vash-check (+ .ps1)` | Entry point: Stage 0 freeze and version check | A (CODE) | Calls src/vash/cli check; run first in every session and pipeline | W1 |
| `bin/vash-load (+ .ps1)` | Entry point: clean-slate load of .claude/ and CLAUDE.md from the freeze | A (CODE) | Calls src/vash/cli load; started by the SessionStart hook | W1 |
| `bin/vash-ava (+ .ps1)` | Entry point: run one AvA activity | A (CODE) | Calls src/vash/cli ava; used by ava.yml and by hand | W1 |

## scaffold/project/ — what vash init writes

The skeleton every new project repository starts from (renamed from templates/project/, decision D2).

| Path | Purpose | How it is used | Wave |
|---|---|---|---|
| `project-stack.json` | The freeze, filled from the project's ACCEPTED stack ADR | The project's single source of truth | W1 |
| `README.md` | Project front page stub | The project team fills it | W1 |
| `decisions/ADR-001-stack.md` | First ADR: the chosen (or adopted) stack, Status PROPOSED | The human accepts it; then the freeze is written | W1 |
| `audit/ (prompts, ava_logs, validation, metrics)` | Committed audit trail of the project | Every round of the project is saved here | W1 |
| `ci/ (from catalog/ci/<choice>/)` | The pipeline for the chosen CI system, e.g. .github/workflows/vash.yml calling VASH's reusable workflows by release tag, or .gitlab-ci.yml, or local git hooks | The project's whole pipeline | W1 |
| `.gitignore, .env.example` | Ignore rules (data/intake/, runtime/), key names | Keep secrets and client input out of git | W1 |

## .github/ — VASH's own CI and the GitHub Actions adapter

VASH's own checks (VASH itself is hosted on GitHub), plus the reusable workflows that implement the github-actions CI choice for projects. GitHub only runs workflows from this folder, so they live here; other CI systems keep their templates in catalog/ci/.

| Path | Purpose | How it is used | Wave |
|---|---|---|---|
| `workflows/ci.yml` | VASH's own checks: tests, lint, Gate 1, schema validation, licence check | Every push and PR to VASH | W1 |
| `workflows/security.yml` | Secret scan, CodeQL, dependency review | Every push and PR; free on a public repo | W2 |
| `workflows/release.yml` | On a release tag: changelog, GitHub Release, package publish | Produces the versions projects pin | W3 |
| `workflows/ava.yml` | VASH's own AvA loop | Runs VASH's own reviews | W1 |
| `workflows/project-sync.yml` | Syncs VASH's plan to its GitHub Project board (configurable, nothing hard-coded) | VASH's own board | W1 |
| `workflows/reusable-light.yml` | Light project jobs (lint, checks, status), hosted | Called by projects | W1 |
| `workflows/reusable-heavy.yml` | Heavy project jobs (deploy, tests, UI), self-hosted, one at a time | Called by private projects | W1 |
| `workflows/reusable-merge-gate.yml` | Merge only with ACCEPTED ADR + approval label + audit of direct pushes | Called by private projects | W1 |
| `workflows/reusable-post-release.yml` | Scheduled live UI tests, results as issues | Called by projects | W3 |
| `ISSUE_TEMPLATE/` | Bug, feature and catalog-submission forms | Outsiders open structured issues | W1 |
| `pull_request_template.md` | PR checklist (AvA score, laws, linked issue) | Every PR | W1 |
| `CODEOWNERS` | Who must review which folders (method/, catalog/ → owner) | GitHub requests the right reviewer | W1 |
| `dependabot.yml` | Weekly updates for actions and dependencies | Keeps pins current | W2 |
| `scripts/` | Today's AvA scripts | Kept only until src/vash/ava/ replaces them | W1 |

## iac/, examples/, tests/, docs/

Infrastructure code per cloud (iac/<cloud>/), a working example, the test suite, and the user documentation.

| Path | Purpose | How it is used | Wave |
|---|---|---|---|
| `iac/oci/modules/compute/` | OCI Ampere A1 VM (runner + Ollama) | Optional free self-hosted engine | W1 |
| `iac/oci/modules/database/` | Always Free Autonomous Database | For Oracle-stack projects | W1 |
| `iac/oci/modules/networking/` | VCN, subnets, security lists | Shared by the modules above | W1 |
| `iac/oci/environments/always-free/` | main.tf, variables.tf, outputs.tf, README | One command creates the free environment | W1 |
| `examples/hello-blueprint/` | Tiny project made by vash init on the design-only pack, with its brief and outputs | New users run it to see VASH end to end | W3 |
| `tests/engine/` | Tests for every engine module | Run by ci.yml | W1 |
| `tests/fixtures/` | Per Gate 1 rule: one sample that must fail, one that must pass (R8). Only obviously fake values; allow-listed in the scanner configs | Proves the checks still work | W1 |
| `tests/catalog/` | ai-manifest.json valid; every licence allowed; every tool run against at least two options of each category (two packs, and a real plus a fake adapter for forge, ci, cloud and llm) to prove no vendor is hard-coded | Run by ci.yml | W1 |
| `tests/examples/` | Runs the example project end to end | Proves a release works for a new user | W3 |
| `docs/README.md` | Index of the documentation, by reader: new user, project team, contributor | Entry point of docs/ | W2 |
| `docs/getting-started.md` | Install, vash init, first project | First doc for a new user | W2 |
| `docs/concepts.md` | Method, engine, catalog; layers; freeze; AvA | Explains how VASH thinks | W2 |
| `docs/using-vash.md` | Daily use: activities, decisions, upgrading the VASH pin | Day-to-day guide | W2 |
| `docs/catalog-guide.md` | Choosing and adding stack packs, skills, agents | For users and contributors | W2 |
| `docs/reference/` | cli.md, project-stack.md, ai-manifest.md field references; versioning.md (semver from 3.0.0, upgrades, deprecations) | Looked up while working | W2 |
| `docs/design/` | Approved design documents: vision, objectives, scope, stakeholders, 2-6 application framework | Why VASH is built this way | W1 |
| `docs/faq.md` | Cost, privacy, licences, Claude vs free models | Self-service help | W3 |

## VASH building itself

VASH is its own first project, laid out exactly like any project made with vash init. Its review trail stays in this repository under audit/ (decision D1).

| Path | Purpose | By | How it is used | Wave |
|---|---|---|---|---|
| `plan/README.md` | How VASH plans its own work: issues on GitHub, activities in activity_list.md, decisions in decisions/ | A | Entry point for VASH's own planning | W1 |
| `plan/activity_list.md` | VASH's own roadmap (activities 0.1 … 7.11) | A→H | The orchestrator picks the next activity from it | W1 |
| `plan/operations/` | VASH's own operating notes (today's p1, p2, routine instructions) | A | How VASH's own sessions and routines run | W1 |
| `plan/triggers/` | Files that start an AvA run (control, not history) | E | Read by ava.yml | W1 |
| `decisions/ADR-*.md` | VASH's architecture decisions (ADR-001 …) | A→H | Accepted by the owner; superseded, never edited after ACCEPTED | W1 |
| `decisions/N-N_decision.md` | Decision per activity (APPROVED / REJECTED / MODIFY) | H | Unlocks the next activity | W1 |
| `decisions/README.md` | ADR format and rules | A | Reference | W1 |
| `audit/README.md` | What each audit folder holds and how to read a review trail | A | Entry point for anyone checking how VASH was built | W1 |
| `audit/prompts/` | Every locked prompt | A | Saved before any work starts | W1 |
| `audit/artifacts/` | Every artifact as reviewed | A | What the Senior scored | W1 |
| `audit/ava_logs/` | Every round's log | A | Full public review history | W1 |
| `audit/validation/` | Summary per activity | A | What the human reads before deciding | W1 |
| `audit/metrics/` | Monthly cost-meter summaries | E | Tracks minutes, storage, tokens | W1 |
| `.claude/settings.json` | Tracked: SessionStart hook that runs bin/vash-load, plus permissions | A→H | Lets a cloud session load itself before any work | W1 |
| `.claude/agents, skills, hooks` | Generated: only the frozen ones, linked from catalog/ | E (loader) | Git-ignored; rebuilt by vash load every session | W1 |
| `runtime/` | Git-ignored scratch: drafts, checkpoints, raw logs. Never committed | E | Temporary; never relied on | W1 |

## Conventions

- **Naming.** Folders and docs: lowercase-kebab (getting-started.md, stack-pack.schema.json). Python modules: snake_case. Activities: N.N in the plan, N-N in file names (5-1_artifact.md). ADRs: ADR-NNN-kebab-title.md, numbered per repository; a reference to another repository carries its name (owner/repo:ADR-001). Activity decisions: N-N_decision.md. AvA logs: N-N_round<n>.md. Stack packs, adapters and catalog entries: lowercase-kebab ids equal to their folder name (oracle-apex, github-actions, oci-always-free).
- **File formats.** Markdown for method, docs, plans, decisions and audit records. JSON for project-stack.json, ai-manifest.json, stack.json and thresholds; JSON Schema (draft 2020-12) for method/schemas/. YAML for CI workflows. TOML for pyproject.toml. Python 3.11+ for the engine. POSIX shell and PowerShell for the thin bin/ wrappers. HCL for iac/. Every text file UTF-8 with LF line endings (enforced by .gitattributes and Gate 1).
- **Branch strategy.** main is always releasable and changes only through pull requests (on the public VASH repository a GitHub ruleset requires review and green checks). Work branches: activity/N-N-short-name for activities, fix/<issue>-short-name for bugs, docs/<short-name> for documentation; one squashed commit per push. Releases: semver tags vX.Y.Z on main with release notes; projects pin a tag. Pipeline-only fixes follow the same PR route (no direct pushes to main).
- **Project repository (scaffold).** vash init writes: project-stack.json, README.md, decisions/ADR-001-stack.md (PROPOSED), audit/ (prompts, ava_logs, validation, metrics), the pipeline from catalog/ci/<choice>/, the stack pack's outputs/ layout, .gitignore (runtime/, .env, data/ incl. data/intake/) and .env.example. Nothing else; the project adds its own application folders as its stack pack describes.
- **Loader / provisioner search (LAW 3).** Searched for tools that create a repository from a template and keep it updated: GitHub template repositories (vendor feature, tied to GitHub), Cookiecutter (open source, BSD-3-Clause, one-time generation), Copier (open source, MIT, generation plus later updates from the template), git submodules (pinning VASH itself). Decision proposed: vash init uses Copier for generating and updating scaffold/project/ (host-independent, keeps projects upgradable), submodules or the package version pin VASH, and the loader is a thin script over these. Licences to re-check with the licence verifier before adoption.

## How it is used

- **Building any project with VASH.** You install VASH and run vash init in your own (private) repository; you pick a stack and your LLM, git host, CI and cloud from the catalog, and VASH writes your project's freeze and folders. You give a brief, agents draft every step and a second agent reviews it, and you only approve the decisions and the merge; nothing of yours ever goes back into VASH.
- **VASH's own issues and enhancements.** Anyone reports a bug or idea as a GitHub issue on the VASH repository (using the issue forms). The owner accepts it into plan/activity_list.md, agents do it as an activity with a review, the owner approves it in decisions/, and it ships in the next VASH release that projects can choose to upgrade to.

## Design rules

- **Technology independence and $0 come first.** They outrank every other rule. Every technology layer (stack, LLM, git host, CI/CD, cloud) is a catalog choice made per project in project-stack.json; only free and open-source options are accepted (VASH's own Claude use is the one owner exception, OD-1).
- **Vendor-free core.** No vendor or stack name appears in src/vash/core/ or the tools. They read the project's choice for each category and load catalog/<category>/<choice> and src/vash/adapters/<category>/<choice>; a new technology is a catalog entry plus an adapter, never a core change. Proved by tests/catalog/ with two options per category.
- **Project state on its own git host.** Each project's issues, board and PRs live on the git host it chose, reached only through the forge adapter (R9 amended from 'GitHub only'); VASH's own state lives on VASH's repository.
- **Runtime is never committed.** runtime/ is git-ignored scratch. VASH's own committed review trail is audit/; another project's logs live only in that project's repository.
- **bin/ holds no logic.** Each bin/ entry point, shell and .ps1 alike, is a thin wrapper that only runs python -m vash.cli <command> with its arguments; all logic lives in the Python package, so nothing is maintained in two languages.
- **One LLM interface.** src/vash/adapters/llm/ exposes one internal interface (generate a reply for a prompt on a named route, from the route settings in project-stack.json) that knows nothing of freellmpool's, LiteLLM's or any tool's CLI or API. Each tool sits behind it as an implementation, so swapping freellmpool for LiteLLM changes no line in supervisor/ or tools/.
- **Generic packs only.** Stack packs are built from public vendor and open-source tooling only, never from any project's code. No project or client names, schemas, tables or data ever appear in catalog/; a Gate 1 check fails on them.
- **Fork vs run.** Assets VASH may fork or link are submodules in catalog/external/. Run-only tools (AGPL free-claude-code) are recorded in ai-manifest.json with use: run and installed at a pinned tag, never added as submodules.
- **Generated files.** ai-manifest.json, CLAUDE.md, CHANGELOG.md and the generated parts of .claude/ are written by the engine only; a check fails if they differ from their sources.
- **Role to agent mapping.** Every catalog/agents file names the method role and side (Junior / Senior) it plays; method/roles/registry.md links back.
- **Fixtures stay fake.** tests/fixtures/ uses obviously fake values and is allow-listed in the scanner configs, so the public repository's secret scanning stays clean.
- **Versioning.** One scheme: package version = release tag = method version, semver from 3.0.0 (docs/reference/versioning.md).
- **LLM route safety.** Intake always calls local Ollama directly, never the pool. If the pool fails to start, the other roles use one configured fallback route (local Ollama) and the run is logged as degraded; R12 is amended to allow this single fixed fallback, still no custom routing logic. freellmpool is pinned with its hash; LiteLLM is the replacement candidate.

## Bootstrap

- **Stage A — today's scripts, fixed.** First fix .github/scripts: no stalemate auto-approve, two model routes, audit/ paths. Then they run the AvA loop for wave 1.
- **Stage B — build the vash command.** The fixed scripts run the CODE activities that build src/vash/cli, loader/, tools/ (stack check, Gate 1) and ava/.
- **Stage C — self-hosting test.** vash ava re-runs one review of its own code and passes; then ava.yml switches to bin/vash-ava and the old scripts are retired.

## Build waves

- **Wave 1 — the core plus the pilot's technology.** Root essentials, method/, catalog/stacks/_template/, design-only/ and oracle-apex/ (from public Oracle tooling), catalog/llm, forge, ci, cloud entries for the pilot choices, catalog/skills, agents, hooks, src/vash/core (incl. interfaces.py, exceptions.py) + cli (with stubs for later commands) + loader + ava + tools (stack check, Gate 1) + mcp write guard, adapters: forge/github, ci/github-actions and ci/local-hooks (the no-CI fallback), cloud/oci, llm (Ollama + configured routes), iac/oci/, bin/, scaffold/project/, .github ci.yml, ava.yml, project-sync.yml, reusable light / heavy / merge-gate workflows, tests/engine, fixtures, catalog, docs/design/, plan/, decisions/, audit/. Pilots: the owner's private Oracle APEX projects (Oracle APEX + Autonomous Database + OCI Always Free + GitHub), each adopting VASH through its own ADR in its own repository.
- **Wave 2 — more of the engine.** src/vash/supervisor/, the full MCP server around the wave 1 write guard, freellmpool and free-claude-code routes in production use, cost meter, canary injector, licence verifier, security.yml, dependabot, docs/ (user guides).
- **Wave 3 — more technology options.** Adapters and catalog entries for gitlab, forgejo / gitea, local git, gitlab-ci, forgejo-actions and further clouds; examples/, tests/examples, release.yml with package publishing, reusable-post-release.yml, docs/faq.

## Feedback review

| Set | Point | Verdict | Result |
|---|---|---|---|
| `Set 1` | 1.1 bin/ vs src/vash/ | Partly valid | bin/ was listed with one bootstrap script; now each entry point is defined and holds no logic |
| `Set 1` | 1.2 catalog path scalability | Valid | Vendor-free core rule (all categories) and a two-option test per category |
| `Set 1` | 1.3 no runtime/ in the repo | Not valid on facts | runtime/ exists as git-ignored scratch; VASH's own trail is audit/ (kept, D1). The principle holds and is now a rule |
| `Set 2` | 2.1 bootstrap paradox | Valid, with a condition | Bootstrap stages A–C; the old scripts' faults are fixed first |
| `Set 2` | 2.2 maintenance overhead | Valid, adjusted | Whole structure frozen; build waves 1–3; wave 1 is the minimum for anyone's first project, with the design-only pack (D4) |
| `Set 2` | 2.3 freellmpool fallback | Partly valid | Intake never uses the pool; one configured (not hard-coded) fallback with R12 amended; pinned with hash |
| `Set 3 (Claude)` | 3.1 .claude/ in cloud sessions | High | settings.json tracked with a SessionStart hook |
| `Set 3 (Claude)` | 3.2 two templates folders | Medium | templates/project/ renamed scaffold/project/ (D2) |
| `Set 3 (Claude)` | 3.3 schemas filed as templates | Medium | method/schemas/ with three schemas |
| `Set 3 (Claude)` | 3.4 roles vs agents | Medium | Mapping rule |
| `Set 3 (Claude)` | 3.5 version scheme | Medium | Semver from 3.0.0; versioning.md |
| `Set 3 (Claude)` | 3.6 package name | Medium | vash is free on PyPI (checked 5 Nov 2026); kept |
| `Set 3 (Claude)` | 3.7 triggers filed as audit | Low | Moved to plan/triggers/ |
| `Set 3 (Claude)` | 3.8 ai-manifest.json location | Low | Kept at the root, generated only |
| `Set 3 (Claude)` | 3.9 fixtures and scanners | Low | Fake values, allow-listed |
| `Set 3 (Claude)` | 3.10 client detail in packs | High | Generic packs rule with a Gate 1 check |
| `Set 3 (Claude)` | 3.11 AGPL tool as a submodule | Low | Fork vs run rule |
| `Set 3 (Claude)` | 3.12 no governance file | Low | GOVERNANCE.md added |
| `Set 3 (Claude)` | 3.13 generated CLAUDE.md drift | Low | Kept: a check fails on drift |
| `Set 3 (Claude)` | 3.14 script paths after the move | Medium | Part of bootstrap stage A |

## Decisions

| ID | Decision | Status |
|---|---|---|
| `D1` | Keep VASH's own review trail in this repository (audit/) | Owner: keep |
| `D2` | Rename templates/project/ to scaffold/project/ | Owner: accepted |
| `D4` | Stack pack in wave 1 | Owner: option A - design-only in wave 1 (works for anyone, no technology needed). Updated by D6: oracle-apex is also in wave 1 for the pilots. VASH names no project |
| `D5` | Technology independence everywhere | Owner: technology independence and $0 outrank every rule; every layer (stack, LLM, git host, CI/CD, cloud) is a catalog category with adapters, chosen per project |
| `D6` | Pilots | Owner: testing starts on the owner's private Oracle APEX projects, so the oracle-apex pack and the GitHub, GitHub Actions, OCI and LLM adapters are in wave 1. The pilots adopt VASH through their own ADRs, in their own repositories |
| `D7` | Minor completions (note feedback) | Applied: core/exceptions.py with named errors; data/ (incl. data/intake/) ignored in VASH, the folder exists only in projects; catalog/ci/local-hooks and its adapter moved to wave 1 |
| `D8` | Freeze | Owner, 6 Nov 2026: the structure is frozen with no changes. Wave 1 implementation notes recorded as rules: one LLM interface independent of any tool; bin/ wrappers only call python -m vash.cli |
| `D9` | Wave 1 implementation gaps | Owner, 6 Nov 2026: src/vash/mcp/ write guard moved to wave 1 (R6 holds for the pilots); src/vash/core/interfaces.py adapter contract added in wave 1; cli stubs for later-wave commands (cost) with NotAvailableYet, reporting the routes actually configured |
| `D3` | Package name | Checked: vash is free on PyPI (also vash-framework, vash3, vash-ai); vash kept. A name is only held once a first release is published |

## Where today's files go

| Today | New place |
|---|---|
| `knowledge/laws.md` | method/laws.md |
| `knowledge/checklists/*` | method/ava/checklists/* |
| `knowledge/tech_providers/ai_models.md` | catalog/llm/ (split into one file per route) |
| `knowledge/tech_providers/cloud_free_tier.md` | catalog/cloud/ and catalog/forge/ (GitHub quotas) |
| `knowledge/tech_providers/platforms.md` | catalog/platforms.md |
| `knowledge/activity_list.md` | plan/activity_list.md |
| `knowledge/p1, p2, routine_instructions.md` | plan/operations/ |
| `vash_framework/agents/2-1 … 2-5` | method/roles, ava, groups, handshakes, sdlc |
| `vash_framework/vision/*, architecture/2-6…` | docs/design/ |
| `vash_framework/blueprint, platform, skills (READMEs only)` | removed (replaced by docs/ and catalog/) |
| `.claude/skills/*, agents/*, hooks/*` | catalog/skills, catalog/agents, catalog/hooks (.claude/settings.json stays, tracked) |
| `.claude/skills/search_log.md` | catalog/search-log.md |
| `runtime/prompts, artifacts, ava_logs, validation` | audit/… |
| `runtime/triggers` | plan/triggers/ |
| `runtime/drafts` | runtime/ (git-ignored) |
| `decisions/*` | stays |
| `.github/scripts/*` | stays until src/vash/ replaces it |
| `knowledge/CLAUDE.md, .github/CLAUDE.md, .claude/CLAUDE.md` | one generated root CLAUDE.md |

## Frozen

1. **Technology choices.** five catalog categories (stacks, llm, forge, ci, cloud) with one adapter each in src/vash/adapters/, and the vendor-free core
2. **Structure.** the four product areas, scaffold/project/, method/schemas/, plan/triggers/, tracked .claude/settings.json, GOVERNANCE.md
3. **Rules.** the twelve design rules, starting with technology independence and $0, and including LLM route safety (R12 amendment) and project state on its own git host (R9 amendment)
4. **Bootstrap and waves.** stages A–C and waves 1–3
5. **Names.** package and command vash, semver from 3.0.0, repository vash-framework (renamed from vash3-framework by owner decision, 8 Nov 2026)
