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
- `vash onboard oci`: `--subnet-id` reuses an existing public subnet (no network created, SSH rule checked); the compartment name is asked (default `vash`) or given with `--compartment`, and a new one is created only after a yes.
- `vash onboard oci`: optional inventory of compartments, VCNs and subnets (numbered table with owner), delete by S.No or OCID after a dependency check (in-use objects blocked) and a final yes, and pick an existing public subnet from the table.
- Bootstrap: always reinstalls VASH (the version number does not change between fixes, so a plain upgrade kept old code).
- `vash onboard oci`: no hardcoded object names (prefix: default `vash` after a yes, else typed; `<prefix>-runner`, `<prefix>-vcn` ...), existing VMs listed and reusable (install over SSH, never deleted), SSH key chosen by the owner (new `<prefix>-key` on no, never overwritten).
- `vash onboard oci`: VMs can be deleted from the inventory (boot volume deleted, block volumes detached and kept, VM first so its IPs do not block its subnet or VCN, name typed to confirm).
- `vash onboard oci`: compartments that hold resources are emptied with Oracle's compartment cleaner (oci-automation-hub, pinned; dry-run plan, Resource Manager backup, typed DELETE, Cloud Shell sign-in added); the table uses direct listings (no search lag); "Continue with the VASH VM setup now?" after cleanup, and `--cleanup-only`.
- Catalog: UPL-1.0 allowed; vendor-first rule; LAW 3 search record for the OCI tools.
- IaC: network and VM now use Oracle's CD3 Automation Toolkit modules (v2026.2.2); VASH's own network and compute modules are removed. The free-tier database keeps VASH's module (CD3's adb module has no free-tier option).
- `vash onboard oci`: vault for VASH's secrets: existing vaults and keys are listed and picked by S.No, or a free virtual vault and an HSM key are created in a security compartment (default `security`, or a typed name); `--no-vault` skips it.
- `vash onboard oci`: compartments, vaults and keys are created with Oracle's CD3 Automation Toolkit modules (`identity/iam-compartment`, `security/vault`, `security/key`) in the new terraform environment `foundation`, instead of oci CLI create calls; a failed create is not retried later, and OCI's vault limit is explained.
- `vash onboard oci`: when Oracle has no free A1 capacity, it offers to keep trying every 5 minutes for up to 3 hours; e-mail through OCI Notifications (CD3 notification module) when the VM is launched, when VASH is ready and when the setup fails (`--notify-email`).
- Freezing (rule R7): VASH's own `project-stack.json` pins VASH and its 3 agents and 8 skills to the commit of release v3.0.0 (0448d26: v3.0.0 was re-cut to hold every change up to the VM choice and the database) instead of 'to-verify'; `vash init` pins a new project to the commit of the VASH that created it (from pip's record of a git install, or the git checkout); `vash check` (Stage 0) reports any 'to-verify' or other non-commit pin.
- AvA runner: a code artifact is saved without the model's markdown fence (```python ... ```) and any sentence around it, when the answer holds exactly one fenced block; the critic reviews the same cleaned code. Documents keep their markdown.
- GitHub Actions on Node 24: actions/checkout v7.0.1, actions/setup-python v7.1.0 and actions/dependency-review-action v5.0.0 (pinned by commit) in every workflow and in the project CI template; the Node 20 versions were deprecated.
- Live and development versions: the bootstrap installs the newest GitHub release by default, `--version vX.Y.Z` a named one, `--channel dev` main; the VM gets the same VASH. `release.yml` publishes a release from a tag that matches `pyproject.toml`. The VM's Ollama (0.40.16) and GitHub Actions runner (2.338.2, SHA-256 checked) are pinned.
- Three release tracks, live, test and dev: `--channel test` installs the newest release including pre-releases (tags `vX.Y.Z-rc.N`, always published as pre-releases by `release.yml`), the default (`--channel live`, earlier `stable`) the newest full release, `--channel dev` main; an unknown channel stops.
- `vash onboard oci --database` (or `--database-only`, no VM): an Always Free Autonomous Database `<prefix>-db` (mutual TLS) in the project compartment; its admin password is generated, kept only in a vault secret `<prefix>-db-admin-password` and given to terraform through the environment (never in a file or on a command line). A new network goes to its own compartment (`network` by default, `--network-compartment`); a network made earlier stays where it is.
- `vash onboard oci` picks the VM that is free: the asked Arm A1 size first, else a basic A1 (1 core, 6 GB, small model `qwen2.5-coder:1.5b`), else the AMD `VM.Standard.E2.1.Micro` (1 GB, no local model; the free model APIs are used), each after a yes, and also when Oracle has no A1 capacity. `--shape a1|micro` forces one. The VM setup handles Arm and AMD (GitHub runner for either CPU, both checksums pinned).
- `vash onboard oci`: an earlier attempt that made no VM (for example stopped by no A1 capacity) no longer locks the next run to its A1 size: the VM is chosen again, and the network that attempt made is kept.
- `engine-local-model.yml`: runs an AvA activity on a real Ollama model on GitHub's runner (weekly, on demand, and on PRs that touch the engine), so the local-model path is tested without an OCI VM.
- AvA runner: the critic's score is read only from an explicit `SCORE: <0-100>` line (the last one); before, the first number after the word "score" counted, so a critic's 40 could be read as 95 and approved. The critic now gets the task with the checklist and artifact, and is told the score format. Each round's log records the real Gate 1 result and findings, the coder and critic route and model, and says what the engine does not check instead of leaving template placeholders.
- End-to-end test of the engine (`tests/e2e`): `vash init`, `vash check` and `vash ava` through the CLI, with the real OpenAI-compatible adapter talking HTTP to a local stand-in model server.
- PR review pipeline (`.github/workflows/pr-review.yml`): checks without AI that can block a merge (ruff, bandit, pip-audit, detect-secrets with a reviewed baseline, actionlint, GitHub dependency review), then an AI reviewer that posts one comment (`vash.adapters.forge.github.pr_review`): Gemini, when the `GEMINI_API_KEY` secret is set; more reviewers are added as entries of the job's matrix. Advisory unless the repository variable `VASH_REVIEW_FAIL_ON` names severities that fail the check.
- Removed `.github/workflows/vash-audit-sync.yml`: its YAML did not parse, it used unpinned actions, ignored Gate 1 failures and pushed to `main`.
- `vash onboard oci`: free-tier guardrails (`--guardrails-only`, also offered once in setup): a quota policy that allows only the Always Free amounts, with limit names read from the tenancy, and a budget that e-mails at the first spend (CD3 quota-policy, budget and budget-alert-rule modules).
- `vash onboard oci`: the dependency check names who holds each IP (the VM, or the service created with the VNIC), a VM name gets 3 tries, and the table shows progress while it reads.
- Fixed: the owner lookup sends the time in the form OCI Search accepts, and a failed lookup shows "owner unknown" instead of stopping the run.
- `vash onboard oci`: deletes continue after a failure (each failure reported with OCI's own message, stdout included), a VM is terminated and then polled (the CLI's --wait-for-state failed in Cloud Shell), and the IP owner guess only considers services that create VNICs.
- `vash onboard oci`: the inventory covers the whole tenancy (this region): every other resource from Resource Search; such a resource is removed through its compartment with Oracle's cleaner, or in the Console when it is in the root.
- `vash onboard oci`: the inventory covers every subscribed region and every parent or child tenancy the login can reach (Tenancy and Region columns); deletes, dependency checks and the cleaner go to the object's own region; Resource Search and the cleaner stay in the signed-in tenancy.
