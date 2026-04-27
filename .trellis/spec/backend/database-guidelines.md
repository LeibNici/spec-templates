# Backend Database Guidelines

> 适用：MySQL 8.0 + MyBatis-Plus 3.5 + Flyway

## SQL Ownership Rules

| 场景 | 位置 | 方法 |
|---|---|---|
| 单表 CRUD | Service | `BaseMapper<T>` + `LambdaQueryWrapper` |
| JOIN / 子查询 | Mapper XML | `resources/mapper/XxxMapper.xml` |
| 复杂动态查询 / 聚合 | Mapper XML | `<if>` / `<choose>` / `<foreach>` |
| 批量写（≤ 500/批） | Mapper XML | `<foreach>` 或 `SqlSession(BATCH)` + `flushStatements` |

### Forbidden

- `@Select` / `@Insert` / `@Update` / `@Delete` 注解 SQL（全部走 XML）
- Controller / Service 中出现 SQL 字符串或 `JdbcTemplate`
- MP `saveBatch` 用于 > 50 条记录（伪批量，循环单插）
- 多表查询用多次单表查询 + Service 内手工 join

---

## DDL 标准

| 规则 | 要求 |
|---|---|
| 字符集 | `utf8mb4` + `utf8mb4_general_ci`（禁 `utf8`、`0900_ai_ci`、`utf8mb4_unicode_ci`） |
| COMMENT | 表与列必须 COMMENT |
| 幂等 | `CREATE TABLE IF NOT EXISTS` |
| 迁移 | Flyway 管理（详见下文） |
| ENUM | 禁用；用 `VARCHAR(30)` + 业务层枚举常量 |
| 索引 | ≤ 6 个/表；高频查询 EXPLAIN |
| 主键 | `BIGINT NOT NULL`（禁 `AUTO_INCREMENT`，由 MP `ASSIGN_ID` 雪花生成） |
| 命名 | Flyway 版本化 `V{N}__{domain}_{desc}.sql` |

---

## Flyway Migration Workflow

### 目录与命名

- migration 目录：`{app-module}/src/main/resources/db/migration/`
- 命名规范：`V{N}__{domain}_{desc}.sql`，例如 `V9__add_oms_contract_table.sql`
- 版本号 `{N}`：单调递增整数，**不可跳号、不可重用、不可修改已部署文件**

### 硬性规则

1. **已部署 V 文件不可修改**：Flyway 用 checksum 校验，改动会导致 `Validate failed: Migration checksum mismatch` 启动失败
2. **不可跳号**：V1→V3（跳过 V2）会导致 `validate-on-migrate` 失败
3. **不可手改 DB**：所有 schema 变更（DDL/INSERT seed）必须通过新 V 文件
4. **不可在业务层注入 Flyway Bean**：Flyway 由 Spring Boot 启动时自动触发
5. **clean 禁用**：`application.yml` 必须配 `spring.flyway.clean-disabled: true`

### 配置（`application.yml`）

```yaml
spring.flyway:
  enabled: ${SPRING_FLYWAY_ENABLED:true}
  locations: classpath:db/migration
  baseline-on-migrate: true
  baseline-version: 0
  table: flyway_schema_history
  encoding: UTF-8
  validate-on-migrate: true
  out-of-order: false
  placeholder-replacement: false  # SQL 含 ${xxx} 字面量时避免替换
  clean-disabled: true
```

### 错误矩阵

| 启动报错 | 原因 | 修复 |
|---|---|---|
| `Validate failed: Migration checksum mismatch` | V 文件被修改 | 恢复原文件或生产用 `flyway repair` |
| `Detected failed migration to version X` | 上次 V{X} 执行失败留残 | 查 `flyway_schema_history success=0`，清理半成品 |
| `Found non-empty schema(s) without schema history table` | 非空库首次接入 | 配置 `baseline-on-migrate: true` + `baseline-version=N` |
| `Unable to insert row for version X` | DB 账号无 history 表写权限 | `GRANT ALL PRIVILEGES ON db.* TO ...` |

### 数据迁移（不属于 Flyway 范围）

- Flyway **只管 schema，不管数据**
- 业务数据迁移用 `mysqldump --no-create-info --complete-insert` 手工处理
- 基础种子数据（admin 账号/角色/菜单/基础字典）用 `V{N}__seed_xxx.sql` 迁移

---

## 公共字段（Required）

```sql
`id`          BIGINT       NOT NULL                COMMENT '主键ID（雪花 MP ASSIGN_ID）',
`create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`create_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
`update_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
`deleted`     TINYINT      NOT NULL DEFAULT 0 COMMENT '逻辑删除 0=正常 1=已删',
```

> 主键 **不用 AUTO_INCREMENT**，由 MP `@TableId(type = ASSIGN_ID)` 在 Java 端用雪花算法生成。DDL 只需 `BIGINT NOT NULL`。

---

## Table Template

```sql
CREATE TABLE IF NOT EXISTS `{{table_name}}` (
  `id`          BIGINT       NOT NULL                COMMENT '主键ID（雪花）',
  `{{col}}`     VARCHAR(64)  NOT NULL                COMMENT '{{注释}}',
  `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by`   VARCHAR(64)  DEFAULT NULL             COMMENT '创建人',
  `update_by`   VARCHAR(64)  DEFAULT NULL             COMMENT '更新人',
  `deleted`     TINYINT      NOT NULL DEFAULT 0       COMMENT '逻辑删除 0=正常 1=已删',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_{{table_name}}_{{col}}` (`{{col}}`),
  KEY `idx_{{table_name}}_{{col}}` (`{{col}}`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='{{表注释}}';
```

---

## MyBatis-Plus 约定

- 分页：`Page<T>`（MP 内置）
- 逻辑删除：`@TableLogic` 注在 `deleted` 字段
- 自动填充：`MetaObjectHandler` 处理 create_time/update_time/create_by/update_by
- 批量写：JDBC URL 加 `rewriteBatchedStatements=true`

---

## Entity 映射规则

### BaseEntity 继承（Required）

所有持久化实体必须继承 `BaseEntity`，继承公共字段 `id / createTime / updateTime / createBy / updateBy / deleted`。

```java
// CORRECT
@TableName("oms_order")
public class Order extends BaseEntity {
    private String orderNo;
    private String customerName;
}

// FORBIDDEN: 手动重复定义公共字段
public class Order {
    private Long id;            // ← 已在 BaseEntity 中
    private LocalDateTime createTime; // ← 已在 BaseEntity 中
    private Integer deleted;    // ← 已在 BaseEntity 中
    private String orderNo;
}
```

### @TableName（Required）

每个 Entity 必须声明 `@TableName("actual_table_name")`，即使类名与表名符合驼峰→下划线映射。

### @TableField 策略

| 场景 | @TableField | 正确做法 |
|---|---|---|
| Java camelCase ↔ DB snake_case（自动映射） | 禁止冗余标注 | `private String orderNo;` → `order_no` ✅ |
| 非数据库字段 | `exist=false` | `@TableField(exist = false) private List<Item> items;` ✅ |

**仅允许 `exist=false` 用途。禁止用 `@TableField` 做列名映射。**

### 禁止用 @TableField 掩盖命名偏差

```java
// FORBIDDEN
@TableField("product_model")
private String productCode;  // ← Java 叫 code，DB 叫 model，语义矛盾

// CORRECT: 改 Java 字段名，让自动映射生效
private String productModel; // → 自动映射 product_model ✅
```

**铁律**：Java 字段名与 DB 列名必须语义一致，通过 `camelCase ↔ snake_case` 自动映射对应。当发现不一致时：
1. **改 Java 字段名**对齐 DB 列名（优先，影响范围可控）
2. 若 DB 列名本身不合理，走 **Flyway 迁移改 DB 列名**，再让 Java 字段自动对齐
3. **禁止**用 `@TableField("xxx")` 做列名映射来"解决"不一致——这是在掩盖问题

### VO/DTO 包位置

- VO/DTO/Command 对象放在 `dto/` 或 `vo/` 包，禁止放在 `domain/` 包
- `domain/` 包仅放持久化实体（Entity）

### Entity × DDL 必填字段契约（Required-Field Contract）

**铁律**：DDL 中声明为 `NOT NULL` **且无 `DEFAULT`** 的列，MP insert 时必须保证 Entity 字段非 null，否则 MySQL 抛 `Field 'xxx' doesn't have a default value` → `DataIntegrityViolationException` → 400。

**选其一**（优先级从上到下）：

| 方案 | 适用场景 | 示例 |
|---|---|---|
| DDL 加 DEFAULT | 枚举状态列、开关字段 | `status VARCHAR(20) NOT NULL DEFAULT 'PENDING'` |
| 调用方显式 setter | 业务语义决定的字段 | `order.setOrderNo(generated)` before `insert` |
| `@TableField(fill=INSERT)` + MetaObjectHandler | 公共填充字段（createBy / createTime） | 见 `BaseEntity` |

**禁止**：`new Entity()` 只 set 主键或部分字段就 `mapper.insert()`，依赖 DDL"默认会有默认值"。

### 反例

```java
// DDL: stage VARCHAR(30) NOT NULL COMMENT '阶段'   ← 无 DEFAULT
OrderProgress p = new OrderProgress();
p.setOrderId(orderId);           // stage 没 set
p.setSnapshotTime(LocalDateTime.now());
progressMapper.insert(p);
// → MySQL: Field 'stage' doesn't have a default value
// → 前端收到 400「数据校验失败，请检查输入内容」（真因被脱敏）
```

**修法**：
1. 读路径别 insert（GET 无副作用，见 `code-smell-prevention.md §6.1`）
2. 必须 insert 时，在 Entity 显式 set 所有 NOT NULL 无 DEFAULT 列
3. 或 Flyway 新增 migration 给列加 DEFAULT（适合枚举默认状态列）

### 新增 DDL/Entity 检查清单

- [ ] 新 `NOT NULL` 列是否有业务默认值？有 → 加 `DEFAULT`；无 → 确认所有写入点显式赋值
- [ ] Entity 新字段是否对应 DB 列？用自动映射，不用 `@TableField("...")` 掩盖偏差
- [ ] 所有 `mapper.insert(entity)` 调用点是否覆盖新增列？grep `new XxxEntity()` 检查赋值路径
- [ ] 批量导入/定时任务路径也要检查（首次运行才会触发空列 bug）

---

## 分页 + GROUP BY 聚合模板

场景：主列表按某维度（`material_code` / `order_no` / `product_model` …）**聚合**，子列表/明细走另一接口按 FK 拉详情。

### 硬性要求

- 必须走 **Mapper XML**（`LambdaQueryWrapper` 无法表达 `COUNT(DISTINCT)` / `SUM(CASE WHEN)`）
- MP 分页：Mapper 方法首参 `Page<VO>`，MP 拦截器自动加 `LIMIT`
- 返回类型是 **VO**（`vo/XxxGroupedVO`），**禁止**返回 Entity（聚合后已非实体概念）
- 必须 `resultMap` 显式映射列名 → VO 字段（别名用 camelCase）

### XML 模板

```xml
<resultMap id="OrderGroupedMap" type="com.{org}.{biz}.vo.OrderGroupedVO">
    <result column="customerCode"  property="customerCode"/>
    <result column="customerName"  property="customerName"/>
    <result column="orderTotal"    property="orderTotal"/>
    <result column="orderCount"    property="orderCount"/>
    <result column="pendingCount"  property="pendingCount"/>
</resultMap>

<select id="selectGroupedPage" resultMap="OrderGroupedMap">
    SELECT
        customer_code                                        AS customerCode,
        MAX(customer_name)                                   AS customerName,
        COALESCE(SUM(amount), 0)                             AS orderTotal,
        COUNT(DISTINCT order_no)                             AS orderCount,
        SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END)  AS pendingCount
    FROM oms_order
    WHERE deleted = 0
    <if test="customerCode != null and customerCode != ''">
        AND customer_code LIKE CONCAT('%', #{customerCode}, '%')
    </if>
    GROUP BY customer_code
    ORDER BY orderTotal DESC, customer_code ASC
</select>
```

### Mapper 接口签名

```java
Page<OrderGroupedVO> selectGroupedPage(
    Page<OrderGroupedVO> page,
    @Param("customerCode") String customerCode);
```

### 常见反模式

| 反模式 | 问题 | 修法 |
|---|---|---|
| Service 端先查全量再内存 `groupingBy` | 数据量大时 OOM + 分页错位 | 聚合下推 SQL |
| 返回 `Map<String,Object>` | 违反签名契约铁律，类型擦除丢失 | 定义 VO |
| 不用 `COUNT(DISTINCT)` 直接 `COUNT(*)` | 同一业务键被重复计数 | `COUNT(DISTINCT 业务键)` |
| 只写 `SUM`、不加 `COALESCE` | null 导致前端 `Number(null)` 显示 `NaN` | `COALESCE(SUM(...), 0)` |
| 无 `ORDER BY` | 分页翻页数据漂移 | 显式 ORDER BY 至少一列稳定排序 |
| 聚合列放 Entity 实体 | Entity 字段污染、Insert 路径踩坑 | 放 `vo/XxxGroupedVO` |

### 索引配合

- `GROUP BY` 列必须有索引
- 若表已触及"单表索引 ≤ 6"上限，先审计无用索引再新增
- EXPLAIN 应看到 `Using index for group-by` 或 `type=range/ref`，避免 `Using filesort + Using temporary`

---

## Data Dictionary

- code → name 映射在后端 dict 表维护
- 前端通过 dict API 全局复用
- Forbidden：前端硬编码 `Record<string, string>` 映射
