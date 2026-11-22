# VASH 3.0 — Skills Search Log
# LAW 3: Document every search before building

## Search 1: Prompt Engineering Skill

SEARCHED:
- GitHub marketplace: NeoLabHQ/prompt-engineering
- VoltAgent/awesome-agent-skills
- ComposioHQ/awesome-claude-skills
- agensi.io/skills
- skillsmp.com

FOUND:
- NeoLabHQ/context-engineering-kit — prompt-engineering SKILL.md ✅
  URL: github.com/NeoLabHQ/context-engineering-kit
  Stars: High — widely used
  Description: Widely used prompt engineering techniques and patterns,
  including Anthropic best practices and agent persuasion principles

DECISION: REUSE — adapted for VASH context
SOURCE: NeoLabHQ/context-engineering-kit

---

## Search 2: Code/Artifact Reviewer Skill

SEARCHED:
- GitHub: nishilbhave/codeprobe
- agensi.io/skills (116 installs — most popular)
- alirezarezvani/claude-skills (adversarial-reviewer)
- levnikolaevich/claude-code-skills

FOUND:
- nishilbhave/codeprobe — code-reviewer SKILL.md ✅
  Stars: Popular (116 installs on agensi.io)
  Description: Senior-engineer-level review across 9 domains
- alirezarezvani/claude-skills — adversarial-reviewer ✅
  Description: Adversarial review with 3 hostile personas

DECISION: REUSE — adapted adversarial-reviewer for VASH AvA Senior role
SOURCE: alirezarezvani/claude-skills (adversarial-reviewer)

---

## Search 3: Senior Architect Skill

SEARCHED:
- alirezarezvani/claude-skills (engineering-advanced-skills)
- wshobson/agents
- ComposioHQ/awesome-claude-skills (great_cto plugin)

FOUND:
- alirezarezvani/claude-skills — senior-architect SKILL.md ✅
  Description: Reviews architecture and identifies scalability risks
  Proven in production use
- great_cto plugin — 7 specialised subagents including tech-lead ✅

DECISION: REUSE — adapted senior-architect from alirezarezvani/claude-skills
SOURCE: alirezarezvani/claude-skills

---

## Search 4: Multi-Agent/AvA Orchestration Skill

SEARCHED:
- muratcankoylan/multi-agent-patterns
- wshobson/agents (multi-agent orchestration)
- levnikolaevich/claude-code-skills (Two-Agent AI Review)
- ShunsukeHayashi/agent-skill-bus

FOUND:
- muratcankoylan/multi-agent-patterns ✅
  Description: Master orchestrator, peer-to-peer, hierarchical patterns
- wshobson/agents — Agent Teams workflow ✅
  Description: Multi-agent orchestration for full SDLC
- levnikolaevich/claude-code-skills — Two-Agent AI Review ✅
  Description: Claude and Codex review each other's work

DECISION: REUSE — adapted multi-agent-patterns for VASH AvA loop
SOURCE: muratcankoylan/multi-agent-patterns

---

## Summary
TOTAL SKILLS NEEDED: 4
FOUND IN MARKETPLACE: 4 (100%)
REUSED: 4
BUILT NEW: 0
LAW 3 COMPLIANCE: PASS ✅

---

## Search: OCI cleanup, inventory and infrastructure modules (9 Nov 2026)

SEARCHED:
- github.com/oracle-devrel/oci-automation-hub (Oracle, UPL-1.0)
- github.com/oracle-devrel/cd3-automation-toolkit (Oracle, UPL-1.0)
- github.com/AnykeyNL/OCI-SuperDelete (personal project, UPL-1.0)

FOUND:
- oci-automation-hub `oci-compartment-cleaner-sample`: dry-run plan, Resource Manager backup stack,
  typed DELETE, about 53 resource types in dependency order, post-delete verification;
  `network_usage_audit.py` for external users of a compartment's network. Labelled a sample.
  No Cloud Shell (delegation token) sign-in: VASH adds it in its launcher, without changing the tool.
- cd3-automation-toolkit: Terraform modules for every OCI service (network incl. LPG, DRG, VLAN, DNS;
  compute; databases; load balancers; OKE; storage; identity; governance) and export of an existing
  tenancy to Terraform; Excel templates and Jenkins pipelines. Release v2026.2.2.
- OCI-SuperDelete: deletes everything in a compartment; no plan, no backup, -force.
- oci-automation-hub GenAI samples (cloud-ops agent, OKE ops agent, OpenClaw): paid OCI Generative AI.

DECISION:
- REUSE (run) oci-compartment-cleaner at commit 685ae12a021874609d0125619580356ca904dbeb for emptying
  compartments (src/vash/adapters/cloud/oci/cleaner.py). Status candidate (vendor sample).
- REUSE cd3-automation-toolkit Terraform modules (network/vcn, igw, route-table, sec-list, subnet;
  compute/instance) at release v2026.2.2 in iac/oci/environments/always-free; VASH's own network
  and compute modules removed. Export: later (KYC adoption).
- REUSE cd3-automation-toolkit modules identity/iam-compartment, security/vault and security/key at
  release v2026.2.2 in iac/oci/environments/foundation (src/vash/adapters/cloud/oci/foundation.py):
  every compartment, vault and key onboarding creates (owner rule, 9 Nov 2026: everything CD3 has
  is built with CD3). The oci CLI is kept only for reading (lists, states) and for deletes.
  Also REUSE CD3 managementservices/notification (e-mails), governance/quota-policy,
  costmanagement/budget and budget-alert-rule (free-tier guardrails), release v2026.2.2.
- KEPT VASH's own free-tier Autonomous Database module: the CD3 adb module has no is_free_tier
  option, so it cannot create an Always Free database (LAW 1); the vendor option is not equal here.
- REJECTED OCI-SuperDelete: the vendor's cleaner is equal or better (vendor-first rule).
- RECORDED, NOT USED (LAW 1): the paid GenAI samples, for a later paid tier.
- UPL-1.0 added to catalog/licences.json (owner decision, 9 Nov 2026).

## 18 Nov 2026: database password secret and network compartment (vash onboard oci)
- SEARCHED cd3-automation-toolkit v2026.2.2 modules/security (cloud-guard-configuration,
  cloud-guard-target, firewall, key, vault) and modules/database (adb, cdb, db-home, dbsystem-vm-bm,
  exa-infra, exa-vmcluster, mysql-*, pdb): no module for vault secrets.
- USED the vendor's oci CLI (`oci vault secret create-base64`, request read from a private file) for the
  database admin password secret; reading it back with `oci secrets secret-bundle get`.
- KEPT VASH's own free-tier database module, now in the foundation environment too (is_free_tier and
  mutual TLS; the password is ignored after creation so it never has to be sent again).
- The network compartment uses the CD3 iam-compartment module already in use; the CD3 network modules
  take its id.

## 22 Nov 2026: setup in the background and in parallel (vash onboard oci)
- SEARCHED for a vendor service that runs terraform outside the shell: OCI Resource Manager (Oracle, free,
  runs terraform jobs inside OCI, keeps the state, shows jobs and logs in the Console), OCI DevOps build
  pipelines (Oracle, needs a project, a repository and build runners: more parts for the same result),
  Cloud Shell background processes (end with the session after about 20 minutes idle), a detached process on a
  bastion (ends with that machine).
- USED OCI Resource Manager (vendor-native, $0, LAW 1 and R9): iac/oci/environments/vash-stack is one terraform
  graph, so terraform builds in parallel whatever does not depend on something else.
- REUSE the same CD3 modules (v2026.2.2) inside the stack; the database password is made with HashiCorp's
  random provider and kept with the OCI provider's oci_vault_secret (CD3 has no secrets module), so no person
  and no file sees it; HashiCorp's time provider waits out IAM's delay and a new vault's DNS.
- KEPT the step-by-step path as `--in-shell` (and for work on an existing VM).
