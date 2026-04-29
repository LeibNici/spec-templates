# Thinking Guides

> **Purpose**: Expand your thinking to catch things you might not have considered.

---

## Why Thinking Guides?

**大多数 bug 与技术债来自"没想到这一茬"**，而非技能不足：

- 没想到层与层之间会发生什么 → 跨层 bug
- 没想到代码模式在重复 → 处处重复代码
- 没想到边界情况 → 运行时错误
- 没想到未来维护者 → 不可读代码

These guides help you **ask the right questions before coding**.

---

## Available Guides

| Guide | Purpose | When to Use |
|-------|---------|-------------|
| [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md) | 识别模式、减少重复 | 注意到模式在重复 |
| [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md) | 思考跨层数据流 | 跨多层的特性 |
| [Build & Dependency Governance Guide](./build-dependency-governance-guide.md) | build 文件分层、版本归属集中化 | 改 `pom.xml` / build 配置 / 依赖版本 |
| [Dev Server Lifecycle Guide](./dev-server-lifecycle-guide.md) | 前后端开发服启动 / 停止 / 重启 / 健康检查 SOP | 启动/重启前后端、清端口、登录自测、调试 500 响应 |
| [Parallel Execution Default](./parallel-execution-default.md) | 多任务默认开 Agent Team 并行作业 | 跨 ≥2 模块、≥4 文件编辑、研究+实现并存 |
| [Full-Stack Workflow](./full-stack-workflow.md) | 不 mock 的全栈开发 5 步流程 | 每开一个新 feature；前后端同期开发 |
| [Git Workflow](./git-workflow/_index.md) | 分支模型、Conventional Commits、PR 规范、Merge 策略 | 团队 ≥ 2 人协作；新人 onboarding |
| [i18n Strategy](./i18n-strategy/_index.md) | 国际化策略：vue-i18n + Spring MessageSource + 字典 + 错误响应 | 项目要支持英文/多语言；新建用户可见文案 |

---

## Quick Reference: Thinking Triggers

### When to Think About Cross-Layer Issues

- [ ] Feature touches 3+ layers (API, Service, Component, Database)
- [ ] Data format changes between layers
- [ ] Multiple consumers need the same data
- [ ] You're not sure where to put some logic

→ Read [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md)

### When to Think About Code Reuse

- [ ] You're writing similar code to something that exists
- [ ] You see the same pattern repeated 3+ times
- [ ] You're adding a new field to multiple places
- [ ] **You're modifying any constant or config**
- [ ] **You're creating a new utility/helper function** ← Search first!

→ Read [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md)

### When to Think About Build & Dependency Governance

- [ ] You're adding or upgrading a dependency/plugin
- [ ] You're modifying `pom.xml` / `build.gradle` / version catalog
- [ ] You see the same version repeated across multiple modules
- [ ] Module build files are starting to diverge in structure/order

→ Read [Build & Dependency Governance Guide](./build-dependency-governance-guide.md)

### When to Think About Dev Server Lifecycle

- [ ] 你要启动/重启 admin 后端或 vite 前端
- [ ] curl 返回 500 / 401 需要定位
- [ ] 端口占用、Flyway 迁移确认、DB 连接串排查
- [ ] 第一次在本会话接触启动命令

→ Read [Dev Server Lifecycle Guide](./dev-server-lifecycle-guide.md)

### When to Default to Agent Team

- [ ] 任务跨 ≥2 个独立模块/层
- [ ] ≥4 文件需要独立编辑
- [ ] 研究（同根扩散排查）+ 实现（主线修复）两类工作并存
- [ ] e2e 多 route 回测 / 多页面验收

→ Read [Parallel Execution Default](./parallel-execution-default.md)

---

## Pre-Modification Rule (CRITICAL)

> **Before changing ANY value, ALWAYS search first!**

```bash
# Search for the value you're about to change
grep -r "value_to_change" .
```

This single habit prevents most "forgot to update X" bugs.

---

## How to Use This Directory

1. **Before coding**: Skim the relevant thinking guide
2. **During coding**: If something feels repetitive or complex, check the guides
3. **After bugs**: Add new insights to the relevant guide (learn from mistakes)

---

## Guide Maintenance Rules（防膨胀契约）

> **Context**：长期运行会让单一 guide 文件膨胀为万 token 级别，被 spec 注入机制全量加入每次 subagent 调用，拖慢所有 check/implement 流程。

### Convention: Guide Split Threshold

**What**: 单个 guide 文件同时满足以下任一条件时，必须拆分，禁止继续追加：

- 文件大小 ≥ **15 KB**
- H2（`## `）章节数 ≥ **15**
- 被 ≥ 3 个 task jsonl 引用且本文件占该 jsonl 总注入字节 ≥ 40%

**Why**: spec 注入量直接决定 subagent 首 token 延迟与 token 成本。

**拆分方法**:

```
guides/
├── <guide-name>/             # 原 <guide-name>.md 改为目录
│   ├── _index.md             # 保留 Problem / Checklist / pattern → 文件名 映射
│   ├── <pattern-1>.md        # 每个 H2 章节拆为独立文件（3~5 KB）
│   ├── <pattern-2>.md
│   └── ...
```

`jsonl` 默认只引 `_index.md`；命中具体关键词时再显式加入子文件引用。

### Enforcement（机器拦截，禁止靠经验）

阈值不能只挂在文档上 —— 否则编辑期没人算字节、commit 期没人盯 H2，最终漂移到爆。**单一真理来源**：`.trellis/scripts/spec_threshold_guard.py`，三层调用：

| 层 | 触发 | 配置位置 | 行为 |
|---|---|---|---|
| L1 编辑期 | Claude Code `Edit` / `Write` 写 `spec/**/*.md` | `.claude/settings.json` → `PostToolUse` → `.claude/hooks/spec-threshold-check.py` | violation 阻断 (exit 2)，warning 提示 |
| L2 提交期 | `git commit` 含 spec 改动 | `.githooks/pre-commit`（启用：`git config core.hooksPath .githooks`） | violation 拒绝 commit，warning 放行 |
| L3 CI 期 | PR / push 到 main | 项目 CI yaml 调 `python3 .trellis/scripts/spec_threshold_guard.py --scan` | violation 失败 |

调用方式：

```bash
# 全量扫描
python3 .trellis/scripts/spec_threshold_guard.py --scan

# 校验改动子集（pre-commit / hook 用法）
python3 .trellis/scripts/spec_threshold_guard.py path/to/spec.md ...

# 机器可读输出
python3 .trellis/scripts/spec_threshold_guard.py --json --scan
```

**退出码语义**：`0` 全过 / `1` 有违规（必须处理）/ `2` 有预警（≥ 80% 阈值，建议处理）。

阈值在脚本顶部常量 `SIZE_LIMIT` / `H2_LIMIT` / `WARN_RATIO` —— 改这里，本节文字数字也要同步改（规则与执行同源原则）。

---

**Core Principle**: 30 minutes of thinking saves 3 hours of debugging.
