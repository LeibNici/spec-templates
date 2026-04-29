# spec-templates

面向 SpringBoot + Vue 全栈项目的 **Trellis spec 模板 Registry**，附带一个 `tools/` 目录提供自定义守护脚本与 hook。

> [English version](README.md)

## 两条分发通道

| 通道 | 内容 | 使用方式 |
|---|---|---|
| **Spec（registry）** | `marketplace/specs/default/{backend,frontend,guides}/**` | Trellis 通过 `trellis init --registry` 自动同步 |
| **Tools（手动）** | Python 守护 + Claude/git hook | `tools/install.sh` 一键安装 |

Registry 通道遵循 [Trellis registry 协议](https://docs.trytrellis.app/zh/templates/specs-index)——协议层规定**只允许 spec 内容**。Tools 通道是兄弟通道，承载 Trellis 本身不分发的项目级自定义增强。

---

## 通道 A — 安装 Spec 模板

```bash
trellis init --registry gh:LeibNici/spec-templates
# Trellis 探测到 marketplace/index.json，自动安装：
#   marketplace/specs/default/  →  <你的项目>/.trellis/spec/
```

安装后**第一件事**：阅读 [`marketplace/specs/default/PLACEHOLDERS.md`](marketplace/specs/default/PLACEHOLDERS.md)，按字典做一次全局占位符替换（项目名、包名、模块 id 等）。

### 你会得到什么

```
.trellis/spec/
├── PLACEHOLDERS.md             # 占位符字典 — 必读
├── backend/
│   ├── api-design.md
│   ├── code-smell-prevention/  # 10 条反模式规则
│   ├── database-guidelines/    # SQL/DDL/Flyway/分页
│   ├── high-volume-tables/     # 大表设计与归档
│   ├── test-strategy/          # 测试分层与执行
│   └── …（命名、日志、生产硬化等）
├── frontend/                   # Vue 规范、hook、类型安全
└── guides/                     # Git workflow、i18n、dev-server 等
```

---

## 通道 B — 安装自定义工具

```bash
# 已 clone：
./tools/install.sh /path/to/target-project

# 远程一键：
curl -sSL https://raw.githubusercontent.com/LeibNici/spec-templates/main/tools/install.sh \
  | bash -s -- /path/to/target-project
```

会拷入：

```
<target>/.trellis/scripts/code_smell_guard.py     # 后/前端 code-smell 规则核心检查器
<target>/.trellis/scripts/spec_threshold_guard.py # spec 覆盖率阈值检查
<target>/.claude/hooks/code-smell-check.py        # PostToolUse：每次编辑触发 L1
<target>/.claude/hooks/spec-threshold-check.py    # Stop hook：会话结束阈值校验
<target>/.claude/hooks/inject-subagent-context.py
<target>/.claude/hooks/statusline.py              # 自定义状态栏
<target>/.githooks/pre-commit                     # L2：git pre-commit 调用同一守护
```

### 三层守护架构

Claude hook 与 git hook 都委托给同一份**权威 Python 守护**：

```
L1  Claude Code PostToolUse  →  .claude/hooks/code-smell-check.py
                                    └─ 调用 .trellis/scripts/code_smell_guard.py
L2  Git pre-commit           →  .githooks/pre-commit
                                    └─ 调用 .trellis/scripts/code_smell_guard.py
L3  CI                       →  你的 pipeline.yaml
                                    └─ 调用 .trellis/scripts/code_smell_guard.py
```

三层都查同一份规则——本地编辑、提交、流水线之间不会出现"在我机器上能过"的不一致。

### 配置（install.sh 之后手动一步）

安装器**故意不改** `.claude/settings.json`，避免覆盖你项目原有的 hook 配置。请自己在 settings.json 加：

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

激活 git hook：

```bash
git -C /path/to/target-project config core.hooksPath .githooks
```

---

## 仓库结构

```
spec-templates/
├── README.md                  # 英文（GitHub 默认显示）
├── README_CN.md               # ← 你正在看
├── marketplace/               # Trellis registry 协议目录
│   ├── index.json             #   模板索引
│   └── specs/
│       └── default/           #   SpringBoot+Vue spec 模板
└── tools/                     # 自定义守护/hook（手动安装）
    ├── install.sh
    ├── code_smell_guard.py
    ├── spec_threshold_guard.py
    ├── .claude-hooks/
    └── .githooks/
```

## 设计原则

1. **Registry 只装 spec**——不夹带 Trellis 核心运行时（scripts、workflow.md、config.yaml 等），那些由 npm 全局包 `@mindfoldhq/trellis@beta` 在 `trellis init` 时自行写入，registry 不掺手。
2. **Tools 显式手动安装**——避免与消费端项目原有的 hook 配置冲突；安装器只拷文件，不动 settings.json。
3. **不存放任何个人数据**——`.trellis/workspace/`、`.trellis/tasks/`、`.trellis/.developer` 全部 gitignored，避免 journal/任务历史被提交。

## License

MIT（或按你的项目实际配置）。
