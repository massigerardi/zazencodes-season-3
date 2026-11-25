#!/usr/bin/env bash
# Copy the factory into a project. Run from this folder.
#
#   ./install.sh <project>              for Claude Code (.claude/)
#   ./install.sh --opencode <project>   for OpenCode (.opencode/)
OPENCODE=
if [ "$1" = "--opencode" ]; then
  OPENCODE=1
  shift
fi
TARGET=${1:?usage: ./install.sh [--opencode] <project>}
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

cp -R "./factory" "$TARGET"
cd "$TARGET" || exit 1
echo "/factory/jobs/" >> .gitignore

for file in "${FILES[@]}"; do
  mkdir -p "$(dirname "$file")"
  cp "$F/$file" "$file"
done

if [ -n "$OPENCODE" ]; then
  CONFIG=.opencode/opencode.json
  if [ ! -e "$CONFIG" ]; then
    cp "$F/$CONFIG" "$CONFIG"
  elif ! cmp -s "$F/$CONFIG" "$CONFIG"; then
    echo "$CONFIG already exists. Add these permission entries to it:"
    cat "$F/$CONFIG"
  fi
fi
echo "Installed the factory. Nothing is committed."
