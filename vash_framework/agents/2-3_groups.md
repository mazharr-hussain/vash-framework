# VASH 3.0 — Group Configurations

## What Are Groups

Groups are collections of agent roles that collaborate on specific phases of a project. Each group has a defined lead role, supporting roles, AvA pairings, and the SDLC phases it covers.

---

## Group 1: Discovery and Requirements

**Purpose:** Transform a client brief into structured, verifiable requirements.

**Lead Role:** Business Analyst (BA)

**Supporting Roles:** Project Manager (PM), UI/UX Designer

**SDLC Phases Covered:**
- Brief intake and decomposition
- Stakeholder analysis
- Functional requirements definition
- User story mapping
- Acceptance criteria definition

**AvA Pairings:**
- BA Junior → BA Senior (primary)
- UI/UX Junior → UI/UX Senior (for UX requirements)
- Cross-review: BA Senior reviews UI/UX artifacts for requirement consistency

**Parallel Opportunities:**
- BA and UI/UX can work in parallel once brief is decomposed
- Functional requirements and UX flows are independent

**Entry Criteria:** Approved project brief from Human Owner

**Exit Criteria:** All FRDs approved + acceptance criteria defined

---

## Group 2: Architecture and Design

**Purpose:** Define the technology-agnostic system architecture and all design decisions.

**Lead Role:** Solution Architect (SA)

**Supporting Roles:** Data Engineer (DE), AI/ML Engineer (when AI components present)

**SDLC Phases Covered:**
- System architecture definition
- Technology selection (ADRs)
- Data model design
- API contract definition
- Security design principles
- Integration design

**AvA Pairings:**
- SA Junior → SA Senior (primary, using senior-architect skill)
- DE Junior → DE Senior
- Cross-review: DE Senior reviews SA data architecture artifacts
- Cross-review: SA Senior reviews DE pipeline designs

**Parallel Opportunities:**
- Data model and API contracts can run in parallel after HLD approved
- Security design can run in parallel with data model

**Entry Criteria:** Approved FRDs from Group 1

**Exit Criteria:** All ADRs approved + data models approved + API contracts approved

---

## Group 3: User Experience

**Purpose:** Define all user interaction patterns, flows, and component specifications.

**Lead Role:** UI/UX Designer

**Supporting Roles:** Business Analyst (reference only)

**SDLC Phases Covered:**
- User flow definition
- Component specification
- Accessibility requirements
- Interaction pattern library
- Error state definitions

**AvA Pairings:**
- UI/UX Junior → UI/UX Senior (primary)
- Cross-review: BA Senior reviews UX flows against requirements

**Parallel Opportunities:**
- UX work runs in parallel with Group 2 architecture work
- Both depend on Group 1 output only

**Entry Criteria:** Approved FRDs from Group 1

**Exit Criteria:** All user flows approved + component specs approved

---

## Group 4: Engineering Design

**Purpose:** Translate architecture decisions into detailed technical specifications ready for implementation.

**Lead Role:** Software Engineer (SE)

**Supporting Roles:** Data Engineer (DE), DevOps Engineer

**SDLC Phases Covered:**
- Module design and interfaces
- API implementation specifications
- Database schema finalisation
- Service boundary definitions
- Error handling specifications
- Performance requirements

**AvA Pairings:**
- SE Junior → SE Senior (primary)
- DE Junior → DE Senior
- Cross-review: SE Senior reviews DE schema for ORM compatibility
- Cross-review: DE Senior reviews SE APIs for data access patterns

**Parallel Opportunities:**
- Frontend and backend engineering specs can run in parallel
- Multiple service specs can run in parallel if independent

**Entry Criteria:** Approved ADRs and data models from Group 2

**Exit Criteria:** All module designs approved + API specs approved

---

## Group 5: Quality Assurance

**Purpose:** Define comprehensive test strategies, test cases, and quality gates.

**Lead Role:** QA Engineer

**Supporting Roles:** AI/ML Engineer (for AI component testing)

**SDLC Phases Covered:**
- Test strategy definition
- Test case authoring
- Edge case cataloguing
- Performance benchmark definition
- Security test scenarios
- AI evaluation framework (when applicable)

**AvA Pairings:**
- QA Junior → QA Senior (primary)
- Cross-review: SE Senior reviews test cases for technical feasibility
- Cross-review: AI/ML Senior reviews AI evaluation frameworks

**Parallel Opportunities:**
- Unit test cases and integration test cases can run in parallel
- QA work runs in parallel with Group 4 engineering design

**Entry Criteria:** Approved FRDs from Group 1 + API contracts from Group 2

**Exit Criteria:** All test plans approved + edge cases catalogued

---

## Group 6: Infrastructure and Operations

**Purpose:** Design the deployment architecture, CI/CD pipelines, and operational runbooks.

**Lead Role:** DevOps Engineer

**Supporting Roles:** Solution Architect (reference only)

**SDLC Phases Covered:**
- Infrastructure design (IaC)
- CI/CD pipeline design
- Environment definitions (dev/staging/prod)
- Monitoring and alerting design
- Disaster recovery design
- Deployment runbooks

**AvA Pairings:**
- DevOps Junior → DevOps Senior (primary, using senior-architect skill)
- Cross-review: SA Senior reviews infrastructure for architecture compliance

**Parallel Opportunities:**
- CI/CD design and infrastructure design can run in parallel
- Multiple environment specs can run in parallel

**Entry Criteria:** Approved ADRs from Group 2

**Exit Criteria:** All IaC designs approved + deployment runbooks approved

---

## Group 7: AI and Intelligence

**Purpose:** Design all AI/ML components, model selections, prompt strategies, and evaluation frameworks.

**Lead Role:** AI/ML Engineer

**Supporting Roles:** Data Engineer, QA Engineer

**SDLC Phases Covered:**
- Model selection and justification (ADRs)
- Prompt template design
- RAG architecture (when applicable)
- Fine-tuning strategy (when applicable)
- AI evaluation framework
- Bias and safety assessment

**AvA Pairings:**
- AI/ML Junior → AI/ML Senior (primary)
- Cross-review: DE Senior reviews data pipelines feeding AI components
- Cross-review: QA Senior reviews evaluation frameworks

**Parallel Opportunities:**
- Model selection and prompt design can run in parallel
- Multiple AI components can be designed in parallel

**Entry Criteria:** Approved FRDs + data models from Groups 1 and 2

**Exit Criteria:** All model ADRs approved + evaluation frameworks approved

---

## Group Summary Table

| # | Group | Lead | Key Cross-Reviews | Parallel With |
|---|-------|------|-------------------|---------------|
| 1 | Discovery | BA | None | None (first) |
| 2 | Architecture | SA | DE↔SA | Group 3 |
| 3 | UX | UI/UX | BA reviews UX | Group 2 |
| 4 | Engineering | SE | SE↔DE | Group 5 |
| 5 | QA | QA | SE reviews tests | Group 4 |
| 6 | Infrastructure | DevOps | SA reviews infra | Group 4, 5 |
| 7 | AI/Intelligence | AI/ML | DE+QA cross-review | Group 4, 5 |

## Sequencing Rules
```
Group 1 → must complete before Groups 2, 3, 7
Groups 2 + 3 → can run in parallel
Group 2 → must complete before Groups 4, 6
Groups 4 + 5 + 6 + 7 → can run in parallel
All groups → must complete before blueprint
```
