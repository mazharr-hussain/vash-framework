#!/bin/bash
# VASH onboarding for OCI Cloud Shell.
#   curl -fsSL https://raw.githubusercontent.com/mazharr-hussain/vash-framework/main/bootstrap/oci-cloudshell.sh | bash -s -- [options]
# Which VASH is installed (here and on the VM it builds):
#   (default)          live: the newest full GitHub release, e.g. v3.1.0
#   --channel test     test: the newest release including pre-releases, e.g. v3.2.0-rc.1
#   --channel dev      dev: whatever is on main now
#   --version v3.0.0   that release exactly (also how to go back to an earlier one)
# Every other option is passed to `vash onboard oci` (for example --runner-repo owner/name, --down, --yes).
set -euo pipefail
REPO="mazharr-hussain/vash-framework"

CHANNEL="live"
VERSION=""
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --channel) CHANNEL="${2:-}"; shift 2 ;;
    --channel=*) CHANNEL="${1#*=}"; shift ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --version=*) VERSION="${1#*=}"; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

if [ -n "${VASH_SOURCE:-}" ]; then
  REF="custom"
elif [ -n "$VERSION" ]; then
  case "$VERSION" in v*) ;; *) VERSION="v$VERSION" ;; esac
  REF="$VERSION"
elif [ "$CHANNEL" = "dev" ]; then
  REF="main"
elif [ "$CHANNEL" = "test" ]; then
  # The releases list is newest first and includes pre-releases (test versions).
  REF=$(curl -fsSL "https://api.github.com/repos/$REPO/releases?per_page=1" 2>/dev/null | tr "," "\n" \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1 || true)
  if [ -z "$REF" ]; then
    echo "No VASH release found (or GitHub could not be reached): installing the development version (main)."
    REF="main"
  fi
elif [ "$CHANNEL" = "live" ] || [ "$CHANNEL" = "stable" ]; then
  REF=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | tr "," "\n" \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1 || true)
  if [ -z "$REF" ]; then
    echo "No VASH release found (or GitHub could not be reached): installing the development version (main)."
    REF="main"
  fi
else
  echo "Unknown --channel '$CHANNEL': use live, test or dev" >&2
  exit 2
fi
export VASH_SOURCE="${VASH_SOURCE:-git+https://github.com/$REPO.git@$REF}"
echo "Installing VASH $REF ($VASH_SOURCE)"

python_ok() {
  "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null
}

PY=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null && python_ok "$candidate"; then
    PY="$candidate"
    break
  fi
done

VENV="$HOME/.vash/venv"
if [ -n "$PY" ]; then
  [ -x "$VENV/bin/vash" ] || "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  # --force-reinstall: the development version keeps the same version number between changes.
  "$VENV/bin/pip" install -q --upgrade --force-reinstall "$VASH_SOURCE"
else
  # No Python 3.11+ here: uv fetches a standalone Python into the home folder (no root needed).
  if ! command -v uv >/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  [ -x "$VENV/bin/vash" ] || uv venv --python 3.12 "$VENV"
  uv pip install -q --python "$VENV/bin/python" --reinstall-package vash "$VASH_SOURCE"
fi

# `vash` on the path in every new shell (Cloud Shell keeps the home folder): added once to ~/.bashrc.
PATH_LINE='export PATH="$HOME/.vash/venv/bin:$PATH"  # added by the VASH setup'
if ! grep -qF "$PATH_LINE" "$HOME/.bashrc" 2>/dev/null; then
  printf '\n%s\n' "$PATH_LINE" >> "$HOME/.bashrc"
  echo "Added VASH to your path: new shells know \`vash\` (in this one: source ~/.bashrc)"
fi

# Run with the terminal as stdin, so the confirmations work under `curl | bash`.
if [ -t 0 ]; then
  exec "$VENV/bin/vash" onboard oci ${ARGS[@]+"${ARGS[@]}"}
else
  exec "$VENV/bin/vash" onboard oci ${ARGS[@]+"${ARGS[@]}"} <"${VASH_TTY:-/dev/tty}"
fi
