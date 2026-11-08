# ADR-002: Freeze the VASH repository structure

- **ID:** ADR-002
- **Title:** Freeze the VASH repository structure
- **Status:** ACCEPTED
- **Date:** 2026-11-06
- **Activity:** 5.1 (vash_framework/platform/5-1_repo_structure.md), brought forward by owner decision
- **Builds on:** ADR-001 (VASH as the application framework, PROPOSED)
- **Decided by:** Human owner (changes Status to ACCEPTED or rejects)

## Context
VASH is a public tool that anyone can use for any project. Its repository held design documents in
knowledge/, vash_framework/ and runtime/, with no place for the method, catalog, engine and project
scaffold as separate products. The owner and Claude designed the structure over a working session
(5-6 Nov 2026), checked it against three feedback sets, and the owner froze it (v7) with decisions D1-D9.

## Decision
| # | Decision |
|---|---|
| D1 | VASH's own review trail stays in this repository, committed under audit/; runtime/ is git-ignored scratch and is never committed. |
| D2 | The project skeleton is scaffold/project/ (renamed from templates/project/); method/templates/ holds forms only and method/schemas/ the schemas. |
| D3 | Package and command name vash (free on PyPI, checked 5 Nov 2026); semver from 3.0.0 shared by package, release tag and method; repository name vash-framework (owner decision 8 Nov 2026; was vash3-framework). |
| D4 | The design-only stack pack is in wave 1 so VASH works for anyone with no technology chosen. VASH names no application. |
| D5 | Technology independence and $0 outrank every other rule: every technology layer (stack, LLM, git host, CI/CD, cloud) is a catalog category with one adapter per option, chosen per project in project-stack.json; the core names no vendor. R9 becomes "the project's own git host, through the forge adapter". |
| D6 | Pilots are the owner's private Oracle APEX projects, so the oracle-apex pack and the GitHub, GitHub Actions, OCI and LLM adapters are in wave 1; each pilot adopts VASH through its own ADR in its own repository. |
| D7 | src/vash/core/exceptions.py with named errors; data/ (incl. data/intake/) ignored in VASH, the folder exists only in projects; catalog/ci/local-hooks and its adapter in wave 1. |
| D8 | The structure is frozen. One LLM interface independent of any tool; bin/ wrappers only call python -m vash.cli. |
| D9 | src/vash/mcp/ write guard in wave 1 (R6 holds for the pilots); src/vash/core/interfaces.py adapter contract in wave 1; CLI stubs for later-wave commands through NotAvailableYet, reporting the routes actually configured. |

Activity 5.1 completes the frozen structure with what its description requires and the freeze did not
change: naming conventions, file formats (with .gitattributes for LF / UTF-8), branch strategy, the
project repository contents, and the LAW 3 search for the loader / provisioner (Copier proposed).

## Consequences
- The files are moved into this layout later, as a separate step (activity 7.2), keeping history and
  updating the AvA scripts' paths in the same change (bootstrap stage A).
- Folders are created only when their wave starts; the structure lists them all.
- Rule R12 is amended (one configured fallback route to local Ollama) and R9 is amended (project state
  on its own git host), both PROPOSED with this ADR.
- Any change to the structure needs a new owner decision that supersedes this ADR.
