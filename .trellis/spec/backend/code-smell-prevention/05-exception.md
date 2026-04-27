## 5. 异常处理

### 5.1 Catch 块规则

| 场景 | 处理方式 |
|---|---|
| 业务校验失败 | `throw new BusinessException("message")` |
| 可恢复的解析错误 | `log.warn` + 返回默认值/null |
| 不可恢复的系统错误 | `log.error` + rethrow 或包装为 BusinessException |
| 绝对禁止 | 空 catch `{}` / `catch (Exception ignored)` |

### 5.2 批量操作错误收集

参见 `error-handling.md` 中的"批量操作跳过规则"。

### 5.3 禁止异常控制流

```java
// FORBIDDEN: 用异常做业务分支
try { Integer.parseInt(s); return true; }
catch (NumberFormatException e) { return false; }

// CORRECT: 先检查再操作
return s != null && s.matches("\\d+");
```
