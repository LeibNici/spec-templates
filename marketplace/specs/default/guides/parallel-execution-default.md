# 多任务并行作业默认模式（Agent Team Default）

> **铁律**：当任务可被切分成 ≥2 条**独立**子线时，**默认**开启 Agent Team 并行作业，而不是单线程顺序处理。
>
> 主对话只做**调度 + 综合**；具体研究/编辑/扫描交给并发 subagent。

---

## 触发判定（满足任一即开 Team）

| 信号 | 例子 |
|------|------|
| 跨 ≥2 个独立模块/层（无写依赖） | DB schema 改动 + 后端服务改动 + 前端类型改动 |
| 同时需要"研究 + 实现"两类工作 | 调研同根 bug 范围 + 主线修主 bug |
| 跨 ≥4 个文件的独立编辑 | 批量改 5 个 mapper / 6 个组件 |
| break-loop 系统性扩散排查阶段 | 找所有同 pattern 隐患点 |
| `e2e-test` / 多页面回归 | 多个 route 各自验证 |
| 新功能：DDL + 后端 + 前端三层 | Wave1 (DDL+后端) → Wave2 (前端) |

---

## 默认不开 Team 的场景

- **单文件单点修改**（< 3 处编辑），主线直接做
- **连续强依赖**：步骤 B 必须读步骤 A 的结果（无法并行）
- **纯问答 / 解释**：不写文件
- **风险高的破坏性操作**（DROP / rm -rf / force push）：必须主线确认，不交给 subagent

---

## Team 组成模板

| 角色 | subagent_type | 职责 |
|------|---------------|------|
| **Lead**（=主对话） | — | 拆解任务、并发派发、综合产出、用户确认 |
| **Research / Scout** | `trellis-research`（只读，产物落 `research/`）/ `Explore`（轻量只读，不持久化）| 同根问题扫描、上下文检索、规范查阅 |
| **Implement** | `trellis-implement` | 实际编辑代码（不可 commit） |
| **Check** | `trellis-check` | 编译、lint、跑测、回测 |
| **Break-Loop** | `trellis-break-loop` | 修完 bug 后的根因分析与防腐建议（替代旧 `debug` 角色）|

---

## 派发原则（Concurrency Rules）

1. **同一波内的 agent 必须无写依赖**：禁止 Wave1 内一个 agent 改 A.java，另一个 agent 也改 A.java
2. **研究 vs 实现 永远分开**：先 research → 主线综合 → 再派 implement。把"基于研究决定怎么改"留在主线，**禁止**让单一 implement agent 同时承担研究与改动
3. **一次消息内并行调用**：多个 Agent tool call 写在同一条 assistant 消息里，避免顺序起
4. **报告字数限制**：派 agent 时明确"<300 字 / <500 字"，避免回炒占用主线 context
5. **后台运行的判定**：长时（>2 min）扫描类 → `run_in_background:true`，主线继续做不冲突的事

---

## 调用顺序

1. 用户给目标 → 主线判断是否触发 Team
2. 触发 → 拆 Wave1 任务 → 单条消息并发起 research / explore agent
3. 收齐结果 → 主线综合 → 拆 Wave2 implement agent（必要时多个并发）
4. implement 完 → 派 check agent 验编译/测试
5. 主线汇报 + 等用户确认 commit

---

## 反模式（必须避免）

- ❌ **Agent 全分给后端遗漏前端**
- ❌ **顺序起 agent**（每个 agent 一条消息，丢失并行红利）
- ❌ **一个 agent 同时研究 + 改代码**（决策不透明，主线无法干预）
- ❌ **agent 之间有写冲突**（同一波改同一文件 → 后改覆盖前改）
- ❌ **不交代字数上限**（agent 回炒 5KB 报告，主线 context 飙升）
- ❌ **跨 4+ 模块顺序编辑不开 Agent**

---

## 触发关键词

多任务、批量、扫描、回测、并行、agent team、研究 + 实现、cross-module、Wave1/Wave2、break-loop 扩散、e2e-test 多 route
