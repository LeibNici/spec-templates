#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostToolUse hook: enforce backend/frontend code-smell rules on every Edit/Write.

Wires the L1 layer of the three-layer guard:
    L1  Claude Code PostToolUse        (this file)
    L2  Git pre-commit                 (.githooks/pre-commit)
    L3  CI                             (project-specific yaml)

All three call into the same authoritative checker:
    .trellis/scripts/code_smell_guard.py

Exit-code mapping for Claude Code:
    0  silent (file ok or not a code file the guard handles)
    2  blocking — violation found; Claude must fix before continuing
    non-zero other  — non-blocking warning; Claude sees the message
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GUARD = REPO_ROOT / ".trellis" / "scripts" / "code_smell_guard.py"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return 0

    # code_smell_guard handles "is this a file I check?" itself.
    result = subprocess.run(
        ["python3", str(GUARD), file_path],
        capture_output=True,
        text=True,
    )

    rc = result.returncode

    if rc == 0:
        return 0  # silent: file fine or not a checked file

    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")
    if result.stdout:
        sys.stderr.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stderr.write("\n")

    if rc == 1:
        sys.stderr.write(
            "Action required: fix the code-smell violation before any further edits "
            "(see .trellis/spec/backend/code-smell-prevention/_index.md).\n"
        )
        return 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
