#!/usr/bin/env bash
# Install the Decision Profile skills into Claude Code's user skills directory.
# Copies the three skills (me, me-add, me-ask) into ~/.claude/skills/.
# Never touches your existing profiles/ data.
set -euo pipefail

DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SRC="$(cd "$(dirname "$0")/skills" && pwd)"

mkdir -p "$DEST"
for s in me me-add me-ask; do
  echo "Installing $s → $DEST/$s"
  # --ignore-existing on profiles keeps any local data intact.
  rsync -a --exclude='*.dpf.json' --exclude='*.report.md' \
        --exclude='__pycache__' --exclude='*.pyc' \
        "$SRC/$s/" "$DEST/$s/"
done

echo
echo "Done. Restart Claude Code (or /reload) and try:  /me-add <name> <lang>"
