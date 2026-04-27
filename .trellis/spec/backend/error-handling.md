# Backend Error Handling

## Response Pattern

```java
R.ok(data);                                       // code=200
R.fail("msg");                                    // code=500
throw new BusinessException("可读错误信息");        // GlobalExceptionHandler 捕获
```

- `BusinessException` 必须映射到 4xx/5xx HTTP 状态
- Forbidden：错误条件返回 HTTP 200

---

## Catch 块规则

| 场景 | 必须做的 |
|---|---|
| 非关键错误 | 最低 `log.warn(msg, e)` |
| 影响数据一致性 | 必须 rethrow（必要时包装为 BusinessException） |
| 外部系统超时 | log + 返回安全默认值（软失败） |

### Forbidden

- 空 catch：`catch (Exception e) { }` 或 `catch (Exception ignored) { }`
- 吞掉影响业务状态的异常

### Correct Pattern

```java
try {
    externalService.call();
} catch (TimeoutException e) {
    log.warn("External service timeout, using default: {}", e.getMessage());
    return defaultValue;
}
```

---

## 批量操作跳过规则

批量操作跳过记录时，必须收集原因并返回给调用方。

### Forbidden

```java
// WRONG: 静默跳过
for (Item item : items) {
    if (!isValid(item)) continue;  // 信息丢失
    process(item);
}
```

### Correct Pattern

```java
List<SkipReason> skipped = new ArrayList<>();
for (Item item : items) {
    if (!isValid(item)) {
        skipped.add(new SkipReason(item.getId(), "validation failed: ..."));
        continue;
    }
    process(item);
}
return BatchResult.of(processed, skipped);
```

---

## GlobalExceptionHandler

- 捕获所有未处理异常
- `BusinessException` 映射到合适的 HTTP 状态
- 记录请求体时脱敏敏感字段（password / token / secret / apiKey）
- 返回 `R.fail(msg)` 带可读消息

---

## 异常控制流（铁律）

```java
// FORBIDDEN: 用异常做业务分支
try { Integer.parseInt(s); return true; }
catch (NumberFormatException e) { return false; }

// CORRECT: 先检查再操作
return s != null && s.matches("\\d+");
```

---

## 静默跳过反模式（参见 code-smell-prevention.md §9）

批处理 / 分发 / 转发类代码遇到"本条处理不了"时，**单纯 `log.warn + continue/return` 是静默失败的温床**。

必须配合：
1. 错误计数回传调用方（`skipped` / `failureDetails` 列表）
2. Micrometer counter（生产环境可告警）
3. `failureDetails` 列表携带跳过原因

```java
int skipped = 0;
List<String> skipReasons = new ArrayList<>();
for (Item item : items) {
    if (item.getKey() == null) {
        skipped++;
        skipReasons.add(item.getId() + ":缺 key");
        skippedCounter.increment();   // micrometer
        continue;
    }
    process(item);
}
result.put("skippedCount", skipped);
result.put("skipReasons", skipReasons);
```
