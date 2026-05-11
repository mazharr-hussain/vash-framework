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
