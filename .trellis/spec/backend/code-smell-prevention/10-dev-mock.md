## 10. Dev/Test 基础设施反模式（铁律）

**铁律**：标记为 `dev` / `test` / `mock` / `Profile("dev")` 的 Java 代码**同样适用本 spec 全部约束**，不允许"因为是 dev 就绕过"。命名带 "Dev" 不是 spec 弱化区。

### 反模式

| # | 反模式 | 违反条款 |
|---|---|---|
| 1 | `@PostConstruct` 启动 Bean 直接 INSERT/UPDATE 业务表 | §3 硬编码 SQL + §4 防腐层 |
| 2 | `@Profile("dev")` Bean 用 JdbcTemplate 写 SQL 字符串绕开 Mapper | §1 弱类型传递 + §3 |
| 3 | dev/test 包跨模块直接操作业务表 | §4 防腐层 |
| 4 | 手动 ID 生成 `SELECT IFNULL(MAX(id),0)+1` | 项目 IdWorker/Snowflake 规范 |
| 5 | "种子数据"塞进 Java 启动钩子（不是 Flyway 也不是 Mapper） | 启动 Bean 不应改业务数据 |

### 正确做法

| 场景 | 正确路径 |
|---|---|
| Dev 环境一次性种子数据（不入生产） | `docs/dev-bootstrap.sql` 手工脚本，幂等 INSERT IGNORE |
| Dev 行为开关（关闭某些校验） | `application-{profile}.yml` + `@ConditionalOnProperty` |
| 测试 fixture 数据 | 测试代码用 Mapper / Service 接口，与 prod 同路径 |
| Mock 外部依赖 | 实现外部接口的 Mock 类（同 prod 类型签名），不直接操作业务表 |

### 检查清单（写 dev/test/mock 代码时）

- [ ] 是否在 `@PostConstruct` 里写了任何 INSERT/UPDATE 业务表？→ 改 docs/*.sql
- [ ] 是否用了 JdbcTemplate 写 SQL 字符串？→ 改 Mapper（与 prod 同路径）
- [ ] 是否跨模块直接操作另一模块的业务表？→ 改走 Service 接口或 CrossModuleMapper
- [ ] 是否手动拼 ID？→ 用 BaseEntity / IdWorker
- [ ] 命名是否暗示"临时"（Dev / Mock / Tmp）让 reviewer 心理放松？→ 标记不重要，规则一致
