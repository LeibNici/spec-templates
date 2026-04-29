# 04 · Entity 映射规则

## BaseEntity 继承（Required）

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

## @TableName（Required）

每个 Entity 必须声明 `@TableName("actual_table_name")`，即使类名与表名符合驼峰→下划线映射。

## @TableField 策略

| 场景 | @TableField | 正确做法 |
|---|---|---|
| Java camelCase ↔ DB snake_case（自动映射） | 禁止冗余标注 | `private String orderNo;` → `order_no` ✅ |
| 非数据库字段 | `exist=false` | `@TableField(exist = false) private List<Item> items;` ✅ |

**仅允许 `exist=false` 用途。禁止用 `@TableField` 做列名映射。**

## 禁止用 @TableField 掩盖命名偏差

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

## VO/DTO 包位置

- VO/DTO/Command 对象放在 `dto/` 或 `vo/` 包，禁止放在 `domain/` 包
- `domain/` 包仅放持久化实体（Entity）

## Entity × DDL 必填字段契约（Required-Field Contract）

**铁律**：DDL 中声明为 `NOT NULL` **且无 `DEFAULT`** 的列，MP insert 时必须保证 Entity 字段非 null，否则 MySQL 抛 `Field 'xxx' doesn't have a default value` → `DataIntegrityViolationException` → 400。

**选其一**（优先级从上到下）：

| 方案 | 适用场景 | 示例 |
|---|---|---|
| DDL 加 DEFAULT | 枚举状态列、开关字段 | `status VARCHAR(20) NOT NULL DEFAULT 'PENDING'` |
| 调用方显式 setter | 业务语义决定的字段 | `order.setOrderNo(generated)` before `insert` |
| `@TableField(fill=INSERT)` + MetaObjectHandler | 公共填充字段（createBy / createTime） | 见 `BaseEntity` |

**禁止**：`new Entity()` 只 set 主键或部分字段就 `mapper.insert()`，依赖 DDL"默认会有默认值"。

## 反例

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
1. 读路径别 insert（GET 无副作用，见 `../code-smell-prevention/06-method-design.md §6.1`）
2. 必须 insert 时，在 Entity 显式 set 所有 NOT NULL 无 DEFAULT 列
3. 或 Flyway 新增 migration 给列加 DEFAULT（适合枚举默认状态列）

## 新增 DDL/Entity 检查清单

- [ ] 新 `NOT NULL` 列是否有业务默认值？有 → 加 `DEFAULT`；无 → 确认所有写入点显式赋值
- [ ] Entity 新字段是否对应 DB 列？用自动映射，不用 `@TableField("...")` 掩盖偏差
- [ ] 所有 `mapper.insert(entity)` 调用点是否覆盖新增列？grep `new XxxEntity()` 检查赋值路径
- [ ] 批量导入/定时任务路径也要检查（首次运行才会触发空列 bug）
