# 01 · SQL Ownership Rules

| 场景 | 位置 | 方法 |
|---|---|---|
| 单表 CRUD | Service | `BaseMapper<T>` + `LambdaQueryWrapper` |
| JOIN / 子查询 | Mapper XML | `resources/mapper/XxxMapper.xml` |
| 复杂动态查询 / 聚合 | Mapper XML | `<if>` / `<choose>` / `<foreach>` |
| 批量写（≤ 500/批） | Mapper XML | `<foreach>` 或 `SqlSession(BATCH)` + `flushStatements` |

## Forbidden

- `@Select` / `@Insert` / `@Update` / `@Delete` 注解 SQL（全部走 XML）
- Controller / Service 中出现 SQL 字符串或 `JdbcTemplate`
- MP `saveBatch` 用于 > 50 条记录（伪批量，循环单插）
- 多表查询用多次单表查询 + Service 内手工 join

> 日志/流水类表（操作日志、审计、消息记录、状态历史）的特化规范——冗余列、月分区、AOP 写入、三层归档，见 [`../high-volume-tables/_index.md`](../high-volume-tables/_index.md)。
