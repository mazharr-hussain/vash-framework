# VASH 3.0 — Scope and Boundaries

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

### Source Code Production (Phase 1 of VASH)
VASH 3.0 produces design artifacts only.
Actual source code generation is a future phase (VASH 4.0).

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

### Technology Constraint
All VASH development uses Claude + GitHub + Python only.
No other development tools regardless of quality or convenience.

### Cost Constraint
VASH platform infrastructure must use free tier until VASH generates revenue.
No paid platforms in the VASH engine itself.

### Quality Constraint
No artifact reaches the human without passing AvA.
Minimum score thresholds are non-negotiable.

### Scope Constraint
VASH designs software — it does not write it (in 3.0).
Any activity that produces runnable code is out of scope for this phase.

---

## ASSUMPTIONS

1. The human owner has a clear product vision and can articulate it in a brief
2. The GitHub repository is accessible and the OAuth token is valid
3. Claude Pro subscription provides sufficient usage for development activities
4. The human owner can review and decide within 24 hours of notification
5. All client projects submitted to VASH are legal and ethical

---

## WHAT VASH 3.0 EXPLICITLY WILL NOT ATTEMPT

- Replace human judgment on critical business decisions
- Produce legally binding documents
- Guarantee the security of generated designs without human security review
- Operate autonomously without any human oversight
- Build itself (VASH cannot bootstrap itself from scratch — Phase 0 requires human setup)
