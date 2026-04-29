# High-Volume Tables（日志/流水类高写入表规范）

> 治理只增不减、长期运行后查询变慢的"沉默杀手"表（操作日志、审计流水、消息记录、状态变更轨迹等）。
> 配套：`../database-guidelines/_index.md`（DDL 通用规范）、`../topology-agnostic.md`（异步写入与 ShedLock）、`../api-design.md`（分页查询规范）。

---

## Pattern Index

| Section | File |
|---|---|
| 1. 识别"日志/流水"类表 | [01-identification.md](./01-identification.md) |
| 2. 表设计铁律（冗余列 + DDL + 索引 + 分区） | [02-table-design.md](./02-table-design.md) |
| 3. 写入路径（AOP + 独立线程池） | [03-write-path.md](./03-write-path.md) |
| 4. 查询规范（强制时间范围 + 游标分页 + 导出） | [04-query-rules.md](./04-query-rules.md) |
| 5. 归档与生命周期（三层存储 + 自动迁移） | [05-archival.md](./05-archival.md) |
| 6. Forbidden Patterns + Code Review Checklist | [06-forbidden-and-review.md](./06-forbidden-and-review.md) |
| 7. 扩展场景与超规范情形 | [07-extensions.md](./07-extensions.md) |

---

## Quick Decision

```
识别表是否落入本规范
    ↓
表名含 _log/_record/_history/_trace/_event/_audit  ─┐
写 QPS > 读 QPS                                    ├─→ 任一命中 → 必须按本规范设计
仅 INSERT，永不更新                                 │
查询常按时间窗口                                    ┘
    ↓
按 02-table-design.md 建表（冗余列 + 月分区 + 4 索引）
按 03-write-path.md 写入（AOP + 独立线程池 + AFTER_COMMIT）
按 04-query-rules.md 查询（必填时间 + 前缀 LIKE + 游标分页）
按 05-archival.md 归档（90 天热 / 1 年温 / 5+ 年冷）
```

---

## 设计目标

| 目标 | 实现 |
|---|---|
| 写不影响业务事务 | AOP 切面 + `@TransactionalEventListener(AFTER_COMMIT)` + 独立线程池 |
| 查询毫秒级响应 | 关键字段冗余成列 + 4 个固定索引 + 月分区 |
| 长期运行不膨胀 | 90 天 DROP PARTITION + 温冷归档 |
| 政府/审计合规 | 冷数据 OSS Parquet 5-10 年 / 永久保留 |
| 双机环境一致性 | 迁移任务 `@SchedulerLock`（见 topology-agnostic.md） |

---

→ See [`../quality-guidelines.md`](../quality-guidelines.md) for code limits (function/file size, nesting).
→ See [`../topology-agnostic.md`](../topology-agnostic.md) for `@SchedulerLock` and async executor rules.
