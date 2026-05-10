# .claude/agents/

This folder contains Claude Code subagent definitions for the VASH 3.0 framework.

Subagents run in their own context windows, allowing parallel or isolated execution of tasks. Each agent definition specifies the agent's role, tools, and behaviour.

## Agents in this project
- junior-creator — generates VASH artifacts in an isolated context
- senior-validator — reviews and scores artifacts in an isolated context
- prompt-engineer — produces optimised prompts in an isolated context
