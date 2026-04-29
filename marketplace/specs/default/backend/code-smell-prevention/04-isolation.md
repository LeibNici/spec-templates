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
