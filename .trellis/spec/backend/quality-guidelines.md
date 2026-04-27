# Backend Quality Guidelines

## 代码硬性上限（实战宽松档）

| 指标 | 上限 | 超限处理 |
|---|---|---|
| 函数 | ≤ 80 行 | 抽方法（IDEA 默认 50，Sonar 默认 100，本档取中间值） |
| 文件 | ≤ 500 行 | 按职责拆类（Sonar 默认） |
| 嵌套 | ≤ 4 层 | 提前 return / 抽方法 |
| 位置参数 | ≤ 5 个 | 封装对象（IDEA 默认） |
| 圈复杂度 | ≤ 15 | 拆分逻辑（Sonar 默认） |
| 魔法数字 | 0 | 提取常量（除 0/1/-1） |

> Controller / ServiceImpl 不再单独设上限，统一走"文件 ≤ 500"。

---

## 注释策略（分层）

Java 后端是**长期维护对象**+ 公开接口是**契约**，注释策略与前端不同：

| 代码层 | 要求 | Checkstyle |
|---|---|---|
| Controller 公开方法 | **必须 Javadoc**（说明业务语义 + `@param` + `@return`） | `MissingJavadocMethod` 强制 |
| public Service 接口 | **必须 Javadoc** | 同上 |
| public 类型（DTO / VO / Command / Enum） | **必须 Javadoc**（类层 + 关键字段） | `JavadocType` 强制 |
| public 工具方法 | **必须 Javadoc** | 同上 |
| protected 方法 | **建议 Javadoc**（继承链关键扩展点） | warning |
| private 方法 / 内部实现 | 默认无；WHY 非显然时加一行（隐藏约束、bug workaround） | 不强制 |
| `@Override` 实现 | 默认无（继承父类 Javadoc） | 不强制 |

### Javadoc 模板（最低要求）

```java
/**
 * 创建订单。
 * <p>幂等：相同 orderNo 重复调用返回首次创建结果。</p>
 *
 * @param dto 订单创建请求
 * @return 创建后的订单 VO（含主键）
 * @throws BusinessException 客户不存在 / 库存不足
 */
@PostMapping
public R<OrderVO> create(@RequestBody @Valid OrderCreateDTO dto) { ... }
```

**禁止**：
- 空 Javadoc：`/** Create order. */`（重复方法名）
- 翻译式 Javadoc：`/** 设置订单号 */ public void setOrderNo(...)`（getter/setter 不写）
- 注释代码块（`// old impl ...`）—— 删掉，git history 是真相

---

## Controller 铁律

Controller = 参数绑定 + `@Valid` + 调 Service + 封装 `R<T>`。仅此而已。

### Forbidden in Controller

| 禁止项 | 反例模式 |
|---|---|
| 业务逻辑 | if/else 含领域规则、数据转换、超出 @Valid 的校验 |
| `@Transactional` | 事务属于 Service 层 |
| `@Scheduled` | 定时任务放 `task/` 包 |
| Mapper 注入 | 数据访问必须经 Service |
| `JdbcTemplate` | SQL 属 Mapper XML |
| `Map<String,Object>` 入参 | 用 DTO + `@Valid`；出参用 VO |
| 手写 Map↔Entity 转换 | 用 `BeanUtils.copyProperties` 或 MapStruct |
| 硬编码枚举↔中文映射 | 后端透传 code，前端 dict 映射 label |
| 异步分发 | `@Async` / `CompletableFuture` 属 Service |
| 工具方法 | 抽到 `common` 模块 `utils/` |

### Correct Pattern

```java
@PostMapping
public R<XxxVO> create(@RequestBody @Valid XxxCreateDTO dto) {
    return R.ok(xxxService.create(dto));
}
```

---

## Service 铁律

- 单一职责；超过 500 行按 Query/Command 拆分
- 写操作必须 `@Transactional(rollbackFor = Exception.class)`
- 已有 `@Transactional` 必须显式 `rollbackFor`
- 禁用 `JdbcTemplate`；数据访问只经 Mapper
- 禁止空 catch（最低 `log.warn`）

---

## Scheduled Task 规则

- 必须放 `task/` 或 `job/` 包，类名以 `Task` / `Job` 结尾
- Controller / Service 内禁用 `@Scheduled`
- 必须配 ShedLock：`@SchedulerLock(name, lockAtMostFor, lockAtLeastFor)`

---

## 事件驱动 & 状态机

- 跨模块解耦：`applicationEventPublisher.publishEvent(new XxxEvent(...))`
- Listener：`@EventListener` + 幂等
- 状态流转：`SELECT ... FOR UPDATE` + 前置状态检查 + `UPDATE`
- 幂等 INSERT：`select → insert → catch DuplicateKeyException → re-select`

---

## 缓存规则

- `RedisCacheManager` 显式配置（TTL、JSON 序列化、模块 key 前缀）
- TTL 分级：dict 2h | 主数据 30min | 热点 ≤ 5min | 写操作 → `@CacheEvict`
- 反模式防护：穿透 → 布隆过滤器/缓存 null | 击穿 → `sync=true` | 雪崩 → TTL 加抖动
- 启动：`ApplicationRunner` 预热 dict / 菜单 / 权限树

---

## 并发 & 幂等

- 优先乐观锁（`@Version`）；悲观锁仅用于状态流转（持有 < 1s）
- 分布式锁：Redis 细粒度（`lock:inventory:{skuId}`）
- 写 API（POST/PUT/DELETE）：token / 业务幂等键 / DB 唯一约束 任选其一

---

## 性能规则

- 循环内禁止逐项远程调用；批量预加载到 `Map<key, value>`
- 消除 SQL N+1：用 `IN (...)` 或 `GROUP BY`
- 列表 API 必须分页；`OFFSET > 10000` 用游标（`WHERE id > lastId`）

---

## Mock 策略

### 测试基础设施（必须保留）

每个业务模块 `pom.xml` 必须保留：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

它打包 `<scope>test</scope>`，**不进生产 jar**，零运行时成本。
提供 JUnit 5 / Mockito / AssertJ / Spring Test / JsonPath 全套。
**禁止**因"暂时不写测试"为理由移除——剥夺团队随时写测试的能力。

### 允许的 Mock

| 类型 | 位置 | 用途 |
|---|---|---|
| `Mockito.mock()` / `@Mock` | `src/test/java/` 单元测试 | mock 外部服务 / DB 边界 |
| `@MockBean` | `src/test/java/` 集成测试 | **谨慎使用**，优先 Testcontainers 真起依赖 |
| `integration/` 软失败 | 业务代码 | 第三方未对接时返安全默认值（详见 `directory-structure.md`） |

### 严禁的 Mock

- 业务代码（`controller/` / `service/`）里 `if (devMode) return fakeXxx`
- `@Profile("dev")` Bean 写死假业务数据 return
- `dev` 包里 `@PostConstruct` INSERT 假数据进业务表（详见 `code-smell-prevention.md §10`）

### 全栈协作工作流

后端在新功能开发时**先搭空接口契约**（10 分钟），让前端立即可接真路径——比让前端用 mock 工具更快、更准。详见 `.trellis/spec/guides/full-stack-workflow.md`。

---

## 测试基础设施 & Mock 策略

### spring-boot-starter-test 必须保留（铁律）

每个业务模块（不含 `common` 这种纯 POJO 模块）必须保留：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

- 提供 JUnit 5 / Mockito / AssertJ / JsonPath / Spring Test
- `<scope>test</scope>` 保证不打进生产 jar，零运行时成本
- **禁止**因为"项目不写测试"就移除——剥夺了团队随时写测试的能力

### Mock 分级允许

| 类型 | 评价 |
|---|---|
| 单元测试 `@Mock` / `Mockito.mock()` | ✅ 必需 |
| 集成测试 `@MockBean` 替换上下游 Service | ⚠️ 谨慎用，优先 Testcontainers 真起依赖 |
| 集成测试 Testcontainers（真起 MySQL / Redis） | ✅ 推荐 |
| H2 内存 DB | ⚠️ 不推荐（与 MySQL 行为差异） |

### 严禁

- `@Profile("dev")` Bean 在生产代码里 return 写死的假业务数据
- Controller / Service 里出现 `if (devMode) return fakeXxx`
- `dev` 包 `@PostConstruct` 写 INSERT 业务表（详见 `code-smell-prevention.md §10`）

### 全栈开发流程

后端先搭空接口契约（Controller + DTO/VO + 空 Service Impl），前端基于此写真 axios，前后端并行填实——比写 mock 数据更快、零联调切换。详见 `.trellis/spec/guides/full-stack-workflow.md`。

---

## 异步规则

以下场景禁止同步：批量导入 > 500 行 | 导出 > 10K 行 | 批量审批 > 50 | 三方同步 > 100。

模式：`@Async` + Redis 进度 + 前端轮询（返回 `taskId`，显示"处理中"）。

### 事务边界规则（防超时）

- `@Transactional` 命令方法内禁止在请求线程做重活
- 重活定义：循环远程调用 / 循环 `calculate*` / 大批量写 / 任何可能 > 1s 的路径
- 必须模式：先持久化状态 → `TransactionSynchronizationManager.afterCommit` + `TaskExecutor` 分发
- 命令响应契约必须显式异步受理：`runNo/taskId + async=true + status=QUEUED`
- 后端切异步契约时，前端类型/消息分支必须同 PR 更新

---

## 依赖规则

- 父/根 build 文件持有版本与构建策略：
  - 依赖版本：`properties` + `<dependencyManagement>`
  - 插件版本：`<pluginManagement>`
- 子模块只声明使用；集中管理的依赖/插件不得重定义 `<version>`
- 新增/升级依赖必须先在父 pom 集中加入，再被子模块消费
- 临时子模块版本覆盖必须在注释中带 issue 链接 + 移除计划
- Forbidden：`xxx-all` 包（如 `hutool-all` → 用 `hutool-core`）
- Forbidden：Swagger / SpringDoc / Springfox 依赖

---

## Code Review Checklist

- [ ] Controller 无业务逻辑，无 Mapper/JdbcTemplate 注入
- [ ] 写操作有 `@Transactional(rollbackFor = Exception.class)`
- [ ] 无空 catch
- [ ] API 契约无 `Map<String,Object>`
- [ ] 状态门禁规则在命令入口与候选查询入口保持一致
- [ ] 所有 `@Scheduled` 在 `task/` 包内 + ShedLock
- [ ] 无魔法数字
- [ ] 所有文件在尺寸上限内
- [ ] 父子 build 治理（无未管理的子模块版本漂移）
- [ ] 命令 API 重活走"异步受理"契约 + afterCommit 分发
- [ ] `mvn clean package -DskipTests` 通过
