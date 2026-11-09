# Changelog

All notable changes to this project will be documented in this file.
This is a hand-written seed for bootstrap stage A; it will be engine-generated in the future.

## [Unreleased]
### Added
- Initial repository scaffolding, governance, security policies, and the build system.
- Added the VASH method and AvA protocol (Step 2).
- Added the core engine, interfaces, registry and freeze loading (Step 3).
- Added GitHub, CI, OCI, Ollama and OpenAI-compatible adapters (Step 4).
- Added Stage 0 and Gate 1 deterministic tools (Step 5).
- Added the CLI, loader and AvA runner (Step 6).
- Added the catalog, stack packs, scaffold and OCI IaC (Step 7).
- Added VASH's own CI, templates and freeze (Step 8).
- Packaged method, catalog and scaffold in the wheel; `pip install` works without `VASH_HOME`.
- Added `vash onboard oci`: one Cloud Shell command creates the Always Free runner VM and installs VASH, terraform and Ollama.
- Added iteration mode (agile delivery): optional `delivery` block in the freeze, FEATURE activities with their checklist, and `feature:`/`iteration:` traced in every AvA log.
- Added portable skills and agents: `vash skill new|validate|suggest`, `vash agent new`, project skills/ and agents/, AGENTS.md and .agents/skills/ for every coding tool, skills in prompts for plain model APIs, Gate 1 rule G1-13 (official skills-ref validator) and rule R15.
- Renamed the skill prompt-engineer to prompt-engineering (agents are roles, skills are know-how); the agent keeps prompt-engineer.
- Fixed `vash onboard oci` in OCI Cloud Shell (FIPS mode): reuses id_ed25519 or id_rsa, and falls back to RSA 4096 when ed25519 is refused.
