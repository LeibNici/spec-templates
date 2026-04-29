## 9. 静默跳过反模式谱系（Silent Skip Patterns）

**铁律**：批处理 / 分发 / 转发 类代码遇到"本条处理不了"的情况时，**单纯 `log.warn + continue/return` 是静默失败的温床**。下游看到的只是"0 条结果"，定位成本极高。必须配合：(1) 错误计数回传调用方；(2) Micrometer counter（生产环境可告警）；(3) `failureDetails` 列表携带跳过原因。

### 反模式家族

| # | 形态 | 症状 |
|---|---|---|
| 1 | `default` 分支仅 log | 未知 type 永不同步，下游看不到 |
| 2 | `null-continue` | 批处理点击后 0 条结果，日志一行 warn |
| 3 | `try-catch-return-default` | 软失败永远绿灯，下游误以为正常 |
| 4 | `empty-list-fallback` | 空数据被静默换轨，业务难辨 |
| 5 | `catch-log-swallow` | 表不存在/字段变更全无感知 |
| 6 | `DuplicateKeyException-ignore` | 幂等键撞车被吞，业务事件丢失 |

### 反例（FORBIDDEN）

```java
// 批处理静默跳过
for (Schedule s : schedules) {
    if (s.getOrderId() == null) {
        log.warn("跳过 {}", s.getScheduleNo());
        continue;          // ❌ 调用方只看到少了结果
    }
    ...
}

// default 静默放过
switch (changeType) {
    case "QUANTITY" -> handleQty(...);
    default -> log.warn("未知 {}", changeType);   // ❌
}

// 所有异常返回默认"没事"
try { ... }
catch (Exception e) {
    log.warn("失败，软失败返回100%");
    return defaultReadiness();    // ❌ 表不存在也 100% 绿灯
}
```

### 正例（REQUIRED）

```java
// 跳过必须回传 + 计数
int skipped = 0;
List<String> skipReasons = new ArrayList<>();
for (Schedule s : schedules) {
    if (s.getOrderId() == null) {
        skipped++;
        skipReasons.add(s.getScheduleNo() + ":缺 orderId");
        skippedCounter.increment();   // ✓ micrometer
        continue;
    }
    ...
}
result.put("skippedCount", skipped);
result.put("skipReasons", skipReasons);   // ✓ 回传

// default 必须可观测
default -> {
    log.warn("未知 {}, changeType={}", orderNo, changeType);
    unknownChangeTypeCounter.increment();
    throw new BusinessException("不支持的变更类型: " + changeType);
}
```

### 检查清单

- [ ] 所有 `continue` / `return null` / `return default` 分支是否都配 counter 或 `failureDetails` 收集？
- [ ] 调用方能否从返回值看出"跳过了多少条、为什么"？不能看出即是 bug
- [ ] `try/catch` 是否因为"软失败"而把异常整个吞掉？至少要把异常堆栈 log + 计数
- [ ] 整个批次 0 条结果时，是"数据本就是空"还是"被静默跳过"？调用方必须能区分
