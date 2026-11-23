#!/bin/bash
# First-boot install for the VASH runner VM (Ubuntu 24.04; Arm A1 or AMD Micro).
# Rendered by `vash onboard`: @@VASH_SOURCE@@, @@MODEL@@ and @@RUN_USER@@ are filled in before upload.
# Re-running is safe; progress goes to /var/log/vash-onboard.log.
set -euo pipefail
exec >>/var/log/vash-onboard.log 2>&1
echo "== vash onboard start $(date -u +%FT%TZ)"
# A rerun (vash onboard oci --update) starts from "not ready" so nobody reads an old result.
rm -f /var/lib/vash/ready /var/lib/vash/doctor.txt /var/lib/vash/smoke.txt

VASH_SOURCE="@@VASH_SOURCE@@"
# Fixed versions: a new release of a tool never changes this VM by surprise. Update them here, in a PR.
OLLAMA_VERSION="0.40.16"
CONTEXT_LENGTH=16384  # tokens the VM's model reads at once (Ollama's CPU default is 4096)
GATEWAY_VERSION="1.108.3"  # LiteLLM, the model gateway (catalog/llm/litellm.md)
HARNESS_VERSION="2.2.6"  # OpenCode, the chat harness (npm checks the package's checksum)
MCP_VERSION="2.3.0"  # the official MCP Python SDK, for `vash mcp`
KAGGLE_VERSION="2.2.5"  # Kaggle's official client, for free GPU jobs (`vash gpu`)
RUNNER_VERSION="2.338.2"
RUNNER_SHA256_ARM64="670adb2f268fe21dcbb58b3db0e0aa9d5b3bddfe2c651481336e561ff86de945"  # pragma: allowlist secret (published checksum)
RUNNER_SHA256_X64="baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40"  # pragma: allowlist secret (published checksum)
# Empty on a basic VM too small for a local model (the AMD Micro has 1 GB): VASH then uses the free model APIs.
MODEL="@@MODEL@@"
RUN_USER="@@RUN_USER@@"
export DEBIAN_FRONTEND=noninteractive

# A fresh VM runs Ubuntu's own updates at first boot and after a restart; they hold apt's locks (seen live:
# "Could not get lock /var/lib/apt/lists/lock"). Wait for the lock files themselves (not process names: Ubuntu's
# unattended-upgrade-shutdown helper runs all the time), and let apt wait too.
wait_for_apt() {
  for _ in $(seq 1 120); do
    fuser /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock >/dev/null 2>&1 || return 0
    sleep 10
  done
  echo "apt is still locked after 20 minutes; trying anyway"
}
APT=(apt-get -o DPkg::Lock::Timeout=1200 -y)
wait_for_apt
"${APT[@]}" update
"${APT[@]}" install python3 python3-venv python3-pip git curl unzip jq gnupg ca-certificates

# Terraform (HashiCorp apt repository).
# The signing key is fetched on every run, so a removed or outdated key file is repaired (seen live: NO_PUBKEY).
# --batch --yes: a rerun overwrites the key file instead of asking (seen live: "gpg: cannot open '/dev/tty'").
curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --batch --yes --dearmor -o /usr/share/keyrings/hashicorp.gpg
if ! command -v terraform >/dev/null; then
  echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(. /etc/os-release && echo "$VERSION_CODENAME") main" \
    > /etc/apt/sources.list.d/hashicorp.list
  wait_for_apt
  "${APT[@]}" update
  "${APT[@]}" install terraform
fi

# VASH in its own venv, on PATH for every user.
if [ ! -x /opt/vash/bin/vash ]; then
  python3 -m venv /opt/vash
fi
/opt/vash/bin/pip install --upgrade pip
/opt/vash/bin/pip install --upgrade "$VASH_SOURCE"
# The version number stays the same between changes, so pip would keep the old code (seen live: the VM kept a VASH
# without `vash mcp`, `doctor` and `gateway`): reinstall VASH itself every time, its dependencies only when needed.
/opt/vash/bin/pip install --force-reinstall --no-deps "$VASH_SOURCE"
ln -sf /opt/vash/bin/vash /usr/local/bin/vash

# Ollama (local $0 model) and the default model, when the VM has room for one.
if [ -n "$MODEL" ]; then
  if ! command -v ollama >/dev/null; then
    curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION="$OLLAMA_VERSION" sh
  fi
  # A longer context than Ollama's 4k default on a CPU: the web chat sends its instructions and VASH's tool list
  # with every question, and 4k cut them off (seen live: the model answered with a made-up tool call).
  install -d -m 0755 /etc/systemd/system/ollama.service.d
  printf '[Service]\nEnvironment=OLLAMA_CONTEXT_LENGTH=%s\n' "$CONTEXT_LENGTH" \
    > /etc/systemd/system/ollama.service.d/vash.conf
  systemctl daemon-reload
  systemctl enable ollama
  systemctl restart ollama
  for _ in $(seq 1 30); do
    ollama list >/dev/null 2>&1 && break
    sleep 2
  done
  ollama pull "$MODEL"
fi

case "$(uname -m)" in
  aarch64) RUNNER_ARCH=arm64; RUNNER_SHA256="$RUNNER_SHA256_ARM64" ;;
  x86_64) RUNNER_ARCH=x64; RUNNER_SHA256="$RUNNER_SHA256_X64" ;;
  *) echo "Unsupported CPU $(uname -m)"; exit 1 ;;
esac

# GitHub Actions runner files (registration is done later over SSH, the token never lands on disk here).
RUNNER_DIR=/home/$RUN_USER/actions-runner
if [ ! -x "$RUNNER_DIR/config.sh" ]; then
  mkdir -p "$RUNNER_DIR"
  curl -fsSL -o /tmp/actions-runner.tar.gz \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
  echo "$RUNNER_SHA256  /tmp/actions-runner.tar.gz" | sha256sum -c -
  tar -xzf /tmp/actions-runner.tar.gz -C "$RUNNER_DIR"
  rm -f /tmp/actions-runner.tar.gz
  wait_for_apt
  "$RUNNER_DIR/bin/installdependencies.sh"
  chown -R "$RUN_USER:$RUN_USER" "$RUNNER_DIR"
fi

# The model gateway (LiteLLM) on 127.0.0.1:4000: one address, a model per kind of work, fallbacks to the next model
# and finally to this VM's model. Its own key is made here once; provider keys come later with
# `vash onboard oci --keys` (kept in the vault and in /etc/vash/gateway.env, readable by root only).
if [ ! -x /opt/vash-gateway/bin/litellm ]; then
  python3 -m venv /opt/vash-gateway
fi
/opt/vash-gateway/bin/pip install --upgrade pip
/opt/vash-gateway/bin/pip install "litellm[proxy]==$GATEWAY_VERSION"
install -d -m 0755 /etc/vash
[ -f /etc/vash/gateway.env ] || install -m 0600 /dev/null /etc/vash/gateway.env
if [ ! -s /etc/vash/gateway-key ]; then
  echo "sk-vash-$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 32)" > /etc/vash/gateway-key
fi
chown "root:$RUN_USER" /etc/vash/gateway-key && chmod 0640 /etc/vash/gateway-key
# No model yet (an AMD Micro before any provider key): the gateway starts once keys are added.
GATEWAY_READY=1
vash gateway config --out /etc/vash/gateway.yaml --env /etc/vash/gateway.env --vm-model "$MODEL" || GATEWAY_READY=0
cat > /etc/systemd/system/vash-gateway.service <<UNIT
[Unit]
Description=VASH model gateway (LiteLLM)
After=network-online.target ollama.service
[Service]
User=$RUN_USER
EnvironmentFile=/etc/vash/gateway.env
ExecStart=/bin/bash -c 'VASH_GATEWAY_KEY=\$\$(cat /etc/vash/gateway-key) exec /opt/vash-gateway/bin/litellm --config /etc/vash/gateway.yaml --host 127.0.0.1 --port 4000'
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
if [ "$GATEWAY_READY" = 1 ]; then
  systemctl enable vash-gateway
  systemctl restart vash-gateway
  for _ in $(seq 1 60); do
    curl -fsS -o /dev/null http://127.0.0.1:4000/health/liveliness && break
    sleep 3
  done
fi

# The chat harness (OpenCode) and VASH's tools for it (`vash mcp`). OpenCode's settings are machine-wide
# (/etc/opencode, written by VASH, above any user setting): it thinks with the model gateway (the VM's model until
# provider keys are added) and drives VASH through MCP. `vash-chat` starts it in ~/projects.
/opt/vash/bin/pip install "mcp==$MCP_VERSION" "kaggle==$KAGGLE_VERSION" six
wait_for_apt
"${APT[@]}" install nodejs npm
npm install -g "@opencode/cli@$HARNESS_VERSION"
install -d -m 0755 /etc/opencode
cat > /etc/opencode/opencode.json <<'JSON'
{
  "$schema": "https://opencode.ai/config.json",
  "providers": {
    "vash": {
      "name": "VASH model gateway",
      "env": ["VASH_GATEWAY_KEY"],
      "package": "@opencode/ai/providers/openai-compatible",
      "settings": {"baseURL": "http://127.0.0.1:4000/v1", "apiKey": "{file:/etc/vash/gateway-key}"},
      "models": {
        "vash-coding": {"name": "VASH coding"},
        "vash-docs": {"name": "VASH documents"},
        "vash-prompt": {"name": "VASH prompts"},
        "vash-test": {"name": "VASH tests"},
        "vash-review": {"name": "VASH review"},
        "vash-local": {"name": "VASH: the VM's own model (Ollama)"}
      }
    }
  },
  "model": "vash/vash-coding",
  "mcp": {
    "timeout": {"execution": 600000},
    "servers": {"vash": {"type": "local", "command": ["/usr/local/bin/vash", "mcp"]}}
  }
}
JSON
PROJECTS="/home/$RUN_USER/projects"
install -d -o "$RUN_USER" -g "$RUN_USER" "$PROJECTS"
cat > "$PROJECTS/AGENTS.md" <<'MD'
# VASH front desk

You talk with the owner of VASH, a virtual software house. You do not write the deliverables yourself:
VASH's own agents write, check (Gate 1) and review them (AvA). Use the `vash` tools:

1. `list_projects`, or `new_project` for a new piece of work.
2. `new_task`: a short task id, the kind of work (code, test, artifact for documents, feature, prompt) and a
   clear request that says what the result must contain.
3. `run_task`, then `task_status` until it is finished, then `read_result` to show the owner the result.
4. `doctor` when something does not work.
MD
chown "$RUN_USER:$RUN_USER" "$PROJECTS/AGENTS.md"
cat > /usr/local/bin/vash-chat <<'SH'
#!/bin/bash
# Chat with VASH: OpenCode in ~/projects, thinking with the model gateway, VASH's tools attached.
export VASH_GATEWAY_KEY="$(cat /etc/vash/gateway-key 2>/dev/null)"
cd "$HOME/projects" && exec opencode "$@"
SH
chmod 0755 /usr/local/bin/vash-chat

mkdir -p /var/lib/vash
{
  echo "vash=$(vash --version) from $VASH_SOURCE"
  echo "terraform=$(terraform version | head -1)"
  echo "gateway=litellm $GATEWAY_VERSION $(systemctl is-active vash-gateway)"
  echo "harness=$(opencode --version 2>/dev/null | head -1) (start it with: vash-chat)"
  if [ -n "$MODEL" ]; then
    echo "ollama=$(ollama --version 2>&1 | tail -1)"
    echo "model=$MODEL"
    echo "context=$CONTEXT_LENGTH tokens"
  else
    echo "model=none (basic VM: VASH uses the free model APIs)"
  fi
} > /var/lib/vash/ready
echo "== vash onboard done $(date -u +%FT%TZ)"

# Check that VASH works here, with nothing done by hand: a small test project set to this VM's model, the health
# check in it, then one real AvA task. Results: /var/lib/vash/doctor.txt and /var/lib/vash/smoke.txt
# (`vash onboard oci --status` shows them). A failure here is reported, it does not undo the install.
set +e
SMOKE="/home/$RUN_USER/projects/vash-smoke"
rm -rf "$SMOKE"
sudo -u "$RUN_USER" -H bash -c "
  set -e
  mkdir -p '$(dirname "$SMOKE")' && cd '$(dirname "$SMOKE")'
  vash init vash-smoke >/dev/null
  cd vash-smoke
  # The test uses the model this VM pulled (a basic VM has a smaller one than the default).
  [ -z '$MODEL' ] || python3 - <<'PY'
import json
p = 'project-stack.json'
d = json.load(open(p))
for r in d['models']['routes'].values():
    if r['adapter'] == 'ollama':
        r['model'] = '$MODEL'
json.dump(d, open(p, 'w'), indent=2)
PY
" > /var/lib/vash/smoke.txt 2>&1
sudo -u "$RUN_USER" -H vash doctor --repo "$SMOKE" > /var/lib/vash/doctor.txt 2>&1
echo "exit=$?" >> /var/lib/vash/doctor.txt
if [ -n "$MODEL" ]; then
  sudo -u "$RUN_USER" -H bash -c "
    cd '$SMOKE'
    printf '%s\\n' 'type: code' \\
      'Write a Python function is_valid_iban(iban: str) -> bool that checks the IBAN checksum (mod 97).' \\
      'Include three doctest examples.' > audit/prompts/T1_prompt.md
    timeout 3600 vash ava T1
  " >> /var/lib/vash/smoke.txt 2>&1
  code=$?
  {
    echo "exit=$code"
    grep -hE '^\*\*(SCORE|VERDICT)|ROUTE:' "$SMOKE"/audit/ava_logs/*.md 2>/dev/null | tail -n 12
  } >> /var/lib/vash/smoke.txt
  echo "== vash smoke test done (exit $code) $(date -u +%FT%TZ)"
else
  echo "skipped: no model on this VM (it uses the free model APIs)" >> /var/lib/vash/smoke.txt
fi
