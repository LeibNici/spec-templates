# Code Smell Prevention Rules

> 重构实战沉淀的防腐检查清单。开发时先 grep 自查，避免规模化漂移。

---

## 1. 弱类型传递（全链路禁止）

**铁律：全链路禁止 `Map<String,Object>` / `JSONObject` / `Object` 作为方法签名的入参或返回值。**

| 层 | 入参 | 返回 |
|---|---|---|
| Controller | DTO + `@Valid` | `R<VO>` |
| Service | DTO / Command / 具体类型 | VO / Entity / 具体类型 |
| Mapper | `@Param` 具体类型 | Entity / VO |

**唯一例外**：`CrossModuleMapper` 返回 `Map` 且调用方在同一方法内立即转为 VO。

### Forbidden

```java
// Service 签名用 Map
void approve(Map<String, Object> params);
Map<String, Object> getDashboard();

// Mapper 返回 List<Map> 且直接透传到 Controller
List<Map<String, Object>> listOrders();

// 用 Object 逃避泛型
R<Object> getOrder(Long id);

// JSONObject 在 Service 间传递
JSONObject data = new JSONObject();
data.put("orderNo", orderNo);
otherService.process(data);
```

---

## 2. 单一职责（SRP）

**一个 ServiceImpl 只承担一个职责域。超过 2 个职责域时必须拆分。**

### 职责域分类

| 职责域 | 命名模式 | 示例 |
|---|---|---|
| 核心 CRUD | `XxxServiceImpl` | OrderServiceImpl |
| 同步/定时 | `XxxSyncServiceImpl` | OrderSyncServiceImpl |
| 导入/导出 | `XxxImportServiceImpl` | BomImportServiceImpl |
| 查询/报表 | `XxxQueryServiceImpl` | OrderQueryServiceImpl |
| 工作流 | `XxxWorkflowServiceImpl` | DeliveryWorkflowServiceImpl |
| 分析/统计 | `XxxAnalysisServiceImpl` | InventoryAnalysisServiceImpl |

### 拆分信号

- ServiceImpl 超过 500 行
- 一个类注入 > 8 个依赖
- 方法间无共享状态（互相不调用）
- 存在 `@Scheduled` + CRUD + 报表在同一类

---

## 3. 硬编码

### 3.1 状态值常量化

```java
// FORBIDDEN: 裸字符串散落各处
order.setStatus("WAITING_PRODUCTION");
if ("COMPLETED".equals(order.getStatus())) { ... }

// CORRECT: 常量类集中定义
public final class OrderStatus {
    public static final String WAITING = "WAITING_PRODUCTION";
    public static final String COMPLETED = "COMPLETED";
    private OrderStatus() {}
}
order.setStatus(OrderStatus.WAITING);
```

**规则：同一状态字符串出现 ≥2 处，必须提取为常量。**

### 3.2 业务阈值可配

```java
// FORBIDDEN: 硬编码阈值
if (daysUntilPurchase <= 7) { urgency = "URGENT"; }

// CORRECT: 配置表或 @Value
private static final int WARNING_THRESHOLD_DAYS =
    Integer.parseInt(configService.getValue("mrp.warning.days", "7"));
```

### 3.3 日期格式集中

```java
// FORBIDDEN: "yyyy-MM-dd" 散落 N 处
LocalDate.parse(s, DateTimeFormatter.ofPattern("yyyy-MM-dd"));

// CORRECT: 常量定义
public final class DateFormats {
    public static final DateTimeFormatter ISO_DATE = DateTimeFormatter.ofPattern("yyyy-MM-dd");
}
```

### 3.4 数字字面量

除 `0 / 1 / -1` 外，所有数字字面量必须命名为 `private static final` 常量。

---

## 4. 防腐层（模块边界隔离）

**模块边界 = 防腐边界。跨模块只通过 Service 接口或 CrossModuleMapper。**

### 允许的跨模块访问方式

| 方式 | 适用场景 | 示例 |
|---|---|---|
| CrossModuleMapper (XML) | 只读查询，同数据库 | OrderCrossModuleMapper 查 `inventory_record` |
| 模块 Service 接口 | 读写操作 | `omsApiLogService.getLastSyncTime()` |
| Spring Event | 解耦通知 | `OrderShippedEvent` |

### Forbidden

```java
// 直接注入外模块 Mapper
@Autowired private OrderMapper orderMapper; // ← 在 inventory 模块中

// 直接注入外模块 Entity
import com.{org}.oms.domain.SalesOrder; // ← 在 inventory 模块中

// JdbcTemplate 绕过 ORM
jdbcTemplate.queryForList("SELECT * FROM oms_sales_order WHERE ...");

// Service 中拼 SQL 表名
String sql = "SELECT * FROM " + tableName;
```

### CrossModuleMapper 规范

- 每模块最多一个：`XxxCrossModuleMapper`
- 返回 `Map<String, Object>` 或本模块 VO，禁止返回外模块 Entity
- XML 中 SQL 必须注释说明查询的是哪个模块的表
- 只做只读查询；跨模块写入必须通过 Service 接口

---

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

---

## 6. 方法设计

| 规则 | 说明 |
|---|---|
| 禁止 Boolean 参数 | `start(id, true)` → 拆为 `start(id)` + `forceStart(id)` |
| 位置参数 ≤ 5 | 超过则封装为 DTO/Command |
| 方法 ≤ 80 行 | 超出则提取子方法 |
| 命名与行为一致 | `getXxx` 无副作用；`saveXxx` 不做查询；`deleteXxx` 不返回新建对象 |
| 写操作返回结果 | `void save(order)` → `Order save(order)`，调用方无需再查 |
| 查询方法不写入 | 带 `query/list/get/page/find` 前缀的方法禁止包含写操作 |
| `getOrCreateXxx` 反模式 | Query/GET 路径禁止此类方法；物化/快照建行只能在 Sync/Job 写路径 |

### 6.1 反模式：GET 路径隐式写库（快照占位行）

**症状**：查询接口首次调用向 `xxx_snapshot / xxx_progress` 表插入一行"空占位"，之后读取。

```java
// FORBIDDEN: GET 路径写库 + 插空记录依赖 DDL 默认值
@Override
public OrderProgressVO getOrderProgress(Long orderId) {
    OrderProgress snapshot = getOrCreateSnapshot(orderId);  // ← 查询里 insert
    return toVo(order, snapshot);
}
private OrderProgress getOrCreateSnapshot(Long orderId) {
    OrderProgress p = mapper.selectOne(...);
    if (p == null) {
        p = new OrderProgress();  // 只填 orderId，依赖 DDL 默认值
        p.setOrderId(orderId);
        mapper.insert(p);          // DDL 若 stage NOT NULL 无 DEFAULT 即炸
    }
    return p;
}
```

**问题**：
1. 违反 `getXxx` 无副作用铁律
2. 与 DDL `NOT NULL` 无 DEFAULT 列存在隐式依赖，首行插入必炸
3. 多节点并发首次查询会触发唯一约束冲突/重复行

**正确做法**：
- 读路径 `selectOne(...)` 返回可能为 null，VO 装配侧判空
- 物化/快照行只由单写者（`XxxSyncServiceImpl` 定时任务 / `XxxJob`）创建
- 首次插入时必须显式赋值所有 NOT NULL 无 DEFAULT 列

---

## 7. 前后端一致性补充

| 规则 | 说明 |
|---|---|
| 成功码统一 | 后端 `code: 0` = 成功，前端判断 `code === 0` |
| 日期格式统一 | 后端 `LocalDateTime` → JSON ISO 8601 字符串，前端 dayjs 解析 |
| 枚举值来源统一 | 系统枚举 → 前端 `src/constants/`；业务字典 → dict API |
| 金额精度统一 | 后端 `BigDecimal` → JSON number，前端显示时 `toFixed(2)` |
| 分页参数统一 | `{ page: 1, size: 20 }` → 后端 `pageNum` / `pageSize` |
| 主键占位不预置 | 前端 `emptyForm()` 主键字段必须 `undefined`，禁止 `id: 0` / `id: ''`；否则 MP `@TableId(IdType.ASSIGN_ID)` 会被击穿，首次 INSERT id=0，第二次主键冲突 |

---

## 8. 历史违规文件的修正义务（铁律）

**铁律：修改任何文件前，必须先核对该文件是否已违反当前规范；若有违规，当次变更必须把整个文件按现行规范整体修正，不允许仅改新增部分、沿用旧写法、或以"preexisting tech debt / 不在本次范围"为理由保留违规代码。**

### Why

新代码跟随旧模式是规范漂移最大的根源。旧文件里的 `JdbcTemplate`、SQL 字符串、`Map<String,Object>` 等违规写法被当作参考模板，导致违规面持续扩散。长此以往，规范文档的权威性被稀释。

### 触发场景（非穷举）

- Service/Controller 内持有 `JdbcTemplate` 字段或出现 SQL 字符串
- Adapter / Service 方法签名回退到 `Map<String,Object>` / `JSONObject`
- 实体未继承 `BaseEntity`、手动维护 `id/createTime/...`
- Controller 内调用 `@Scheduled` / 注入 Mapper
- `@Select("...")` / `@Update("...")` 注解形式 SQL
- 跨模块直连他人 Entity / Mapper

### Forbidden

```java
// 文件已经持有 JdbcTemplate，我只改我新增的分支，不动老的 → 不允许
class XxxAdapterImpl {
    private final JdbcTemplate jdbcTemplate;           // 历史违规
    void oldMethod() { jdbcTemplate.update("INSERT..."); }   // 历史违规（不改）
    void newMethod() { jdbcTemplate.update("INSERT..."); }   // 新增但沿用旧写法 ❌
}
```

### Required

```java
// 新增 Mapper + XML，把整个文件里的 JDBC 写法一次性迁完
class XxxAdapterImpl {
    private final XxxBridgeMapper xxxBridgeMapper;
    void oldMethod() { xxxBridgeMapper.insertX(param); }  // 整体修正 ✓
    void newMethod() { xxxBridgeMapper.updateY(param); }  // 新增亦合规 ✓
}
```

### 执行检查清单

- [ ] 动某文件前先 grep：`JdbcTemplate` / `jdbcTemplate\.` / `"SELECT |"INSERT |"UPDATE |"DELETE ` / `Map<String,\s*Object>` 作为 Controller/Service 方法签名 / `@Select\(` / `@Update\(`
- [ ] 命中任一项即判定该文件违规，当次变更必须整体修正
- [ ] 若本次变更确实无法完成整体修正（如影响面过大），必须在 PR 描述中用独立任务挂起并给出修正计划
- [ ] 修正完成后再次 grep 同一批 pattern，确认该文件零命中

---

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

---

## 10. Dev/Test 基础设施反模式（铁律）

**铁律**：标记为 `dev` / `test` / `mock` / `Profile("dev")` 的 Java 代码**同样适用本 spec 全部约束**，不允许"因为是 dev 就绕过"。命名带 "Dev" 不是 spec 弱化区。

### 反模式

| # | 反模式 | 违反条款 |
|---|---|---|
| 1 | `@PostConstruct` 启动 Bean 直接 INSERT/UPDATE 业务表 | §3 硬编码 SQL + §4 防腐层 |
| 2 | `@Profile("dev")` Bean 用 JdbcTemplate 写 SQL 字符串绕开 Mapper | §1 弱类型传递 + §3 |
| 3 | dev/test 包跨模块直接操作业务表 | §4 防腐层 |
| 4 | 手动 ID 生成 `SELECT IFNULL(MAX(id),0)+1` | 项目 IdWorker/Snowflake 规范 |
| 5 | "种子数据"塞进 Java 启动钩子（不是 Flyway 也不是 Mapper） | 启动 Bean 不应改业务数据 |

### 正确做法

| 场景 | 正确路径 |
|---|---|
| Dev 环境一次性种子数据（不入生产） | `docs/dev-bootstrap.sql` 手工脚本，幂等 INSERT IGNORE |
| Dev 行为开关（关闭某些校验） | `application-{profile}.yml` + `@ConditionalOnProperty` |
| 测试 fixture 数据 | 测试代码用 Mapper / Service 接口，与 prod 同路径 |
| Mock 外部依赖 | 实现外部接口的 Mock 类（同 prod 类型签名），不直接操作业务表 |

### 检查清单（写 dev/test/mock 代码时）

- [ ] 是否在 `@PostConstruct` 里写了任何 INSERT/UPDATE 业务表？→ 改 docs/*.sql
- [ ] 是否用了 JdbcTemplate 写 SQL 字符串？→ 改 Mapper（与 prod 同路径）
- [ ] 是否跨模块直接操作另一模块的业务表？→ 改走 Service 接口或 CrossModuleMapper
- [ ] 是否手动拼 ID？→ 用 BaseEntity / IdWorker
- [ ] 命名是否暗示"临时"（Dev / Mock / Tmp）让 reviewer 心理放松？→ 标记不重要，规则一致
