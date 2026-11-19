#!/bin/bash
# First-boot install for the VASH runner VM (Ubuntu 24.04; Arm A1 or AMD Micro).
# Rendered by `vash onboard`: @@VASH_SOURCE@@, @@MODEL@@ and @@RUN_USER@@ are filled in before upload.
# Re-running is safe; progress goes to /var/log/vash-onboard.log.
set -euo pipefail
exec >>/var/log/vash-onboard.log 2>&1
echo "== vash onboard start $(date -u +%FT%TZ)"

VASH_SOURCE="@@VASH_SOURCE@@"
# Fixed versions: a new release of a tool never changes this VM by surprise. Update them here, in a PR.
OLLAMA_VERSION="0.40.16"
RUNNER_VERSION="2.338.2"
RUNNER_SHA256_ARM64="670adb2f268fe21dcbb58b3db0e0aa9d5b3bddfe2c651481336e561ff86de945"  # pragma: allowlist secret (published checksum)
RUNNER_SHA256_X64="baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40"  # pragma: allowlist secret (published checksum)
# Empty on a basic VM too small for a local model (the AMD Micro has 1 GB): VASH then uses the free model APIs.
MODEL="@@MODEL@@"
RUN_USER="@@RUN_USER@@"
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl unzip jq gnupg ca-certificates

# Terraform (HashiCorp apt repository).
if ! command -v terraform >/dev/null; then
  curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg
  echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(. /etc/os-release && echo "$VERSION_CODENAME") main" \
    > /etc/apt/sources.list.d/hashicorp.list
  apt-get update -y
  apt-get install -y terraform
fi

# VASH in its own venv, on PATH for every user.
if [ ! -x /opt/vash/bin/vash ]; then
  python3 -m venv /opt/vash
fi
/opt/vash/bin/pip install --upgrade pip
/opt/vash/bin/pip install --upgrade "$VASH_SOURCE"
ln -sf /opt/vash/bin/vash /usr/local/bin/vash

# Ollama (local $0 model) and the default model, when the VM has room for one.
if [ -n "$MODEL" ]; then
  if ! command -v ollama >/dev/null; then
    curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION="$OLLAMA_VERSION" sh
  fi
  systemctl enable --now ollama
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
  "$RUNNER_DIR/bin/installdependencies.sh"
  chown -R "$RUN_USER:$RUN_USER" "$RUNNER_DIR"
fi

mkdir -p /var/lib/vash
{
  echo "vash=$(vash --version) from $VASH_SOURCE"
  echo "terraform=$(terraform version | head -1)"
  if [ -n "$MODEL" ]; then
    echo "ollama=$(ollama --version 2>&1 | tail -1)"
    echo "model=$MODEL"
  else
    echo "model=none (basic VM: VASH uses the free model APIs)"
  fi
} > /var/lib/vash/ready
echo "== vash onboard done $(date -u +%FT%TZ)"
