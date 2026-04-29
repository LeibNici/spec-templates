# Backend Logging Guidelines

## Log Path：禁用相对路径（铁律）

**铁律**：`logback-spring.xml` / `logback.xml` 中**禁止**使用相对路径作为 `LOG_PATH`，否则日志会落到 Spring Boot 启动时的 `cwd` 下，污染任意目录。

**反例**：

```xml
<property name="LOG_PATH" value="./logs"/>  <!-- 相对路径 -->
```

→ 不同启动方式（IDE / mvn / java -jar / docker）会让日志散落到多个目录。
→ 治标方案（.gitignore 黑名单）只阻止入库，不阻止文件被生成。**根因是配置层假设 cwd**。

**正确写法**：

```xml
<!-- 优先读环境变量 LOG_PATH，未设时落到家目录（保证绝对路径） -->
<property name="LOG_PATH" value="${LOG_PATH:-${user.home}/.{app-name}-logs/${APP_NAME}}"/>
```

| 环境 | 期望路径 | 配置方式 |
|---|---|---|
| dev | `~/.{app-name}-logs/{app-name}/` | 默认值（`user.home` 是 JVM 系统属性，永远绝对） |
| prod | `/var/log/{app-name}/` | 启动脚本设 `LOG_PATH=/var/log/{app-name}` 环境变量覆盖 |
| CI | tmpdir | 启动命令 `-DLOG_PATH=/tmp/ci-logs` |

**Review Checklist**：

- [ ] 所有 `<property name="*PATH" value="..."/>` 不能以 `.` / `./` 开头
- [ ] 所有产出物路径（uploads / cache / pid / lock）同等要求
- [ ] 启动 SOP 不依赖"必须 cd 到目标目录"——配置层独立于 cwd

---

## Production Format

- JSON 格式，使用 `logstash-logback-encoder`
- 日志级别：`root=WARN`, `com.{org}=INFO`
- Forbidden：生产环境打印 MyBatis SQL（`mybatis-plus.configuration.log-impl` 必须不设）

---

## TraceId

- Servlet Filter 把 `traceId` 注入 MDC（每次请求）
- 所有日志携带 traceId 用于请求关联
- Pattern：`%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n`

---

## Sensitive Data Masking

| 字段类型 | 脱敏规则 | 示例 |
|---|---|---|
| password | `***` | `***` |
| token | 前 8 字符 + `***` | `eyJhbGci***` |
| phone | 中间 4 位 `****` | `138****5678` |
| ID card | 中间位 `****` | `310***********1234` |
| apiKey / secret | 前 4 字符 + `***` | `sk-a***` |

### Forbidden

- 任何环境下打印完整 token / password / secret
- `System.out.println` 调试（用 `log.debug`）
- 生产环境记录完整 request/response body 不脱敏

### Correct Pattern

```java
log.info("User login: userId={}", userId);
// NOT: log.info("User login: token={}", token);
```

---

## Log Level 使用

| 级别 | 何时用 |
|---|---|
| ERROR | 不可恢复故障，需人工介入 |
| WARN | 可恢复问题、catch 块软失败、降级行为 |
| INFO | 业务里程碑（created / approved / synced）、启动 |
| DEBUG | 详细流程、SQL 参数（仅 dev） |
