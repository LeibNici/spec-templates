# 5. 归档与生命周期

> 三层存储 + ShedLock 自动迁移 + 跨层查询路由。

---

## 5.1 三层存储架构

```
T0           T+90 天          T+1 年                   T+5~10 年
 │              │                  │                        │
 ▼              ▼                  ▼                        ▼
[热分区表]──→[温归档表]──────────→[冷数据 OSS Parquet]──→ 长期保留 / 到期清理
 MySQL         MySQL              OSS / MinIO
 主表          sys_operation_     sys_operation_log/
 月分区        log_archive        year=2026/month=04.parquet
```

| 层 | 保留期 | 存储 | 查询性能 | 用途 |
|---|---|---|---|---|
| 热（hot） | 90 天 | MySQL 主表分区 | 毫秒级 | 业务侧高频查询 |
| 温（warm） | 1 年 | MySQL 归档表（同库） | 秒级 | 偶尔回查 |
| 冷（cold） | 5-10 年 / 永久 | OSS / MinIO Parquet 文件 | 分钟级 | 合规审计 |

---

## 5.2 自动迁移任务（ShedLock 调度）

```java
@Component
@RequiredArgsConstructor
public class OperationLogLifecycleJob {

    private final OperationLogArchiveService archiveService;

    /** 每月 1 号 02:00：热表 → 温归档表 */
    @Scheduled(cron = "0 0 2 1 * ?")
    @SchedulerLock(name = "opLog.hotToWarm", lockAtMostFor = "PT1H")
    public void migrateHotToWarm() {
        // 1. 找出 4 个月前的分区（保留 3 个月热数据 + 当月）
        // 2. INSERT INTO sys_operation_log_archive SELECT FROM ...
        // 3. 校验行数一致
        // 4. ALTER TABLE sys_operation_log DROP PARTITION pYYYYMM
        archiveService.hotToWarm();
    }

    /** 每月 1 号 03:00：温表 → 冷存储 Parquet */
    @Scheduled(cron = "0 0 3 1 * ?")
    @SchedulerLock(name = "opLog.warmToCold", lockAtMostFor = "PT2H")
    public void migrateWarmToCold() {
        // 1. 找出 13 个月前的数据
        // 2. dump 成 Parquet 文件（按月一个），上传 OSS
        // 3. 校验 checksum
        // 4. DELETE FROM sys_operation_log_archive WHERE create_time < ...
        archiveService.warmToCold();
    }

    /** 每月 1 号 01:30：预创建未来 3 个月分区 */
    @Scheduled(cron = "0 30 1 1 * ?")
    @SchedulerLock(name = "opLog.preCreatePartitions", lockAtMostFor = "PT10M")
    public void preCreatePartitions() {
        // ALTER TABLE sys_operation_log REORGANIZE PARTITION pmax INTO (...)
        archiveService.preCreatePartitions(3);
    }
}
```

铁律：
- 三个任务**必须 `@SchedulerLock`**（双机环境防双触发，见 `../topology-agnostic.md` 铁律 1）
- LockProvider 必须用 `JdbcTemplateLockProvider`，禁止 `RedisLockProvider`
- 失败 / 校验不一致 → **告警**，不自动重试（避免删错数据）
- DROP PARTITION 是**秒级**操作，不锁业务表（远好于 `DELETE WHERE create_time < ...`）

---

## 5.3 跨层查询路由

```java
public PageResult<OperationLogVO> queryAcrossTiers(OperationLogQuery query) {
    LocalDate end = query.getEndDate();
    LocalDate cutHot  = LocalDate.now().minusDays(90);
    LocalDate cutWarm = LocalDate.now().minusYears(1);

    if (end.isAfter(cutHot)) {
        return queryHot(query);                     // 主表
    }
    if (end.isAfter(cutWarm)) {
        return queryWarm(query);                    // 归档表
    }
    return queryColdAsync(query);                   // 冷数据：返回 taskId，异步生成下载链接
}
```

前端**不感知数据在哪**——拿到的要么是分页结果，要么是 taskId（冷数据走异步导出）。

---

## 5.4 政府/合规场景的特殊要求

| 要求 | 实现 |
|---|---|
| 长期保留（5-10 年 / 永久） | 冷数据 Parquet 永不删除 |
| 数据不可篡改 | OSS 启用 WORM（Write Once Read Many）|
| 审计追溯链路完整 | `biz_type` + `biz_no` + `request_id` 三件套 |
| 异地容灾 | OSS 跨地域复制 + MySQL 主从延迟 1h（见 `../topology-agnostic.md`） |
| 定期审计抽查 | 每季度跑校验任务 sample 1% 数据校验 checksum |

---

→ 下一步：[06-forbidden-and-review.md](./06-forbidden-and-review.md)
