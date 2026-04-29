# Test Strategy

> 后端测试规范。覆盖测试分层、命名约定、覆盖率门禁、Testcontainers 用法、Mock 边界。
> 与 `quality-guidelines.md` §测试与 Mock 配套（保留 spring-boot-starter-test 依赖是基础前提）。

→ See `quality-guidelines.md` §测试与 Mock for the high-level rules.

---

## Pattern → File Mapping

| Topic | File |
|---|---|
| 一、测试分层 | [01-layering.md](./01-layering.md) |
| 二、命名约定 | [02-naming.md](./02-naming.md) |
| 三、单元测试（70%） | [03-unit.md](./03-unit.md) |
| 四、切片测试（20%） | [04-slice.md](./04-slice.md) |
| 五、集成测试（10%） | [05-integration.md](./05-integration.md) |
| 六、覆盖率门禁 | [06-coverage.md](./06-coverage.md) |
| 七、Mock 策略 | [07-mock.md](./07-mock.md) |
| 八、测试数据隔离 | [08-data-isolation.md](./08-data-isolation.md) |
| 九、测试执行策略 | [09-execution.md](./09-execution.md) |
| 十、Forbidden Patterns + Code Review Checklist + 相关 spec | [10-forbidden-and-review.md](./10-forbidden-and-review.md) |
