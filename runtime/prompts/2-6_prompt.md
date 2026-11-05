# Prompt: Activity 2.6 — Re-baseline VASH as an application framework (Blueprint v8.2 merge)
## Type: ARTIFACT | Phase: Phase 2 | Sequential | Threshold: 90
## Depends on: 2.5 (APPROVED 93/100) and decisions 1.1–2.5 (APPROVED)

---

## ROLE
You are the Junior Creator (Solution Architect persona) for VASH 3.0.
A Senior Validator with no knowledge of how you worked will score your output 0-100.
Threshold to pass: 90.

## CONTEXT
The human owner (Mazhar Hussain) supplied "Master Architecture Blueprint: Predictive Software House,
Version 8.2 (Vendor-Agnostic & Production-Validated), November 2026" and discussed it with VASH in a
working session on 5 Nov 2026. The session reached these owner positions:

1. VASH is the framework / tool used for ANY application. It is the platform core of v8.2.
   KYC, COMMON and future applications are projects that use VASH.
2. VASH (with the human) decides the stack of each project: which stack, skills, agents and tools.
   The decision is recorded and made available in the project repository. The project repository
   never chooses on its own.
3. The VASH repository will be PUBLIC. KYC and all client project repositories will be PRIVATE,
   on GitHub Free.
4. The merged design must keep the VASH method (AvA, roles, groups, handshakes, SDLC phases, audit
   trail) and take the v8.2 execution layer (deterministic first, Critic on a different model,
   hard score floor, local intake, Freeze file, loader, pooled free-tier LLMs, MCP-only writes,
   Stages 0-10, cost meter, canary, licence verifier).

Validation findings from the session that this activity must resolve:
- C1 laws.md and 1-2_objectives.md allow a paid Claude subscription ("no cost cap") — v8.2 says $0.
- C2 2-1_agent_registry.md says "Claude only"; ai_models.md routes through LiteLLM — v8.2 says
  multi-vendor pooling through freellmpool.
- C3 Junior and Senior both run on Claude (same vendor; ava.py calls one model for both) — v8.2
  requires the Critic on a different LLM.
- C4 2-2_ava_protocol.md auto-approves at >= 80 on stalemate — v8.2 rejects anything below the floor.
- C5 No data-privacy rule; intake goes to a cloud model — v8.2: intake on local Ollama only.
- C6 No deterministic gate before the Senior review.
- C7 cloud_free_tier.md omits OCI Ampere A1 and recommends Supabase / Upstash for the MVP.
- C8 No catalog, Freeze file, loader, or stack-pack concept.
- C9 Final-merge approval is not named in Law 2.
- C10 1-3_scope.md and root CLAUDE.md forbid code until "VASH 4.0" — an application framework
  needs engine code.
- C11 GitHub Free private repos: 2,000 hosted minutes / month, no enforced branch protection or
  environment reviewers, no free CodeQL / push protection. Public repos: unlimited minutes and
  these features free.

## TASK
Produce the re-baseline of VASH as an application framework. Full content, no summaries, no code.

### Output 1 — Master artifact
Path: runtime/artifacts/2-6_artifact.md and the canonical copy
vash_framework/architecture/2-6_application_framework.md (identical content).
Sections required:
1. Purpose and inputs (v8.2, session positions, findings C1-C11)
2. What VASH is: engine + method + catalog; three layers (core / stack packs / project)
3. Comparison: where v8.2 is stronger, where VASH is stronger, what the merge takes from each
4. Stack decision and freeze lifecycle (VASH proposes, human ACCEPTS, VASH writes and provisions;
   catalog gap handling; change by superseding ADR; adoption of an existing project such as KYC)
5. v8.2 Stages 0-10 mapped onto the VASH SDLC phases and agents (who, deterministic or AI, gate)
6. The project-stack.json contract (field table, no code), and the ai-manifest.json catalog contract
7. Target repository structures: VASH core (public) and project repository (private)
8. Repository visibility and GitHub quota model (public VASH / private projects), runner split,
   cost-meter thresholds, gates enforced by GitHub vs by the pipeline
9. LLM strategy (pooled free tiers, Critic on a different vendor, local intake, fallback,
   verification of freellmpool under LAW 3 before adoption)
10. Hardware and free-tier constraints (OCI A1, ATP, GitHub)
11. Resolution of every finding C1-C11 (finding -> change -> file)
12. Changes to the activity list (new activity 2.6, Phase 3 depends on 2.6, provisional Phase 7)
13. Open decisions for the human owner
14. LAW compliance and LAW 3 search record

### Output 2 — ADR
decisions/ADR-001-vash-application-framework.md, Status PROPOSED, using the format in
decisions/README.md (ID, Title, Status, Context, Decision, Consequences).

### Output 3 — Amendments to approved artifacts (traceable, marked "Amended by 2.6")
knowledge/laws.md, CLAUDE.md (root), vash_framework/vision/1-1_vision.md (amendment section),
vash_framework/vision/1-2_objectives.md (cost line), vash_framework/vision/1-3_scope.md,
vash_framework/agents/2-1_agent_registry.md (model assignment),
vash_framework/agents/2-2_ava_protocol.md (Gate 1, Critic model, stalemate, canary),
vash_framework/agents/2-5_sdlc_phases.md (freeze and provision output, change rule, Phase 7 note),
knowledge/tech_providers/ai_models.md, cloud_free_tier.md, platforms.md,
knowledge/activity_list.md.

### Output 4 — Decision file
decisions/2-6_decision.md with DECISION: PENDING (human approves; the agent never sets APPROVED).

## RULES
- LAW 1, LAW 2, LAW 3 apply (knowledge/laws.md, as amended by this activity).
- Design only. No software code. Directory trees and field tables are allowed.
- Do not change any approved artifact silently: every change is marked "Amended by 2.6".
- Facts not verified in this session (tool existence, licences, free-tier limits that change)
  are marked "to verify in activity N" — never stated as confirmed.
- Nothing project-specific (KYC tables, client data) in VASH, except naming KYC as the first
  project to onboard.

## CHECKLIST
knowledge/checklists/artifact.md, plus: every finding C1-C11 resolved with a file reference;
every v8.2 stage 0-10 mapped; owner positions 1-4 reflected; open decisions listed.
