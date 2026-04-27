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
