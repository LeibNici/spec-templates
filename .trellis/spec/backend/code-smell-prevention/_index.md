# Code Smell Prevention Rules

> 重构实战沉淀的防腐检查清单。开发时先 grep 自查，避免规模化漂移。

---

## Pattern Index

| Pattern | File |
|---|---|
| 1. 弱类型传递 | [01-weak-typing.md](./01-weak-typing.md) |
| 2. 单一职责 | [02-srp.md](./02-srp.md) |
| 3. 硬编码 | [03-hardcoding.md](./03-hardcoding.md) |
| 4. 防腐层 | [04-isolation.md](./04-isolation.md) |
| 5. 异常处理 | [05-exception.md](./05-exception.md) |
| 6. 方法设计 | [06-method-design.md](./06-method-design.md) |
| 7. 前后端一致性补充 | [07-cross-layer.md](./07-cross-layer.md) |
| 8. 历史违规文件的修正义务 | [08-historical-fix.md](./08-historical-fix.md) |
| 9. 静默跳过反模式谱系 | [09-silent-skip.md](./09-silent-skip.md) |
| 10. Dev/Test 基础设施反模式 | [10-dev-mock.md](./10-dev-mock.md) |

---

## Enforcement（机器拦截，禁止靠经验）

部分铁律已编码进 `.trellis/scripts/code_smell_guard.py`，三层调用：

| 层 | 触发 | 配置位置 | 行为 |
|---|---|---|---|
| L1 编辑期 | Claude Code `Edit` / `Write` 写 `*.java` | `.claude/settings.json` → `PostToolUse` → `.claude/hooks/code-smell-check.py` | violation 阻断 (exit 2) |
| L2 提交期 | `git commit` 含 `*.java` 改动 | `.githooks/pre-commit`（启用：`git config core.hooksPath .githooks`） | violation 拒绝 commit |
| L3 CI 期 | PR / push 到 main | 项目 CI yaml 调 `python3 .trellis/scripts/code_smell_guard.py --scan` | violation 失败 |

调用方式：

```bash
# 全量扫描
python3 .trellis/scripts/code_smell_guard.py --scan

# 校验改动子集（pre-commit / hook 用法）
python3 .trellis/scripts/code_smell_guard.py path/to/Foo.java ...

# 机器可读输出
python3 .trellis/scripts/code_smell_guard.py --json --scan

# 单行豁免（同行或上方一行）
// spec-allow: B12 reason=integration adapter requires legacy behavior
@Transactional
```

**当前已编码规则**：
- `B12` — `@Transactional` 必须声明 `rollbackFor`（来源：`quality-guidelines.md` §Service 铁律）

新增规则的流程：在 `code_smell_guard.py` 顶部加 `RULES` 表 + 检查函数；本文表格补该规则编号 + 来源文件。

---

→ See [`quality-guidelines.md`](../quality-guidelines.md) for code limits (function/file size, nesting, complexity).
