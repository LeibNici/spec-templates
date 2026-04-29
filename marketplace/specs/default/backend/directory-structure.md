# Backend Directory Structure

> 适用：Java 17 + Spring Boot 3.x + Maven 多模块

## Project Layout

```
{app-name}-backend/
  {app}-common/         # 统一响应 R<T>、BaseEntity、异常、常量枚举、工具
  {app}-framework/      # JWT、Security、Redis、WebMvc、日志切面
  {app}-integration/    # 外部系统适配器（interface + 真实 Impl）
  {app}-{biz}/          # 业务模块（可多个，只依赖 common + framework）
  {app}-admin/          # 启动入口，聚合所有模块
sql/                    # 仅历史脚本（新变更走 Flyway，见 database-guidelines/03-flyway-workflow.md）
```

> `{biz}` 是业务模块占位符（如 `order` / `inventory` / `user`），按业务域命名。

---

## Module Dependencies

- `common` — 无外部依赖，纯 POJO + 工具
- `framework` — 依赖 `common`，提供基础设施
- `{biz}` — 依赖 `common` + `framework`，**禁止**业务模块间直接依赖
- `integration` — 依赖 `common`，外部系统适配
- `admin` — 聚合层，启动入口

跨模块通信走 `ApplicationEvent` 或 admin 聚合层 Facade。

---

## Business Module Structure

每个业务模块标准目录：

```
{app}-{biz}/src/main/java/com/{org}/{biz}/
  controller/          # REST 接口（Query/Command 拆分）
  service/             # 接口定义
    impl/              # 实现类
  mapper/              # MyBatis-Plus Mapper 接口
  domain/              # 实体类（仅 Entity）
  dto/                 # 入参 DTO / Command
  vo/                  # 出参 VO
  task/                # 定时任务（@Scheduled + ShedLock）
  event/               # 领域事件
  constants/           # 模块常量

resources/mapper/{biz}/  # Mapper XML 文件
```

---

## Module Checklist

每个业务模块必须产出：

- [ ] `domain/` — Entity（继承 BaseEntity）
- [ ] `dto/` + `vo/` — 入参/出参对象
- [ ] `mapper/` — Mapper 接口 + XML
- [ ] `service/` — 接口 + impl
- [ ] `controller/` — REST 接口
- [ ] Flyway `V{N}__{biz}_xxx.sql` — DDL 脚本
- [ ] 前端 `views/{biz}/` + `api/{biz}.ts` + 路由

---

## Integration Module Structure

```
{app}-integration/src/main/java/com/{org}/integration/
  adapter/
    XxxAdapter.java          # interface
  impl/
    XxxAdapterImpl.java      # @Component 真实实现
```

- 不提供 Mock / Stub
- 未对接时软失败（log + 返回安全默认值）
- 测试凭据 `application-dev.yml` 注入；生产凭据走环境变量

---

## Forbidden Patterns

- 业务模块间直接 `@Autowired` 注入
- `common` 模块引入 Spring 注解（除 `@Component` 等基础注解）
- 工具方法散落在 Controller / Service（必须放 `common` 模块 `utils/`）
- 跨模块直接注入他人 Mapper / Entity（必须走 Service 接口或 CrossModuleMapper）
