# VASH 3.0 — Scope and Boundaries
Amendments marked "Amended by 2.6" are PROPOSED: they take effect when ADR-001 is ACCEPTED; until then the earlier text (git history) applies.

## IN SCOPE — What VASH Does

### Design and Planning
- Architecture Decision Records (ADRs)
- High-Level Design (HLD) documents
- Data models and schema definitions
- API contracts (OpenAPI 3.0 specs)
- Infrastructure design (technology-agnostic)
- Security design principles
- Test strategy and test plans
- Deployment runbooks

### Process and Requirements
- Functional Requirements Documents (FRDs)
- Business Process Maps (BPMN-style)
- User story decomposition
- Acceptance criteria definition
- Domain model documentation

### Quality Control
- Adversarial AvA review on every artifact
- Compliance checking against VASH laws
- Technology agnosticism verification
- Cross-artifact consistency checking

### Project Management
- Activity sequencing and dependency management
- Parallel activity identification and execution
- Human milestone gate management
- Artifact versioning and history

---

## OUT OF SCOPE — What VASH Does NOT Do

### Source Code Production (Amended by 2.6, ADR-001 D9)
Until the blueprint (6.1) is approved, VASH produces design artifacts only.
From Phase 7 — Engine Build, VASH builds its own engine code; projects' code is then built by the
engine inside each project's private repository, under the same AvA loop.

### Infrastructure Provisioning
VASH produces IaC templates and runbooks.
Actual cloud provisioning requires human execution or a separate deployment agent.

### Live System Operation
VASH designs monitoring and observability strategies.
It does not operate, monitor, or maintain live systems.

### Legal and Compliance Decisions
VASH can surface compliance requirements and design for them.
Final legal and regulatory decisions require qualified human professionals.

### Financial Decisions
VASH can model costs and present trade-offs.
Final budget and investment decisions are the human owner's responsibility.

### Third-Party Negotiations
VASH can define vendor requirements and evaluation criteria.
Actual vendor selection, negotiation, and contracting is human work.

---

## CONSTRAINTS

### Technology Constraint (Amended by 2.6)
VASH development uses GitHub + Python + open-source tools from the VASH catalog.
AI work runs on pooled free-tier LLMs and local models; the existing Claude tooling is kept for VASH's
own development until the owner changes it (OD-1).
Each project's technology is decided by VASH with the human (ADR) and frozen in the project's
project-stack.json.

### Cost Constraint (Amended by 2.6)
$0: open source and free tiers only, for the VASH engine and for every project. No paid SaaS.

### Visibility Constraint (Added by 2.6)
VASH is public. Client projects are private. No client data enters the VASH repository.

### Quality Constraint
No artifact reaches the human without passing AvA.
Minimum score thresholds are non-negotiable.

### Scope Constraint (Amended by 2.6, ADR-001 D9)
Until the blueprint (6.1) is approved, VASH designs software and does not write it; any activity that
produces runnable code is out of scope until then. From activity-list Phase 7, CODE activities build
the engine under the code checklist.

---

## ASSUMPTIONS

1. The human owner has a clear product vision and can articulate it in a brief
2. The GitHub repository is accessible and the OAuth token is valid
3. (Amended by 2.6) The pooled free tiers and the local model provide sufficient capacity for development activities — to verify in 3.3; Claude remains the main tooling for VASH's own development until the owner changes it (OD-1)
4. The human owner can review and decide within 24 hours of notification
5. All client projects submitted to VASH are legal and ethical

---

## WHAT VASH 3.0 EXPLICITLY WILL NOT ATTEMPT

- Replace human judgment on critical business decisions
- Produce legally binding documents
- Guarantee the security of generated designs without human security review
- Operate autonomously without any human oversight
- Build itself (VASH cannot bootstrap itself from scratch — Phase 0 requires human setup)

---

## Amendment by 2.6 — In Scope Additions
- The VASH catalog (ai-manifest.json) and stack packs (stacks/)
- Deciding each project's stack with the human and writing its Freeze file (project-stack.json)
- Provisioning project repositories (Freeze file, pinned VASH, workflows, audit folders)
- From Phase 7: the engine (supervisor, deterministic gate tools, loader, cost meter, canary injector,
  licence verifier, reusable workflows, IaC for the self-hosted runner)
