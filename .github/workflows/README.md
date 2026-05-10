# .github/workflows/

This folder contains GitHub Actions workflow definitions for VASH 3.0 automation.

## Planned workflows
- va.yml — triggered by issues labelled ash-activity; runs the AvA loop
- parallel.yml — triggered by issues labelled ash-parallel; runs parallel-safe activities concurrently
- 
otify.yml — triggered on PR merge to main; sends activity completion notification

All workflows comply with LAW 1 (open source actions only) and LAW 2 (agent over human).
