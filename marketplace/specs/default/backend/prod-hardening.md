# Production Hardening

## Security Hardening

| 规则 | 要求 |
|---|---|
| Secret fail-fast | Prod profile 中所有敏感配置 **无默认值**；缺失即启动失败 |
| Docker 密码 | 通过 `.env` 文件（gitignore）；禁止：明文 yml 提交到 git |
| 登录限流 | Redis 滑窗：5 req/min/IP + 连续失败锁 15min |
| XSS Filter | Servlet Filter 全局转义用户输入；富文本端点用白名单 |
| CORS（prod） | 具体 `allowedOrigins` 域名；禁止 `allowedOriginPatterns=*` + `allowCredentials=true` |
| 错误日志脱敏 | GlobalExceptionHandler 对 request body 中的 password/token/secret/apiKey 脱敏 |

---

## Config Hardening (prod profile)

```yaml
server:
  shutdown: graceful
  tomcat:
    threads:
      max: ${TOMCAT_MAX_THREADS:200}
      min-spare: ${TOMCAT_MIN_SPARE:20}
    max-connections: ${TOMCAT_MAX_CONN:8192}
    accept-count: ${TOMCAT_ACCEPT_COUNT:100}
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

所有线程/连接池参数走环境变量：

```yaml
async:
  core-size: ${ASYNC_CORE_SIZE:8}
  max-size: ${ASYNC_MAX_SIZE:32}
spring.datasource.hikari:
  maximum-pool-size: ${HIKARI_MAX_POOL:30}
```

- JVM 参数走 Dockerfile `ENV JAVA_OPTS`；禁止：`ENTRYPOINT` 内硬编码
- Prod secret：纯 `${}` 占位符，无默认值

---

## 容量公式

- **HikariCP**：`max-pool-size = CPU 核数 * 2 + 1`（单实例）；400 并发双实例 → 25-30/实例
- **Tomcat**：默认 200 线程；400 并发双实例足够

---

## 限流策略

| 维度 | 策略 | 值 |
|---|---|---|
| 全局 QPS | 令牌桶 | 2000 req/s（按硬件调整） |
| 用户级 | 滑窗 | 60 req/min |
| 登录 | 滑窗 + 锁 | 5/min/IP，连续失败 15min 锁 |
| 导出/报表 | 并发限制 | ≤ 3 并发导出任务 |

---

## 读写分离

代码用 `@DS("slave")` 表达读意图；实际路由按环境配置控制。

> 主从同步部署 + VIP 漂移场景的应用代码约束（ShedLock / Sentinel / 健康检查 / 连接池），见 [`topology-agnostic.md`](./topology-agnostic.md)。

| 场景 | 注解 | 备注 |
|---|---|---|
| 写方法 | 无（默认 master） | |
| 纯查询 | `@DS("slave")` | 从从库读 |
| 写后立即读（同事务） | 无 | 避免主从延迟 |
| 导出/报表 | `@DS("slave")` | 隔离重查询 |

Forbidden：`if (profile == prod)` 路由分支。

---

## Auth 优化

- JWT 无状态优先（高并发下减少 Redis session 查询）
- 权限缓存：`auth:permissions:{userId}` → Redis，TTL = token TTL；角色/权限变更时清除
- Token 刷新：access_token 2h + refresh_token 7d

---

## JWT & 白名单

- JWT secret 必须可配置（环境变量）
- 白名单：仅 `/api/auth/**`, `/actuator/health`, `/actuator/info`
- 密码：BCrypt only

---

## Prod 必填环境变量

无默认值（缺失启动失败）：

- `JWT_SECRET`
- `DB_PASSWORD`
- `REDIS_PASSWORD`
- 其他第三方集成 secret（按项目）

带安全默认值的调优变量：

- `HIKARI_MIN_IDLE` / `HIKARI_MAX_POOL` / `HIKARI_IDLE_TIMEOUT` / `HIKARI_MAX_LIFETIME` / `HIKARI_CONN_TIMEOUT`
- `TOMCAT_MAX_THREADS` / `TOMCAT_MIN_SPARE` / `TOMCAT_MAX_CONN` / `TOMCAT_ACCEPT_COUNT`
- `ASYNC_CORE_SIZE` / `ASYNC_MAX_SIZE` / `ASYNC_QUEUE`
- `SHUTDOWN_GRACE`（默认 30s）
- `CORS_ALLOWED_ORIGINS`（逗号分隔域名；生产必须显式配置）
- `LOGIN_IP_WINDOW` / `LOGIN_IP_MAX` / `LOGIN_FAIL_LOCK_MIN` / `LOGIN_FAIL_THRESHOLD`

---

## Good / Base / Bad Cases

- **Good（符合规范）**
  - `application-prod.yml` 中写 `secret: ${JWT_SECRET}`（纯占位符）
  - Controller 注入 `HttpServletRequest`，调 `ClientIpUtils.extract(request)` 传给 Service
  - 新建 Filter 用 `@Order(Ordered.HIGHEST_PRECEDENCE + N)` + `OncePerRequestFilter`
- **Base（可接受但非理想）**
  - 第三方集成 secret 允许空默认值 `${THIRD_PARTY_SECRET:}`，只要对应 `enabled` 默认 false
  - dev profile CORS `*` + `allowedOriginPatterns` 组合（Spring 专为 credentials=true 兼容设计）
- **Bad（禁止）**
  - `secret: ${JWT_SECRET:hardcoded-default}` — 明文默认值出现在代码库
  - `getHeader("Authorization")` 经过 XSS 包装后再被 Spring Security 解析 — 必须走白名单
  - Service 方法硬编码调用 `RedisTemplate` 做限流逻辑而非注入限流组件
  - GlobalExceptionHandler 直接把 request body 写入 MDC 不脱敏
