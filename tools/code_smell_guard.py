#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code_smell_guard.py — Enforce backend/frontend spec rules at the code layer.

Companion to spec_threshold_guard.py: that file checks the spec docs
themselves; this one checks code against the rules the spec mandates.

Rules currently implemented:
    B12  @Transactional must declare rollbackFor
         (spec: backend/quality-guidelines.md §Service 铁律)

Why this exists
    Spec rules written only as prose drift over time — review misses
    them, new code copies neighboring violations, the audit on RuoYi-Vue
    found 17 instances of B12 hidden in core ServiceImpls. Encoding the
    rule as a build-time check turns it from "people remember" into
    "machine refuses".

Usage
    code_smell_guard.py [--scan] [--json] [PATH ...]

    --scan          scan all *.java in the repo
    PATH ...        check listed paths (file or directory) only
    --json          machine-readable output

Exit codes
    0  no violations
    1  at least one violation

Per-line suppression
    // spec-allow: B12 reason=integration adapter requires legacy behavior

    Place on the same line as @Transactional, or on the line directly
    above. Reason is required (free text after `reason=`); a missing
    reason still suppresses but is discouraged in review.

Wired from
    L1  .claude/hooks/code-smell-check.py        (PostToolUse)
    L2  .githooks/pre-commit                     (after spec_threshold_guard)
    L3  CI                                       (project-specific yaml)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

# --- Repo discovery -----------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent  # .trellis/scripts/.. → repo


# --- Annotation finder (balanced-paren aware) ---------------------------------
def find_annotations(text: str, name: str) -> list[tuple[int, str]]:
    """Locate every `@<name>` plus its argument string (or '' if none).

    Handles multi-line args:
        @Transactional(
            propagation = REQUIRED,
            rollbackFor = Exception.class
        )
    """
    target = "@" + name
    out: list[tuple[int, str]] = []
    i = 0
    while True:
        idx = text.find(target, i)
        if idx == -1:
            return out
        end = idx + len(target)
        # word boundary: avoid @TransactionalEventListener etc.
        if end < len(text) and (text[end].isalnum() or text[end] == "_"):
            i = end
            continue
        # skip whitespace, then check for '('
        j = end
        while j < len(text) and text[j] in " \t\r\n":
            j += 1
        args = ""
        if j < len(text) and text[j] == "(":
            depth = 1
            k = j + 1
            while k < len(text) and depth > 0:
                ch = text[k]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                k += 1
            args = text[j + 1 : k - 1]
            i = k
        else:
            i = end
        out.append((idx, args))


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def is_suppressed(text: str, idx: int, rule_id: str) -> bool:
    """True if a `spec-allow: <rule_id>` comment sits on the same or prev line."""
    line_start = text.rfind("\n", 0, idx) + 1
    line_end = text.find("\n", idx)
    if line_end == -1:
        line_end = len(text)
    same = text[line_start:line_end]
    if "spec-allow:" in same and rule_id in same:
        return True
    if line_start == 0:
        return False
    prev_end = line_start - 1
    prev_start = text.rfind("\n", 0, prev_end) + 1
    prev = text[prev_start:prev_end]
    return "spec-allow:" in prev and rule_id in prev


# --- Rules --------------------------------------------------------------------
RULE_B12 = {
    "id": "B12",
    "summary": "@Transactional must declare rollbackFor",
    "spec_ref": "backend/quality-guidelines.md §Service 铁律",
    "fix_hint": "rollbackFor = Exception.class",
}


def check_b12(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    violations: list[dict] = []
    for idx, args in find_annotations(text, "Transactional"):
        if "rollbackFor" in args:
            continue
        if is_suppressed(text, idx, RULE_B12["id"]):
            continue
        violations.append(
            {
                "rule": RULE_B12["id"],
                "path": str(path),
                "line": line_of(text, idx),
                "summary": RULE_B12["summary"],
                "spec_ref": RULE_B12["spec_ref"],
                "fix_hint": RULE_B12["fix_hint"],
            }
        )
    return violations


JAVA_RULES: list = [check_b12]


# --- Target collection --------------------------------------------------------
def collect_java(args: list[str]) -> list[Path]:
    files: list[Path] = []
    if not args or args == ["--scan"]:
        files.extend(REPO_ROOT.rglob("*.java"))
        return files
    for raw in args:
        p = Path(raw)
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        if p.is_dir():
            files.extend(p.rglob("*.java"))
        elif p.is_file() and p.suffix == ".java":
            files.append(p)
    return files


# --- Output -------------------------------------------------------------------
def relpath(p: str) -> str:
    pp = Path(p)
    try:
        return str(pp.relative_to(REPO_ROOT))
    except ValueError:
        return str(pp)


def format_human(violations: list[dict]) -> str:
    lines = []
    for v in violations:
        lines.append(
            f"❌ [{v['rule']}] {relpath(v['path'])}:{v['line']} — {v['summary']}"
        )
    return "\n".join(lines)


# --- Main ---------------------------------------------------------------------
def main(argv: list[str]) -> int:
    json_mode = "--json" in argv
    args = [a for a in argv if a != "--json"]

    java_targets = collect_java(args)
    if not java_targets:
        if json_mode:
            print(json.dumps({"checked": 0, "violations": []}))
        return 0

    violations: list[dict] = []
    for p in java_targets:
        for rule in JAVA_RULES:
            violations.extend(rule(p))

    if json_mode:
        print(
            json.dumps(
                {"checked": len(java_targets), "violations": violations},
                ensure_ascii=False,
            )
        )
    else:
        if violations:
            sys.stderr.write(format_human(violations) + "\n\n")
            sys.stderr.write(
                f"checked={len(java_targets)} violations={len(violations)}\n"
            )
            sys.stderr.write(
                f"rule: {RULE_B12['spec_ref']}\n"
                f"fix:  add `{RULE_B12['fix_hint']}` to the annotation\n"
                f"suppress: `// spec-allow: B12 reason=...` on same/previous line\n"
            )

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
