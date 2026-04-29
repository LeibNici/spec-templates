# spec-templates

A **Trellis spec template registry** for SpringBoot + Vue full-stack projects, plus a companion `tools/` directory with custom guards and hooks.

> [中文版 README](README_CN.md)

## Two distribution channels

| Channel | What | How |
|---|---|---|
| **Spec (registry)** | `.trellis/spec/{backend,frontend,guides}/**` | Trellis pulls automatically via `trellis init --registry` |
| **Tools (manual)** | Python guards + Claude/git hooks | One-shot install via `tools/install.sh` |

The registry channel is governed by the [Trellis registry protocol](https://docs.trytrellis.app/zh/templates/specs-index) — only spec content is allowed there. The tools channel is a sibling for project-level adaptations Trellis itself does not distribute.

---

## Channel A — Install spec templates

```bash
trellis init --registry gh:LeibNici/spec-templates
# → Trellis finds marketplace/index.json and installs
#   marketplace/specs/default/  →  <your-project>/.trellis/spec/
```

After install, **read [`marketplace/specs/default/PLACEHOLDERS.md`](marketplace/specs/default/PLACEHOLDERS.md) and run the global token replacement** for your project name / package / module ids.

### What you get

```
.trellis/spec/
├── PLACEHOLDERS.md             # token dictionary — read first
├── backend/
│   ├── api-design.md
│   ├── code-smell-prevention/  # 10 anti-pattern rules
│   ├── database-guidelines/
│   ├── high-volume-tables/
│   ├── test-strategy/
│   └── ... (naming, logging, prod-hardening, ...)
├── frontend/                   # Vue conventions, hooks, type safety
└── guides/                     # git workflow, i18n, dev-server, ...
```

---

## Channel B — Install custom tools

```bash
# from a clone:
./tools/install.sh /path/to/target-project

# or one-shot from raw:
curl -sSL https://raw.githubusercontent.com/LeibNici/spec-templates/main/tools/install.sh \
  | bash -s -- /path/to/target-project
```

This copies:

```
<target>/.trellis/scripts/code_smell_guard.py     # backend/frontend code-smell rules
<target>/.trellis/scripts/spec_threshold_guard.py # spec coverage threshold check
<target>/.claude/hooks/code-smell-check.py        # PostToolUse: per-edit guard (calls L1)
<target>/.claude/hooks/spec-threshold-check.py    # session-end / Stop hook
<target>/.claude/hooks/inject-subagent-context.py
<target>/.claude/hooks/statusline.py              # custom status line
<target>/.githooks/pre-commit                     # L2 git pre-commit (calls same guard)
```

### Three-layer guard architecture

Both Claude hooks and the git hook delegate to the same authoritative Python guards:

```
L1  Claude Code PostToolUse  →  .claude/hooks/code-smell-check.py
                                    └─ calls .trellis/scripts/code_smell_guard.py
L2  Git pre-commit           →  .githooks/pre-commit
                                    └─ calls .trellis/scripts/code_smell_guard.py
L3  CI                       →  your-pipeline.yaml
                                    └─ calls .trellis/scripts/code_smell_guard.py
```

### Wiring (manual, after install.sh)

The installer cannot edit your `.claude/settings.json` (it would conflict with each project's own settings). Add hooks yourself, e.g.:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": ".claude/hooks/code-smell-check.py" }]
      }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": ".claude/hooks/spec-threshold-check.py" }] }
    ]
  }
}
```

Activate the git hook:

```bash
git -C /path/to/target-project config core.hooksPath .githooks
```

---

## Repository layout

```
spec-templates/
├── README.md                  # ← you are here
├── marketplace/               # Trellis registry protocol
│   ├── index.json             #   template index
│   └── specs/
│       └── default/           #   the SpringBoot+Vue spec template
└── tools/                     # Custom guards/hooks (manual install)
    ├── install.sh
    ├── code_smell_guard.py
    ├── spec_threshold_guard.py
    ├── .claude-hooks/
    └── .githooks/
```

## License

MIT (or as configured in your project).
