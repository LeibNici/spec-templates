# Backend Development Guidelines

> 适用于 **Java 17 + Spring Boot 3.x + MyBatis-Plus + MySQL 8 + Redis 7** 多模块项目
> 阈值采用"实战宽松档"（贴近 Sonar 默认 + IDEA 实战调高值），见 `quality-guidelines.md`

---

## Applies To

- `{app}-backend/**`
- Spring Boot modules, MyBatis-Plus mappers, Flyway migrations, backend tests, deployment config.

---

## Pre-Development Checklist

Before writing any backend code, read these files based on your task:

- **All tasks**: `quality-guidelines.md` + `naming-conventions.md`
- **Refactor / cleanup tasks**: `code-smell-prevention/_index.md`
- **Database changes**: `database-guidelines/_index.md` + `dict-and-relation-strategy.md`
- **新增业务表 / 关联字段 / 字典字段**: `dict-and-relation-strategy.md`
- **Error handling / exception flow**: `error-handling.md`
- **Batch / import / sync / dispatch result**: `batch-result-observability.md`
- **Dev / test / mock / profile-specific code**: `dev-test-code-policy.md`
- **Logging changes**: `logging-guidelines.md`
- **Audit / operation log / trace table**: `audit-log-pattern.md` + `high-volume-tables/_index.md`
- **Production config / deployment**: `prod-hardening.md`
- **New module**: `directory-structure.md`
- **State lifecycle / approval flow / workflow status**: `state-transition-pattern.md`
- **Derived records must freeze master-data version**: `versioned-reference-pattern.md`
- **Cross-module notification after commit**: `domain-event-pattern.md`
- **External API / bridge / master-data sync integration**: `external-system-integration.md`
- **Current-row reads on versioned / hierarchical / tenant / soft-delete tables**: `database-guidelines/07-effective-row-filter.md`
- **Cross-layer feature**: also read `../shared/index.md` + `../guides/full-stack-workflow.md`
- **Dependency / build config change**: `dependency-policy.md` + `../guides/build-dependency-governance-guide.md`

---

## Quality Checklist

- [ ] Controller, Service, Mapper, DTO, VO, and SQL ownership follow the relevant backend specs.
- [ ] Transactional methods declare rollback behavior where required by `quality-guidelines.md`.
- [ ] State transitions are centralized when lifecycle rules are non-trivial.
- [ ] Derived records explicitly choose reference, snapshot, or versioned-reference semantics.
- [ ] Batch-like flows expose counts, failure details, and metrics instead of silent skips.
- [ ] Dev/test/profile-specific code follows the same layer and data rules as production code.
- [ ] Current-view SQL on stateful tables includes effective-row predicates.
- [ ] Database changes include Flyway/DDL review and Entity mapping checks when applicable.
- [ ] Same-process cross-module side effects use after-commit events when fire-and-forget is intended.
- [ ] External system calls are behind adapters with request id, timeout, idempotency, and error mapping.
- [ ] Audit/operation logs are after-commit, sanitized, and designed as high-volume tables when needed.
- [ ] API shape, IDs, timestamps, enums, and errors match `../shared/`.
- [ ] Tests or targeted verification match the blast radius of the change.

---

## Spec Map

| Guide | Scope | Status |
|-------|-------|---|
| [Directory Structure](./directory-structure.md) | 多模块工程布局、模块依赖、业务模块标准目录 | Filled |
| [Quality Guidelines](./quality-guidelines.md) | 代码硬性上限、Controller/Service/Mapper 铁律、并发幂等、异步契约 | Filled |
| [Naming Conventions](./naming-conventions.md) | 类型/字段/方法/SQL 命名、Entity↔DB 语义一致、响应层枚举字段铁律 | Filled |
| [Database Guidelines](./database-guidelines/_index.md) | SQL 归属、DDL 标准、Flyway 工作流、Entity 映射、聚合分页模板 | Filled |
| [Error Handling](./error-handling.md) | 异常体系、catch 块规则、批量错误收集、GlobalExceptionHandler | Filled |
| [Logging Guidelines](./logging-guidelines.md) | 绝对路径、JSON 格式、TraceId、敏感数据脱敏 | Filled |
| [Code Smell Prevention](./code-smell-prevention/_index.md) | 弱类型禁用、SRP、防腐层、静默跳过反模式、历史违规修正义务 | Filled |
| [Dict & Relation Strategy](./dict-and-relation-strategy.md) | 字典双轨制、关联字段存 ID 还是值、BaseEntity 审计字段约定 | Filled |
| [API Design](./api-design.md) | URL 风格、HTTP 方法语义、分页参数、批量操作、版本管理、幂等头 | Filled |
| [Error Code](./error-code.md) | 错误码格式、模块前缀、HTTP 与业务码双层、与 i18n 集成 | Filled |
| [Batch Result Observability](./batch-result-observability.md) | 批处理 / 导入 / 同步 / 分发的成功、跳过、失败明细与 metrics | Filled |
| [Dev/Test Code Policy](./dev-test-code-policy.md) | dev/test/mock/profile 代码同规，禁止启动钩子假数据和绕层写表 | Filled |
| [State Transition Pattern](./state-transition-pattern.md) | 多状态对象的集中流转表、Action、历史状态 normalize、产出门禁 | Filled |
| [Versioned Reference Pattern](./versioned-reference-pattern.md) | Reference / Snapshot / Versioned Reference 选型与历史版本冻结 | Filled |
| [Domain Event Pattern](./domain-event-pattern.md) | 同进程跨模块 AFTER_COMMIT 事件、listener 幂等与失败处理 | Filled |
| [External System Integration](./external-system-integration.md) | 外部系统 Adapter 边界、requestId、幂等、超时、同步批量写入 | Filled |
| [Audit Log Pattern](./audit-log-pattern.md) | 操作审计字段、AFTER_COMMIT 写入、脱敏、高写入表治理 | Filled |
| [Test Strategy](./test-strategy/_index.md) | 测试分层、命名约定、覆盖率门禁、Testcontainers 用法 | Filled |
| [Prod Hardening](./prod-hardening.md) | 安全配置、容量公式、限流策略、读写分离 | Filled |
| [Topology-Agnostic](./topology-agnostic.md) | 部署形态无关代码规范、ShedLock、Sentinel、健康检查、连接池超时（Active-Passive + Witness 拓扑） | Filled |
| [High-Volume Tables](./high-volume-tables/_index.md) | 日志/流水类表治理：冗余列、月分区、AOP 写入、三层归档（热/温/冷） | Filled |
| [Lint Policy](./lint-policy.md) | Checkstyle / SpotBugs / PMD 规则意图清单（字面层防腐） | Filled |
| [Dependency Policy](./dependency-policy.md) | 依赖直接/传递禁用清单、maven-enforcer-plugin 配置、例外报备 | Filled |

---

**Language**: 中英混排（术语英文，铁律中文）。
