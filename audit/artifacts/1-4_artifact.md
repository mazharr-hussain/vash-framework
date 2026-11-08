# VASH 3.0 — Stakeholder Map

## Stakeholder 1: The Human Owner

**Who:** Solo founder, product owner, or team lead who submits projects to VASH.

**Needs:**
- Fast, high-quality technical artifacts without managing a team
- Simple interaction model — brief in, decision out
- Confidence that outputs are reviewed and trustworthy
- Full visibility into what was produced and why

**Interaction Points:**
- Submits initial project brief
- Receives GitHub Issue notifications for each milestone
- Types APPROVED / REJECTED / MODIFY in Project 1 chat
- Reviews final blueprint before handoff

**What They Never Do:**
- Write prompts for individual agents
- Review intermediate AvA debates
- Manage GitHub Actions or infrastructure
- Debug pipeline failures

---

## Stakeholder 2: The Junior Creator Agent

**Who:** The generative AI agent producing first-draft artifacts.

**Needs:**
- Clear activity description from activity_list.md
- Locked prompt from Prompt Engineer
- Context from dependency artifacts
- Laws and checklist available

**Interaction Points:**
- Receives locked prompt from Prompt Engineer agent
- Reads knowledge/ files for context
- Writes artifact to runtime/artifacts/
- Receives Senior objections for revision rounds

**Constraints:**
- No memory of previous Senior reviews
- No access to Senior session history
- Cannot approve its own work

---

## Stakeholder 3: The Senior Validator Agent

**Who:** The adversarial AI agent reviewing and scoring Junior artifacts.

**Needs:**
- Artifact from Junior Creator
- Relevant checklist from knowledge/checklists/
- Laws from knowledge/laws.md
- No access to Junior's thought process

**Interaction Points:**
- Reads artifact from runtime/artifacts/
- Applies code-reviewer and senior-architect skills
- Writes scored review to runtime/ava_logs/
- Passes objections back to Junior via orchestrator

**Constraints:**
- Isolated context window — no Junior memory
- Cannot pass without meeting threshold
- Must provide specific objections with exact locations

---

## Stakeholder 4: The Prompt Engineer Agent

**Who:** The AI agent that generates optimal locked prompts before every activity.

**Needs:**
- Current activity description
- Laws and constraints
- Dependency artifact context

**Interaction Points:**
- Reads activity from knowledge/activity_list.md
- Generates locked prompt
- Saves to runtime/prompts/
- Passes to Junior Creator

**Constraints:**
- Prompt must be unambiguous before locking
- Must embed all three laws
- Must specify output format and path

---

## Stakeholder 5: The AvA Orchestrator

**Who:** The Python script (ava.py) that manages the complete AvA loop.

**Needs:**
- TASK_ID from GitHub Actions environment
- Claude Code CLI available on GitHub VM
- OAuth token in CLAUDE_CODE_OAUTH_TOKEN secret
- Read/write access to repo

**Interaction Points:**
- Triggered by GitHub Actions on issue label
- Calls Junior and Senior Claude Code sessions
- Parses scores from ava_logs
- Writes summaries to runtime/validation/
- Updates activity status in activity_list.md

**Constraints:**
- Python stdlib only — no pip installs
- Max 3 rounds per activity
- Must handle stalemate and escalation

---

## Stakeholder 6: GitHub Actions

**Who:** The free CI/CD infrastructure that orchestrates the pipeline.

**Needs:**
- Properly formatted workflow files
- CLAUDE_CODE_OAUTH_TOKEN secret
- GITHUB_TOKEN for repo write access

**Interaction Points:**
- Triggers on issue label (vash-activity / vash-parallel)
- Triggers on push to main (notify)
- Runs ava.py on Ubuntu VM
- Commits results back to repo
- Creates notification issues

**Constraints:**
- Free tier: 2000 minutes/month
- Ubuntu runner: no persistent state
- Must install Claude Code CLI on every run

---

## Stakeholder 7: The Client (Future)

**Who:** The end customer who will use the software built by VASH.

**Current Status:** Out of scope for VASH 3.0 design phase.
**Future Relevance:** Their requirements become the project brief submitted by the Human Owner.

---

## Stakeholder Interaction Summary

```
Human Owner
    │
    ├── submits brief ──────────────────► GitHub Issue (vash-activity)
    │                                           │
    │                                           ▼
    │                                    GitHub Actions VM
    │                                           │
    │                                    ava.py orchestrator
    │                                     │         │
    │                               Prompt Engineer  │
    │                                     │          │
    │                               Junior Creator   │
    │                                     │          │
    │                               Senior Validator │
    │                                     │          │
    │                               runtime/validation/
    │                                           │
    │                                    notify.yml
    │                                           │
    └── reviews GitHub Issue ◄──────────────────┘
        types decision
```
