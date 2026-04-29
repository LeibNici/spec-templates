# 字典与关联字段策略

> 本文件解决两类高频架构决策：**字典数据归属**与**关联字段类型**。
> 与 `database-guidelines/_index.md`（DDL 标准）、`naming-conventions.md`（响应层枚举字段铁律）、`frontend/hook-guidelines.md`（前端 useDict）配套使用。

---

## 一、字典策略（双轨制）

**铁律**：禁止任何形式的硬编码字典——前端 `Record<string,string>` 字典、后端 `if/else` 中文判断、SQL 里写死的状态字符串都不允许。

但分两条轨道，**用错轨道反而是反模式**：

| 类型 | 例子 | 归属 | 为什么 |
|---|---|---|---|
| **系统枚举**<br>仅发版变更 | 订单状态 PENDING/APPROVED/SHIPPED、审批动作 APPROVE/REJECT、HTTP 错误码、操作类型 | Java `enum` 类<br>+<br>前端 `src/constants/*-status.ts` | 业务逻辑 `if (status == APPROVED)` 走编译期类型检查；写入 DB 反而引入"字典丢失"故障面 |
| **业务字典**<br>运行时可配 | 客户类型、地区、回款方式、物料分类、设备分组、岗位类别 | DB `sys_dict_type` + `sys_dict_data`<br>+<br>前端 `useDict('xxx')` composable | 业务运营要能加减选项，不能为加一个"政府客户"分类发版 |

### 分界线判定

问自己：**这个值是不是业务逻辑分支依赖的？**
- ✅ 是 → 系统枚举（Java enum）
- ❌ 否（仅展示 / 筛选 / 配置）→ 业务字典（DB）

边界例子：
- 订单状态 `WAITING_PRODUCTION`：业务逻辑要根据状态走不同流程 → **系统枚举**
- 客户行业（制造业/服务业/零售业）：仅作展示和筛选维度 → **业务字典**
- 优先级 P0/P1/P2：常用业务分支 → 系统枚举（部分场景下可争议）

**判错代价不对称**：把系统枚举做成 DB 字典只是"麻烦一点"；把业务字典做成 enum，每次新增分类要发版+编译，运营投诉到产品。

---

## 二、字典 schema 标准（业务字典）

抄 RuoYi 标准（中文 Java 后台事实标准），适配本项目 BaseEntity：

```sql
CREATE TABLE IF NOT EXISTS `sys_dict_type` (
  `id`         BIGINT       NOT NULL                COMMENT '主键ID（雪花）',
  `dict_type`  VARCHAR(64)  NOT NULL                COMMENT '字典类型 code，如 customer_type',
  `dict_name`  VARCHAR(64)  NOT NULL                COMMENT '字典名称（管理后台显示）',
  `status`     TINYINT      NOT NULL DEFAULT 1      COMMENT '0禁用 1启用',
  `remark`     VARCHAR(255) DEFAULT NULL            COMMENT '备注',
  `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_by`   VARCHAR(64) DEFAULT NULL,
  `update_by`   VARCHAR(64) DEFAULT NULL,
  `deleted`     TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_dict_type` (`dict_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='字典类型表';

CREATE TABLE IF NOT EXISTS `sys_dict_data` (
  `id`         BIGINT       NOT NULL                COMMENT '主键ID（雪花）',
  `dict_type`  VARCHAR(64)  NOT NULL                COMMENT '关联 sys_dict_type.dict_type',
  `dict_code`  VARCHAR(64)  NOT NULL                COMMENT '字典值 code，如 VIP',
  `dict_label` VARCHAR(64)  NOT NULL                COMMENT '字典值显示名，如 大客户',
  `sort`       INT          NOT NULL DEFAULT 0      COMMENT '排序',
  `status`     TINYINT      NOT NULL DEFAULT 1      COMMENT '0禁用 1启用',
  `extra`      VARCHAR(500) DEFAULT NULL            COMMENT '附加属性（JSON：颜色/图标/CSS class）',
  `remark`     VARCHAR(255) DEFAULT NULL,
  `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_by`   VARCHAR(64) DEFAULT NULL,
  `update_by`   VARCHAR(64) DEFAULT NULL,
  `deleted`     TINYINT     NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_dict_data` (`dict_type`, `dict_code`),
  KEY `idx_dict_type` (`dict_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='字典数据表';
```

### 业务表如何用业务字典

```sql
-- ❌ 错误：把 dict_label 存进业务表（中文/可变值进表 = 字典改名后业务表全脏）
CREATE TABLE oms_customer (
  ...
  customer_type VARCHAR(64) NOT NULL COMMENT '客户类型，如 大客户'  -- 中文
);

-- ✅ 正确：业务表存 dict_code，前端通过 dict_type + dict_code 映射 dict_label
CREATE TABLE oms_customer (
  ...
  customer_type VARCHAR(64) NOT NULL COMMENT '客户类型 code（关联 sys_dict_data.dict_code，dict_type=customer_type）'
);
```

### 后端响应层

```java
// ✅ 透传 code，让前端 useDict 映射
return CustomerVO.builder()
    .customerType(customer.getCustomerType())  // "VIP" 字符串
    .build();

// ❌ 后端越权翻译为 label
return CustomerVO.builder()
    .customerType(dictService.getLabel("customer_type", customer.getCustomerType()))  // "大客户"
    .build();
```

详见 `naming-conventions.md` "响应层枚举字段（铁律）"。

### 缓存策略

字典数据**必须缓存**（Redis 或 Caffeine 本地）：

- key 格式：`dict:data:{dict_type}` → `List<DictDataVO>`
- TTL：2h
- 失效：管理后台 update / insert / delete `sys_dict_data` 时 `@CacheEvict("dict:data:" + dictType)`
- 启动预热：`ApplicationRunner` 把所有 `status=1` 的字典预加载

---

## 三、关联字段策略

### 3.1 默认：业务关联存 ID（不建 DB FK 约束）

```sql
CREATE TABLE oms_order (
  id              BIGINT      NOT NULL,
  order_no        VARCHAR(64) NOT NULL,
  customer_id     BIGINT      NOT NULL COMMENT '客户ID（应用层 join sys_customer）',
  product_id      BIGINT      NOT NULL COMMENT '产品ID',
  ...
  KEY idx_customer_id (customer_id),
  KEY idx_product_id  (product_id)
);
```

**铁律**（与阿里 P3C 一致）：

- 字段名：`xxx_id`（明示是 ID 关联）
- **DB 层不建 `FOREIGN KEY` 约束**（分库分表后失效；级联删除危险；迁移成本高）
- 应用层在 Service 或 Mapper XML 内 LEFT JOIN 拿展示字段
- 列表 API 返回 VO 时**包含展示字段**（如 `customerName`），前端不再二次查

**展示字段拼装方式**（任选其一）：

```xml
<!-- ✅ 方案 A：Mapper XML 内 LEFT JOIN -->
<select id="pageOrder" resultMap="OrderVOMap">
  SELECT o.*, c.customer_name AS customerName
  FROM oms_order o
  LEFT JOIN sys_customer c ON c.id = o.customer_id
  WHERE o.deleted = 0
</select>
```

```java
// ✅ 方案 B：Service 内批量预加载（适合多关联表）
List<Order> orders = orderMapper.selectList(...);
Set<Long> customerIds = orders.stream().map(Order::getCustomerId).collect(toSet());
Map<Long, String> customerNameMap = customerService.batchGetNames(customerIds);
return orders.stream()
    .map(o -> toVO(o, customerNameMap.get(o.getCustomerId())))
    .toList();
```

### 3.2 例外：审计快照场景

合同条款、审批记录、合规留痕——**冻结当时的值**：

```sql
CREATE TABLE oms_contract (
  ...
  signer_id              BIGINT      NOT NULL COMMENT '签约人 ID（关联 sys_user）',
  signer_name_snapshot   VARCHAR(64) NOT NULL COMMENT '签约时的姓名快照（用户改名后此字段不变，审计需要）',
  signed_at              DATETIME    NOT NULL,
  ...
);
```

**判定标准**：业务上"修改了用户信息后历史记录是否应该跟着变"？
- 应该跟着变 → 仅存 ID（多数业务表）
- 不应该跟着变 → 存 ID + `_snapshot` 字段（合同 / 审批 / 留痕）

**反模式**：因为"懒得 JOIN"就把所有关联字段都做成快照——会引入数据漂移和理解成本。

### 3.3 公共审计字段（BaseEntity）—— 本项目特例

**本项目 BaseEntity 用 VARCHAR(64) username（沿用 RuoYi 生态）**：

```java
public class BaseEntity {
    private Long id;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private String createBy;   // ⚠️ 用户名字符串，不是 user_id
    private String updateBy;   // ⚠️
    private Integer deleted;
}
```

```sql
create_by  VARCHAR(64)  DEFAULT NULL COMMENT '创建人（用户名）',
update_by  VARCHAR(64)  DEFAULT NULL COMMENT '更新人（用户名）',
```

**为什么不是 user_id**：

| 选择 | VARCHAR username（本项目） | BIGINT user_id（大厂主流） |
|---|---|---|
| 用户改名 | 历史记录显示旧名 | 历史记录显示新名 |
| 审计语义 | ✅ 自带快照 | 需要单独 snapshot 字段 |
| 列表展示 | 直接读 | 需 JOIN |
| 跨服务 | 简单（不依赖 user-service） | 需 user 服务或冗余 |
| 工程改造成本 | — | 极高（所有 Mapper/VO/前端联动） |

**结论**：本项目业务关联用 ID（按 §3.1），但公共审计字段用 username（沿用历史 + 审计快照需求）。**这是有意决策，不是设计漏洞**。

**禁止**：
- 在新业务表里把 `create_by` 改成 `BIGINT`（破坏 BaseEntity 一致性）
- 在 BaseEntity 之外另开 `creator_id BIGINT` 字段（与 `create_by` 重复，徒增混乱）

如果某业务确实需要按 user_id 关联（如"我创建的订单"列表用 SSO 返回的 user_id 过滤），则**用 username 过滤**：先把 token 中的 user_id 转成 username 再 `WHERE create_by = #{username}`。

### 3.4 跨服务 / 高频展示性能场景

**冗余字段 + 显式注释**：

```sql
CREATE TABLE oms_order (
  ...
  customer_id    BIGINT      NOT NULL COMMENT '客户ID',
  customer_name  VARCHAR(64) NOT NULL COMMENT '冗余：客户名快照（来源 sys_customer，列表高频展示，定时同步）',
  ...
);
```

**铁律**：冗余字段必须在 COMMENT 里**明示来源**和**同步策略**——否则后续维护无法判断是有意冗余还是数据漂移。

适用场景：
- 列表展示是高频接口，JOIN 拖慢响应（QPS > 100）
- 跨服务调用，无法 JOIN
- 报表 / 导出场景需要历史快照

不适用场景：
- 仅为"懒得 JOIN"
- 内部管理后台（QPS 低，JOIN 完全够）

---

## 四、决策树

```
关联到另一张表的字段，怎么存？
│
├─ 是公共审计字段（create_by / update_by）？
│   └─ ✅ VARCHAR(64) username（本项目特例，BaseEntity 已定）
│
├─ 是业务关联的主字段（订单→客户、订单→产品）？
│   ├─ 业务上"改名后历史是否应该跟着变"？
│   │   ├─ 是 → ✅ 仅存 ID + JOIN 拿展示字段
│   │   └─ 否（合同/审批/留痕） → ✅ ID + _snapshot 双字段
│   └─ DB 层 ❌ 不建 FOREIGN KEY 约束
│
├─ 是高频展示且 JOIN 性能瓶颈？
│   └─ ✅ ID（主存）+ 冗余 _name 字段，COMMENT 明示来源 + 同步策略
│
└─ 是字典值（客户类型 / 地区 / 物料分类）？
    └─ ✅ 存 dict_code（VARCHAR），关联 sys_dict_data，前端 useDict 映射 label
```

---

## 五、Review 清单

新增业务表 / 字段时 PR 必过：

- [ ] 关联字段命名是 `xxx_id`（ID 派）或 `xxx_code`（字典派）
- [ ] DB 层无 `FOREIGN KEY` 约束
- [ ] 公共字段（create_by/update_by）走 BaseEntity，未单独覆写
- [ ] 冗余字段（如 `customer_name` 与 `customer_id` 并存）COMMENT 已说明来源 + 同步方式
- [ ] 业务字典字段（如 `customer_type`）类型是 VARCHAR，存 dict_code 不存 dict_label
- [ ] 系统枚举字段（如 `order_status`）有对应的 Java `*Enum` 类
- [ ] VO 响应：枚举/字典字段透传 code，**禁止**调 `dictService.getLabel()` 或 `Enum.getLabel()` 翻译
- [ ] 审计快照场景（合同/审批）有 `_snapshot` 字段且 COMMENT 说明
