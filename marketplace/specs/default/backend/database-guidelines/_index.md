# Backend Database Guidelines

> 适用：MySQL 8.0 + MyBatis-Plus 3.5 + Flyway

---

## Pattern Index

| Section | File |
|---|---|
| 1. SQL 归属（单表/JOIN/批量） | [01-sql-ownership.md](./01-sql-ownership.md) |
| 2. DDL 标准 + 公共字段 + Table Template | [02-ddl-standard.md](./02-ddl-standard.md) |
| 3. Flyway 迁移工作流 | [03-flyway-workflow.md](./03-flyway-workflow.md) |
| 4. Entity 映射规则（BaseEntity / @TableName / @TableField / NOT NULL 契约）| [04-entity-mapping.md](./04-entity-mapping.md) |
| 5. 分页 + GROUP BY 聚合模板 + MyBatis-Plus 约定 + Data Dictionary | [05-pagination-aggregation.md](./05-pagination-aggregation.md) |

---

## Quick Decision

```
新增 schema 变更
    ↓
单表 CRUD ──────→ Service + BaseMapper + LambdaQueryWrapper        见 01
JOIN/聚合 ──────→ Mapper XML（resultMap + COUNT(DISTINCT)）        见 01 / 05
新建表    ──────→ DDL 用 Table Template（utf8mb4 + 公共字段）       见 02
列变更    ──────→ Flyway V{N}__{domain}_{desc}.sql（不改已部署 V）  见 03
新建 Entity → @TableName + extends BaseEntity；不用 @TableField 列名映射  见 04
分页聚合查询 ──→ Page<VO> + Mapper XML + COALESCE(SUM())          见 05
```

---

## 配套规范

- 日志/流水类高写入表的特化规范（冗余列、月分区、AOP 写入、三层归档）：[`../high-volume-tables/_index.md`](../high-volume-tables/_index.md)
- Entity 字典字段与关联字段策略：[`../dict-and-relation-strategy.md`](../dict-and-relation-strategy.md)
- 字段命名规范：[`../naming-conventions.md`](../naming-conventions.md)
- 部署形态约束（ShedLock/Sentinel/读写分离）：[`../topology-agnostic.md`](../topology-agnostic.md)
