# Backend Naming Conventions

> 目标：命名可读、语义一致、跨层不漂移。
> 适用范围：所有后端模块（common / framework / integration / biz / admin）。

---

## 1. 总原则（必须遵守）

1. **语义优先于简写**：`plannedStartDate` 优于 `psd`
2. **单一概念单一命名**：同一概念在同一层不要出现 `status/state/flag` 混用
3. **字段名、getter/setter、DB 列语义一致**：禁止"字段 A + getter B"的别名式实现
4. **跨层名称尽量一致**：Entity → VO → TS interface 默认同名，仅边界转换时允许映射
5. **禁止模糊名**：`data`, `info`, `temp`, `obj`, `map1`, `list2`

---

## 2. 包与目录命名

| 对象 | 规范 | 示例 |
|---|---|---|
| package | 全小写，按模块分层 | `com.{org}.{biz}.service.impl` |
| 目录 | 与 package 一致 | `src/main/java/.../controller` |
| 资源目录 | `mapper/` 固定 | `src/main/resources/mapper` |

---

## 3. 类型命名（类 / 接口 / 枚举）

| 类型 | 后缀/模式 | 示例 |
|---|---|---|
| Controller | `*Controller` | `OrderController` |
| Service 接口 | `*Service` | `OrderService` |
| Service 实现 | `*ServiceImpl` | `OrderServiceImpl` |
| Mapper | `*Mapper` | `OrderMapper` |
| Entity | 业务名词，**不加** `Entity` 后缀 | `Order` |
| DTO | `*DTO` | `OrderCreateDTO` |
| VO | `*VO` | `OrderProgressVO` |
| Command / Request | `*Command` / `*Request` | `ConfirmOrderCommand` |
| Event | `*Event` | `OrderShippedEvent` |
| Task / Job | `*Task` / `*Job` | `OrderSyncJob` |
| Enum | `*Enum`（或业务明确常量类） | `OrderStatusEnum` |
| 常量类 | `*Constants`，`final + private ctor` | `OrderConstants` |

### 禁止

- `XxxService` 与 `XxxManager` 同时表示同一职责
- `Util` 泛化大杂烩（应拆分为领域化工具类）
- `DTO/VO` 放在 `domain/` 包（放 `dto/`、`vo/`）

---

## 4. 字段命名

### 4.1 Java 字段

- `lowerCamelCase`
- 布尔字段优先语义词：`enabled`, `deleted`, `locked`（避免 `isIsEnabled`）
- 时间字段按粒度：`*Date`（日期）、`*Time`（日期时间）、`*At`（审计时间点）
- 数量/金额/比率明确后缀：`*Qty`, `*Amount`, `*Rate`

### 4.2 Entity 与 DB 列

- DB 列：`snake_case`
- Entity 字段：与列通过 camel↔snake 自动映射
- `@TableField` 仅允许 `exist=false`
- 发现语义不一致时：
  1. 优先改 Java 字段名对齐列名
  2. 若列名不合理，新增 Flyway 迁移改列名，再同步 Java
  3. 禁止用 `@TableField("xxx")` 掩盖偏差

### 4.3 Getter/Setter 一致性（强制）

- getter/setter 必须与字段同名语义一致
- 禁止"字段 `status` + getter `getFreezeFlag()`"这类跨语义别名
- 若需兼容旧接口，优先在转换层（Assembler/Mapper）处理，不在 Entity 内做双语义访问器

---

## 5. 方法命名

| 层 | 命名动词 | 示例 |
|---|---|---|
| Controller | `list/get/create/update/delete/confirm/reject` | `confirmOrder` |
| Service | 业务动作 + 对象 | `freezeInventory`, `allocateStock` |
| Mapper | `select/insert/update/delete + By...` | `selectByOrderNo` |
| Query Service | `query/page/list/find`（只读） | `pageOrder` |
| Command Service | `create/confirm/cancel/dispatch`（写） | `dispatchOrder` |

### 禁止

- `getXxx` 内执行写操作
- `saveXxx` 既创建又审核又推送外部系统（应拆分）
- 布尔参数控制分支：`start(id, true)`（改为 `start` / `forceStart`）

---

## 6. 常量命名

- `private static final` 使用 `UPPER_SNAKE_CASE`
- 常量名必须带单位/语义：`DEFAULT_LOCK_MINUTES`，不要 `DEFAULT_VALUE`
- 魔法数字必须提取常量（`0/1/-1` 例外）

---

## 7. SQL / 索引 / Flyway 命名

| 对象 | 规范 | 示例 |
|---|---|---|
| 表名 | `module_entity` | `oms_order` |
| 主键 | `id` | `BIGINT NOT NULL` |
| 状态列 | `*_status`（枚举语义）或明确业务名 | `order_status` |
| 标记列 | `*_flag` 或明确含义 | `freeze_flag` |
| 索引 | `idx_*` / `uk_*` | `idx_oms_order_customer_id` |
| Flyway | `V{N}__{domain}_{desc}.sql` | `V11__oms_add_priority_column.sql` |

---

## 8. 缩写白名单

允许：`id`, `no`, `qty`, `vo`, `dto`, `api`, `url`, `ip`, `db`, `sql`, `sku`, `erp`。
其他缩写默认禁止，除非在模块 README/Spec 中定义。

---

## 9. Review 清单（命名专项）

- [ ] 类名是否体现职责与层级（Controller/Service/Mapper/DTO/VO）
- [ ] Entity 字段是否可由 camel↔snake 自动映射
- [ ] 是否出现 `@TableField("col")` 用于列名映射（禁止）
- [ ] getter/setter 与字段语义是否一致
- [ ] 方法名是否与行为一致（读写分离）
- [ ] 常量命名是否明确语义与单位
- [ ] 新增状态字段是否避免泛化 `status`（有歧义时加领域前缀）
- [ ] VO/Mapper.toFrontend 响应枚举字段是否直接透传 code（禁止调用 `Enum.getLabel()` 覆盖原字段）

### 响应层枚举字段（铁律）

```java
// FORBIDDEN：Mapper/VO 构造响应时做 code→label 翻译
m.put("status", OrderStatus.getLabel(s.getStatus()));

// CORRECT：透传 code，label 交给前端 src/constants
m.put("status", s.getStatus());

// CORRECT（双字段，确需 label 的场景如 Excel 导出）
m.put("status", s.getStatus());
m.put("statusText", OrderStatus.getLabel(s.getStatus()));
```

此规则覆盖所有出参字段：`status`/`type`/`priority`/`category` 等。

---

## 10. 反例与正例

### 反例（禁止）

```java
private Integer status; // 实际是冻结标记

public Integer getFreezeFlag() { // 字段和 getter 语义不一致
    return status;
}
```

### 正例 A（保持现状，不改 DB）

```java
private Integer status; // 冻结标记：0正常 1冻结
```

### 正例 B（语义升级，改 DB）

```sql
ALTER TABLE wms_inventory CHANGE COLUMN status freeze_flag TINYINT NOT NULL DEFAULT 0;
```

```java
private Integer freezeFlag;
```
