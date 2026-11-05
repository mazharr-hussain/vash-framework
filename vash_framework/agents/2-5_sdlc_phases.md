# VASH 3.0 — SDLC Phases Complete Sequence
Amendments marked "Amended by 2.6" are PROPOSED: they take effect when ADR-001 is ACCEPTED; until then the earlier text (git history) applies.

## Overview

VASH 3.0 follows a structured Software Development Lifecycle with 8 phases. Each phase has defined entry criteria, exit criteria, responsible groups, artifacts produced, and parallel execution opportunities.

---

## Phase 1: Brief Intake

**Purpose:** Transform the human owner's brief into a validated, structured input ready for decomposition.

**Privacy (Amended by 2.6, rule R2):** The brief and any client data are processed by the local model
only; raw input is kept in the project's git-ignored intake folder.

**Entry Criteria:** Human submits project brief via GitHub Issue or P1 chat

**Exit Criteria:** Brief validated against handshake 1 schema. All required fields present. PM confirms understanding.

**Responsible Group:** Group 1 (Discovery) — PM leads

**Activities:**
- Read and parse project brief
- Validate required fields present
- Identify ambiguities and return to human if needed
- Create activity list for this project
- Identify which groups are needed

**Artifacts Produced:**
- Validated brief saved to project/briefs/[project_id]_brief.md
- Preliminary activity list for the project

**Parallel Safe:** NO — must complete before anything else

**Human Gate:** YES — human confirms brief is correctly understood

---

## Phase 2: Requirements Discovery

**Purpose:** Translate the validated brief into complete, verifiable functional requirements.

**Entry Criteria:** Validated brief approved by human

**Exit Criteria:** All FRDs approved by human. Every requirement has acceptance criteria. Scope boundaries confirmed.

**Responsible Group:** Group 1 (Discovery) — BA leads, UI/UX supports

**Activities:**
- Stakeholder analysis
- Functional requirements decomposition
- User story mapping
- Acceptance criteria definition
- Scope boundary confirmation
- UX requirements definition (parallel with functional)

**Artifacts Produced:**
- FRDs (one per domain area)
- User story map
- Acceptance criteria document
- UX requirements specification
- Scope confirmation document

**Parallel Safe:** BA and UI/UX work in parallel once brief decomposed

**Human Gate:** YES — human approves all FRDs before architecture begins

---

## Phase 3: Architecture Design

**Purpose:** Define the technology-agnostic system architecture and all major technical decisions.

**Entry Criteria:** Approved FRDs from Phase 2

**Exit Criteria:** All ADRs approved. Data models approved. API contracts approved. Technology selections justified with free-tier confirmation.

**Responsible Group:** Group 2 (Architecture) — SA leads, DE supports

**Activities:**
- High-level design (HLD) definition
- Technology selection (one ADR per major decision)
- Data model design
- API contract definition (OpenAPI 3.0)
- Security design principles
- Integration design
- LAW 1 compliance verification for every selection
- Stack selection from the VASH catalog: stack pack, skills, agents, tools, runner, budget (Amended by 2.6)
- Catalog gap handling: search, licence check, AvA, catalog ADR before use (Amended by 2.6)

**Artifacts Produced:**
- HLD document
- ADR per technology decision
- Stack ADR (PROPOSED -> ACCEPTED by the human) in the project repository (Amended by 2.6)
- On ACCEPTED: project-stack.json written by the engine, and the project repository provisioned
  (pinned VASH, pinned workflows, audit folders) — deterministic, no AI (Amended by 2.6)
- Entity-relationship diagrams
- OpenAPI 3.0 specifications
- Security design document
- Integration map

**Parallel Safe:** Data model and API contracts parallel after HLD approved

**Human Gate:** YES — human approves HLD and ADRs before engineering begins

---

## Phase 4: UX Design

**Purpose:** Define all user interaction patterns, flows, and component specifications.

**Entry Criteria:** Approved FRDs from Phase 2

**Exit Criteria:** All user flows approved. Component specifications complete. Accessibility requirements defined.

**Responsible Group:** Group 3 (UX) — UI/UX Designer leads

**Activities:**
- User flow definition per user type
- Component specification
- Interaction pattern library
- Error state definitions
- Accessibility requirements (WCAG compliance)
- Responsive design specifications

**Artifacts Produced:**
- User flow documents (one per user journey)
- Component specification library
- Interaction pattern document
- Accessibility requirements document
- Error state catalog

**Parallel Safe:** YES — runs in parallel with Phase 3 Architecture

**Human Gate:** YES — human approves UX flows before engineering begins

---

## Phase 5: Engineering Design

**Purpose:** Translate architecture decisions and UX specs into detailed technical specifications ready for implementation.

**Entry Criteria:** Approved HLD from Phase 3 + approved UX flows from Phase 4

**Exit Criteria:** All module designs approved. API implementation specs complete. Service boundaries defined.

**Responsible Group:** Group 4 (Engineering) — SE leads, DE supports

**Activities:**
- Module design and interface definitions
- API implementation specifications
- Database schema finalisation
- Service boundary definitions
- Error handling specifications
- Performance requirements definition
- Frontend component technical specs

**Artifacts Produced:**
- Module design documents
- Detailed API specs (beyond OpenAPI — implementation notes)
- Final database schemas
- Service mesh design
- Error catalog
- Performance SLA document

**Parallel Safe:** Frontend and backend specs can run in parallel

**Human Gate:** YES — human approves engineering design before QA and infra begin

---

## Phase 6: Quality Assurance Design

**Purpose:** Define comprehensive test strategies, test cases, and quality gates.

**Entry Criteria:** Approved FRDs from Phase 2 + API contracts from Phase 3

**Exit Criteria:** All test plans approved. Every requirement has a test case. Every API endpoint has edge case tests.

**Responsible Group:** Group 5 (QA) — QA Engineer leads

**Activities:**
- Test strategy definition
- Unit test case authoring
- Integration test case authoring
- Edge case cataloguing
- Performance benchmark definition
- Security test scenarios
- AI evaluation framework (when applicable)
- Regression test planning

**Artifacts Produced:**
- Test strategy document
- Unit test case catalog
- Integration test case catalog
- Edge case catalog
- Performance benchmark specifications
- Security test plan
- AI evaluation framework (if AI components)

**Parallel Safe:** YES — runs in parallel with Phase 5 Engineering Design

**Human Gate:** YES — human approves test plans before blueprint

---

## Phase 7: Infrastructure Design

**Purpose:** Design the deployment architecture, CI/CD pipelines, and operational runbooks.

**Entry Criteria:** Approved ADRs from Phase 3

**Exit Criteria:** All IaC designs approved. CI/CD pipeline designed. Deployment runbooks complete.

**Responsible Group:** Group 6 (Infrastructure) — DevOps Engineer leads

**Activities:**
- Infrastructure design (technology-agnostic IaC)
- CI/CD pipeline design
- Environment definitions (dev/staging/prod)
- Monitoring and alerting design
- Disaster recovery design
- Security hardening design
- Deployment runbook authoring

**Artifacts Produced:**
- Infrastructure design document (IaC specifications)
- CI/CD pipeline design
- Environment configuration schemas
- Monitoring and alerting design
- DR plan
- Security hardening checklist
- Deployment runbooks

**Parallel Safe:** YES — runs in parallel with Phases 5 and 6

**Human Gate:** YES — human approves infrastructure design before blueprint

---

## Phase 8: Blueprint Assembly

**Purpose:** Consolidate all phase outputs into a single, coherent technical blueprint for implementation.

**Entry Criteria:** All phases 1-7 approved. All artifacts have passed AvA. All human gates cleared.

**Exit Criteria:** Blueprint approved by human. All artifacts indexed. Deliverable package complete.

**Responsible Group:** All groups contribute — SA leads consolidation

**Activities:**
- Artifact index compilation
- Consistency check across all artifacts
- Cross-reference validation (requirements → design → tests)
- Conflict resolution (any contradictions between artifacts)
- Blueprint document assembly
- Deliverable package preparation
- Known limitations documentation
- Recommended next steps authoring

**Artifacts Produced:**
- Master technical blueprint (single document)
- Artifact index (all artifacts with paths and scores)
- Known limitations document
- Recommended next steps document
- Project deliverable package

**Parallel Safe:** NO — depends on all previous phases

**Human Gate:** YES — final human approval of complete blueprint

---

## Phase Sequence and Parallel Map

```
Phase 1: Brief Intake
    ↓
Phase 2: Requirements Discovery
    ↓
Phase 3: Architecture ──────────────── Phase 4: UX Design
    ↓                                        ↓
Phase 5: Engineering Design ──── Phase 6: QA Design ──── Phase 7: Infrastructure
    ↓                                ↓                        ↓
    └────────────────────────────────┴────────────────────────┘
                                     ↓
                              Phase 8: Blueprint Assembly
                                     ↓
                              Human Final Approval
```

---

## Human Gate Summary

| Phase | Gate Trigger | What Human Reviews |
|-------|-------------|-------------------|
| 1 | Brief validated | Brief understanding correct? |
| 2 | FRDs complete | Requirements complete and correct? |
| 3 | Architecture complete | ADRs and technology selections correct? |
| 4 | UX complete | User flows correct? |
| 5 | Engineering design complete | Module designs correct? |
| 6 | QA design complete | Test coverage adequate? |
| 7 | Infrastructure complete | Infrastructure design correct? |
| 8 | Blueprint assembled | Blueprint complete and ready? |

---

## Artifact Traceability Matrix

Every artifact traces back to a requirement:

```
Brief → Requirements (Phase 2)
Requirements → Architecture decisions (Phase 3)
Requirements → UX flows (Phase 4)
Architecture + UX → Engineering specs (Phase 5)
Requirements + Architecture → Test cases (Phase 6)
Architecture → Infrastructure design (Phase 7)
All artifacts → Blueprint (Phase 8)
```

This ensures no orphaned artifacts and no untested requirements.

---

## Amendment by 2.6 — Freeze Change Rule and Execution Stages

### Freeze change rule
A project's project-stack.json changes only through a new ADR that supersedes the earlier one, accepted
by the human, followed by Stage 0 and the full pipeline. A deterministic check refuses any change to the
Freeze file that does not name an ACCEPTED ADR. Upgrading the pinned VASH version follows the same rule.

### Execution stages (Blueprint v8.2 Stages 0-10)
The build, review, pipeline, fix-loop, release and post-release stages that follow Phase 8 are mapped
in vash_framework/architecture/2-6_application_framework.md, Section 5. They are execution stages, not SDLC phases; they are built by activity-list Phase 7 — Engine Build
and apply to projects, each in its own repository.
