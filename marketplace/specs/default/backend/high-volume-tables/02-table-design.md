# 2. 表设计铁律

> 冗余列设计 + DDL 模板 + 索引策略 + 分区粒度。

---

## 2.1 业务关键字段必须冗余成列

操作日志的查询模式是**确定性追溯**而非全文检索：「谁干了啥、对什么对象、什么时候」。所以**关键查询字段必须从 `payload` 中冗余出独立列**，不允许在 JSON 上做查询。

通用四件套（操作日志类）：

| 列 | 含义 | 示例 | 可空 |
|---|---|---|---|
| `user_id` | 操作者主键 | 8001 | ❌ |
| `biz_type` | 操作目标类型 | `ORDER` / `USER` / `ROLE` / `DICT` / `LOGIN` | ❌ |
| `biz_id` | 操作目标内部主键 | 12345 | ✅（如登录无目标） |
| `biz_no` | 操作目标可读编号 | `SO20260428001` / `zhangsan` | ✅ |
| `action` | 操作类型 | `CREATE` / `UPDATE` / `DELETE` / `LOGIN` | ❌ |

实例：

| 业务场景 | biz_type | biz_id | biz_no | action |
|---|---|---|---|---|
| 创建销售订单 SO20260428001 | `ORDER` | 12345 | SO20260428001 | CREATE |
| 修改用户 zhangsan 的角色 | `USER` | 8001 | zhangsan | UPDATE |
| 启用角色「采购员」 | `ROLE` | 5 | PURCHASER | ENABLE |
| 修改字典 order_status | `DICT` | 33 | order_status | UPDATE |
| 用户登录 | `LOGIN` | NULL | NULL | LOGIN |

**Forbidden**：把"订单号 / 用户名 / 字典 key"塞进 `payload JSON` 后用 `payload LIKE '%xxx%'` 查询——全表扫，垮。

---

## 2.2 标准 DDL 模板（按月分区）

```sql
CREATE TABLE sys_operation_log (
  id           BIGINT       NOT NULL AUTO_INCREMENT,
  user_id      BIGINT       NOT NULL                       COMMENT '操作者ID',
  user_name    VARCHAR(64)                                  COMMENT '操作者用户名快照',
  biz_type     VARCHAR(30)  NOT NULL                       COMMENT '操作目标类型',
  biz_id       BIGINT                                       COMMENT '操作目标内部主键',
  biz_no       VARCHAR(64)                                  COMMENT '操作目标业务编号',
  action       VARCHAR(30)  NOT NULL                       COMMENT '操作类型',
  request_id   VARCHAR(64)                                  COMMENT '链路追踪 ID',
  ip           VARCHAR(45)                                  COMMENT '客户端 IP（含 IPv6）',
  cost_ms      INT                                          COMMENT '业务方法耗时',
  result       VARCHAR(10)  NOT NULL DEFAULT 'SUCCESS'     COMMENT 'SUCCESS/FAIL',
  error_msg    VARCHAR(500)                                 COMMENT '失败时错误摘要',
  payload      JSON                                         COMMENT '详情快照，禁止参与查询',
  create_time  DATETIME(3)  NOT NULL                       COMMENT '操作时间',
  PRIMARY KEY (id, create_time),
  KEY idx_user_time     (user_id, create_time),
  KEY idx_biz_time      (biz_type, biz_no, create_time),
  KEY idx_action_time   (action, create_time),
  KEY idx_create_time   (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='操作日志（按月分区）'
PARTITION BY RANGE (TO_DAYS(create_time)) (
  PARTITION p202604 VALUES LESS THAN (TO_DAYS('2026-05-01')),
  PARTITION p202605 VALUES LESS THAN (TO_DAYS('2026-06-01')),
  PARTITION p202606 VALUES LESS THAN (TO_DAYS('2026-07-01')),
  PARTITION pmax    VALUES LESS THAN MAXVALUE
);
```

设计要点：
- **主键含分区键**（`PRIMARY KEY (id, create_time)`）—— MySQL 分区表硬要求
- **4 个固定索引**覆盖典型查询模式，每分区数据量受控
- `payload JSON` **仅用于详情展示**，禁止 `WHERE payload->>'$.xxx' = ...` 或 `LIKE '%...%'`
- `user_name` 是快照而非外键（用户改名后日志保留当时名字）
- `result` + `error_msg` 让"失败操作"也能进日志（便于审计）

---

## 2.3 索引策略

| 索引 | 覆盖查询 |
|---|---|
| `(user_id, create_time)` | 「张三某时段干了啥」 |
| `(biz_type, biz_no, create_time)` | 「谁动过订单 SO20260428001」「张三对订单干了啥」 |
| `(action, create_time)` | 「某时段所有删除操作」 |
| `(create_time)` | 兜底全表时间窗口扫描（少用） |

**禁止**：在 `payload` JSON 字段上加索引（即便是 generated column）—— JSON 索引维护成本高、selectivity 差。

---

## 2.4 分区粒度选择

| 日均写入 | 分区粒度 | 单分区行数 |
|---|---|---|
| < 5 万 | **按月** ⭐ 默认 | 100-150 万 |
| 5 万 - 30 万 | 按月 | 150-900 万 |
| 30 万 - 200 万 | 按周 | 200-1400 万 |
| > 200 万 | 按日 + 异地 | — |

**默认按月**。除非业务暴涨预期 10 倍，不要主动选周/日（分区数太多元数据开销大）。

---

→ 下一步：[03-write-path.md](./03-write-path.md)
