#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostToolUse hook: enforce spec defragmentation contract on every Edit/Write.

Wires the L1 layer of the three-layer guard:
    L1  Claude Code PostToolUse        (this file)
    L2  Git pre-commit                 (.githooks/pre-commit)
    L3  CI                             (project-specific yaml)

All three call into the same authoritative checker:
    .trellis/scripts/spec_threshold_guard.py

Exit-code mapping for Claude Code:
    0  silent (file ok or not a spec file)
    2  blocking — violation found; Claude must split before continuing
    non-zero other  — non-blocking warning; Claude sees the message
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GUARD = REPO_ROOT / ".trellis" / "scripts" / "spec_threshold_guard.py"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return 0

    # spec_threshold_guard handles "is this a spec file?" itself.
    result = subprocess.run(
        ["python3", str(GUARD), file_path],
        capture_output=True,
        text=True,
    )

    rc = result.returncode

    if rc == 0:
        return 0  # silent: file fine or not a spec md

    # Forward the guard's findings to Claude via stderr.
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")

    if rc == 1:
        # Hard violation → blocking exit so Claude is forced to address it.
        sys.stderr.write(
            "Action required: split the file before any further edits "
            "(see .trellis/spec/guides/index.md §Convention).\n"
        )
        return 2

    # rc == 2 (warning) → non-blocking, but visible.
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
