# Topology-Agnostic Code（部署形态无关代码规范）

> 一份 jar 包能在 1 台 / 2 台 / 3 台机器上正确运行，无需改代码。
> 配套：`prod-hardening.md`（容量与安全）、`high-volume-tables/_index.md`（日志/流水类表治理）、运维侧 `ops/deployment-blueprint.md`（待写）。

---

## 一、目标拓扑

默认假设：**Active-Passive + Witness**（3 节点），单机部署是其退化形态。

| 节点 | 角色 | 流量 | 关键服务 |
|---|---|---|---|
| 机器 1 | Primary（持 VIP） | 100% | App + Nginx + Keepalived(MASTER) + MySQL master + Redis master + Sentinel |
| 机器 2 | Standby（应用 running，weight=0） | 0%，failover 后 100% | App + Nginx + Keepalived(BACKUP) + MySQL slave + Redis slave + Sentinel |
| 机器 3 | Witness（仲裁 + 灾备 + 监控） | 永远 0% | Sentinel + MySQL delayed slave (1h) + Prometheus + XtraBackup |

**铁律**：业务代码不得感知"我在哪台机器上"。下面 9 条全部围绕这一点。

---

## 二、9 条铁律

### 铁律 1 · `@Scheduled` 必须配 `@SchedulerLock`

```java
@Scheduled(cron = "0 0 2 * * ?")
@SchedulerLock(name = "dailyReportJob",
               lockAtMostFor = "PT10M",
               lockAtLeastFor = "PT1M")
public void dailyReport() { ... }
```

LockProvider 配置：

```java
@Bean
public LockProvider lockProvider(DataSource dataSource) {
    return new JdbcTemplateLockProvider(dataSource);   // ← 锁存 MySQL master
}
```

**Forbidden**：
- `@Scheduled` 无 `@SchedulerLock` → failover 双触发（"日报发两份"）
- `RedisLockProvider` → A/B Redis 异步复制，failover 时锁会丢

**单机部署**：JdbcTemplateLockProvider 锁本地，零开销。

> ShedLock 在 MySQL 自动建一张 `shedlock` 内部表，**不属于业务 SQL**，与"Service 禁写 SQL"铁律不冲突（同 MyBatis-Plus 内部用 JDBC 一个道理）。

### 铁律 2 · 用户文件禁止落本地磁盘

| 文件类型 | 允许位置 | 禁止位置 |
|---|---|---|
| 用户上传 | MinIO / OSS / DB BLOB | `/data/uploads/` 等本地目录 |
| 异步导出产物 | MinIO + 返回签名 URL | 本地临时文件 + sessionId 取 |
| 编译临时文件 | 本地（一次性，无状态） | — |

**Forbidden**：
```java
file.transferTo(new File("/data/uploads/" + filename));   // ❌ failover 后丢
```

**正解**（MinIO）：
```java
minioClient.putObject(PutObjectArgs.builder()
    .bucket("uploads").object(key).stream(file.getInputStream(), size, -1).build());
```

### 铁律 3 · 禁止内存级全局状态

任何符合下列任一描述的内存数据结构必须迁出：

- `static Map<...>` 缓存业务数据
- `BlockingQueue<...>` 内存任务队列
- 应用启动时 `init()` 加载到内存的字典
- 验证码 / OTP / 一次性 nonce

**例外**：纯只读 Caffeine 本地缓存，TTL ≤ 60s，应用启动时从 DB 加载，**允许**。

### 铁律 4 · 禁止 `HttpSession` 存业务状态

```java
http.csrf(AbstractHttpConfigurer::disable)
    .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
```

- 鉴权统一 JWT 无状态
- CSRF 关闭（JWT + SameSite Cookie 已防御 CSRF）
- 验证码 / OTP / 多步表单草稿 → Redis（接受 failover 时丢失，前端兜底重发）

**Forbidden**：
- `session.setAttribute("captcha", ...)` → failover 验证码失效
- 默认 `SecurityContextHolder` 存 session（必须改 STATELESS）

### 铁律 5 · Redis 仅放可重建数据

| 类型 | 允许 | 禁止 |
|---|---|---|
| 限流计数器 | ✅ | — |
| 字典 / 权限缓存 | ✅ | — |
| 验证码 / OTP（短 TTL） | ✅ | — |
| 分布式锁 | ❌ | 用 ShedLock JDBC（铁律 1） |
| 异步任务队列 | ❌ | 用 MySQL 表或 RocketMQ |
| 跨请求业务状态（多步表单进度） | ❌ | 客户端 localStorage 或 DB |

**判定标准**：Redis 数据丢失，业务**不能挂**。挂了说明放错位置。

### 铁律 6 · 数据源连接配置走逻辑名，不硬编码 IP

```yaml
# ✅ 正确
spring:
  datasource:
    url: jdbc:mysql://${DB_VIP}:3306/biz?useSSL=false&serverTimezone=Asia/Shanghai
  data:
    redis:
      sentinel:
        master: mymaster
        nodes: ${REDIS_SENTINEL_NODES}   # A:26379,B:26379,C:26379
```

**Forbidden**：
```yaml
spring.datasource.url: jdbc:mysql://192.168.1.10:3306/biz   # ❌ failover 不跟随
spring.data.redis.host: 192.168.1.10                        # ❌ 必须 Sentinel 模式
```

- MySQL 连 VIP（keepalived 漂移自动跟随）
- Redis **必须** Sentinel 模式（客户端从 3 节点 Sentinel 自动发现 master）
- 一切 IP 走环境变量，prod profile 无默认值（参考 `prod-hardening.md`）

### 铁律 7 · 连接池强制短生命周期

```yaml
spring.datasource.hikari:
  max-lifetime: 1800000      # 30min，强制重建连接
  keepalive-time: 600000     # 10min keepalive 探活
  connection-timeout: 3000   # 3s 拿不到连接报错
  validation-timeout: 2000
```

理由：VIP 漂移后老连接处于 TCP 半开（half-open）状态，操作系统默认 7200s 才检测；强制 30min 重建可大幅缩短"切换后僵死"窗口。

HTTP 客户端（RestTemplate / Feign / OkHttp）同样：

| 项 | 上限 |
|---|---|
| connectTimeout | 3s |
| readTimeout | 10s |
| writeTimeout | 10s |
| **禁止** | 默认无超时 |

### 铁律 8 · 健康检查必含外部依赖

```yaml
management:
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true
  health:
    db.enabled: true
    redis.enabled: true
```

暴露端点：

| 端点 | 探活内容 | 用途 |
|---|---|---|
| `/actuator/health/liveness` | JVM 活着 | Keepalived `vrrp_script` 探活 |
| `/actuator/health/readiness` | JVM + DB + Redis 全活 | Nginx upstream 健康检查 |

**Forbidden**：`management.endpoint.health.show-details: never` → failover 检测失效

### 铁律 9 · 写后立即读必须强制 master

主从异步/半同步复制存在秒级延迟，关键写操作后的读必须显式走 master：

```java
@Service
public class OrderService {

    @Transactional
    public OrderVO create(OrderCreateDTO dto) { ... }   // 默认 master

    @DS("master")   // ← 写后读强制 master
    public OrderVO getJustCreated(Long id) {
        return orderMapper.selectById(id);
    }
}
```

约定：

| 路径 | 数据源 |
|---|---|
| 默认查询 | `@DS("slave")` 或不标注 |
| 写后 5 秒内的读 | `@DS("master")` 强制 |
| 报表 / 导出 | `@DS("slave")`（隔离重查询） |
| 写后跨服务读关键路径 | 前端携带 `X-Read-Master: true`，网关层路由 |

---

## 三、Forbidden Patterns 速查

| 反模式 | 后果 | 正解 |
|---|---|---|
| `@Scheduled` 无 `@SchedulerLock` | failover 双触发 | 必加 + JDBC provider |
| `transferTo("/data/...")` | failover 文件丢 | MinIO / BLOB |
| `static Map<Long, Cache>` | 多机数据漂移 | Redis 或 Caffeine TTL≤60s |
| `session.setAttribute("biz", ...)` | failover 状态丢 | JWT + Redis 临时 |
| Redis 存分布式锁 | 主从异步丢锁 | ShedLock JDBC |
| 硬编码 `192.168.x.x` | failover 不跟随 | VIP / Sentinel 逻辑名 |
| HikariCP 默认无 maxLifetime | 半开连接卡死 | 30min 强制重建 |
| `health.show-details: never` | 切换失败感知不到 | always + probes |
| 写后立即 `@DS("slave")` 读 | 主从延迟读不到 | `@DS("master")` |
| `@Async` 用内存 ExecutorService | A 重启异步任务丢 | DB 任务表 + 重试 |

---

## 四、Code Review Checklist

- [ ] 所有 `@Scheduled` 带 `@SchedulerLock`，且 LockProvider 是 `JdbcTemplateLockProvider`
- [ ] 所有上传 / 导出文件落 MinIO 或 BLOB，无 `new File("/data/...")`
- [ ] 无业务级 `static` 容器作缓存（除 Caffeine TTL ≤ 60s 只读）
- [ ] Spring Security 配置 `STATELESS` + `csrf().disable()`
- [ ] Redis 中数据满足"丢了能重建"
- [ ] `application.yml` 无硬编码 IP，Redis 用 Sentinel 模式
- [ ] HikariCP `max-lifetime ≤ 1800s` + HTTP 客户端有显式超时
- [ ] `/actuator/health/liveness` + `/readiness` 都暴露
- [ ] 写后立即读路径走 `@DS("master")`
- [ ] 关键异步任务持久化到 DB / MQ，不依赖内存队列

---

## 五、单机部署的差异（极少）

部署到 1 台机器时，以上规范**全部仍然生效**，没有任何放宽：

| 规范 | 单机表现 |
|---|---|
| ShedLock JDBC | 锁本地，无开销 |
| MinIO / Sentinel | 单节点起即可（Sentinel quorum=1） |
| MySQL 半同步复制 | 关掉 |
| `@DS("master")` / `@DS("slave")` | 同一数据源，路由都走 master |
| Keepalived | 不部署，VIP 直接绑物理 IP |

**核心理念**：单机是 N 机的退化形态，不是另一种模式。一份代码 + 一份配置（仅 IP / 开关差异），通吃 1~3 台机器。

---

## 六、与其他规范的关系

| 规范 | 关系 |
|---|---|
| `prod-hardening.md` | 提供容量公式、限流策略、生产 secret 规则 |
| `database-guidelines/_index.md` | DDL / 索引 / Flyway，与本规范无冲突 |
| `error-handling.md` | 批量任务跳过规则与铁律 5（异步队列禁内存）配合 |
| `dependency-policy.md` | ShedLock / MinIO / Sentinel 客户端依赖纳入白名单 |
| `i18n-strategy/` | 本规范不涉及 i18n |
| 运维侧 `ops/deployment-blueprint.md`（待写） | keepalived / nginx / Sentinel 部署脚本与本规范配套 |

---

## 七、待补充章节（后续 PR）

- 部署示意图（含 VIP 漂移、Sentinel 仲裁、延迟从库时序）
- failover 演练 SOP（每季度一次）
- RTO / RPO 指标定义
- 半同步复制 + ID 错位的 MySQL 配置模板
