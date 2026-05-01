#!/usr/bin/env sh
# claude-codex-dispatch installer
# Usage: curl -fsSL https://raw.githubusercontent.com/fredchu/claude-codex-dispatch/main/install.sh | sh

set -e

REPO="https://github.com/fredchu/claude-codex-dispatch.git"
SKILL_NAME="claude-codex-dispatch"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
TARGET="$SKILLS_DIR/$SKILL_NAME"

printf "\n📦 Installing %s\n" "$SKILL_NAME"
printf "   Target: %s\n\n" "$TARGET"

check_dep() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "⚠️  %s not found in PATH. %s\n" "$1" "$2"
    return 1
  fi
}

DEPS_OK=1
check_dep codex   "Install: https://github.com/openai/codex" || DEPS_OK=0
check_dep python3 "Required for the dispatch wrapper."         || DEPS_OK=0
check_dep git     "Required to clone the repo."                || { echo "❌ git is required, aborting."; exit 1; }

if [ ! -d "$SKILLS_DIR" ]; then
  printf "📁 Creating %s\n" "$SKILLS_DIR"
  mkdir -p "$SKILLS_DIR"
fi

if [ -d "$TARGET" ]; then
  printf "ℹ️  Already installed at %s\n" "$TARGET"
  printf "   To update: cd %s && git pull\n\n" "$TARGET"
  exit 0
fi

printf "⬇️  Cloning %s\n" "$REPO"
git clone --depth 1 "$REPO" "$TARGET"

printf "\n🔍 Smoke test:\n"
if "$TARGET/bin/codex-dispatch" --help >/dev/null 2>&1; then
  printf "   ✅ Launcher runs.\n"
else
  printf "   ⚠️  Launcher failed --help; inspect %s\n" "$TARGET"
fi

printf "\n✅ Installed %s\n" "$SKILL_NAME"
printf "\nNext steps:\n"
printf "  1. Restart Claude Code (or run /reload-plugins) to pick up the skill\n"
printf "  2. Read the SKILL.md for the contract:\n"
printf "     %s/SKILL.md\n" "$TARGET"
printf "  3. Try the worker example:\n"
printf "     cat %s/examples/worker.md\n\n" "$TARGET"

if [ "$DEPS_OK" -eq 0 ]; then
  printf "⚠️  Some optional deps missing — install them before first dispatch.\n\n"
fi
