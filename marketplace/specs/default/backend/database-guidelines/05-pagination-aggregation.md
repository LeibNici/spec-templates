# 05 · 分页 + 聚合 + MyBatis-Plus 约定 + Data Dictionary

## MyBatis-Plus 约定

- 分页：`Page<T>`（MP 内置）
- 逻辑删除：`@TableLogic` 注在 `deleted` 字段
- 自动填充：`MetaObjectHandler` 处理 create_time/update_time/create_by/update_by
- 批量写：JDBC URL 加 `rewriteBatchedStatements=true`

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

> 业务字典与关联字段（存 ID 还是值）的完整策略，见 [`../dict-and-relation-strategy.md`](../dict-and-relation-strategy.md)。
