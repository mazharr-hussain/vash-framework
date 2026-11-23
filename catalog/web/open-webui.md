---
id: open-webui
type: tool
source: https://github.com/open-webui/open-webui
fork: null
licence: Open WebUI License (BSD-3-Clause with a branding clause)
use: run
version: 0.13.3
commit: to-verify
stacks: []
search_log: search-log.md
status: candidate
---
# Open WebUI

The web chat on the VM (127.0.0.1 only, published by the tunnel): it thinks with the model gateway (`vash-coding`
by default, every `vash-<kind>` alias listed) and uses VASH's tools through `vash mcp --http` (an MCP tool server).
The login is the tunnel's e-mail login (trusted header); password sign-up is off. Installed by `vash-web.sh` from
PyPI, the wheel checked against its checksum. Licence: BSD-3 with a clause that keeps the Open WebUI branding (it
can only be removed under 50 users or with a licence); VASH does not change the branding.
