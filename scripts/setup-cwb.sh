#!/usr/bin/env bash
# Install IMS Open Corpus Workbench (CWB) on macOS via Homebrew and set up a
# default registry + data directory.

set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "Error: Homebrew is required. https://brew.sh" >&2
  exit 1
fi

if ! command -v cwb-encode >/dev/null 2>&1; then
  echo "Installing CWB via Homebrew ..."
  brew install cwb 2>/dev/null || brew install --cask cwb 2>/dev/null || {
    echo "brew install cwb failed. Try a custom tap:" >&2
    echo "  brew tap cwb/cwb && brew install cwb" >&2
    exit 1
  }
else
  echo "CWB already installed: $(which cwb-encode)"
fi

# Set up default registry and data directories
registry_dir="$HOME/.local/share/cwb/registry"
data_dir="$HOME/.local/share/cwb/data"
mkdir -p "$registry_dir" "$data_dir"

echo "Registry: $registry_dir"
echo "Data:     $data_dir"

# Suggest a shell rc entry
cat <<EOF

To make CWB use these directories by default, add to ~/.zshrc:
  export CORPUS_REGISTRY="$registry_dir"

Verify with:
  cwb-encode --help | head -5
  cwb-describe-corpus --help | head -5
  cqp -h
EOF
