#!/usr/bin/env bash
# install.sh — install custom Trellis guards / hooks into a target project.
#
# What this does (idempotent):
#   1) Copy custom Python guards into <target>/.trellis/scripts/
#       - code_smell_guard.py
#       - spec_threshold_guard.py
#   2) Copy custom Claude Code hooks into <target>/.claude/hooks/
#       - code-smell-check.py
#       - spec-threshold-check.py
#       - inject-subagent-context.py
#       - statusline.py
#   3) Copy git pre-commit hook into <target>/.githooks/
#   4) Copy checkstyle.xml into <target>/ (project root, where Maven expects it)
#   5) Copy .editorconfig into <target>/  (cross-IDE format unification)
#   6) Copy CLAUDE.md into <target>/      (Claude Code project rules; paired with PLACEHOLDERS.md)
#
# What this does NOT do:
#   - Touch <target>/.trellis/spec/        (use `trellis init --registry ...` instead)
#   - Modify <target>/.claude/settings.json (you must wire hooks yourself; see README)
#   - Overwrite checkstyle.xml / .editorconfig / CLAUDE.md if they already exist (skips with warning)
#   - Touch AGENTS.md (managed by `trellis init` / `trellis update`, not by us)
#
# Usage:
#   ./tools/install.sh                       # install into current directory
#   ./tools/install.sh /path/to/target       # install into target directory
#   curl -sSL https://raw.githubusercontent.com/LeibNici/spec-templates/main/tools/install.sh | bash -s -- /path/to/target

set -euo pipefail

TARGET="${1:-$(pwd)}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "$TARGET" ]]; then
  echo "[install.sh] target directory not found: $TARGET" >&2
  exit 1
fi

echo "[install.sh] target = $TARGET"
echo "[install.sh] source = $SOURCE_DIR"

mkdir -p "$TARGET/.trellis/scripts"
mkdir -p "$TARGET/.claude/hooks"
mkdir -p "$TARGET/.githooks"

cp -v "$SOURCE_DIR/code_smell_guard.py"      "$TARGET/.trellis/scripts/"
cp -v "$SOURCE_DIR/spec_threshold_guard.py"  "$TARGET/.trellis/scripts/"

cp -v "$SOURCE_DIR/.claude-hooks/code-smell-check.py"        "$TARGET/.claude/hooks/"
cp -v "$SOURCE_DIR/.claude-hooks/spec-threshold-check.py"    "$TARGET/.claude/hooks/"
cp -v "$SOURCE_DIR/.claude-hooks/inject-subagent-context.py" "$TARGET/.claude/hooks/"
cp -v "$SOURCE_DIR/.claude-hooks/statusline.py"              "$TARGET/.claude/hooks/"

cp -v "$SOURCE_DIR/.githooks/pre-commit" "$TARGET/.githooks/"
chmod +x "$TARGET/.githooks/pre-commit"

copy_if_absent() {
  local src="$1" dst="$2"
  if [[ -e "$dst" ]]; then
    echo "[install.sh] WARN: $dst already exists — keeping yours, not overwriting."
  else
    cp -v "$src" "$dst"
  fi
}

copy_if_absent "$SOURCE_DIR/checkstyle.xml"  "$TARGET/checkstyle.xml"
copy_if_absent "$SOURCE_DIR/.editorconfig"   "$TARGET/.editorconfig"
copy_if_absent "$SOURCE_DIR/CLAUDE.md"       "$TARGET/CLAUDE.md"

echo
echo "[install.sh] done. Next steps:"
echo "  1) Wire the Claude hooks in $TARGET/.claude/settings.json (see README §Tools)."
echo "  2) Activate git hooks:  git -C $TARGET config core.hooksPath .githooks"
echo "  3) Wire checkstyle in your Maven pom.xml (maven-checkstyle-plugin → configLocation=checkstyle.xml)."
echo "  4) Search & replace placeholders in CLAUDE.md per marketplace/specs/default/PLACEHOLDERS.md."
