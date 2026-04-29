# 7. 扩展场景与超规范情形

> 下面情形需要超出本规范的设计，请单独评审。

---

## 7.1 全文检索

**场景**：「找包含某关键词的所有日志」、`biz_no` 全模糊或后缀匹配、payload 字段任意检索。

**方案**：
- 操作日志同步到 ES（Canal 监听 binlog → Kafka → ES）
- 前端查询走 ES，详情查询回 MySQL（ES 只存索引必要字段）
- ES 索引按月滚动（`op-log-2026-04`），与 MySQL 分区策略对齐
- 冷数据迁出 ES 的同时迁出 MySQL（保持双层一致）

**适用项目**：toC 高频查询、运营平台、风控系统。中后台/政府审计场景**通常不需要**——确定性追溯比相关性排序更重要。

---

## 7.2 高写入 QPS（> 1000/s）

**场景**：秒杀、IoT 数据采集、广告点击流。

**方案**：
- 削峰：先写 RocketMQ / RedisStream / Kafka，消费者批量入库
- 消费者每 100ms 或每 100 条触发一次批量 INSERT（`rewriteBatchedStatements=true`）
- 消费者侧仍用本规范的 AOP 注解 + 独立线程池

**适用项目**：日均写入 > 1 亿。中后台 200-300 用户**远不到**这个量级。

---

## 7.3 多租户隔离

**场景**：SaaS 平台、跨组织日志严格隔离。

**方案**：
- 加 `tenant_id` 列（NOT NULL）
- 分区键改 `(tenant_id, create_time)` 复合分区，或子分区
- 索引前缀加 `tenant_id`：`(tenant_id, user_id, create_time)` 等
- 查询 API **必带** `tenant_id`，由网关层强制注入

---

## 7.4 跨地域复制

**场景**：异地容灾、合规要求数据多副本异地保存。

**方案**：
- MySQL binlog → Canal → 异地 MySQL（同 schema）
- OSS Parquet 跨地域复制（OSS 本身支持）
- ES 异地集群（CCR 跨集群复制）

**注意**：异地复制延迟通常 100ms+，不影响本规范的查询路径（本规范都是异步 + 历史数据）。

---

## 7.5 实时聚合 / 数据大屏

**场景**：实时统计"今日操作总数"、"过去 1h Top 活跃用户"。

**方案**：
- **不要**对操作日志表做实时聚合 SQL（即使分区也慢）
- 异步消费写入 Redis ZSet / HyperLogLog
- 大屏定时拉 Redis，TTL 5min
- 历史聚合走离线计算（每日凌晨跑 batch job）

---

## 7.6 与其他规范的关系

| 规范 | 关系 |
|---|---|
| `../database-guidelines/_index.md` | 通用 DDL 标准（utf8mb4 / 公共字段 / Flyway）；本规范是其特化 |
| `../topology-agnostic.md` | 铁律 1（`@SchedulerLock`）+ 铁律 5（Redis 仅放可重建数据）配合本规范 |
| `../api-design.md` | 分页参数 / 批量操作命名规范，本规范继承 |
| `../error-handling.md` | 切面失败"仅 log.warn 不重试"延伸自批量跳过反模式 |
| `../prod-hardening.md` | 读写分离 `@DS("slave")` 用于查询和导出 |

---

## 7.7 何时**不**用本规范

下列表**不**适用本规范：

| 表类型 | 走哪个规范 |
|---|---|
| 业务主表（order / inventory / user）| `../database-guidelines/_index.md` |
| 字典 / 配置表（sys_dict / sys_config）| `../database-guidelines/_index.md` + `../dict-and-relation-strategy.md` |
| 临时表（tmp_*）| 按需清理，不分区 |
| 关联中间表（user_role）| 业务库设计 |
| 报表汇总表（写多但有 UPDATE 操作） | 数据仓库或独立 OLAP |

---

→ 回到 [`_index.md`](./_index.md)
