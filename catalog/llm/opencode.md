---
id: opencode
type: tool
source: https://github.com/anomalyco/opencode
fork: null
licence: MIT
use: run
version: 2.2.6
commit: to-verify
stacks: []
search_log: search-log.md
status: candidate
---
# OpenCode

The chat harness on the VM: the owner talks to VASH here. Installed by the VM setup from npm (`@opencode/cli`,
pinned, checksum checked by npm), with machine-wide settings in /etc/opencode written by VASH: the model gateway as
its provider and `vash mcp` as its tools. Started with `vash-chat` on the VM or `vash onboard oci --chat`.
