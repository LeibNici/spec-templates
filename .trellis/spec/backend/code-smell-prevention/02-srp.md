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
