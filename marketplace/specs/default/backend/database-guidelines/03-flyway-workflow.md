# 03 · Flyway Migration Workflow

## 目录与命名

- migration 目录：`{app-module}/src/main/resources/db/migration/`
- 命名规范：`V{N}__{domain}_{desc}.sql`，例如 `V9__add_oms_contract_table.sql`
- 版本号 `{N}`：单调递增整数，**不可跳号、不可重用、不可修改已部署文件**

## 硬性规则

1. **已部署 V 文件不可修改**：Flyway 用 checksum 校验，改动会导致 `Validate failed: Migration checksum mismatch` 启动失败
2. **不可跳号**：V1→V3（跳过 V2）会导致 `validate-on-migrate` 失败
3. **不可手改 DB**：所有 schema 变更（DDL/INSERT seed）必须通过新 V 文件
4. **不可在业务层注入 Flyway Bean**：Flyway 由 Spring Boot 启动时自动触发
5. **clean 禁用**：`application.yml` 必须配 `spring.flyway.clean-disabled: true`

## 配置（`application.yml`）

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

## 错误矩阵

| 启动报错 | 原因 | 修复 |
|---|---|---|
| `Validate failed: Migration checksum mismatch` | V 文件被修改 | 恢复原文件或生产用 `flyway repair` |
| `Detected failed migration to version X` | 上次 V{X} 执行失败留残 | 查 `flyway_schema_history success=0`，清理半成品 |
| `Found non-empty schema(s) without schema history table` | 非空库首次接入 | 配置 `baseline-on-migrate: true` + `baseline-version=N` |
| `Unable to insert row for version X` | DB 账号无 history 表写权限 | `GRANT ALL PRIVILEGES ON db.* TO ...` |

## 数据迁移（不属于 Flyway 范围）

- Flyway **只管 schema，不管数据**
- 业务数据迁移用 `mysqldump --no-create-info --complete-insert` 手工处理
- 基础种子数据（admin 账号/角色/菜单/基础字典）用 `V{N}__seed_xxx.sql` 迁移
