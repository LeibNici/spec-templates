# 1. 识别"日志/流水"类表

> 决定一张表是否落入本规范治理。

---

## 识别规则

满足下面 **任一** 条件即归入本规范：

1. 表名含 `_log` / `_record` / `_history` / `_trace` / `_event` / `_audit`
2. 写 QPS > 读 QPS（典型审计、操作日志）
3. 数据**永不更新**（仅 INSERT + 偶尔按时间清理）
4. 业务侧常按时间窗口查询（"近 7 天 / 近 30 天"）

---

## 典型实例

| 表名 | 业务领域 |
|---|---|
| `sys_operation_log` | 系统操作日志（最常见） |
| `sys_login_log` | 登录登出审计 |
| `audit_log` | 合规审计流水 |
| `message_send_record` | 消息/通知发送记录 |
| `order_status_history` | 订单状态变更轨迹 |
| `inventory_movement_record` | 库存出入流水 |
| `payment_callback_log` | 支付回调流水 |

---

## 反例（**不**适用本规范）

| 表 | 理由 |
|---|---|
| `sys_user` / `sys_role` | 主数据，CRUD 频繁，按 `../database-guidelines/_index.md` |
| `order` / `order_item` | 业务主表，存在 UPDATE，按业务库设计 |
| `sys_dict` / `sys_config` | 字典配置，读多写少 + 体量小 |
| `tmp_*` | 临时表，按需清理而非分区 |

---

## 决策流程

```
新建一张表
    ↓
表名带 log/record/history/trace/event/audit?
    ├── 是 → 落入本规范
    └── 否 → 看读写比 + 是否更新
              ├── 写多读少 + 仅 INSERT → 落入本规范
              └── 否 → 走 ../database-guidelines/_index.md
```

---

→ 落入本规范后，下一步：[02-table-design.md](./02-table-design.md)
