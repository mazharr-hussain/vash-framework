# ADR-001: Make VASH the application framework for every project (Blueprint v8.2 merge)

- **ID:** ADR-001
- **Title:** Make VASH the application framework for every project
- **Status:** ACCEPTED
- **Date:** 2026-11-05
- **Activity:** 2.6 (vash_framework/architecture/2-6_application_framework.md)
- **Decided by:** Human owner (changes Status to ACCEPTED or rejects)

## Context
The owner's Master Architecture Blueprint v8.2 (November 2026) defines an 11-stage, deterministic-first
AI software house with a Freeze file per project, pooled free-tier LLMs, local intake and a $0 mandate.
VASH (activities 0.1-2.5) defines the method: three laws, AvA, 10 roles, 7 groups, 7 handshakes and
8 SDLC phases. A validation on 5 Nov 2026 found eleven conflicts or gaps between the two (C1-C11 in the
activity 2.6 artifact). The owner stated that VASH is the framework used for any application, that VASH
with the human decides each project's stack, and that VASH is public while client projects are private.

## Decision
| # | Decision |
|---|---|
| D1 | VASH is the application framework: method + engine + catalog, used unchanged by every project. Public, MIT licence. |
| D2 | Three layers: core (VASH), stack packs (VASH `stacks/`), project (one private repository per application). The core contains no stack; projects contain no copies of VASH components. |
| D3 | VASH's agents propose each project's stack, skills, agents and tools from the catalog; the human ACCEPTS the ADR; the engine writes `project-stack.json` into the project and provisions it. The Freeze file changes only through a superseding ACCEPTED ADR. |
| D4 | A missing asset is searched, licence-checked, AvA-reviewed and accepted into the VASH catalog before any project can freeze it. |
| D5 | Human approval of the final merge: GitHub rulesets in VASH (public); pipeline-enforced approval label + ACCEPTED ADR in private projects (GitHub Free cannot enforce protection there). Residual risk (direct push, label, allow-list or workflow changed by a writer) accepted with mitigations: owner-only write access, engine changes only by PR, allow-list and workflows under the Freeze-change rule, scheduled audit job raising an issue for any commit not merged by the gated job. |
| D6 | One CI system: GitHub Actions. VASH runs on hosted runners only. Private projects: light jobs hosted (target ≤ 3 billed minutes per push), heavy jobs on one OCI A1 host, one heavy job at a time across all projects (host-wide lock; runner registration per repository on a personal account, or one organization runner — to be verified in 3.4). Mirrors and OCI DevOps only by later ADR. |
| D7 | LLMs: pooled free tiers from many vendors through a vetted pooling tool (v8.2 names freellmpool: on PyPI, MIT; full check in activity 3.3); OpenRouter as one pool provider; Critic on a different vendor from the Coder; client data and intake on local Ollama only; local fallback. Coding-agent harness sessions through free-claude-code (AGPL-3.0-only, run unmodified as a separate local service, never forked or linked; proxy authentication and loopback-only required; open-source harness by default), subject to OD-7. freellmpool excludes local models from automatic routing, so the local fallback is a separate engine route. |
| D8 | AvA hardening: deterministic Gate 1 before every Senior review; no approval below threshold (stalemate auto-approve removed); floor 88; canary checks of the Critic. |
| D9 | Scope: design-only until the blueprint (6.1) is approved; engine code in scope from activity-list Phase 7 (provisional activities 7.1-7.11, new activity type CODE with its own checklist). |
| D10 | Owner exception (OD-1 answered 5 Nov 2026): VASH's own development uses Claude as its main AI tooling until the owner changes it by a new ADR (no end date); free routes for VASH's own work stay optional (OD-7); residual risk accepted: the engine every project runs is built and reviewed on one vendor, reduced by Gate 1, canaries (from 7.9) and an optional free-provider Senior; recorded in each AvA log as a same-vendor limitation; no project depends on a paid service. |
| D11 | Same folder names in VASH and projects: `audit/` holds the committed audit trail (prompts, AvA logs, validations, metric summaries); `runtime/` is always git-ignored (checkpoints, raw logs, scratch). VASH moves today's runtime/ audit folders to audit/ in 7.2. |
| D12 | KYC is the first project: adopted through its own ADR "Adopt existing stack" (activity 7.11), in the KYC repository (referenced as kyc:ADR-001; ADR ids are per repository). |

## Consequences
- Amended (marked "Amended by 2.6", PROPOSED until this ADR is ACCEPTED; the earlier text applies until
  then): knowledge/laws.md, CLAUDE.md, vision 1-1, 1-2, 1-3, agents 2-1, 2-2, 2-5,
  knowledge/tech_providers/*, knowledge/activity_list.md, knowledge/checklists/code.md (new),
  .claude/skills/vash-orchestrator and multi-agent-patterns (stalemate rule).
- Phase 3 activities depend on 2.6 and take the artifact as input; Phase 7 (engine build) is added
  provisionally, confirmed by 6.2.
- Implementation debt carried to activity-list Phase 7: the AvA script uses one model for Junior and
  Senior (two routes in 7.7) and still auto-approves at ≥ 80 (removed in 7.8) (interim: the orchestrator skills never auto-approve); actions pinned by tag; no LICENSE file; full-history secret scan before the
  repository goes public.
- Unverified facts (pooling tool, licences, free-tier limits, A1 reclaim policy, self-hosted runner
  charges) are assigned to activities 3.3, 3.4 and 4.x and must not be treated as confirmed.
- OD-1 was answered by the owner on 5 Nov 2026 (D10). Open decisions OD-2 to OD-7 (artifact Section 13)
  are answered by the owner when accepting this ADR.
