#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spec_threshold_guard.py — Enforce spec defragmentation contract.

Authoritative thresholds (mirror of `.trellis/spec/guides/index.md`
§Convention: Guide Split Threshold):
    file size   >= 15 KB        → violation (must split)
    H2 sections (`^## `) >= 15  → violation (must split)
    file size   >= 80% of limit → warning (consider splitting soon)
    H2 sections >= 80% of limit → warning

Usage:
    spec_threshold_guard.py [--scan] [--json] [PATH ...]

Modes:
    no args / --scan : scan all .md files under the active spec root
                       (.trellis/spec after install, marketplace/specs/default in this repo)
    PATH ...         : check only the listed files (skips non-md / non-spec)

Output:
    stderr  human-readable findings
    stdout  (with --json) machine-readable JSON

Exit codes:
    0  no violations and no warnings
    1  at least one violation (size or H2 over hard limit)
    2  no violations but at least one warning (>= 80% of limit)

Wired from three places (single source of truth):
    L1  Claude Code PostToolUse hook  (.claude/settings.json)
    L2  Git pre-commit hook           (.githooks/pre-commit)
    L3  CI step                       (project-specific yaml)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# --- Thresholds ---------------------------------------------------------------
SIZE_LIMIT = 15 * 1024     # bytes
H2_LIMIT = 15              # count
WARN_RATIO = 0.80          # 80% of limit triggers a warning

H2_RE = re.compile(r"^## ", re.MULTILINE)

# --- Repo discovery -----------------------------------------------------------
THIS_FILE = Path(__file__).resolve()


def find_repo_root() -> Path:
    """Find the project or template repo root without assuming install path."""
    starts = [Path.cwd().resolve(), THIS_FILE.parent]
    for start in starts:
        current = start
        while current != current.parent:
            if (current / ".trellis" / "spec").is_dir():
                return current
            if (current / "marketplace" / "specs" / "default").is_dir():
                return current
            if (current / ".git").exists() and (current / ".trellis").is_dir():
                return current
            current = current.parent
    return THIS_FILE.parent.parent.parent


def find_spec_root(repo_root: Path) -> Path:
    """Use installed project specs first, then this registry's source template."""
    installed = repo_root / ".trellis" / "spec"
    if installed.is_dir():
        return installed
    template = repo_root / "marketplace" / "specs" / "default"
    if template.is_dir():
        return template
    return installed


REPO_ROOT = find_repo_root()
SPEC_ROOT = find_spec_root(REPO_ROOT)


def is_spec_md(path: Path) -> bool:
    """True if path is a markdown file under the active spec root."""
    try:
        path.resolve().relative_to(SPEC_ROOT.resolve())
    except ValueError:
        return False
    return path.suffix == ".md" and path.is_file()


def measure(path: Path) -> tuple[int, int]:
    """Return (size_bytes, h2_count) for path."""
    text = path.read_text(encoding="utf-8")
    size = len(text.encode("utf-8"))
    h2 = len(H2_RE.findall(text))
    return size, h2


def classify(size: int, h2: int) -> tuple[str, list[str]]:
    """Return (level, reasons) where level ∈ {'ok','warn','violation'}."""
    reasons: list[str] = []
    if size >= SIZE_LIMIT:
        reasons.append(f"size {size}B >= {SIZE_LIMIT}B")
    if h2 >= H2_LIMIT:
        reasons.append(f"H2 sections {h2} >= {H2_LIMIT}")
    if reasons:
        return "violation", reasons

    if size >= int(SIZE_LIMIT * WARN_RATIO):
        reasons.append(f"size {size}B >= 80% of {SIZE_LIMIT}B")
    if h2 >= int(H2_LIMIT * WARN_RATIO):
        reasons.append(f"H2 sections {h2} >= 80% of {H2_LIMIT}")
    if reasons:
        return "warn", reasons
    return "ok", []


def collect_targets(args: list[str]) -> list[Path]:
    """Decide what to scan based on CLI args."""
    if not args or args == ["--scan"]:
        return sorted(SPEC_ROOT.rglob("*.md"))
    out: list[Path] = []
    for raw in args:
        p = Path(raw)
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        if is_spec_md(p):
            out.append(p)
    return out


def format_human(rows: list[dict]) -> str:
    if not rows:
        return ""
    lines = []
    for r in rows:
        rel = Path(r["path"]).relative_to(REPO_ROOT)
        icon = {"violation": "❌", "warn": "⚠️ ", "ok": "✓"}[r["level"]]
        lines.append(f"{icon}  {rel}  ({'; '.join(r['reasons'])})")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    json_mode = "--json" in argv
    args = [a for a in argv if a not in ("--json",)]

    targets = collect_targets(args)
    if not targets:
        if json_mode:
            print(json.dumps({"checked": 0, "rows": []}))
        return 0

    rows: list[dict] = []
    for p in targets:
        size, h2 = measure(p)
        level, reasons = classify(size, h2)
        if level == "ok":
            continue
        rows.append({
            "path": str(p),
            "level": level,
            "size_bytes": size,
            "h2_count": h2,
            "reasons": reasons,
        })

    violations = [r for r in rows if r["level"] == "violation"]
    warnings = [r for r in rows if r["level"] == "warn"]

    if json_mode:
        print(json.dumps({
            "checked": len(targets),
            "violations": len(violations),
            "warnings": len(warnings),
            "rows": rows,
        }, ensure_ascii=False))
    else:
        if rows:
            print(format_human(rows), file=sys.stderr)
            print("", file=sys.stderr)
            print(
                f"checked={len(targets)} violations={len(violations)} warnings={len(warnings)}",
                file=sys.stderr,
            )
            print(
                "rule: .trellis/spec/guides/index.md §Convention: Guide Split Threshold",
                file=sys.stderr,
            )

    if violations:
        return 1
    if warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
