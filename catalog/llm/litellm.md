---
id: litellm
type: tool
source: https://github.com/BerriAI/litellm
fork: null
licence: MIT
use: run
version: 1.108.3
commit: to-verify
stacks: []
search_log: search-log.md
status: candidate
---
# LiteLLM

The model gateway on the VM (owner requirement, method/requirements.md point 3): one OpenAI-compatible address,
a model per kind of work (`vash-coding`, `vash-review`, `vash-docs`, `vash-prompt`, `vash-test`), fallbacks to the
next model and finally to the VM's own model. MIT outside its `enterprise/` folder, which VASH does not use.
Pinned on PyPI to 1.108.3 (7 Nov 2026), installed by the VM setup into its own virtual environment.
The models per kind of work are in `gateway.json` beside this file.
