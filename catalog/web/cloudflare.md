---
id: cloudflare
type: tool
source: https://github.com/cloudflare/cloudflared
fork: null
licence: Apache-2.0
use: run
version: 2026.11.0
commit: to-verify
stacks: []
search_log: search-log.md
status: candidate
---
# Cloudflare Tunnel and Access (Zero Trust Free)

The VM's web chat at the owner's own address, behind an e-mail login (a one-time code is e-mailed), with no port
opened on the VM: `cloudflared` (Apache-2.0, the release's .deb, checksum checked) connects out. The tunnel, its
route, the DNS name and the login are made through Cloudflare's API by `vash onboard oci --web` (adapter
`web/cloudflare`), with one API token the owner makes once (Zone DNS Edit, Cloudflare Tunnel Edit, Access: Apps
and Policies Edit), kept in the vault. Free plan: up to 50 Zero Trust users; the service itself is not open source.
