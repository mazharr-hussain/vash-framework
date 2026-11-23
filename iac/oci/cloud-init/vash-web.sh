#!/bin/bash
# The VASH web chat on the VM (run by `vash onboard oci --web`, after the VASH install): Open WebUI on 127.0.0.1,
# thinking with the model gateway and using VASH's tools (`vash mcp --http`), published by a Cloudflare Tunnel
# behind a Cloudflare Access login. Nothing listens on a public port: cloudflared connects out.
# Rendered by `vash onboard`: @@RUN_USER@@ and @@WEB_URL@@ are filled in before upload. The tunnel's connector
# token is not in this file: it arrives separately in /etc/vash/tunnel-token (root only).
# Re-running is safe; progress goes to /var/log/vash-web.log.
set -euo pipefail
exec >>/var/log/vash-web.log 2>&1
echo "== vash web start $(date -u +%FT%TZ)"
rm -f /var/lib/vash/web-ready

# Fixed versions (at least two weeks old); update them here, in a PR.
WEBUI_VERSION="0.13.3"  # Open WebUI (8 Nov 2026), Open WebUI License (BSD-3 with a branding clause)
WEBUI_SHA256="6b20b33fa485b6b64c55577f2e0186515d53a922bd39e1bab5dadcbe1c9a4cc1"  # pragma: allowlist secret (PyPI checksum of the wheel)
CONNECTOR_VERSION="2026.11.0"  # cloudflared (12 Nov 2026), Apache-2.0, the release's .deb from GitHub
# Checksums of the release's .deb files (computed from the GitHub release downloads on 23 Nov 2026). Cloudflare's
# apt repository keeps only its newest version, so it cannot hold a fixed version.
CONNECTOR_SHA256_ARM64="ce671bc2b4afbd16b43f9a3c279527e9e2be8b30b87648047a1f95cccfbacdfd"  # pragma: allowlist secret (checksum)
CONNECTOR_SHA256_X64="5305dbaf62984e92e7daa29cdd6a35a4797edc23385d4c5b8422ff97eb96a19b"  # pragma: allowlist secret (checksum)
RUN_USER="@@RUN_USER@@"
WEB_URL="@@WEB_URL@@"
MCP_PORT=8765
WEB_PORT=8080
export DEBIAN_FRONTEND=noninteractive
APT=(apt-get -o DPkg::Lock::Timeout=1200 -y)

[ -s /etc/vash/tunnel-token ] || { echo "no tunnel token in /etc/vash/tunnel-token"; exit 1; }
[ -x /opt/vash/bin/vash ] || { echo "VASH is not installed: run vash onboard oci --update first"; exit 1; }

# 1. VASH's tools over HTTP for the web page (127.0.0.1 only).
cat > /etc/systemd/system/vash-mcp.service <<UNIT
[Unit]
Description=VASH tools for the web chat (MCP over HTTP, 127.0.0.1)
After=network-online.target
[Service]
User=$RUN_USER
WorkingDirectory=/home/$RUN_USER/projects
Environment=VASH_PROJECTS=/home/$RUN_USER/projects
ExecStart=/usr/local/bin/vash mcp --http --port $MCP_PORT
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target
UNIT

# 2. Open WebUI in its own venv; the wheel is checked against its published checksum before it is installed.
if [ ! -x /opt/vash-web/bin/pip ]; then
  python3 -m venv /opt/vash-web
fi
/opt/vash-web/bin/pip install --upgrade pip
WHEEL_DIR=$(mktemp -d)
/opt/vash-web/bin/pip download --no-deps --dest "$WHEEL_DIR" "open-webui==$WEBUI_VERSION"
WHEEL="$WHEEL_DIR/open_webui-$WEBUI_VERSION-py3-none-any.whl"
echo "$WEBUI_SHA256  $WHEEL" | sha256sum -c -
/opt/vash-web/bin/pip install "$WHEEL"
rm -rf "$WHEEL_DIR"
install -d -o "$RUN_USER" -g "$RUN_USER" -m 0700 /var/lib/vash-web
if [ ! -s /etc/vash/web-secret ]; then
  head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' > /etc/vash/web-secret
fi
chown "root:$RUN_USER" /etc/vash/web-secret && chmod 0640 /etc/vash/web-secret
# VASH's tools as an MCP tool server (Open WebUI's TOOL_SERVER_CONNECTIONS format).
TOOLS='[{"type":"mcp","url":"http://127.0.0.1:'$MCP_PORT'/mcp","path":"","auth_type":"none","key":"","config":{"enable":true},"info":{"id":"vash","name":"VASH","description":"Projects, tasks and AvA runs of VASH"}}]'
cat > /etc/vash/web.env <<ENV
DATA_DIR=/var/lib/vash-web
WEBUI_URL=$WEB_URL
WEBUI_NAME=VASH
OPENAI_API_BASE_URL=http://127.0.0.1:4000/v1
ENABLE_OLLAMA_API=false
ENABLE_PERSISTENT_CONFIG=false
WEBUI_AUTH_TRUSTED_EMAIL_HEADER=Cf-Access-Authenticated-User-Email
ENABLE_SIGNUP=false
DEFAULT_USER_ROLE=user
DEFAULT_MODELS=vash-coding
ENABLE_TOOL_SERVERS=true
TOOL_SERVER_CONNECTIONS=$TOOLS
ANONYMIZED_TELEMETRY=false
SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ENV
chmod 0644 /etc/vash/web.env
# The login is Cloudflare Access: the first allowed e-mail that opens the page becomes the page's admin, the others
# are users; nobody can sign up with a password. Only 127.0.0.1 is served, so only the tunnel reaches it.
cat > /etc/systemd/system/vash-web.service <<UNIT
[Unit]
Description=VASH web chat (Open WebUI, 127.0.0.1)
After=network-online.target vash-gateway.service vash-mcp.service
[Service]
User=$RUN_USER
EnvironmentFile=/etc/vash/web.env
ExecStart=/bin/bash -c 'OPENAI_API_KEY=\$\$(cat /etc/vash/gateway-key) WEBUI_SECRET_KEY=\$\$(cat /etc/vash/web-secret) exec /opt/vash-web/bin/open-webui serve --host 127.0.0.1 --port $WEB_PORT'
Restart=on-failure
RestartSec=15
[Install]
WantedBy=multi-user.target
UNIT

# 3. cloudflared at the fixed version, checked against its checksum before it is installed.
if [ "$(cloudflared --version 2>/dev/null | awk '{print $3}')" != "$CONNECTOR_VERSION" ]; then
  case "$(uname -m)" in
    aarch64) ARCH=arm64; SUM="$CONNECTOR_SHA256_ARM64" ;;
    *) ARCH=amd64; SUM="$CONNECTOR_SHA256_X64" ;;
  esac
  DEB="/tmp/cloudflared-$CONNECTOR_VERSION-$ARCH.deb"
  curl -fsSL -o "$DEB" "https://github.com/cloudflare/cloudflared/releases/download/$CONNECTOR_VERSION/cloudflared-linux-$ARCH.deb"
  echo "$SUM  $DEB" | sha256sum -c -
  "${APT[@]}" install --allow-downgrades "$DEB"
  rm -f "$DEB"
fi
# The connector runs as a service with the token from its own root-only file (never on a command line).
cat > /etc/systemd/system/vash-tunnel.service <<'UNIT'
[Unit]
Description=VASH tunnel (cloudflared, connects out; no port is opened)
After=network-online.target vash-web.service
Wants=network-online.target
[Service]
ExecStart=/usr/bin/cloudflared --no-autoupdate tunnel run --token-file /etc/vash/tunnel-token
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
for unit in vash-mcp vash-web vash-tunnel; do
  systemctl enable "$unit"
  systemctl restart "$unit"
done
# Open WebUI's first start downloads its small models and sets up its database (a few minutes).
for _ in $(seq 1 120); do
  curl -fsS -o /dev/null "http://127.0.0.1:$WEB_PORT/health" && break
  sleep 5
done
{
  echo "web=open-webui $WEBUI_VERSION $(systemctl is-active vash-web) at $WEB_URL"
  echo "tools=vash mcp --http $(systemctl is-active vash-mcp)"
  echo "tunnel=$(cloudflared --version 2>&1 | head -1) $(systemctl is-active vash-tunnel)"
} > /var/lib/vash/web-ready
echo "== vash web done $(date -u +%FT%TZ)"
