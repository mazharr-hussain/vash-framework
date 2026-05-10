# .claude/hooks/

This folder contains Claude Code hook definitions for the VASH 3.0 framework.

Hooks are shell commands that execute automatically in response to Claude Code events (e.g. before a tool call, after a session ends). They enforce workflow rules without requiring human intervention.

## Hook conventions
- Hooks must not modify knowledge/laws.md
- Pre-push hooks verify AvA score thresholds are met
- Post-session hooks save all runtime output files
