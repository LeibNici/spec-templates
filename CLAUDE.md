# {Project Name} — 项目开发规范

> 本文件为铁律摘要，主对话级别强制生效。详细规范按主题拆分至 `.trellis/spec/`，按需加载。

---

## 技术栈（按项目实际填写）

| 层 | 技术 |
|---|---|
| 后端 | Java 17 + Spring Boot 3.x + Spring Security + jjwt + MyBatis-Plus 3.5 + MySQL 8.0 + Redis 7 + Flyway + ShedLock |
| 前端 | Vue 3 + TypeScript 5 + Vite 5 + Element Plus 2 + Pinia + Axios（拦截器 `return res.data`）+ dayjs |
| 构建 | Maven 多模块，父 pom `spring-boot-starter-parent` |

---

## 代码硬性上限（实战宽松档）

| 指标 | 上限 | 超限处理 |
|---|---|---|
| 函数 | ≤ 80 行 | 抽方法 |
| 文件 | ≤ 500 行 | 按职责拆类 |
| Vue 文件 | ≤ 500 行 | 抽 composable + 拆子组件 |
| 嵌套 | ≤ 4 层 | 提前 return / 抽方法 |
| 位置参数 | ≤ 5 个 | 封装对象 |
| 圈复杂度 | ≤ 15 | 拆分逻辑 |

---

## 分层铁律（后端）

**Controller** — 仅参数绑定 + `@Valid` + 调 Service + 封装 `R<T>`

- 禁止：业务逻辑 / `@Transactional` / `@Scheduled` / 注入 Mapper / 注入 JdbcTemplate / 发起异步
- 禁止：`Map<String, Object>` 接收或返回；入参用 DTO + `@Valid`，出参用 VO
- 禁止：手写 Map↔Entity 转换 / 硬编码枚举↔中文映射

**Service** — 单一职责，写操作必须 `@Transactional(rollbackFor = Exception.class)`

- 禁止：空 catch 块（最低 `log.warn`）/ 批量跳过不收集原因 / JdbcTemplate
- 禁止：`@Scheduled`（必须放 `task/` 或 `job/` 包 + ShedLock）

**Mapper** — SQL 统一 XML 维护

- 单表 CRUD → `BaseMapper<T>` + `LambdaQueryWrapper`
- 连表/复杂查询 → Mapper XML
- 禁止：`@Select` / `@Insert` 等注解 SQL / Controller/Service 中出现 SQL 字符串

---

## 安全铁律

- JWT 密钥可配，prod 无默认值（缺失启动失败）
- 密码 BCrypt；日志禁打 password / token / 身份证 / 手机号
- 禁止：Swagger / SpringDoc / Springfox 依赖
- 禁止：`xxx-all` 全量包（如 hutool-all）
- CORS 生产环境禁止 `allowedOriginPatterns=*` + `allowCredentials=true`
- 登录限流：Redis 滑窗 5次/min/IP + 连续失败锁 15min

---

## 前端铁律

- 响应已自动拆包（`return res.data`），禁止写 `.data`
- API 函数必须声明泛型，禁止 `<any>` 返回类型
- 必须配置 `app.config.errorHandler` + `window.onunhandledrejection`
- 数据字典：系统枚举 → `src/constants/` 集中维护；业务字典 → dict API + `useDict`
- 禁止：前端硬编码 `Record<string, string>` 字典映射
- 搜索框 debounce 300ms / 提交按钮 `:loading` 防重 / el-tree 禁 `default-expand-all`
- HTTP 错误按状态码归因（502="服务正在重启或维护中"，非"服务器内部错误"）
- 用 `<script setup lang="ts">`，禁用 Options API；新建组件遵守 SFC 顺序

---

## 数据规范

- 公共字段：`id BIGINT PRI | create_time | update_time | create_by | update_by | deleted TINYINT DEFAULT 0`
- DDL：utf8mb4_general_ci | 字段+表必须 COMMENT | IF NOT EXISTS | Flyway 管理
- 禁止：ENUM 类型（用 VARCHAR(30)）/ utf8 / 0900_ai_ci
- 单表索引 ≤ 6；高频查询 EXPLAIN 验索引

---

## Entity 映射铁律

- 所有持久化实体必须继承 `BaseEntity`（禁止手动重复定义 id/createTime/updateTime/createBy/updateBy/deleted）
- 所有实体必须声明 `@TableName("actual_table")`
- Java 字段名与 DB 列名必须语义一致（camelCase ↔ snake_case 自动映射）
- `@TableField` 仅允许 `exist=false`（非持久字段）；禁止 `@TableField("col")` 列名映射掩盖偏差
- 字段不一致时改 Java 字段名对齐 DB（优先），或 Flyway 迁移改 DB 列名
- VO/DTO/Command 放 `dto/` 或 `vo/` 包，禁止放 `domain/` 包

---

## 前后端契约铁律

- 前端 TS interface 必须与后端 Java VO/DTO 字段一一对应（名称、类型、可选性）
- 后端 VO/DTO 变更时，必须同步更新前端 `src/types/` 对应 interface
- 后端响应枚举字段直接透传 **code**（禁止 `Enum.getLabel()` 翻译）；前端用 `src/constants/` 映射 label
- 前端类型文件按后端模块组织：`src/types/{biz}/`

---

## 代码坏味道铁律

- 全链路禁止 `Map<String,Object>` / `JSONObject` / `Object` 作为方法签名入参或返回值（唯一例外：CrossModuleMapper 返回 Map 且立即转 VO）
- 同一状态字符串出现 ≥2 处 → 必须提取为常量类（`XxxStatus`）；业务阈值 → 配置表或 `@Value`
- 一个 ServiceImpl 只承担一个职责域，超过 2 个职责域必须拆分子服务
- 跨模块只通过 Service 接口或 CrossModuleMapper 访问，禁止注入外模块 Mapper/Entity
- 禁止空 catch 块（最低 `log.warn`）；批量操作失败必须收集原因返回调用方
- 禁止 Boolean flag 参数（拆为独立方法）；位置参数 ≤ 5 个（超出封装 DTO）
- `getXxx` 无副作用；`saveXxx` 不做额外查询；查询方法禁止包含写操作
- 详细规则见 `.trellis/spec/backend/code-smell-prevention/_index.md`

---

## 构建与启动

- 后端：`mvn clean package -DskipTests -pl {app}-admin -am -f {app}-backend/pom.xml` → `java -jar`（run_in_background）→ curl health
  - **`-am` 是铁律**：省略后 spring-boot repackage 嵌入 .m2 旧依赖 jar，新 Controller 静默 404 无任何启动错误
- 前端：`npm run dev`（run_in_background）
- 禁止：`spring-boot:run` / `mvn install`（写脏 .m2）/ `mvn package -pl xxx`（不带 -am）/ `cd xxx &&`（用 `-f`）/ 不查端口直接启动
- **Flyway**：admin 启动时自动 migrate 到最新 V，新 schema 变更走 `V{N}__{domain}_{desc}.sql`，禁手改表/禁改已部署 V 文件

---

## 多任务并行铁律

- **触发即开 Team**：跨 ≥2 个独立模块/层、≥4 文件独立编辑、研究+实现两类工作并存 → **默认**用 Agent Team 并行，**禁止**单线程顺序处理
- **Wave 分波**：Wave1（DDL+后端 research/implement 并发）→ Wave2（前端依赖后端 API 的并发）
- **研究/实现分离**：先 research agent 出结论 → 主线综合决策 → 再派 implement agent
- **同波无写冲突**：同一波内 agent 不得编辑同一文件；并行调用必须放同一条 assistant 消息内
- 详细规范见 `.trellis/spec/guides/parallel-execution-default.md`

---

## 详细规范（按需加载）

| 场景 | 规范文件 |
|---|---|
| 后端开发 | `.trellis/spec/backend/` 目录下各主题文件 |
| 坏味道防腐 | `.trellis/spec/backend/code-smell-prevention/_index.md` |
| 字典与关联字段策略 | `.trellis/spec/backend/dict-and-relation-strategy.md` |
| REST API 设计 | `.trellis/spec/backend/api-design.md` |
| 错误码体系 | `.trellis/spec/backend/error-code.md` |
| 后端测试策略 | `.trellis/spec/backend/test-strategy.md` |
| 前端开发 | `.trellis/spec/frontend/` 目录下各主题文件 |
| Vue SFC 写法 | `.trellis/spec/frontend/template-style.md` |
| Lint 规则（前/后端） | `.trellis/spec/frontend/lint-policy.md` + `.trellis/spec/backend/lint-policy.md` |
| Checkstyle 配置 | 项目根 `checkstyle.xml`（Maven Checkstyle plugin 直读） |
| 跨层特性 | `.trellis/spec/guides/cross-layer-thinking-guide.md` |
| 国际化（i18n） | `.trellis/spec/guides/i18n-strategy/_index.md` |
| 多任务并行作业 | `.trellis/spec/guides/parallel-execution-default.md` |
| 全栈开发流程（不 mock） | `.trellis/spec/guides/full-stack-workflow.md` |
| Git 工作流 + PR 规范 | `.trellis/spec/guides/git-workflow/_index.md` |
| 开发服启动/停止/健康检查 | `.trellis/spec/guides/dev-server-lifecycle-guide.md` |
| 构建与依赖治理 | `.trellis/spec/guides/build-dependency-governance-guide.md` |
| 生产部署 | `.trellis/spec/backend/prod-hardening.md` |
| 字符层规范 | 项目根 `.editorconfig` |

---

## Git 规范

- 仅用户要求时 commit；格式 `feat(module): 描述` 附 Co-Authored-By
- 不 force push main；不 amend 已推送 commit
