# 02 · DDL 标准

| 规则 | 要求 |
|---|---|
| 字符集 | `utf8mb4` + `utf8mb4_general_ci`（禁 `utf8`、`0900_ai_ci`、`utf8mb4_unicode_ci`） |
| COMMENT | 表与列必须 COMMENT |
| 幂等 | `CREATE TABLE IF NOT EXISTS` |
| 迁移 | Flyway 管理（详见 [03-flyway-workflow.md](./03-flyway-workflow.md)） |
| ENUM | 禁用；用 `VARCHAR(30)` + 业务层枚举常量 |
| 索引 | ≤ 6 个/表；高频查询 EXPLAIN |
| 主键 | `BIGINT NOT NULL`（禁 `AUTO_INCREMENT`，由 MP `ASSIGN_ID` 雪花生成） |
| 命名 | Flyway 版本化 `V{N}__{domain}_{desc}.sql` |

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
