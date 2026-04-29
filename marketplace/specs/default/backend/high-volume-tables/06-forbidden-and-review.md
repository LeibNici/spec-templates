# 6. Forbidden Patterns + Code Review Checklist

---

## Forbidden Patterns

| 反模式 | 后果 | 正解 |
|---|---|---|
| `WHERE payload LIKE '%订单%'` | 全表扫，秒级慢查 | 关键字段冗余成列（biz_type/biz_no） |
| 操作日志写在业务 `@Transactional` 方法里 | 业务事务被日志写卡，回滚还会丢日志 | AOP 切面 + `AFTER_COMMIT` 事件 + 独立线程池 |
| 操作日志表用 `@TableLogic deleted` 软删 | 日志类禁止软删 | 走分区 + DROP PARTITION |
| 不带时间范围的列表查询 | 全表扫 | API 强制 `startDate/endDate` 必填 |
| `LIMIT 100000, 20` 深翻页 | offset 越大越慢 | 游标分页 `WHERE create_time < lastTime` |
| 共用 `@Async` 默认线程池 | 业务异步任务和日志互相拖累 | 独立 `operationLogExecutor` |
| 写入失败 retry-loop | 雪崩，把主库 IOPS 打满 | 失败 `log.warn` + counter，**不重试** |
| 写入入口分散（每 Service 各 `logService.save()`） | 难以统一控制 | 全走 AOP 注解 |
| `payload` 中存大对象（10KB+） | 表膨胀，查询变慢 | payload ≤ 4KB，超长截断或外存 |
| 给 `payload` JSON 字段加索引 | 维护成本高，selectivity 差 | 该字段冗余成独立列再索引 |
| `biz_no LIKE '%xxx%'` 全模糊 | 索引失效 | 仅前缀 LIKE，全文检索走 ES |
| 迁移任务不带 `@SchedulerLock` | 双机环境双触发删错数据 | 必加 + JdbcTemplateLockProvider |
| `RedisLockProvider` 做 ShedLock | 主从异步丢锁 | 用 JDBC（见 `../topology-agnostic.md`） |
| 业务关键 ID（订单号、用户名）只放 payload | 查询无法走索引 | 必须冗余成 `biz_id` / `biz_no` 列 |
| 与业务表共享数据源连接池 | 高峰互相挤占 | 可选独立 DataSource（量大时） |

---

## Code Review Checklist

### 表设计
- [ ] 表名落入"日志/流水"识别规则的，**必须**按本规范设计
- [ ] 业务关键查询字段（订单号 / 用户名 / 字典 key）冗余成独立列，不在 `payload` 上查询
- [ ] 主键含 `create_time`（分区键约束）
- [ ] 4 个固定索引齐全（`user_time` / `biz_time` / `action_time` / `create_time`）
- [ ] DDL 含 `PARTITION BY RANGE`，预留 `pmax` 兜底分区
- [ ] DDL 经 Flyway V 文件管理，不允许手工 `ALTER`

### 写入路径
- [ ] 写入入口走 `@OperationLog` 注解 + AOP 切面，无显式 `logService.save()` 调用
- [ ] 切面用 `@TransactionalEventListener(AFTER_COMMIT)` 监听，不参与业务事务
- [ ] 独立线程池 `operationLogExecutor`，拒绝策略 `CallerRunsPolicy`
- [ ] 切面异常完全吞（log.warn），不影响业务方法
- [ ] SpEL 解析失败兜底（biz_id/biz_no 设 NULL，不阻塞写入）

### 查询路径
- [ ] 查询 API `startDate/endDate` 必填，范围 ≤ 90 天
- [ ] `biz_no` 模糊只允许前缀 LIKE，禁止 `%xxx%`
- [ ] 列表深翻页改游标分页，禁止 `LIMIT 大offset`
- [ ] 跨层查询自动路由（热/温/冷），前端不感知数据位置

### 生命周期
- [ ] 三个生命周期任务（hotToWarm / warmToCold / preCreatePartitions）就位
- [ ] 全部带 `@SchedulerLock`，LockProvider 是 JDBC 类型
- [ ] 迁移失败告警 + 不自动重试
- [ ] 冷数据 Parquet 文件做 checksum 校验
- [ ] 政府/合规场景：OSS WORM + 异地容灾

### 导出
- [ ] 导出强制走 `@DS("slave")`
- [ ] 同步导出 ≤ 1 万行，超过走异步 taskId
- [ ] 同时导出并发 ≤ 3（信号量）

---

→ 下一步（扩展）：[07-extensions.md](./07-extensions.md)
