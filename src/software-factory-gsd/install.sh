#!/usr/bin/env bash
# Copy the factory into a project.
#
#   ./install.sh <project>              for Claude Code (.claude/)
#   ./install.sh --opencode <project>   for OpenCode (.opencode/)
#
# Safe to run again: it updates the factory's scripts and dashboard, and keeps
# the project's factory/backlog.md.
set -euo pipefail

OPENCODE=
if [ "${1:-}" = "--opencode" ]; then
  OPENCODE=1
  shift
fi
TARGET=${1:?usage: ./install.sh [--opencode] <project>}
if [ ! -d "$TARGET" ]; then
  echo "$TARGET is not a folder. Nothing was copied." >&2
  exit 1
fi
TARGET=$(cd "$TARGET" && pwd)
cd "$(dirname "$0")"          # the sources sit beside this script
F=$(pwd)
echo "$F => $TARGET"

if [ -n "$OPENCODE" ]; then
  FILES=(.opencode/commands/factory.md .opencode/agents/*.md)
else
  FILES=(.claude/skills/factory/SKILL.md .claude/agents/*.md)
fi

# Check before copying anything, so a clash leaves the project untouched.
for file in "${FILES[@]}"; do
  if [ -e "$TARGET/$file" ] && ! cmp -s "$file" "$TARGET/$file"; then
    echo "$TARGET/$file already exists and differs. Nothing was copied." >&2
    exit 1
  fi
done

# Named one by one, so local jobs and stray files stay behind.
FILES+=(factory/bin/gsd factory/bin/dashboard factory/dashboard.html)
# The backlog is the project's queue: only create it.
[ -e "$TARGET/factory/backlog.md" ] || FILES+=(factory/backlog.md)

for file in "${FILES[@]}"; do
  mkdir -p "$TARGET/$(dirname "$file")"
  cp "$file" "$TARGET/$file"
done

IGNORE="$TARGET/.gitignore"
if ! grep -qxF "/factory/jobs/" "$IGNORE" 2>/dev/null; then
  # Don't glue the entry to a last line that has no newline.
  if [ -s "$IGNORE" ] && [ -n "$(tail -c 1 "$IGNORE")" ]; then
    echo >> "$IGNORE"
  fi
  echo "/factory/jobs/" >> "$IGNORE"
fi

if [ -n "$OPENCODE" ]; then
  CONFIG=.opencode/opencode.json
  if [ ! -e "$TARGET/$CONFIG" ]; then
    cp "$CONFIG" "$TARGET/$CONFIG"
  elif ! cmp -s "$CONFIG" "$TARGET/$CONFIG"; then
    echo "$CONFIG already exists. Add these permission entries to it:"
    cat "$CONFIG"
  fi
fi
echo "Installed the factory. Nothing is committed."
