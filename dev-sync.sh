#!/usr/bin/env bash

set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="/mnt/d/dev/ComfyUI/custom_nodes/comfyui-lumi-tools"

RSYNC_ARGS=(
  -az
  --delete
  --exclude ".git/"
  --exclude ".venv/"
  --exclude ".ruff_cache/"
  --exclude "__pycache__/"
  --exclude "tmp/"
  --exclude "wildcards/"
  --exclude "*.pyc"
)

EXCLUDE_REGEX='/(\.git|\.venv|\.ruff_cache|__pycache__|tmp|wildcards)(/|$)'

sync_once() {
  mkdir -p "$TARGET_DIR"
  rsync "${RSYNC_ARGS[@]}" "$SOURCE_DIR/" "$TARGET_DIR/"
  printf '[%s] Synced to %s\n' "$(date '+%H:%M:%S')" "$TARGET_DIR"
}

if ! command -v inotifywait >/dev/null 2>&1; then
  echo "Missing dependency: inotifywait (install inotify-tools)"
  exit 1
fi

echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"

sync_once

echo "Watching for changes..."
while inotifywait -q -r \
  -e modify,create,delete,move,attrib \
  --exclude "$EXCLUDE_REGEX" \
  "$SOURCE_DIR"; do
  sync_once
done
