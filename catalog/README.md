# VASH Catalog

The catalog holds every technology choice VASH can make. A project selects one option per category (stack, LLM, forge, CI, cloud) in its `project-stack.json`.

## Categories

- **Stacks**: The technology pack (e.g., `design-only`, `oracle-apex`).
- **LLM**: The AI models (e.g., `ollama`, `anthropic`).
- **Forge**: The Git host (e.g., `github`, `gitlab`).
- **CI**: The pipeline tool (e.g., `github-actions`, `local-hooks`).
- **Cloud**: The infrastructure host (e.g., `oci-always-free`).

## Adding an Option

1. Search for the tool (LAW 3). Document the search in `search-log.md`.
2. Check its licence.
3. Write the catalog entry (with frontmatter).
4. Write the adapter (if it needs code).
5. Submit a PR for AvA review.

Every entry in this catalog is a candidate until the ADR that adopts it is ACCEPTED.
