# VASH basic requirement

The owner's statement of what VASH is (22 Nov 2026). Every activity, design and change is checked against it.
When the plan, the method or the code disagree with this page, this page wins until the owner changes it.

## 1. A complete virtual software house

- The work of a software house is done by AI personas: analyst, architect, developer, tester, reviewer,
  release manager and the others in `roles/registry.md`.
- Every result goes through **AvA** (Agent vs Agent, `ava/protocol.md`): one agent produces it, an independent
  agent reviews and scores it, and nothing passes below the threshold.
- **Agents and personas are chosen per task.** For each task the decision is recorded: one agent that takes
  several personas in turn, or a separate agent per persona. Separate agents are needed where independence is
  required (the reviewer of an AvA pair, rule R4) or where the work runs in parallel.
- **Skills are always used.** Before a task, the skills it needs are listed. A skill that is not in the project or
  the catalog is searched for (catalog, then vendor and open-source indexes), validated (licence, source, the
  skills-ref validator) and then downloaded and pinned; only when nothing suitable exists is a new skill created.
  What was searched and found is recorded (LAW 3, rule R15).

## 2. The cost is always $0

Free tiers and free allowances only (LAW 1). Usage is tracked against every free limit so it is never exceeded.

## 3. Free, open-source tools, services, VMs and GPUs

- The model on the owner's VM is the **gatekeeper**: it understands each request, splits it into tasks, masks
  client data before anything leaves the VM, and decides (within fixed rules) where each task goes. Masked
  answers are unmasked only on the VM.
- Other work goes to free models, free GPUs and free runners, many tasks in parallel.
- **One model gateway** on the VM holds every model key (given once by the owner, kept in the vault, the gateway's
  settings written by VASH, never by hand). VASH asks it only for a kind of work (`vash-coding`, `vash-review`,
  `vash-docs`, `vash-prompt`, `vash-test`, ...); the gateway maps each kind to the right model, falls back to the
  next model when one fails or runs out of free quota, and counts usage. The model on the VM is the last fallback.
  A review model always comes from a different model maker than the model whose work it reviews (rule R4).
  Changing the model for a kind of work is one line in that mapping; projects do not change.
- Deterministic checks come first and cannot be overruled by a model (rule R3).

## 4. Reuse, not recreation

Vendor and vetted open-source tools, skills and modules are used before anything is built (LAW 3). A pooling or
routing tool is reused, never written (rule R12).

## 5. Many ways in

Work can be started from Git (issues, pull requests, comments), from a chat harness, from the command line and
from other channels later. Every way in leads to the same engine, the same rules and the same audit trail. The
owner only briefs, decides, approves and merges (LAW 2).

## Status against this requirement (22 Nov 2026)

| Point | Exists | Missing |
|---|---|---|
| 1 Personas and AvA | AvA loop (one producer, one critic, Gate 1, threshold, 3 rounds); roles registry; skills loader, `vash skill validate`, `vash skill suggest` | persona and agent choice per task; multi-persona workflows across a software-house flow; automatic skill search, validation and download before a task |
| 2 $0 | free-tier guardrails in OCI; Always Free VM and database | usage tracking against free API limits (`vash cost`) |
| 3 Free resources | VM with a local model; free model APIs through the OpenAI-compatible adapter | gatekeeper (understand, split, mask, route, unmask); the model gateway with a model per kind of work (candidate: LiteLLM); parallel tasks; free GPUs |
| 4 Reuse | catalog, search log, CD3 and vendor modules | the automatic skill and tool search of point 1 |
| 5 Many ways in | command line; GitHub pull request checks | starting work from Git issues or comments; chat harness (MCP server); other channels |
