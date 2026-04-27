# Backend Development Guidelines

> 适用于 **Java 17 + Spring Boot 3.x + MyBatis-Plus + MySQL 8 + Redis 7** 多模块项目
> 阈值采用"实战宽松档"（贴近 Sonar 默认 + IDEA 实战调高值），见 `quality-guidelines.md`

---

## Guidelines Index

| Guide | Scope |
|-------|-------|
| [Directory Structure](./directory-structure.md) | 多模块工程布局、模块依赖、业务模块标准目录 |
| [Quality Guidelines](./quality-guidelines.md) | 代码硬性上限、Controller/Service/Mapper 铁律、并发幂等、异步契约 |
| [Naming Conventions](./naming-conventions.md) | 类型/字段/方法/SQL 命名、Entity↔DB 语义一致、响应层枚举字段铁律 |
| [Database Guidelines](./database-guidelines.md) | SQL 归属、DDL 标准、Flyway 工作流、Entity 映射、聚合分页模板 |
| [Error Handling](./error-handling.md) | 异常体系、catch 块规则、批量错误收集、GlobalExceptionHandler |
| [Logging Guidelines](./logging-guidelines.md) | 绝对路径、JSON 格式、TraceId、敏感数据脱敏 |
| [Code Smell Prevention](./code-smell-prevention/_index.md) | 弱类型禁用、SRP、防腐层、静默跳过反模式、历史违规修正义务 |
| [Dict & Relation Strategy](./dict-and-relation-strategy.md) | 字典双轨制、关联字段存 ID 还是值、BaseEntity 审计字段约定 |
| [API Design](./api-design.md) | URL 风格、HTTP 方法语义、分页参数、批量操作、版本管理、幂等头 |
| [Error Code](./error-code.md) | 错误码格式、模块前缀、HTTP 与业务码双层、与 i18n 集成 |
| [Test Strategy](./test-strategy.md) | 测试分层、命名约定、覆盖率门禁、Testcontainers 用法 |
| [Prod Hardening](./prod-hardening.md) | 安全配置、容量公式、限流策略、读写分离 |
| [Lint Policy](./lint-policy.md) | Checkstyle / SpotBugs / PMD 规则意图清单（字面层防腐） |
| [Dependency Policy](./dependency-policy.md) | 依赖直接/传递禁用清单、maven-enforcer-plugin 配置、例外报备 |

---

## Pre-Development Checklist

Before writing any backend code, read these files based on your task:

- **All tasks**: `quality-guidelines.md` + `naming-conventions.md`
- **Refactor / cleanup tasks**: `code-smell-prevention/_index.md`
- **Database changes**: `database-guidelines.md` + `dict-and-relation-strategy.md`
- **新增业务表 / 关联字段 / 字典字段**: `dict-and-relation-strategy.md`
- **Error handling / exception flow**: `error-handling.md`
- **Logging changes**: `logging-guidelines.md`
- **Production config / deployment**: `prod-hardening.md`
- **New module**: `directory-structure.md`
- **Cross-layer feature**: Also read `../guides/`
- **Dependency / build config change**: `dependency-policy.md` + `../guides/build-dependency-governance-guide.md`

---

**Language**: 中英混排（术语英文，铁律中文）。
