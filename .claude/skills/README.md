# .claude/skills/

This folder contains Claude Code skill definitions for the VASH 3.0 framework.

Skills are reusable, named capabilities that Claude executes on demand. Each skill file defines a specific behaviour — such as generating prompts, reviewing artifacts, or orchestrating the AvA loop.

## Skills in this project
- prompt-engineer — generates optimal prompts for VASH activities
- code-reviewer — validates artifact quality against checklists
- senior-architect — reviews architecture decisions
- ash-creator — generates VASH artifacts (Junior role)
- ash-validator — scores and reviews artifacts (Senior role)
- ash-orchestrator — manages the full AvA loop
