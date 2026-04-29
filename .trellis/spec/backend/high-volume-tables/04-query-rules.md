# 4. 查询规范

> 强制时间范围 + 前缀 LIKE + 游标分页 + 导出限制。

---

## 4.1 强制时间范围

```java
@GetMapping("/api/sys/operation-logs")
public R<PageResult<OperationLogVO>> page(@Valid OperationLogQuery query) { ... }

@Data
public class OperationLogQuery {
    @NotNull private LocalDate startDate;            // 必填
    @NotNull private LocalDate endDate;              // 必填

    @AssertTrue(message = "时间范围不得超过 90 天")
    public boolean isRangeValid() {
        return ChronoUnit.DAYS.between(startDate, endDate) <= 90;
    }

    private Long userId;
    private String bizType;
    private String bizNo;
    private String action;
    private Integer pageNum  = 1;
    private Integer pageSize = 20;
}
```

铁律：
- `startDate` / `endDate` **必填**，禁止全表查
- 单次查询时间范围 **≤ 90 天**（热表保留期）；超过自动路由到温/冷数据
- `biz_no` 仅支持**前缀 LIKE**（`'SO2026%'`），禁止 `'%SO2026%'` 或 `'%2026%'`

---

## 4.2 前缀 LIKE 走索引

```sql
-- ✅ 前缀匹配，能走 (biz_type, biz_no, create_time) 索引
WHERE biz_type = 'ORDER' AND biz_no LIKE 'SO2026%'

-- ❌ 全模糊，索引失效
WHERE biz_type = 'ORDER' AND biz_no LIKE '%2026%'

-- ❌ 后缀匹配，索引失效
WHERE biz_type = 'ORDER' AND biz_no LIKE '%001'
```

如需后缀/全模糊查询：参考 [`07-extensions.md`](./07-extensions.md) 的"全文检索"扩展场景。

---

## 4.3 游标分页（替代 offset）

数据量大时禁止 `LIMIT 100000, 20` 这种深翻页：

```sql
-- ❌ 深翻页 offset 越大越慢
SELECT * FROM sys_operation_log
WHERE create_time BETWEEN ? AND ?
ORDER BY create_time DESC
LIMIT 100000, 20;

-- ✅ 游标分页 性能恒定
SELECT * FROM sys_operation_log
WHERE create_time BETWEEN ? AND ?
  AND create_time < #{lastCreateTime}    -- 上一页最后一条的 create_time
ORDER BY create_time DESC
LIMIT 20;
```

API 设计：列表接口超过 1000 行时，**强制返回 `nextCursor` 字段**，前端带回查询。

```json
{
  "code": "0",
  "data": {
    "records": [...],
    "nextCursor": "2026-04-28T10:23:45.123",
    "hasMore": true
  }
}
```

---

## 4.4 导出限制

| 项 | 要求 |
|---|---|
| 数据源 | `@DS("slave")` 强制走从库（参见 `prod-hardening.md`） |
| 同时并发 | ≤ 3（信号量限制） |
| 行数上限 | 同步导出 ≤ 1 万行；超过走异步 taskId + 通知下载 |
| 时间范围 | ≤ 1 年（热+温），超过须异步从冷数据恢复 |
| 文件格式 | xlsx / csv / Parquet（合规审计场景） |

异步导出 API：

```
POST /api/sys/operation-logs:export
→ R<{ taskId: "abc-123", status: "QUEUED" }>

GET /api/sys/operation-logs/export-tasks/{taskId}
→ R<{ status: "DONE", downloadUrl: "https://..." }>
```

---

→ 下一步：[05-archival.md](./05-archival.md)
